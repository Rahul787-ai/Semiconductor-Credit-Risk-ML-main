"""Explicit, read-only source registry and validated identifier joins."""
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
@dataclass(frozen=True)
class Source:
    path: str
    required: tuple = ()
    keys: tuple = ()

B = '04_Banking_Alignment/06_Dashboard_Integration/'
M = '03_Modeling/'
F = '13_Continuous_Ingestion/06_Frozen_Model/artifacts/'
SOURCES = {
 'ecosystem': Source('01_Raw_Data/Semiconductor/Semiconductor_Master/Semiconductor_Ecosystem_Master.csv', ('ecosystem_id','source_project_id','project_scope','company','state','project_type','investment_crore'), ('ecosystem_id',)),
 'canonical': Source('01_Raw_Data/Semiconductor/Semiconductor_Master/Semiconductor_Master_Canonical.csv', ('project_id','company','investment_crore'), ('project_id',)),
 'master': Source(B+'Banking_Dashboard_Master.csv', ('project_id','company'), ('project_id',)),
 'committee': Source('04_Banking_Alignment/04_Outputs/Integrated_Credit_Committee_Register.csv', ('project_id','indicative_model_risk_grade'), ('project_id',)),
 'final': Source('05_Final_Results/FINAL_BANK_CREDIT_FRAMEWORK/FINAL_Bank_Credit_Decision_Support_Full.csv', ('project_id',), ('project_id',)),
 'stress': Source(M+'Phase_3E_Robust_Stress_Test/Robust_Stress_Test_Full.csv', ('project_id','baseline_score','severe_score'), ('project_id',)),
 'mc': Source(M+'Phase_6B_Monte_Carlo_Stress/Monte_Carlo_Project_Risk_Summary.csv', ('project_id','p95_score','p99_score','mean_simulated_score'), ('project_id',)),
 'draws': Source(M+'Phase_6B_Monte_Carlo_Stress/Monte_Carlo_Project_Scores.csv', ('simulation_id',), ('simulation_id',)),
 'borrower': Source(B+'Borrower_Financial_Panel.csv', ('project_id','statement_scope'), ('project_id',)),
 'evidence': Source(B+'Banking_Evidence_Panel.csv', ('project_id','field','verification_status')),
 'gaps': Source(B+'Banking_Data_Gap_Panel.csv', ('project_id','missing_field')),
 'ews': Source(B+'Longitudinal_EWS_Panel.csv', ('project_id','monitoring_maturity'), ('project_id',)),
 'clusters': Source(M+'Phase_3B_Cluster_Validation/Validated_Cluster_Assignments.csv', ('ecosystem_id','validated_cluster','PC1','PC2'), ('ecosystem_id',)),
 'variance': Source(M+'Phase_3A_PCA_KMeans/PCA_Explained_Variance.csv', ('component','explained_variance','cumulative_variance'), ('component',)),
 'validation': Source(M+'Phase_3B_Cluster_Validation/Cluster_Validation_All_Metrics.csv', ('k','silhouette','mean_bootstrap_ari'), ('k',)),
 'segments': Source(M+'Phase_3C_Cluster_Interpretation/Cluster_Economic_Interpretation.csv', ('cluster','key_characteristics'), ('cluster',)),
 'policy': Source('04_Optimization/Phase_4B_Allocation_Sensitivity/Policy_Scenario_Summary.csv', ('scenario_id','max_project_share_limit','max_state_share_limit','min_project_share_limit'), ('scenario_id',)),
 'allocations': Source('04_Optimization/Phase_4B_Allocation_Sensitivity/Allocation_Sensitivity_All_Scenarios.csv', ('scenario_id','project_id','allocation_share'), ('scenario_id','project_id')),
 'scaler': Source(F+'Frozen_Scaler_Parameters.csv', ('feature','mean','scale_ddof0'), ('feature',)),
 'components': Source(F+'Frozen_PCA_Components.csv', ('feature','PC1','PC7'), ('feature',)),
 'centroids': Source(F+'Frozen_Cluster_Centroids.csv', ('validated_cluster','PC1','PC7'), ('validated_cluster',)),
 'reference_pca': Source(F+'Frozen_Reference_PCA_Scores.csv', ('ecosystem_id','PC1','PC7'), ('ecosystem_id',)),
 'cross_method': Source(M+'Phase_6C_Cross_Method_Validation/Cross_Method_Validation_Metrics.csv', ('comparison','spearman_rho')),
 'manifest': Source(F+'Frozen_Model_Manifest.json'),
 'frozen_validation': Source(F+'Frozen_Model_Validation.json'),
 'method': Source('13_Continuous_Ingestion/07_Automated_Evaluation/Phase_13F_Method_Validation.json'),
 'new_mc': Source('13_Continuous_Ingestion/07_Automated_Evaluation/New_Project_Monte_Carlo_Status.csv', ('project_id',), ('project_id',)),
}

def fingerprint(root=ROOT):
    return tuple((name, hashlib.sha256((root/s.path).read_bytes()).hexdigest() if (root/s.path).exists() else 'MISSING') for name,s in SOURCES.items())

