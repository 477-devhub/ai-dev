/* 477 blind human grading UI (System A / System B).
 * Loads only: blind_manifest.json, review/data/rubric.json, cases/ITEM_XX/{system_A,system_B,reference}.json, /video/...
 * Never loads reveal_map_private.json or other reviewers' grades. Scores are entered only by the reviewer.
 */
'use strict';

const PACK = 'p0_vs_p1_v1';
const METRICS = ['event_understanding', 'temporal_understanding', 'evidence_grounding', 'uncertainty_handling'];
const NOTE_KEY = { event_understanding: 'event', temporal_understanding: 'temporal', evidence_grounding: 'evidence', uncertainty_handling: 'uncertainty' };
const SYSTEMS = ['System_A', 'System_B'];
const SRC_HELP = {
  HV: 'human_verified_observation: 사람이 원본 영상으로 확인한 사실',
  PR: 'project_defined_reference: 477 프로젝트 정의 reference',
  CS: 'project clip-selection 기록',
  SA: 'AI Hub source annotation — 참고 맥락, 정답 아님',
  DER: 'source/clip-selection 시각을 clip 상대시간으로 환산한 근사치 (영상으로 확인)',
};

let manifest, rubric, reviewer, state;
const cache = {};
let view = { item: null, system: 'System_A' };

// ------------------------------------------------------------------ helpers
function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'class') el.className = v;
    else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else if (k === 'html') el.innerHTML = v;
    else el.setAttribute(k, v === true ? '' : v);
  }
  for (const kid of kids.flat()) {
    if (kid === null || kid === undefined || kid === false) continue;
    el.appendChild(typeof kid === 'string' || typeof kid === 'number' ? document.createTextNode(String(kid)) : kid);
  }
  return el;
}
const fmt = (x, d = 2) => (x === null || x === undefined ? 'n/a' : Number(x).toFixed(d));
function toast(msg) { const t = document.getElementById('toast'); t.textContent = msg; t.hidden = false; clearTimeout(toast._t); toast._t = setTimeout(() => (t.hidden = true), 2600); }
async function getJSON(url) { const r = await fetch(url, { cache: 'no-store' }); if (!r.ok) throw new Error(url + ' ' + r.status); return r.json(); }
function srcBadges(src) {
  if (!src) return null;
  return src.split('+').map(s => { const key = s.replace(/\(.*\)/, ''); return h('span', { class: 'src', title: SRC_HELP[key] || s }, s); });
}

// ------------------------------------------------------------------ state
const storeKey = () => `477gp:${PACK}:${reviewer}`;
function blankAssessment(item) {
  const a = { event_understanding: null, temporal_understanding: null, evidence_grounding: null, uncertainty_handling: null,
    overclaim_flags: [], notes: { event: '', temporal: '', evidence: '', uncertainty: '', overall: '' },
    video_confirmed: false, evidence_compared: false, submitted: false, submitted_at: null };
  const task = taskOf(item);
  if (task === 'attention') { a.ranking = { top1_correct: null, full_order_correct: null }; a.camera_helper = {}; }
  if (task === 'multi_camera') a.multiview = { second_view_added: null, assumed_sync: null, asserted_cross_camera_identity: null };
  return a;
}
function taskOf(item) { return manifest.items.find(x => x.item_id === item).task; }
function loadState() {
  try { const raw = localStorage.getItem(storeKey()); if (raw) state = JSON.parse(raw); } catch (e) { state = null; }
  if (!state || state.pack_version !== PACK) state = { pack_version: PACK, reviewer_id: reviewer, items: {} };
  for (const it of manifest.items) {
    state.items[it.item_id] = state.items[it.item_id] || {};
    for (const s of SYSTEMS) state.items[it.item_id][s] = Object.assign(blankAssessment(it.item_id), state.items[it.item_id][s] || {});
  }
}
function save() { try { localStorage.setItem(storeKey(), JSON.stringify(state)); } catch (e) { toast('localStorage 저장 실패 — Export를 사용하세요'); } renderTop(); renderNav(); }
const A = (item, sys) => state.items[item][sys];
const total = a => METRICS.every(m => a[m] !== null) ? METRICS.reduce((s, m) => s + a[m], 0) : null;
function countSubmitted() { let n = 0; for (const it of manifest.items) for (const s of SYSTEMS) if (A(it.item_id, s).submitted) n++; return n; }

function exportObj() {
  const out = { pack_version: PACK, reviewer_id: reviewer, exported_at: new Date().toISOString(),
    progress: { submitted: countSubmitted(), total: manifest.total_assessments } };
  for (const it of manifest.items) {
    out[it.item_id] = {};
    for (const s of SYSTEMS) { const a = JSON.parse(JSON.stringify(A(it.item_id, s))); a.total = total(a); out[it.item_id][s] = a; }
  }
  return out;
}

