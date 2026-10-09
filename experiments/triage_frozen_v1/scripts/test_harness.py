import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import common
import analyze

def prediction(p=0.01,category='no_clear_incident',review=False,confidence=0.99):
    return {'decision':{'p_incident':p,'category':category,'human_review_required':review,
                        'confidence':confidence,'refused_questions':[], 'is_incident':p is not None and p>=0.5}}

class ProtocolTests(unittest.TestCase):
    def test_disabled_suppression_baseline(self):
        self.assertFalse(analyze.can_suppress(prediction(p=0),0))

    def test_unknown_refused_review_and_non_normal_always_escalate(self):
        rows=[prediction(p=None),prediction(review=True),prediction(category='uncertain'),prediction(confidence=0.5)]
        refused=prediction();refused['decision']['refused_questions']=['incident'];rows.append(refused)
        for row in rows:
            self.assertFalse(analyze.can_suppress(row,0.05))

    def test_danger_suppression_is_measured_not_hidden(self):
        p1={'D':prediction()};p4={'D':prediction(p=0.9)}
        result=analyze.evaluate(['D'],{'D':{'reference_binary':'DANGER'}},p1,p4,0.025)
        self.assertEqual(result['stage1_danger_suppressions'],1)
        self.assertEqual(result['final_danger_missed'],1)

    def test_test_stage_requires_policy_lock(self):
        with tempfile.TemporaryDirectory(dir=common.RUN) as tmp:
            root=Path(tmp);plan=root/'run_plan.json'
            common.write(plan,{'calibration_ids':['C'],'test_ids':['T']})
            with patch.object(common,'RUN',root),patch.object(common,'PLAN',plan):
                self.assertEqual(common.stage_ids('calibration'),['C'])
                with self.assertRaises(RuntimeError):common.stage_ids('test')

    def test_test_policy_hash_change_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=common.RUN) as tmp:
            root=Path(tmp);plan=root/'run_plan.json';policy=root/'routing_policy_lock.json'
            common.write(plan,{'test_ids':['T']});common.write(policy,{'threshold':0})
            common.write(root/'ROUTING_POLICY_SHA256.json',{'sha256':common.digest(policy)})
            common.write(policy,{'threshold':0.1})
            with patch.object(common,'RUN',root),patch.object(common,'PLAN',plan):
                with self.assertRaises(RuntimeError):common.stage_ids('test')

    def test_second_test_evaluation_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=common.RUN) as tmp:
            root=Path(tmp);common.write(root/'analysis/final_test_evaluation.json',{'evaluation_number':1})
            with patch.object(analyze,'RUN',root):
                with self.assertRaises(RuntimeError):analyze.test()

if __name__=='__main__':
    unittest.main()
