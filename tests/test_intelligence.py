"""Run with: .venv/Scripts/python.exe -m unittest discover -s tests -v"""
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from intelligence_data import *
from intelligence_services import *
from streamlit.testing.v1 import AppTest

class DataAndAnalytics(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.data,cls.health=load_sources(); cls.master,cls.issues=assemble(cls.data)
    def test_authoritative_counts_and_p95(self):
        self.assertEqual(len(self.master),len(self.data['ecosystem']))
        self.assertEqual(self.master.banking_eligible.sum(),len(self.data['stress']))
        filled=self.master.set_index('project_id').loc[self.data['mc'].project_id,'p95_score']
        np.testing.assert_allclose(filled,self.data['mc'].p95_score)
    def test_filters(self):
        d=filter_projects(self.master,'Tata',{'state':['Gujarat']},'Manufacturing')
        self.assertEqual(len(d),1); self.assertEqual(d.iloc[0].project_id,'SEM-0002')
        self.assertTrue(filter_projects(self.master,'does not exist').empty)
        design=filter_projects(self.master,scope='Design / DLI'); self.assertFalse(design.banking_eligible.any())
    def test_missing_files(self):
        with tempfile.TemporaryDirectory() as temp:
            d,h=load_sources(Path(temp)); self.assertTrue(h.status.eq('UNAVAILABLE').all())
            with self.assertRaises(ValueError): assemble(d)
    def test_duplicate_and_missing_identifiers(self):
        x=self.data['master']; spec=SOURCES['master']
        with self.assertRaises(ValueError): validate_frame(pd.concat([x,x.iloc[:1]]),spec)
        x=x.copy(); x.loc[0,'project_id']=None
        with self.assertRaises(ValueError): validate_frame(x,spec)
    def test_schema_numeric_and_missing_matches(self):
        with self.assertRaises(ValueError): validate_frame(pd.DataFrame({'project_id':['a']}),SOURCES['mc'])
        x=self.data['mc'].copy(); x['p95_score']=x.p95_score.astype(object); x.loc[0,'p95_score']='bad'
        with self.assertRaises(ValueError): validate_frame(x,SOURCES['mc'])
        data=self.data.copy(); data['borrower']=data['borrower'].iloc[:0]; m,_=assemble(data)
        self.assertEqual(len(m),len(self.master))
        data=self.data.copy(); data['mc']=data['mc'].iloc[1:]; _,issues=assemble(data)
        self.assertTrue(any('mc:' in s for s in issues))
    def test_no_percentile_proxy(self):
        data={k:v.copy() if hasattr(v,'copy') else v for k,v in self.data.items()}
        for name in ['master','mc','final','ews']:
            if 'p95_score' in data[name]: data[name]['p95_score']=np.nan
        m,_=assemble(data); self.assertTrue(m.p95_score.isna().all()); self.assertTrue(m.p99_score.notna().any())
    def test_stress_reproduction_changes_and_bounds(self):
        for name,s in stress_engine.SCENARIOS.items():
            out,g=run_stress(self.data['stress'],self.master.project_id,s)
            np.testing.assert_allclose(out.scenario_score,out[name+'_score'],atol=1e-10)
        self.assertTrue((out.scenario_score>out.baseline_score).any())
        with self.assertRaises(ValueError): run_stress(self.data['stress'],self.master.project_id,.6)
        bad=self.data['stress'].copy(); bad.loc[0,'risk_credit_growth']=np.nan
        with self.assertRaises(ValueError): run_stress(bad,self.master.project_id,.1)
    def test_archived_mc_summary(self):
        for _,row in self.data['mc'].iterrows():
            vals=self.data['draws'][row.project_id]
            self.assertAlmostEqual(vals.mean(),row.mean_simulated_score,places=9)
            self.assertAlmostEqual(vals.quantile(.95),row.p95_score,places=9)
        self.assertEqual(self.data['method']['monte_carlo']['status'],'MC_METHOD_REPRODUCTION_REQUIRED')
    def test_allocation_all_policies(self):
        ids=self.master[self.master.banking_eligible].project_id
        for _,p in self.data['policy'].iterrows():
            out,checks=allocate_saved_policy(self.data['allocations'],p,12345,ids)
            self.assertTrue(all(checks.values())); self.assertAlmostEqual(out.scenario_allocation_crore.sum(),12345)
        with self.assertRaises(ValueError): allocate_saved_policy(self.data['allocations'],p,12345,ids,max_state=.01)
        with self.assertRaises(ValueError): allocate_saved_policy(self.data['allocations'],p,12345,ids[:2])
    def test_exports_and_scenario_storage(self):
        parsed=pd.read_csv(io.BytesIO(csv_bytes(self.master)))
        self.assertEqual(len(parsed),len(self.master)); self.assertEqual(list(parsed.columns),list(self.master.columns))
        self.assertIn("'=1+1",csv_bytes(pd.DataFrame({'x':['=1+1']})).decode('utf-8-sig'))
        with tempfile.TemporaryDirectory() as temp,patch('intelligence_services.ROOT',Path(temp)):
            p=archive_scenario('stress',self.master,{'severity':.1},fingerprint())
            self.assertTrue(p.exists()); self.assertTrue(p.with_suffix('.json').exists())
    def test_fingerprint_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); old=fingerprint(root); p=root/SOURCES['master'].path; p.parent.mkdir(parents=True); p.write_text('changed')
            self.assertNotEqual(old,fingerprint(root))