// ------------------------------------------------------------------ start
async function init() {
  const params = new URLSearchParams(location.search);
  reviewer = params.get('reviewer');
  manifest = await getJSON('/blind_manifest.json');
  rubric = await getJSON('/review/data/rubric.json');
  if (!reviewer || !/^[A-Za-z0-9_-]{1,40}$/.test(reviewer)) return renderStart();
  loadState();
  view.item = (state.current && state.current.item) || manifest.items[0].item_id;
  view.system = (state.current && state.current.system) || 'System_A';
  document.getElementById('btnExport').onclick = doExport;
  document.getElementById('btnSave').onclick = () => saveServer(true);
  document.getElementById('fileImport').onchange = doImport;
  document.getElementById('btnGuide').onclick = showGuide;
  document.getElementById('modalClose').onclick = () => (document.getElementById('modal').hidden = true);
  renderTop(); renderNav(); await renderItem();
}

function renderStart() {
  document.getElementById('nav').hidden = true;
  const input = h('input', { type: 'text', value: 'reviewer_01', id: 'rid' });
  const main = document.getElementById('main');
  main.replaceChildren(h('div', { class: 'card start' },
    h('h2', {}, 'Reviewer ID 입력'),
    h('p', {}, '영문/숫자/_/- 만 사용합니다 (예: reviewer_01, reviewer_02). 같은 브라우저에서도 Reviewer ID별로 따로 저장됩니다. 다른 reviewer의 결과는 볼 수 없습니다.'),
    input,
    h('p', {}, h('button', { class: 'primary', onclick: () => {
      const v = input.value.trim();
      if (!/^[A-Za-z0-9_-]{1,40}$/.test(v)) return toast('ID 형식이 올바르지 않습니다');
      location.search = '?reviewer=' + encodeURIComponent(v);
    } }, '채점 시작'))));
}

function renderTop() {
  document.getElementById('reviewerBox').replaceChildren(h('span', {}, 'Reviewer: ', h('b', {}, reviewer)));
  document.getElementById('progressBox').replaceChildren(h('span', {}, 'Progress: ', h('b', {}, `${countSubmitted()} / ${manifest.total_assessments}`), ' assessments'));
}

function renderNav() {
  const nav = document.getElementById('nav');
  nav.replaceChildren(h('div', { class: 'muted', style: 'margin-bottom:8px' }, 'ITEM 목록'),
    ...manifest.items.map(it => {
      const chips = SYSTEMS.map(s => {
        const a = A(it.item_id, s);
        const started = METRICS.some(m => a[m] !== null) || a.notes.overall;
        return h('span', { class: 'chip ' + (a.submitted ? 'done' : started ? 'prog' : '') }, s.replace('System_', '') + (a.submitted ? ' ✓' : ''));
      });
      return h('button', { class: 'navitem' + (view.item === it.item_id ? ' active' : ''), onclick: () => go(it.item_id, firstOpen(it.item_id)) },
        h('div', {}, h('b', {}, it.item_id), ' ', h('span', { class: 'muted' }, it.set)), h('div', { class: 'chips' }, chips));
    }));
}
function firstOpen(item) { return A(item, 'System_A').submitted && !A(item, 'System_B').submitted ? 'System_B' : 'System_A'; }
async function go(item, sys) {
  const same = view.item === item && document.getElementById('assessArea');
  view.item = item; view.system = sys; state.current = { item, system: sys }; save();
  if (same) {
    const it = manifest.items.find(x => x.item_id === item);
    const fresh = renderAssessmentArea(it, await loadCase(item));
    document.getElementById('assessArea').replaceWith(fresh);
    fresh.scrollIntoView({ behavior: 'smooth', block: 'start' });
    return;
  }
  await renderItem(); window.scrollTo(0, 0);
}
function markSel(input) {
  const group = input.closest('.metric, .card');
  group.querySelectorAll(`input[name="${input.name}"]`).forEach(r => r.closest('.opt') && r.closest('.opt').classList.toggle('sel', r.checked));
}
function updTotal(a) { const b = document.getElementById('totalBox'); if (b) b.textContent = total(a) === null ? '— / 8' : `${total(a)} / 8`; }

// ------------------------------------------------------------------ item view
async function loadCase(item) {
  if (!cache[item]) {
    const [ref, a, b] = await Promise.all([getJSON(`/cases/${item}/reference.json`), getJSON(`/cases/${item}/system_A.json`), getJSON(`/cases/${item}/system_B.json`)]);
    cache[item] = { ref, System_A: a, System_B: b };
  }
  return cache[item];
}