def validate_frame(frame, spec):
    missing = set(spec.required)-set(frame.columns)
    if missing: raise ValueError('Missing columns: '+', '.join(sorted(missing)))
    if spec.keys:
        if frame[list(spec.keys)].isna().any().any(): raise ValueError('Missing identifiers')
        if frame.duplicated(list(spec.keys)).any(): raise ValueError('Duplicate identifiers: '+str(frame.loc[frame.duplicated(list(spec.keys),keep=False),list(spec.keys)].to_dict('records')[:5]))
    for c in frame.columns:
        if c.endswith(('_score','_crore','_share')) or c in ('PC1','PC2','validated_cluster'):
            if c in ('financial_measure_type',): continue
            numeric = pd.to_numeric(frame[c],errors='coerce')
            if (frame[c].notna() & numeric.isna()).any(): raise ValueError('Non-numeric values: '+c)
    return frame

def load_sources(root=ROOT):
    data, health = {}, []
    for name,spec in SOURCES.items():
        p=root/spec.path
        row={'source':name,'path':spec.path,'status':'AVAILABLE','rows':None,'file_modified_utc':None,'detail':''}
        try:
            row['file_modified_utc']=datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat()
            if p.suffix=='.json': data[name]=json.loads(p.read_text(encoding='utf-8'))
            else:
                data[name]=validate_frame(pd.read_csv(p),spec)
                row['rows']=len(data[name])
                row['detail']=f'{int(data[name].isna().sum().sum())} missing cells'
        except (OSError, ValueError, KeyError) as exc:
            row.update(status='UNAVAILABLE',detail=str(exc)); data[name] = {} if p.suffix=='.json' else pd.DataFrame()
        health.append(row)
    return data,pd.DataFrame(health)

def join_missing(base, extra, key, name, issues):
    if extra.empty: return base
    if extra[key].duplicated().any() or extra[key].isna().any(): raise ValueError(name+': invalid join identifiers')
    orphan=set(extra[key])-set(base[key])
    expected=base if key=='ecosystem_id' else base[base.project_scope.eq('Manufacturing')]
    unmatched=set(expected[key].dropna())-set(extra[key])
    if unmatched: issues.append(f'{name}: {len(unmatched)} expected records without a match: {sorted(unmatched)}')
    if orphan: issues.append(f'{name}: {len(orphan)} unmatched source identifiers: {sorted(orphan)}')
    x=base.set_index(key); y=extra.set_index(key)
    columns = {c: x[c].combine_first(y[c].reindex(x.index)) if c in y else x[c] for c in x}
    columns.update({c: y[c].reindex(x.index) for c in y if c not in x})
    return pd.DataFrame(columns, index=x.index).reset_index()

def assemble(data):
    if data['ecosystem'].empty: raise ValueError('Ecosystem source unavailable. Restore the registered canonical ecosystem CSV; see Model and Data Health.')
    d=data['ecosystem'].rename(columns={'source_project_id':'project_id'}).copy()
    if d.project_id.isna().any() or d.project_id.duplicated().any(): raise ValueError('Ecosystem project identifiers are missing or duplicated')
    issues=[]
    # Explicit precedence: canonical identity, validated structural assignments, integrated banking,
    # committee, exact stress/MC statistics, then legacy research fields. No latest-file discovery.
    canonical=data['canonical']
    if not canonical.empty:
        new=canonical.loc[~canonical.project_id.isin(d.project_id)].copy()
        if len(new):
            new['project_scope']='Manufacturing'; d=pd.concat([d,new],ignore_index=True)
        for c in ['company','state','project_type','investment_crore']:
            if c in canonical: d[c]=d.project_id.map(canonical.set_index('project_id')[c]).combine_first(d[c])
    d=join_missing(d,data['clusters'][[c for c in ['ecosystem_id','validated_cluster','PC1','PC2'] if c in data['clusters']]],'ecosystem_id','clusters',issues) if not data['clusters'].empty else d
    for name in ['master','committee','stress','mc','borrower','ews','final']:
        extra=data[name].copy()
        # MC exact statistics supersede gaps only; no proxy quantiles.
        d=join_missing(d,extra,'project_id',name,issues)
    for c in ['validated_cluster','final_ews_status','indicative_model_risk_grade','project_stress_vulnerability_class','p95_score','baseline_score','severe_score','PC1','PC2','integrated_evidence_quality_class']:
        if c not in d: d[c]=float('nan')
    d['banking_eligible']=d.project_id.isin(data['stress'].get('project_id',pd.Series(dtype=str))) & d.project_scope.eq('Manufacturing')
    return d,issues

def filter_projects(d, search='', selections=None, scope='All ecosystem'):
    out=d.copy()
    if scope=='Manufacturing': out=out[out.project_scope.eq('Manufacturing')]
    if scope=='Design / DLI': out=out[~out.project_scope.eq('Manufacturing')]
    if search: out=out[out[['company','project_id','project_name']].fillna('').astype(str).agg(' '.join,axis=1).str.contains(search,case=False,regex=False)]
    for col,values in (selections or {}).items():
        if values: out=out[out[col].fillna('Not available').astype(str).isin(values)]
    return out

def csv_bytes(d):
    safe=d.copy()
    for c in safe.select_dtypes(include=['object','str']).columns:
        safe[c]=safe[c].map(lambda v: "'"+v if isinstance(v,str) and v.startswith(('=','+','-','@')) else v)
    return safe.to_csv(index=False,na_rep='Not available').encode('utf-8-sig')
