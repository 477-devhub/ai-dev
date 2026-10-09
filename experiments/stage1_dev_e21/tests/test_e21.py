"""Synthetic integrity/annotation fixtures; never production Human GT."""
import copy,json,sys,tempfile,threading,unittest,urllib.request,urllib.error
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'scripts'))
from dev_common import ROOT,PROJECT,E2,read,write,sha,digest
from review_store import Reviews,export_review_problems
from media_integrity import similarity,source_screen,validate_candidate
from serve_review import handler
from http.server import ThreadingHTTPServer


def review(reviewer='fixture_1',label='CLEAR_NORMAL'):
    return {'reviewer':reviewer,'label':label,'observable_summary':'SYNTHETIC fixture only, not a Human label.',
        'uncertainty_reason':'fixture','watched_full_window':True,'watched_original_context':True,
        'observation_tags':{'recovery_observed':None},'interpretation_tags':{'boundary_context_required':None}}


class DatasetTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'tests'); self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name); self.store=Reviews(self.folder); self.cid='DEV_999_01'
        self.original=self.folder/'original.mp4'; self.original.write_bytes(b'synthetic-original-not-a-video')
        self.clip=self.folder/'clip.mp4'; self.clip.write_bytes(b'synthetic-clip-not-a-video')
        self.source={'source_id':'fixture_source','source_video_path':str(self.original),'source_video_sha256':sha(self.original),
            'scene_group_id':'fixture_scene','physical_group_id':'fixture_phys','independence_status':'INDEPENDENCE_UNVERIFIED'}
        self.c={'candidate_id':self.cid,'source_id':'fixture_source','source_video_path':str(self.original),
            'source_video_sha256':sha(self.original),'clip_path':str(self.clip),'clip_sha256':sha(self.clip),
            'clip_start_sec':0.,'clip_end_sec':5.,'canonical_cv_state_path':None,'canonical_cv_state_sha256':None,
            'neutral_context':'Fixture neutral context','scene_group_id':'fixture_scene','physical_group_id':'fixture_phys'}

    def test_finalized_only_evaluation_and_provenance(self):
        self.assertIn('NOT_FINALIZED',export_review_problems(self.store.get(self.cid)))
        self.store.save(self.cid,review()); self.store.finalize(self.cid,'fixture_finalizer',True)
        self.assertIn('SINGLE_REVIEWER_EXCLUDED_BY_DEFAULT',export_review_problems(self.store.get(self.cid)))
        self.assertEqual(export_review_problems(self.store.get(self.cid),True),[])
        rec=self.store.get(self.cid); rec['reviews'][0]['watched_original_context']=False
        self.assertIn('HUMAN_PROVENANCE_INVALID',export_review_problems(rec,True))

    def test_review_binds_actual_source_clip_window(self):
        self.store.save(self.cid,review(),candidate_media_hash='fixture-original-hash')
        self.store.finalize(self.cid,'fixture_finalizer',True)
        self.assertEqual(export_review_problems(self.store.get(self.cid),True,'fixture-original-hash'),[])
        self.assertIn('REVIEW_MEDIA_CHANGED',export_review_problems(self.store.get(self.cid),True,'fixture-changed-window'))

    def test_canonical_schema_and_clip_link_reject_tamper(self):
        state=read(PROJECT/'experiments/p1_decisions/e1_v2/recovery.canonical.json')
        path=self.folder/'canonical.json'; write(path,state)
        c=dict(self.c,canonical_cv_state_path=str(path),canonical_cv_state_sha256=sha(path))
        with patch('media_integrity.probe',return_value={'duration_sec':5.}):
            self.assertIn('CANONICAL_CLIP_LINK',validate_candidate(c,self.source))
        state['state_version']='invented'; write(path,state); c['canonical_cv_state_sha256']=sha(path)
        with patch('media_integrity.probe',return_value={'duration_sec':5.}):
            self.assertIn('CANONICAL_SCHEMA',validate_candidate(c,self.source))

    def test_source_group_mapping_invalid(self):
        c=dict(self.c,physical_group_id='different')
        with patch('media_integrity.probe',return_value={'duration_sec':5.}):
            self.assertIn('SOURCE_GROUP_MAPPING',validate_candidate(c,self.source))

    def test_hash_validity_and_tamper(self):
        with patch('media_integrity.probe',return_value={'duration_sec':5.}):
            self.assertEqual(validate_candidate(self.c,self.source),['CV_NOT_READY'])
            self.clip.write_bytes(b'tampered')
            self.assertIn('CLIP_PATH_HASH',validate_candidate(self.c,self.source))

    def test_source_mapping_rejected(self):
        c=copy.deepcopy(self.c); c['source_id']='other'
        with patch('media_integrity.probe',return_value={'duration_sec':5.}): self.assertIn('SOURCE_MAPPING',validate_candidate(c,self.source))

    def test_timestamp_range_rejected(self):
        for start,end in [(-1.,5.),(5.,4.),(0.,6.),(float('nan'),5.),(True,5.)]:
            c=dict(self.c,clip_start_sec=start,clip_end_sec=end)
            with patch('media_integrity.probe',return_value={'duration_sec':5.}): self.assertIn('TIMESTAMP_RANGE',validate_candidate(c,self.source))

    def test_frozen_hash_and_group_rejected(self):
        reg=read(E2/'data/exclusion_registry.json')
        s=dict(self.source,source_video_sha256=reg['media_sha256'][0],physical_group_id=reg['physical_group_ids'][0])
        with patch('media_integrity.sha',return_value=reg['media_sha256'][0]):
            errors=source_screen(s)
        self.assertIn('FROZEN_SOURCE_OVERLAP',errors); self.assertIn('PREVIOUS_PHYSICAL_GROUP_ID',errors)

    def test_previous_scene_rejected(self):
        s=dict(self.source,scene_group_id=read(E2/'data/exclusion_registry.json')['scene_group_ids'][0])
        self.assertIn('PREVIOUS_SCENE_GROUP_ID',source_screen(s))

    def test_near_duplicate_and_team_screen(self):
        a=['0011223344556677']*5; b=['0011223344556676']*3
        self.assertTrue(similarity(a,b)); self.assertFalse(similarity(a,['ffffffffffffffff']*5))
        s=dict(self.source,dhash=a); errors=source_screen(s,{'records':[{'path':'TEAM:P001:SRC01','dhash':b}]})
        self.assertTrue(any(e.startswith('NEAR_DUPLICATE_OR_PREVIOUS_SCENE:TEAM') for e in errors))

    def test_invalid_label_and_missing_reviewer(self):
        for values in [{'label':'filename_action'},{'reviewer':''}]:
            with self.assertRaises(ValueError): self.store.save(self.cid,dict(review(),**values))

    def test_original_review_evidence_required(self):
        for field in ('watched_full_window','watched_original_context'):
            with self.assertRaises(ValueError): self.store.save(self.cid,dict(review(),**{field:False}))

    def test_model_output_fields_rejected(self):
        for field in ('p_incident','safe_score','ground_truth','model_prediction'):
            with self.assertRaises(ValueError): self.store.save(self.cid,dict(review(),**{field:.99}))

    def test_unreviewed_once_disagreement_adjudicated_finalized(self):
        self.assertEqual(self.store.status(self.cid),'UNREVIEWED')
        self.store.save(self.cid,review()); self.assertEqual(self.store.status(self.cid),'REVIEWED_ONCE')
        self.store.save(self.cid,review('fixture_2','ANCHORED_DANGER')); self.assertEqual(self.store.status(self.cid),'DISAGREEMENT')
        with self.assertRaises(ValueError): self.store.finalize(self.cid,'fixture_finalizer')
        self.store.adjudicate(self.cid,'fixture_3','AMBIGUOUS','SYNTHETIC adjudication reason')
        self.assertEqual(self.store.status(self.cid),'ADJUDICATED')
        self.store.finalize(self.cid,'fixture_finalizer'); self.assertEqual(self.store.status(self.cid),'FINALIZED')

    def test_single_reviewer_explicit_only(self):
        self.store.save(self.cid,review())
        with self.assertRaises(ValueError): self.store.finalize(self.cid,'fixture_finalizer')
        f=self.store.finalize(self.cid,'fixture_finalizer',allow_single=True)
        self.assertEqual(f['review_basis'],'single_reviewer_explicit'); self.assertEqual(f['human_reviewer_count'],1)

    def test_two_agree_does_not_auto_finalize(self):
        self.store.save(self.cid,review()); self.store.save(self.cid,review('fixture_2'))
        self.assertEqual(self.store.status(self.cid),'AGREEMENT_READY')
        self.assertIsNone(self.store.get(self.cid)['finalization'])
        self.store.finalize(self.cid,'fixture_finalizer'); self.assertEqual(self.store.status(self.cid),'FINALIZED')

    def test_append_only_resume_and_duplicate_reviewer_not_two(self):
        self.store.save(self.cid,review()); self.store.save(self.cid,review())
        second=Reviews(self.folder); self.assertEqual(len(second.get(self.cid)['reviews']),2)
        self.assertEqual(len(second.current(second.get(self.cid))),1)
        with self.assertRaises(ValueError): second.finalize(self.cid,'fixture_finalizer')

    def test_blinding_until_own_submission(self):
        self.store.save(self.cid,review())
        self.assertEqual(self.store.public(self.cid,'fixture_2')['other_reviews'],[])
        self.store.save(self.cid,review('fixture_2')); self.assertEqual(len(self.store.public(self.cid,'fixture_2')['other_reviews']),2)

    def test_finalized_records_immutable(self):
        self.store.save(self.cid,review()); self.store.finalize(self.cid,'fixture_finalizer',True)
        with self.assertRaises(ValueError): self.store.save(self.cid,review('fixture_2'))

    def test_path_traversal_rejected(self):
        with self.assertRaises(ValueError): self.store.get('../../records')

    def test_invalid_auxiliary_tags(self):
        with self.assertRaises(ValueError): self.store.save(self.cid,dict(review(),observation_tags={'observed_person_count':True}))
        with self.assertRaises(ValueError): self.store.save(self.cid,dict(review(),observation_tags={'low_quality':'false'}))

    def test_http_blinding_range_and_csrf(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),handler({'candidates':[self.c]},self.store,'fixture-token'))
        thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start(); self.addCleanup(server.server_close); self.addCleanup(server.shutdown)
        base=f'http://127.0.0.1:{server.server_port}'
        rows=json.load(urllib.request.urlopen(base+'/api/queue'))
        self.assertNotIn('clip_path',rows[0]); self.assertNotIn('source_id',rows[0]); self.assertNotIn('model',rows[0])
        req=urllib.request.Request(base+f'/video/{self.cid}/clip',headers={'Range':'bytes=0-3'})
        with urllib.request.urlopen(req) as r: self.assertEqual(r.status,206); self.assertEqual(r.read(),b'synt')
        bad=urllib.request.Request(base+'/api/review',data=b'{}',headers={'Content-Type':'application/json'})
        with self.assertRaises(urllib.error.HTTPError): urllib.request.urlopen(bad)

    def test_empty_queue_safe(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),handler({'candidates':[]},self.store,'fixture-token'))
        threading.Thread(target=server.serve_forever,daemon=True).start(); self.addCleanup(server.server_close); self.addCleanup(server.shutdown)
        self.assertEqual(json.load(urllib.request.urlopen(f'http://127.0.0.1:{server.server_port}/api/queue')),[])

    def test_canonical_and_v1_v2_abcd_alignment(self):
        sys.path.insert(0,str(E2/'src'))
        from e2_inputs import prepare_arms
        arms=prepare_arms(read(PROJECT/'experiments/p1_decisions/e1_v2/recovery.canonical.json'))
        self.assertEqual(arms['A']['input_hash'],arms['B']['input_hash'])
        self.assertEqual(arms['C']['input_hash'],arms['D']['input_hash'])
        self.assertEqual(arms['A']['canonical_state_hash'],arms['D']['canonical_state_hash'])
        self.assertNotIn('human_gt',arms['D']['input_text'])

    def test_e2_validator_unknown_independence_and_no_fake_gt(self):
        sys.path.insert(0,str(E2/'src')); from e2_dataset import validate_manifest
        m={'schema_version':'e2-development-v1','dataset_id':'synthetic','candidates':[{'candidate_id':'fixture','source_id':'fixture','scene_group_id':'fixture','physical_group_id':'fixture'}]}
        r=validate_manifest(m); self.assertIn('INDEPENDENCE_UNCONFIRMED',r['exclusions']['fixture'])
        self.assertIn('HUMAN_GT_INCOMPLETE',r['exclusions']['fixture'])
        self.assertEqual(validate_manifest({'schema_version':'e2-development-v1','candidates':[]})['eligible'],[])

    def test_duplicate_candidate_manifest_rejected(self):
        sys.path.insert(0,str(E2/'src')); from e2_dataset import validate_manifest
        x={'candidate_id':'fixture','source_id':'fixture','scene_group_id':'fixture','physical_group_id':'fixture'}
        with self.assertRaises(ValueError): validate_manifest({'schema_version':'e2-development-v1','candidates':[x,x]})


if __name__=='__main__': unittest.main()