async function renderItem() {
  const it = manifest.items.find(x => x.item_id === view.item);
  const c = await loadCase(view.item);
  const ref = c.ref;
  const main = document.getElementById('main');
  main.replaceChildren(
    h('div', { class: 'card' },
      h('div', { class: 'itemhead' }, h('h2', {}, `${it.item_id} — ${ref.set}${ref.condition ? ' · ' + ref.condition : ''}`),
        h('span', {}, 'Progress: ', h('b', {}, `${countSubmitted()} / ${manifest.total_assessments}`), ' assessments')),
      h('div', { class: 'muted' }, `Task: ${it.task} · Cameras: ${it.cameras.map(x => x.camera).join(', ')} · ${ref.sampling_note}`)),
    renderVideos(it, ref),
    renderReference(ref),
    renderAssessmentArea(it, c));
}

function renderVideos(it, ref) {
  return h('div', { class: 'card' }, h('h3', {}, 'CCTV Video'),
    h('div', { class: 'muted', style: 'margin-bottom:6px' }, '영상 위 시간은 clip 기준 초입니다. 여러 번 보고, 필요한 구간은 seek/속도 조절을 사용하세요.'),
    h('div', { class: 'videos' }, it.cameras.map(cam => {
      const v = h('video', { src: cam.video_url, controls: true, preload: 'metadata', playsinline: true });
      const tdisp = h('span', { class: 'muted' }, 't = 0.0s');
      v.addEventListener('timeupdate', () => (tdisp.textContent = `t = ${v.currentTime.toFixed(1)}s`));
      const speeds = [0.25, 0.5, 1, 2].map(r => h('button', { type: 'button', onclick: () => (v.playbackRate = r) }, r + 'x'));
      const step = d => h('button', { type: 'button', onclick: () => { v.pause(); v.currentTime = Math.max(0, v.currentTime + d); } }, (d > 0 ? '+' : '') + d + 's');
      return h('div', { class: 'videobox' }, h('div', { class: 'vlabel' }, cam.camera), v,
        h('div', { class: 'vctrl' }, tdisp, ...speeds, step(-1), step(-0.2), step(0.2), step(1)));
    })),
    h('details', { open: true }, h('summary', {}, '영상에서 먼저 확인할 부분'), h('ul', {}, ref.watch_first.map(x => h('li', {}, x)))));
}

function refList(items, ordered) {
  return h(ordered ? 'ol' : 'ul', { class: ordered ? 'timeline' : '' }, items.map(x => typeof x === 'string' ? h('li', {}, x) : h('li', {}, x.text, srcBadges(x.src))));
}

function renderReference(ref) {
  return h('div', { class: 'card' },
    h('h3', {}, 'Reviewer Reference ', h('span', { class: 'muted', style: 'font-weight:400' }, '(private ground truth 기반 · 사람 reviewer 전용)')),
    h('div', { class: 'core' }, h('b', {}, '핵심 observable 사건: '), ref.core_observable_event),
    h('div', { class: 'refgrid' },
      h('div', { class: 'refbox obs' }, h('h4', {}, 'OBSERVABLE REFERENCE — 영상에서 확인되는 사실'), refList(ref.observable_reference)),
      h('div', { class: 'refbox unc' }, h('h4', {}, 'MUST REMAIN UNCERTAIN — 영상만으로 확정할 수 없는 것'), refList(ref.must_remain_uncertain))),
    h('div', { class: 'card', style: 'margin-top:12px' }, h('h3', {}, 'Critical temporal sequence (핵심 시간 순서)'), refList(ref.critical_temporal_sequence, true)),
    h('details', {}, h('summary', {}, 'Evidence that should matter / Known ambiguity'),
      h('b', {}, 'Evidence that should matter'), refList(ref.evidence_that_matters),
      h('b', {}, 'Known ambiguity'), refList(ref.known_ambiguity)),
    h('details', {}, h('summary', {}, 'Strong answer should capture / must NOT assert'),
      h('b', {}, 'What a strong answer should capture'), refList(ref.strong_answer_should_capture),
      h('b', {}, 'What an answer must NOT assert'), refList(ref.must_not_assert)),
    h('details', {}, h('summary', {}, 'prediction에서 중점적으로 볼 부분 / 흔히 하는 착각'),
      h('b', {}, '중점적으로 볼 부분'), refList(ref.focus_fields),
      h('b', {}, '흔히 하는 착각'), refList(ref.common_mistakes)),
    h('details', {}, h('summary', {}, 'Source dataset label (context only — NOT the grading answer)'),
      h('div', { class: 'refbox ctx' }, h('div', {}, h('b', {}, ref.source_label_context.label)), h('div', {}, ref.source_label_context.note))),
    ref.aggregation_rule ? h('details', {}, h('summary', {}, 'ITEM_04 카메라별 보조 판단 방법'), h('div', { class: 'expl' }, ref.aggregation_rule)) : null,
    h('div', { class: 'muted', style: 'margin-top:8px;font-size:12px' }, '출처 태그: HV=사람 확인 사실, PR=프로젝트 reference, CS=clip 선택 기록, SA=source annotation(참고), DER=시각 환산 근사치. 태그에 마우스를 올리면 설명이 보입니다.'));
}