class AppWorkflows(unittest.TestCase):
    def test_all_pages_and_filter_consistency(self):
        app=AppTest.from_file(str(ROOT/'app/community_main.py'),default_timeout=30).run()
        self.assertFalse(app.exception)
        app.sidebar.text_input[0].set_value('Tata').run()
        self.assertEqual(app.metric[0].value,'2')
        self.assertEqual(len(app.dataframe[-1].value),2)
        app.sidebar.radio[0].set_value('Credit Committee and Evidence').run()
        self.assertEqual(len(app.dataframe[0].value),2)
        app.sidebar.text_input[0].set_value('').run()
        for page in ['Project Explorer','Structural ML','Stress Testing','Monte Carlo Analysis','Credit Allocation','Credit Committee and Evidence','Model and Data Health']:
            app.sidebar.radio[0].set_value(page).run(); self.assertFalse(app.exception,page)
    def test_selection_comparison_and_scenarios(self):
        app=AppTest.from_file(str(ROOT/'app/community_main.py'),default_timeout=30).run()
        app.sidebar.radio[0].set_value('Project Explorer').run()
        project=next(w for w in app.selectbox if w.label=='Project'); project.set_value('SEM-0002').run()
        self.assertIn('Tata',app.subheader[0].value)
        comparison=next(w for w in app.multiselect if w.label=='Compare two or three projects')
        comparison.set_value(['SEM-0001','SEM-0002','SEM-0003']).run(); self.assertEqual(len(app.dataframe[-1].value),3)
        app.sidebar.radio[0].set_value('Stress Testing').run()
        baseline=app.dataframe[0].value.scenario_score.copy()
        next(w for w in app.selectbox if w.label=='Scenario').set_value('Severe').run()
        self.assertTrue((app.dataframe[0].value.scenario_score>baseline).any())
        next(w for w in app.button if w.label=='Reset to baseline').click().run()
        np.testing.assert_allclose(app.dataframe[0].value.scenario_score,baseline)
        app.sidebar.radio[0].set_value('Credit Allocation').run()
        next(w for w in app.number_input if w.label=='Scenario budget (₹ crore)').set_value(20000.0).run()
        self.assertAlmostEqual(app.dataframe[0].value.scenario_allocation_crore.sum(),20000)
        next(w for w in app.number_input if w.label=='Maximum state share').set_value(.01).run()
        self.assertTrue(any('Infeasible' in e.value for e in app.error))
        self.assertFalse(app.exception)

if __name__=='__main__': unittest.main()

