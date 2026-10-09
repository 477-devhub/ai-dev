"""Append-only Human reviews. No automatic GT; disagreements never finalize implicitly."""
import threading,re
from pathlib import Path
from dev_common import ROOT,read,write,now,LABELS,digest

LOCK=threading.RLock()
OBS_TAGS=('observed_person_count','posture_transition_present','recovery_observed','close_interaction_present',
    'occlusion_present','low_quality','important_observation_gap')
INTERP_TAGS=('boundary_context_required','operator_review_reason','uncertainty_reason')


def export_review_problems(rec,include_single=False,expected_media_hash=None):
    f=rec.get('finalization'); problems=[]
    if not f: return ['NOT_FINALIZED']
    if f.get('label') not in LABELS or not f.get('reviewer') or not f.get('finalized_at'): problems.append('INVALID_FINALIZATION')
    if f.get('reviews_hash')!=digest(rec['reviews']): problems.append('REVIEW_HISTORY_CHANGED')
    current=Reviews.current(rec)
    if expected_media_hash is not None and any(r.get('review_media_hash')!=expected_media_hash for r in current): problems.append('REVIEW_MEDIA_CHANGED')
    if not current or any(r.get('basis')!='human_original_video' or not r.get('reviewer') or not r.get('reviewed_at')
        or r.get('watched_full_window') is not True or r.get('watched_original_context') is not True
        or not r.get('observable_summary') or r.get('label') not in LABELS for r in current): problems.append('HUMAN_PROVENANCE_INVALID')
    if f.get('review_basis')=='single_reviewer_explicit':
        if not include_single: problems.append('SINGLE_REVIEWER_EXCLUDED_BY_DEFAULT')
    elif f.get('review_basis')=='two_or_more_agreed':
        if len(current)<2 or len({r['label'] for r in current})!=1: problems.append('UNRESOLVED_DISAGREEMENT')
    elif f.get('review_basis')=='adjudicated':
        if not rec.get('adjudication') or not rec['adjudication'].get('reason'): problems.append('ADJUDICATION_MISSING')
    else: problems.append('INVALID_REVIEW_BASIS')
    return problems


class Reviews:
    def __init__(self,root=ROOT): self.root=Path(root)
    def path(self,cid):
        if not re.fullmatch(r'DEV_[0-9]{3}_[0-9]{2}',cid): raise ValueError('invalid candidate ID')
        return self.root/'review/records'/f'{cid}.json'
    def get(self,cid):
        p=self.path(cid)
        return read(p) if p.exists() else {'candidate_id':cid,'reviews':[],'adjudication':None,'finalization':None}
    @staticmethod
    def current(rec):
        out={}
        for r in rec['reviews']: out[r['reviewer']]=r
        return list(out.values())
    def status(self,cid):
        r=self.get(cid); reviews=self.current(r)
        if r['finalization']: return 'FINALIZED'
        if r['adjudication']: return 'ADJUDICATED'
        if not reviews: return 'UNREVIEWED'
        if len(reviews)==1: return 'REVIEWED_ONCE'
        return 'DISAGREEMENT' if len({x['label'] for x in reviews})>1 else 'AGREEMENT_READY'
    def save(self,cid,review,candidate_media_hash=None):
        allowed={'reviewer','label','observable_summary','uncertainty_reason','watched_full_window',
            'watched_original_context','observation_tags','interpretation_tags','playback_evidence'}
        if set(review)-allowed: raise ValueError('unexpected/model fields not accepted')
        if review.get('label') not in LABELS: raise ValueError('invalid label')
        if not re.fullmatch(r'[A-Za-z0-9_.-]{2,64}',review.get('reviewer','')): raise ValueError('reviewer ID required')
        if review.get('watched_full_window') is not True or review.get('watched_original_context') is not True: raise ValueError('Human original video review required')
        if not isinstance(review.get('observable_summary'),str) or not review['observable_summary'].strip(): raise ValueError('observable summary required')
        if review['label']=='AMBIGUOUS' and not review.get('uncertainty_reason','').strip(): raise ValueError('ambiguity reason required')
        for field,keys in [('observation_tags',OBS_TAGS),('interpretation_tags',INTERP_TAGS)]:
            tags=review.get(field,{})
            if not isinstance(tags,dict) or set(tags)-set(keys): raise ValueError('invalid auxiliary tags')
            for key,value in tags.items():
                if key=='observed_person_count':
                    if value is not None and (not isinstance(value,int) or isinstance(value,bool) or value<0): raise ValueError('invalid count')
                elif key.endswith('reason'):
                    if not isinstance(value,str): raise ValueError('reason must be text')
                elif value is not None and not isinstance(value,bool): raise ValueError('tags must be bool or null')
        with LOCK:
            rec=self.get(cid)
            if rec['finalization']: raise ValueError('finalized record immutable; explicit versioned correction required')
            record=dict(review,reviewed_at=now(),basis='human_original_video')
            if candidate_media_hash is not None: record['review_media_hash']=candidate_media_hash
            rec['reviews'].append(record); rec['adjudication']=None
            write(self.path(cid),rec); return self.status(cid)
    def adjudicate(self,cid,reviewer,label,reason):
        with LOCK:
            rec=self.get(cid); current=self.current(rec)
            if rec['finalization']: raise ValueError('already finalized')
            if len(current)<2 or len({r['label'] for r in current})<2: raise ValueError('no unresolved disagreement')
            if not reviewer or reviewer in {r['reviewer'] for r in current} or label not in LABELS or not reason.strip(): raise ValueError('separate Human adjudicator and original video reason required')
            rec['adjudication']={'reviewer':reviewer,'label':label,'reason':reason,'reviewed_at':now()}; write(self.path(cid),rec)
    def finalize(self,cid,reviewer,allow_single=False):
        with LOCK:
            rec=self.get(cid); reviews=self.current(rec)
            if rec['finalization']: return rec['finalization']
            if not reviewer or not reviews: raise ValueError('Human review and finalizer required')
            if rec['adjudication']: label=rec['adjudication']['label']; kind='adjudicated'
            elif len(reviews)>=2 and len({r['label'] for r in reviews})==1: label=reviews[0]['label']; kind='two_or_more_agreed'
            elif len(reviews)==1 and allow_single: label=reviews[0]['label']; kind='single_reviewer_explicit'
            else: raise ValueError('two agreeing reviewers or adjudication required; single only by explicit option')
            rec['finalization']={'label':label,'reviewer':reviewer,'finalized_at':now(),'review_basis':kind,
                'human_reviewer_count':len(reviews),'reviews_hash':digest(rec['reviews'])}
            write(self.path(cid),rec); return rec['finalization']
    def public(self,cid,reviewer):
        rec=self.get(cid); own=[r for r in self.current(rec) if r['reviewer']==reviewer]
        # Other reviewers' answers hidden until this reviewer submitted their own independent review.
        return {'status':self.status(cid),'my_review':own[0] if own else None,
            'other_reviews':self.current(rec) if own else [],'finalization':rec['finalization'] if own else None}