// ------------------------------------------------------------------ assessment area
function renderAssessmentArea(it, c) {
  const item = it.item_id;
  const aDone = A(item, 'System_A').submitted;
  const tabs = h('div', { class: 'tabs' }, SYSTEMS.map(s => {
    const locked = s === 'System_B' && !aDone;
    return h('button', { type: 'button', class: 'tab' + (view.system === s ? ' active' : ''), disabled: locked,
      title: locked ? 'System A를 먼저 제출하세요' : '', onclick: () => go(item, s) },
      s.replace('_', ' ') + (A(item, s).submitted ? ' ✓' : locked ? ' 🔒' : ''));
  }));
  const sys = view.system;
  if (sys === 'System_B' && !aDone) {
    return h('div', { class: 'card', id: 'assessArea' }, tabs, h('div', { class: 'locked' }, 'System A를 먼저 채점·제출하면 System B가 열립니다 (순차 grading으로 상대 비교 bias를 줄입니다).'));
  }
  const pred = c[sys].prediction;
  return h('div', { class: 'card', id: 'assessArea' }, tabs,
    h('div', { class: 'muted', style: 'margin-bottom:8px' }, `${sys.replace('_', ' ')}를 채점 중입니다. 다른 시스템의 점수는 표시되지 않습니다. 각 prediction은 절대평가하세요.`),
    h('div', { class: 'gradewrap' },
      h('div', { class: 'pred' }, h('h3', {}, `${sys.replace('_', ' ')} — Prediction`), renderPrediction(it.task, pred)),
      h('div', {}, renderForm(it, c, sys, pred))));
}

function renderSingle(p) {
  const r = p.risk || {};
  return h('div', {},
    h('div', { class: 'field' }, h('div', { class: 'label' }, 'Event'), h('div', { class: 'event' }, p.event_type)),
    h('div', { class: 'field' }, h('div', { class: 'label' }, 'Incident?'), h('span', { class: 'badge ' + (p.is_incident ? 'yes' : 'no') }, p.is_incident ? 'true' : 'false')),
    h('div', { class: 'field' }, h('div', { class: 'label' }, 'Risk (모델 예측값 — 정답 숫자 없음)'),
      ['severity', 'imminence', 'exposure', 'persistence'].map(k => h('div', { class: 'riskrow' }, h('span', {}, k),
        h('div', { class: 'bar' }, h('span', { style: `width:${Math.round((r[k] || 0) * 100)}%` })), h('span', {}, fmt(r[k]))))),
    h('div', { class: 'field' }, h('div', { class: 'label' }, 'Confidence'), h('span', {}, fmt(p.confidence)), h('span', { class: 'notgraded' }, '  · 채점 대상 아님 (높다고 점수 올리지 않기)')),
    h('div', { class: 'field' }, h('div', { class: 'label' }, 'Temporal summary'), h('div', {}, p.temporal_summary)),
    h('div', { class: 'field' }, h('div', { class: 'label' }, 'Evidence (observations)'), obsTable(p.observations)),
    h('div', { class: 'field' }, h('div', { class: 'label' }, 'Reason'), h('div', {}, p.reason)),
    h('div', { class: 'field' }, h('div', { class: 'label' }, 'Uncertainties'), h('ul', {}, (p.uncertainties || []).map(u => h('li', {}, u)))),
    h('div', { class: 'field' }, h('div', { class: 'label' }, 'Human Review'), h('span', {}, String(p.human_review_required)), h('span', { class: 'notgraded' }, '  · 채점 대상 아님')));
}
function obsTable(obs) {
  return h('table', { class: 'obs' }, h('tr', {}, h('th', {}, 'camera'), h('th', {}, 't (s)'), h('th', {}, 'description')),
    (obs || []).map(o => h('tr', {}, h('td', {}, o.camera), h('td', {}, fmt(o.timestamp_sec, 1)), h('td', {}, o.description))));
}
function renderPrediction(task, p) {
  let body;
  if (task === 'attention') {
    const q = [...p.attention_queue].sort((a, b) => a.rank - b.rank);
    body = h('div', {},
      h('div', { class: 'field' }, h('div', { class: 'label' }, 'Attention queue'),
        h('table', { class: 'obs' }, h('tr', {}, h('th', {}, 'rank'), h('th', {}, 'camera'), h('th', {}, 'reason')),
          q.map(x => h('tr', {}, h('td', {}, x.rank), h('td', {}, h('b', {}, x.camera)), h('td', {}, x.reason))))),
      p.assessments.map(a => h('details', { open: true }, h('summary', {}, `Assessment — ${a.camera}`), h('div', { style: 'padding:6px 0 6px 10px;border-left:3px solid #e5e7eb' }, renderSingle(a.assessment)))));
  } else if (task === 'multi_camera') {
    body = h('div', {}, renderSingle(p),
      h('div', { class: 'field' }, h('div', { class: 'label' }, 'Same incident?'), h('span', { class: 'badge ' + (p.same_incident ? 'yes' : 'no') }, String(p.same_incident))),
      h('div', { class: 'field' }, h('div', { class: 'label' }, 'Camera evidence'),
        Object.entries(p.camera_evidence).map(([cam, obs]) => h('div', {}, h('b', {}, cam), obsTable(obs)))),
      h('div', { class: 'field' }, h('div', { class: 'label' }, 'Cross-camera summary'), h('div', {}, p.cross_camera_summary)),
      h('div', { class: 'field' }, h('div', { class: 'label' }, 'Additional information from second view'), h('ul', {}, (p.additional_information_from_second_view || []).map(x => h('li', {}, x)))));
  } else body = renderSingle(p);
  return h('div', {}, body, h('details', {}, h('summary', {}, 'Raw JSON 보기'), h('pre', { class: 'raw' }, JSON.stringify(p, null, 2))));
}

