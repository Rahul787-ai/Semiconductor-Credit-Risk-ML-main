"""Analytical adapters: reuse the validated stress method; never fit at UI load."""
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
from intelligence_data import ROOT

path=ROOT/'13_Continuous_Ingestion/07_Automated_Evaluation/evaluate_new_projects.py'
spec=importlib.util.spec_from_file_location('validated_stress',path)
stress_engine=importlib.util.module_from_spec(spec)
spec.loader.exec_module(stress_engine)

def run_stress(reference, ids, severity):
    if not 0 <= severity <= .5: raise ValueError('Severity must be within 0.00–0.50')
    if reference.empty: raise ValueError('Stress reference unavailable')
    risks=reference[list(stress_engine.WEIGHTS)].to_numpy(float)
    if not np.isfinite(risks).all() or (risks<0).any() or (risks>1).any(): raise ValueError('Invalid or incomplete risk components')
    gate=stress_engine.validate_deterministic_method(reference)
    if not gate['deterministic_method_reproduction_pass']: raise ValueError('Deterministic reproduction gate failed')
    out=reference[reference.project_id.isin(ids)].copy()
    if out.empty: raise ValueError('No selected projects have validated stress inputs')
    out['scenario_score']=[stress_engine.stress_score(row,severity) for _,row in out.iterrows()]
    out['baseline_rank_filtered']=out.baseline_score.rank(ascending=False,method='min')
    out['scenario_rank_filtered']=out.scenario_score.rank(ascending=False,method='min')
    out['rank_change']=out.baseline_rank_filtered-out.scenario_rank_filtered
    out['score_change']=out.scenario_score-out.baseline_score
    return out,gate

def contributions(row,severity):
    rows=[]
    for c,w in stress_engine.WEIGHTS.items():
        v=float(row[c]); stressed=v+severity*(1-v) if c in stress_engine.MACRO_RISK_COLUMNS else v
        rows.append({'driver':c.removeprefix('risk_').replace('_',' ').title(),'baseline_points':100*w*v,'scenario_points':100*w*stressed})
    return pd.DataFrame(rows)

def allocate_saved_policy(allocations, policy, budget, ids, max_project=None,max_state=None,min_project=None):
    """Scale archived shares, without inventing or claiming to rerun the original solver."""
    if not np.isfinite(budget) or budget<=0: raise ValueError('Budget must be positive')
    d=allocations[allocations.scenario_id.eq(policy.scenario_id)].copy()
    if d.empty or d.project_id.duplicated().any(): raise ValueError('Policy rows missing or duplicated')
    if set(d.project_id)!=set(ids): raise ValueError('Saved policy requires its full manufacturing portfolio. Reset filters; shares cannot be reassigned to a subset.')
    shares=d.allocation_share.to_numpy(float)
    cap=float(policy.max_project_share_limit if max_project is None else max_project)
    state_cap=float(policy.max_state_share_limit if max_state is None else max_state)
    floor=float(policy.min_project_share_limit if min_project is None else min_project)
    states=d.groupby('state').allocation_share.sum()
    checks={'finite_shares':bool(np.isfinite(shares).all()),'budget_total':bool(abs(shares.sum()-1)<1e-8),'project_minimum':bool((shares>=floor-1e-8).all()),'project_maximum':bool((shares<=cap+1e-8).all()),'state_maximum':bool((states<=state_cap+1e-8).all()),'nonnegative':bool((shares>=0).all())}
    if not all(checks.values()): raise ValueError('Infeasible for this saved policy: '+', '.join(k for k,v in checks.items() if not v)+'. Choose another archived policy or relax the review limits. No new solver was run.')
    d['scenario_allocation_crore']=d.allocation_share*budget
    return d,checks

def archive_scenario(kind,frame,settings,fingerprint):
    folder=ROOT/'output/dashboard_scenarios'; folder.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    target=folder/f'{kind}_{stamp}.csv'
    frame.to_csv(target,index=False)
    target.with_suffix('.json').write_text(json.dumps({'kind':kind,'calculated_at_utc':stamp,'settings':settings,'source_hashes':dict(fingerprint),'research_only':True},indent=2),encoding='utf-8')
    return target
