# P4 — Canonical 64 Frames → GPT-6.1 Sol Vision (strong direct-vision upper-bound condition)

P4 is identical to P3 in model (gpt-6.1-sol), reasoning effort (high), taxonomy, risk semantics, priority formula and
common-adapter-v2. The only change is the input: P3 received the compact CV state; P4 receives the 64 canonical frames directly.
No CV state or compact state is sent.

```
benchmark_v1/scripts/load_model_input.py iter_model_frames(item)   uniform_total64_v1 (64 | 22+21+21 | 32+32)
  -> lossless WebP in memory (q50/m2), local round-trip SHA256 check 64/64, base64 data URLs (never written to disk)
  -> POST /v1/responses: one user message = task input_text + 64 x ("F### | CAM_## | t=s.sssS", input_image detail=high)
     gpt-6.1-sol, reasoning.effort=high, text.format json_schema strict, no tools, store=false, default tier
  -> raw_visual_adapter (frame_ref -> camera + exact timestamp; per-camera enums) -> frozen P1 decision adapter
  -> prediction -> frozen common-adapter-v2 -> benchmark_v1/results/p4_gpt61_sol_vision/ (pipeline = vlm_only)
```

## Commands
```bash
cd D:/projects/477/experiments/p4_gpt61_sol_vision
.venv/Scripts/python.exe scripts/smoke_test_p4.py          # synthetic shapes only
.venv/Scripts/python.exe scripts/verify_frame_transport.py # local lossless round-trip, 7 x 64 frames, no API
.venv/Scripts/python.exe scripts/preflight_p4.py           # payload / image count / token estimate vs limits
.venv/Scripts/python.exe scripts/freeze_p4.py
.venv/Scripts/python.exe scripts/run_p4.py --all
.venv/Scripts/python.exe scripts/leakage_audit.py
.venv/Scripts/python.exe scripts/freeze_results.py
# evaluator only after result freeze (P2 evaluator reused unchanged)
.venv/Scripts/python.exe scripts/run_auto_eval.py
.venv/Scripts/python.exe scripts/compare_p0_p4.py
```
The venv pins the same openai 3.26.0 as P3 and adds Pillow. The P3 venv was not modified. Per-item artifacts are
`logs/frame_manifest_ITEM_XX.json` (frame hashes and sizes, no payloads) and `logs/request_text_ITEM_XX.txt` (all text sent).