// ------------------------------------------------------------------ grading form
function predStrings(p) { const out = []; (function walk(v) { if (typeof v === 'string') out.push(v); else if (Array.isArray(v)) v.forEach(walk); else if (v && typeof v === 'object') Object.values(v).forEach(walk); })(p); return out; }

function renderForm(it, c, sys, pred) {
  const item = it.item_id, a = A(item, sys), ref = c.ref;
  const ro = a.submitted;
  const wrap = h('div', {});
  if (ro) wrap.append(h('div', { class: 'submitted' }, `제출 완료 (${a.submitted_at || ''}). 총점 ${total(a)}/8. `,
    h('button', { type: 'button', onclick: () => { a.submitted = false; a.submitted_at = null; save(); go(item, sys); } }, '수정하려면 다시 열기')));
  wrap.append(h('div', { class: 'reminder' }, h('b', {}, 'Score this dimension independently. '), 'A wrong event label does not automatically mean evidence grounding is 0. ',
    h('br'), 'confidence 값과 human_review_required는 채점 대상이 아닙니다. source label 단어 일치로 점수를 주지 마세요.'));

  for (const m of METRICS) wrap.append(metricCard(it, ref, a, m, ro));
  wrap.append(h('div', { class: 'card' }, h('span', {}, 'Total (자동 합산): '), h('span', { class: 'total', id: 'totalBox' }, total(a) === null ? '— / 8' : `${total(a)} / 8`)));
  if (it.task === 'attention') wrap.append(rankingCard(ref, a, pred, ro));
  if (it.task === 'multi_camera') wrap.append(multiviewCard(ref, a, ro));
  wrap.append(flagsCard(a, pred, ro));
  wrap.append(h('div', { class: 'card' }, h('h3', {}, 'Overall reviewer note (optional)'),
    h('textarea', { disabled: ro, oninput: e => { a.notes.overall = e.target.value; save(); } }, a.notes.overall)));
  const errBox = h('div', { class: 'errors' });
  const cb = (key, label) => h('label', {}, h('input', { type: 'checkbox', disabled: ro, checked: a[key], onchange: e => { a[key] = e.target.checked; save(); } }), ' ', label);
  wrap.append(h('div', { class: 'card checks' }, h('h3', {}, '제출 전 확인 (필수)'),
    cb('video_confirmed', '실제 영상을 확인했습니다.'), cb('evidence_compared', 'prediction의 evidence와 영상을 비교했습니다.'),
    ro ? null : h('button', { type: 'button', class: 'primary', style: 'margin-top:8px', onclick: () => submit(it, sys, pred, errBox) }, `${sys.replace('_', ' ')} 제출`), errBox));
  return wrap;
}

function metricCard(it, ref, a, m, ro) {
  const g = rubric.general_rubric[m], spec = ref.metrics[m];
  const card = h('div', { class: 'metric', id: 'metric_' + m });
  const opts = ['2', '1', '0'].map(s => {
    const sel = a[m] === Number(s);
    return h('label', { class: 'opt' + (sel ? ' sel' : '') },
      h('input', { type: 'radio', name: m, value: s, checked: sel, disabled: ro, onchange: e => { a[m] = Number(s); save(); markSel(e.target); updTotal(a); } }),
      h('div', {}, h('span', { class: 'score' }, s), ' ', h('span', { class: 'gen' }, g.short[s]), h('div', { class: 'spec' }, `이 ITEM: ${spec[s]}`)));
  });
  const expl = h('details', {}, h('summary', {}, '자세한 기준 펼치기'),
    h('div', { class: 'expl' }, h('b', {}, `Reviewer tip (${it.item_id})`), spec.tip,
      h('b', {}, '① 2점을 주는 최소 조건'), g.two_min, h('b', {}, '② 1점을 주는 상황'), g.one_when,
      h('b', {}, '③ 0점을 주는 상황'), g.zero_when, h('b', {}, '④ 흔히 헷갈리는 경계 사례'), g.boundary));
  card.append(h('h3', {}, g.title), h('div', { class: 'mq' }, g.question), ...opts, expl);
  if (it.task === 'attention') card.append(helperRow(it, a, m, ro));
  card.append(h('div', { style: 'margin-top:6px' }, h('div', { class: 'muted', style: 'font-size:12px' }, '왜 이 점수를 줬는지 (optional)'),
    h('textarea', { disabled: ro, oninput: e => { a.notes[NOTE_KEY[m]] = e.target.value; save(); } }, a.notes[NOTE_KEY[m]])));
  return card;
}

function helperRow(it, a, m, ro) {
  a.camera_helper[m] = a.camera_helper[m] || {};
  const hh = a.camera_helper[m];
  const cams = it.cameras.map(x => x.camera);
  const sumBox = h('span', {});
  const upd = () => {
    const vals = cams.map(c => hh[c]).filter(v => v !== undefined && v !== null && v !== '');
    if (vals.length < cams.length) { sumBox.textContent = '카메라별 값을 모두 고르면 합계가 표시됩니다.'; return; }
    const s = vals.reduce((x, y) => x + Number(y), 0);
    sumBox.textContent = `합계 ${s}/6 → 기준표상 ${s >= 5 ? '2점' : s >= 2 ? '1점' : '0점'} 범위 (참고용; 최종 점수는 위에서 직접 선택)`;
  };
  const row = h('div', { class: 'helper' }, h('b', {}, '카메라별 보조 판단 (선택):'),
    cams.map(c => h('span', {}, c + ' ', h('select', { disabled: ro, onchange: e => { hh[c] = e.target.value === '' ? null : Number(e.target.value); save(); upd(); } },
      ['', '2', '1', '0'].map(v => h('option', { value: v, selected: String(hh[c] ?? '') === v }, v === '' ? '–' : v))))), sumBox);
  upd();
  return row;
}

function rankingCard(ref, a, pred, ro) {
  const r = ref.ranking;
  const order = [...pred.attention_queue].sort((x, y) => x.rank - y.rank).map(x => x.camera);
  const yn = (key, label, rule) => h('div', { style: 'margin:8px 0' }, h('b', {}, label), h('div', { class: 'muted', style: 'font-size:12px' }, rule),
    ['yes', 'no'].map(v => h('label', { style: 'margin-right:14px' }, h('input', { type: 'radio', name: 'rk_' + key, disabled: ro, checked: a.ranking[key] === v,
      onchange: () => { a.ranking[key] = v; save(); } }), ' ', v)));
  return h('div', { class: 'card', id: 'rankingCard' }, h('h3', {}, 'SET04 Attention Ranking (4-metric 점수와 별도)'),
    h('div', { class: 'reminder' }, h('b', {}, r.notice)),
    h('div', {}, 'Reference order: ', h('b', {}, r.reference_order.join(' > '))),
    h('ul', {}, r.rationale.map(x => h('li', {}, `${x.camera}: ${x.text}`, srcBadges(x.src)))),
    h('div', {}, 'This system\'s queue: ', h('b', {}, order.join(' > '))),
    yn('top1_correct', 'Top-1 Correct?', r.top1_rule), yn('full_order_correct', 'Full Order Correct?', r.full_order_rule),
    h('div', { class: 'muted', style: 'font-size:12px' }, r.independence_note));
}

function multiviewCard(ref, a, ro) {
  const q = ref.multiview_questions;
  const keys = { second_view_added: 'second_view_added', assumed_sync: 'assumed_sync', asserted_identity: 'asserted_cross_camera_identity' };
  return h('div', { class: 'card', id: 'multiviewCard' }, h('h3', {}, 'Multi-camera qualitative checks (main 0–8 점수와 별개)'),
    Object.entries(keys).map(([qk, field]) => h('div', { style: 'margin:10px 0' }, h('b', {}, q[qk].question),
      Object.entries(q[qk].options).map(([opt, desc]) => h('label', { class: 'opt' + (a.multiview[field] === opt ? ' sel' : '') },
        h('input', { type: 'radio', name: 'mv_' + field, disabled: ro, checked: a.multiview[field] === opt, onchange: e => { a.multiview[field] = opt; save(); markSel(e.target); } }),
        h('div', {}, h('b', {}, opt), ' — ', desc))))),
    h('div', { class: 'muted', style: 'font-size:12px' }, ref.multiview_increment_note));
}

function flagsCard(a, pred, ro) {
  const strings = predStrings(pred);
  const list = h('div', {});
  const draw = () => {
    list.replaceChildren(...a.overclaim_flags.map((f, i) => {
      const qc = h('div', {});
      const check = () => {
        const q = (f.quote || '').trim();
        qc.className = 'qcheck ' + (q && strings.some(s => s.includes(q)) ? 'ok' : 'bad');
        qc.textContent = !q ? '인용문을 입력하세요' : strings.some(s => s.includes(q)) ? '✓ prediction에 그대로 존재하는 문장입니다' : '⚠ prediction에서 정확히 일치하는 문장을 찾지 못했습니다 (복사-붙여넣기 권장)';
      };
      check();
      return h('div', { class: 'flag' },
        h('select', { disabled: ro, onchange: e => { f.type = e.target.value; save(); } },
          h('option', { value: '' }, '— flag 종류 선택 —'),
          Object.entries(rubric.overclaim_flags).map(([k, d]) => h('option', { value: k, selected: f.type === k }, `${k} — ${d}`))),
        h('div', { class: 'muted', style: 'font-size:12px;margin-top:6px' }, 'exact_output_quote (prediction 문장을 그대로 복사)'),
        h('textarea', { disabled: ro, oninput: e => { f.quote = e.target.value; save(); check(); } }, f.quote || ''), qc,
        h('div', { class: 'muted', style: 'font-size:12px;margin-top:6px' }, 'why_unsupported (왜 영상/Reference가 뒷받침하지 않는지)'),
        h('textarea', { disabled: ro, oninput: e => { f.reason = e.target.value; save(); } }, f.reason || ''),
        ro ? null : h('button', { type: 'button', style: 'margin-top:6px', onclick: () => { a.overclaim_flags.splice(i, 1); save(); draw(); } }, '이 flag 삭제'));
    }));
  };
  draw();
  return h('div', { class: 'card' }, h('h3', {}, 'Overclaim flags (점수와 별도, 해당 시에만)'),
    h('div', { class: 'muted', style: 'font-size:13px' }, '키워드만 보고 자동으로 체크하지 마세요. 부정문(예: "authorization cannot be determined")은 단정이 아닙니다. flag마다 정확한 인용문과 이유가 필요합니다.'),
    list, ro ? null : h('button', { type: 'button', onclick: () => { a.overclaim_flags.push({ type: '', quote: '', reason: '' }); save(); draw(); } }, '+ Overclaim flag 추가'));
}

function missingFields(it, a, pred) {
  const miss = [];
  for (const m of METRICS) if (a[m] === null) miss.push(rubric.general_rubric[m].title + ' 점수');
  if (!a.video_confirmed) miss.push('"실제 영상을 확인했습니다" 체크');
  if (!a.evidence_compared) miss.push('"prediction의 evidence와 영상을 비교했습니다" 체크');
  const strings = predStrings(pred);
  a.overclaim_flags.forEach((f, i) => {
    if (!f.type) miss.push(`flag #${i + 1} 종류`);
    if (!(f.quote || '').trim()) miss.push(`flag #${i + 1} exact_output_quote`);
    else if (!strings.some(s => s.includes(f.quote.trim()))) miss.push(`flag #${i + 1} 인용문이 prediction 원문과 정확히 일치하지 않음`);
    if (!(f.reason || '').trim()) miss.push(`flag #${i + 1} why_unsupported`);
  });
  if (it.task === 'attention') { if (!a.ranking.top1_correct) miss.push('Top-1 Correct'); if (!a.ranking.full_order_correct) miss.push('Full Order Correct'); }
  if (it.task === 'multi_camera') for (const [k, v] of Object.entries(a.multiview)) if (!v) miss.push('qualitative: ' + k);
  return miss;
}

async function submit(it, sys, pred, errBox) {
  const a = A(it.item_id, sys);
  const miss = missingFields(it, a, pred);
  if (miss.length) { errBox.replaceChildren(h('b', {}, '제출할 수 없습니다. 아래 항목을 완료하세요:'), h('ul', {}, miss.map(x => h('li', {}, x)))); return; }
  a.submitted = true; a.submitted_at = new Date().toISOString();
  save();
  saveServer(false);
  toast(`${it.item_id} ${sys.replace('_', ' ')} 제출 완료`);
  if (sys === 'System_A') return go(it.item_id, 'System_B');
  const idx = manifest.items.findIndex(x => x.item_id === it.item_id);
  const next = manifest.items.slice(idx + 1).concat(manifest.items.slice(0, idx)).find(x => !A(x.item_id, 'System_A').submitted || !A(x.item_id, 'System_B').submitted);
  if (next) return go(next.item_id, firstOpen(next.item_id));
  toast('14개 assessment를 모두 제출했습니다. Export grading JSON을 눌러 저장하세요.');
  renderItem();
}

async function renderItemKeepScroll() { const y = window.scrollY; await renderItem(); window.scrollTo(0, y); }

// ------------------------------------------------------------------ export / import / server save / guide
function doExport() {
  const blob = new Blob([JSON.stringify(exportObj(), null, 2)], { type: 'application/json' });
  const a = h('a', { href: URL.createObjectURL(blob), download: `${reviewer}.json` });
  document.body.append(a); a.click(); a.remove();
  toast(`${reviewer}.json 다운로드 — grades/ 폴더에 저장하세요`);
}
async function saveServer(verbose) {
  try {
    const r = await fetch(`/api/save/${encodeURIComponent(reviewer)}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(exportObj()) });
    if (!r.ok) throw new Error(await r.text());
    if (verbose) toast('서버에 저장됨: grades/' + reviewer + '.json');
  } catch (e) { if (verbose) toast('서버 저장 실패 — Export를 사용하세요'); }
}
function doImport(ev) {
  const f = ev.target.files[0]; if (!f) return;
  const rd = new FileReader();
  rd.onload = () => {
    try {
      const d = JSON.parse(rd.result);
      if (d.pack_version !== PACK) throw new Error('pack_version 불일치');
      if (d.reviewer_id !== reviewer) throw new Error(`이 파일은 ${d.reviewer_id}의 파일입니다 (현재 ${reviewer})`);
      for (const it of manifest.items) for (const s of SYSTEMS) if (d[it.item_id] && d[it.item_id][s]) {
        const x = Object.assign(blankAssessment(it.item_id), d[it.item_id][s]); delete x.total; state.items[it.item_id][s] = x;
      }
      save(); renderItem(); toast('Import 완료');
    } catch (e) { toast('Import 실패: ' + e.message); }
  };
  rd.readAsText(f); ev.target.value = '';
}
function showGuide() {
  const body = document.getElementById('modalBody');
  body.replaceChildren(h('h2', {}, '채점 기준 (모든 ITEM 공통)'),
    h('h3', {}, '공통 원칙'), h('ul', {}, rubric.general_rules.map(r => h('li', {}, r))),
    ...METRICS.map(m => { const g = rubric.general_rubric[m]; return h('div', { class: 'metric' }, h('h3', {}, g.title), h('div', { class: 'mq' }, g.question),
      h('div', { class: 'expl' }, h('b', {}, '① 2점을 주는 최소 조건'), g.two_min, h('b', {}, '② 1점을 주는 상황'), g.one_when,
        h('b', {}, '③ 0점을 주는 상황'), g.zero_when, h('b', {}, '④ 흔히 헷갈리는 경계 사례'), g.boundary)); }),
    h('h3', {}, 'Overclaim flags'), h('ul', {}, Object.entries(rubric.overclaim_flags).map(([k, d]) => h('li', {}, h('code', {}, k), ' — ', d))));
  document.getElementById('modal').hidden = false;
}

init().catch(e => { document.getElementById('main').replaceChildren(h('div', { class: 'card' }, h('b', {}, '로드 실패: '), String(e), h('p', {}, 'scripts/serve_grading.py로 실행한 주소(http://127.0.0.1:...)에서 여세요.'))); });
