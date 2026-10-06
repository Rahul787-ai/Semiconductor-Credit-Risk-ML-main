"""Consolidated financial dashboard, called by banking_dashboard_v2.render_app."""
import json
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from html import escape
from intelligence_data import ROOT,SOURCES,fingerprint,load_sources,assemble,filter_projects,csv_bytes
from intelligence_services import run_stress,contributions,allocate_saved_policy,archive_scenario,stress_engine
from ui_theme import apply_ui,page_header,show_plotly,EWS_COLORS
from reference_theme import apply_reference_theme,card_title,kpi,icon

PAGES=['Portfolio Overview','Project Explorer','Structural ML','Stress Testing','Monte Carlo Analysis','Credit Allocation','Credit Committee and Evidence','Model and Data Health']
DISCLAIMER='Research decision support • Vulnerability scores are not default probabilities or monetary losses. Grades are not official credit ratings; clusters describe structural similarity.'
@st.cache_data(show_spinner=False)
def snapshot(signature): return load_sources()
@st.cache_data(show_spinner=False)
def calculate_stress(reference,ids,severity): return run_stress(reference,ids,severity)

def money(v):
    if pd.isna(v): return 'Not available'
    whole=f'{abs(v):.0f}'; tail=whole[-3:]; lead=whole[:-3]; groups=[]
    while lead: groups.insert(0,lead[-2:]); lead=lead[:-2]
    return ('−' if v<0 else '')+'₹ '+(','.join(groups+[tail]))+' crore'
def text(v): return 'Not available' if pd.isna(v) else str(v)
def table(d,cols=None):
    if cols is not None: d=d[[c for c in cols if c in d]]
    if d.empty: st.info('No records available for the selected projects.'); return
    # Explicit display missingness, while analytical frames retain numeric NaN.
    display=d.copy()
    for col in display.select_dtypes(include=['object','str']).columns:
        display[col]=display[col].fillna('Not available').astype(str)
    if display.isna().any().any(): st.caption('Empty numeric cells: Not available (never treated as zero).')
    friendly={'validated_cluster':'Structural segment','mean_simulated_score':'Mean score','median_simulated_score':'Median score','p95_score':'95th percentile','p99_score':'99th percentile','probability_top_3':'Top-three frequency','monte_carlo_rank_stability':'Ranking stability','baseline_score':'Baseline','scenario_score':'Scenario','project_id':'Project ID','integrated_evidence_quality_class':'Evidence quality','credit_committee_posture':'Review recommendation','project_stress_vulnerability_class':'Vulnerability','final_ews_status':'Early warning'}
    labels={c: st.column_config.NumberColumn(friendly.get(c,c.replace('_crore', ' (₹ crore)').replace('_',' ').title()),format='%.2f') if pd.api.types.is_float_dtype(display[c]) else st.column_config.Column(friendly.get(c,c.replace('_crore', ' (₹ crore)').replace('_',' ').title())) for c in display}
    st.dataframe(display,hide_index=True,width='stretch',column_config=labels)
def download(d,label,filename): st.download_button(label,csv_bytes(d),filename,'text/csv',key=filename)
def chart(fig,key):
    if fig.layout.title.text: st.markdown('**'+fig.layout.title.text+'**')
    fig.update_layout(title=None)
    fig.update_layout(height=360,paper_bgcolor='#ffffff',plot_bgcolor='#ffffff',font=dict(family='Inter, Segoe UI, Arial',size=13,color='#344c73'),margin=dict(l=55,r=25,t=25,b=55),legend=dict(title=None,orientation='h',y=1.12,x=0),hoverlabel=dict(bgcolor='#102235',font_color='#fff',font_size=13),xaxis=dict(showgrid=False,automargin=True),yaxis=dict(gridcolor='#eaf0f6',zeroline=False,automargin=True))
    st.plotly_chart(fig,key=key,width='stretch',theme=None,config={'displayModeBar':False,'responsive':True})
def subset(data,name,ids):
    d=data[name]
    return d[d.project_id.isin(ids)] if not d.empty and 'project_id' in d else pd.DataFrame()
def reset_stress():
    st.session_state['stress_preset']='Baseline'; st.session_state['severity']=0.0

def render_app():
    apply_ui()
    apply_reference_theme()
    with st.spinner('Checking registered data sources…'):
        signature=fingerprint(); data,health=snapshot(signature)
    st.sidebar.markdown(f'<div class="ref-brand">{icon("chip")}<span>SEMICON<br>INTELLIGENCE</span></div>',unsafe_allow_html=True)
    nav=dict(zip(PAGES,['Overview','Projects','Structural ML','Stress Testing','Monte Carlo','Allocation','Credit Committee','Model Health']))
    page=st.sidebar.radio('Workspace',PAGES,format_func=nav.get,label_visibility='collapsed')
    try: master,issues=assemble(data)
    except ValueError as exc:
        st.error(str(exc)); table(health); return
    with st.sidebar.expander('Search & advanced filters'):
        search=st.text_input('Search project or company',placeholder='Company, project name or ID')
        selections={}
        for col,label in [('project_type','Project type'),('validated_cluster','Structural cluster')]:
            choices=sorted(master[col].fillna('Not available').astype(str).unique())
            selections[col]=st.multiselect(label,choices)
    titles=dict(zip(PAGES,['Portfolio overview','Project explorer','Structural ML','Stress testing','Monte Carlo analysis','Credit allocation','Credit committee','Model & data health']))
    subtitles=dict(zip(PAGES,['India semiconductor ecosystem','Compare project risk, evidence and financial context','Explore the structure of the semiconductor ecosystem','Understand how adverse scenarios change vulnerability','Explore completed simulations and tail-risk scores','Review diversified credit-allocation policies','Prioritize review with evidence-led recommendations','Understand analysis readiness and evidence coverage']))
    header, badge, export=st.columns([6,1.65,1.55],vertical_alignment='center')
    with header:
        st.markdown(f'<div class="ref-heading">{titles[page]}</div><div class="ref-subtitle">{subtitles[page]}</div>',unsafe_allow_html=True)
    with badge:
        st.markdown(f'<span class="ref-badge">{icon("flask")}Research prototype</span>',unsafe_allow_html=True)
    with st.container(border=True,key='ref-filters'):
        a,b,c=st.columns(3)
        state=a.selectbox('State',['All states']+sorted(master.state.dropna().astype(str).unique()),label_visibility='collapsed')
        scope=b.selectbox('Data scope',['Manufacturing','All ecosystem','Design / DLI'],label_visibility='collapsed')
        risk=c.selectbox('Vulnerability category',['All risk levels']+sorted(master.project_stress_vulnerability_class.dropna().astype(str).unique()),label_visibility='collapsed')
    if state!='All states': selections['state']=[state]
    if risk!='All risk levels': selections['project_stress_vulnerability_class']=[risk]
    selected=filter_projects(master,search,selections,scope)
    ids=selected.project_id.tolist()
    st.sidebar.caption(f'{len(selected)} selected · {len(master)} in ecosystem')
    with export:
        st.download_button('Export report',csv_bytes(selected),'portfolio_report.csv','text/csv',icon=':material/download:',type='primary')
    model=data['manifest'].get('model_version','Not available')
    stamp=health.loc[health.source.eq('master'),'file_modified_utc'].iloc[0]
    unavailable=health[health.status.ne('AVAILABLE')]
    if len(unavailable): st.warning(f'{len(unavailable)} source(s) unavailable. Affected fields remain unavailable; inspect Model and Data Health.')
    if page=='Model and Data Health':
        health_page(data,health,master,issues); return
    if selected.empty:
        st.info('No projects match these filters. Clear search or one of the sidebar filters to continue.'); return
    if page=='Portfolio Overview': overview(selected,master,data)
    elif page=='Project Explorer': explorer(selected,data)
    elif page=='Structural ML': structural(selected,data)
    elif page=='Stress Testing': stress_page(selected,data,signature)
    elif page=='Monte Carlo Analysis': monte(selected,data)
    elif page=='Credit Allocation': allocation(selected,data,signature)
    elif page=='Credit Committee and Evidence': committee(selected,data)
    with st.expander('Methodology & source information'):
        st.caption(DISCLAIMER)
        st.caption(f'Scope: {scope} · {len(selected)} selected · Saved source file timestamp (UTC): {stamp} · Model: {model}')
    st.markdown('<div class="ref-footer">Semiconductor Credit Intelligence · Evidence-led research</div>',unsafe_allow_html=True)

def overview(d,master,data):
    cols=st.columns(4)
    ev=subset(data,'evidence',d.project_id)
    covered=ev.loc[ev.verification_status.eq('SOURCE_VERIFIED'),'project_id'].nunique() if not ev.empty else 0
    manufacturing=int(master.project_scope.eq('Manufacturing').sum())
    for col,label,value,name in zip(cols,['Ecosystem projects','Manufacturing projects','Design / DLI projects','Evidence coverage'],[len(master),manufacturing,len(master)-manufacturing,f'{covered/len(d):.0%}'],['factory','gear','chip','file']):
        with col: kpi(label,value,name,name=='file')
    left,right=st.columns([1.55,1])
    with left:
        with st.container(border=True,key='ref-risk'):
            x=d[d.banking_eligible].dropna(subset=['baseline_score','severe_score']).sort_values('severe_score',ascending=False)
            card_title('Manufacturing vulnerability',f'Baseline vs severe stress · highest {min(4,len(x))} of {len(x)} eligible projects')
            x=x.head(4)
            if x.empty: st.info('No archived manufacturing stress results in this selection.')
            else:
                short=x.company.str.replace('Private Limited','',regex=False).str.replace('Limited','',regex=False).str.strip().str.slice(0,18)
                fig=go.Figure()
                for field,label,color in [('baseline_score','Baseline','#0875e8'),('severe_score','Severe stress','#21b0a5')]:
                    fig.add_bar(x=x.project_id,y=x[field],name=label,marker_color=color,marker_cornerradius=3,text=x[field].round(1),textposition='outside',textfont=dict(size=11),customdata=x.company,hovertemplate='%{customdata}<br>'+label+': %{y:.2f}<extra></extra>')
                fig.update_layout(barmode='group',bargap=.3,height=290,margin=dict(l=58,r=10,t=22,b=40),paper_bgcolor='#fff',plot_bgcolor='#fff',font=dict(family='Inter, Segoe UI, Arial',color='#344c73',size=11),legend=dict(orientation='h',x=.5,xanchor='center',y=-.25),xaxis=dict(tickmode='array',tickvals=x.project_id,ticktext=short,tickangle=0,showgrid=False),yaxis=dict(title='Vulnerability score (0–100)',range=[0,112],gridcolor='#eaf0f6',zeroline=False,automargin=True))
                st.plotly_chart(fig,key='risk',width='stretch',theme=None,config={'displayModeBar':False})
    with right:
        with st.container(border=True,key='ref-ews'):
            card_title('Early-warning signals',f'Share of {len(d)} selected projects by signal category')
            counts=d.final_ews_status.fillna('Not available').value_counts().reindex(['GREEN','AMBER','RED','Not available'],fill_value=0)
            counts=counts[counts>0]
            colors={'GREEN':'#0c9f78','AMBER':'#f4c433','RED':'#df3548','Not available':'#9bacbf'}
            donut,legend=st.columns([1.25,1],vertical_alignment='center')
            with donut:
                fig=go.Figure(go.Pie(labels=counts.index,values=counts.values,hole=.6,sort=False,marker=dict(colors=[colors[s] for s in counts.index],line=dict(color='#fff',width=2)),textinfo='percent',textposition='inside',textfont=dict(color='#fff',size=13),hovertemplate='%{label}: %{value} projects (%{percent})<extra></extra>'))
                fig.update_layout(height=290,margin=dict(l=0,r=0,t=0,b=0),showlegend=False,paper_bgcolor='#fff',annotations=[dict(text=f'<b>{len(d)}</b><br><span style="font-size:12px">projects</span>',x=.5,y=.5,showarrow=False,font=dict(size=24,color='#0b1534'))])
                st.plotly_chart(fig,key='ews',width='stretch',theme=None,config={'displayModeBar':False})
            with legend:
                notes={'GREEN':'No material signals','AMBER':'Watch list / developing risks','RED':'Significant concerns','Not available':'Evidence not available'}
                for status,count in counts.items():
                    st.markdown(f'<div class="ref-legend"><span class="ref-dot" style="background:{colors[status]}"></span><b>{status}</b> &nbsp; {count} projects<small>{notes[status]}</small></div>',unsafe_allow_html=True)
    with st.container(border=True,key='ref-review'):
        review=d[d.project_stress_vulnerability_class.isin(['HIGH','ELEVATED']) | d.final_ews_status.isin(['AMBER','RED']) | d.integrated_evidence_quality_class.fillna('LOW').isin(['LOW','INSUFFICIENT_EVIDENCE'])]
        review=review.sort_values('project_stress_vulnerability_score',ascending=False,na_position='last')
        card_title('Projects requiring review',f'Highest-priority {min(5,len(review))} of {len(review)} flagged projects · full register below')
        if review.empty: st.info('No selected projects meet these review criteria.')
        else:
            def pretty(v): return text(v).replace('_',' ').capitalize()
            rows=[]
            for _,row in review.head(5).iterrows():
                evidence=pretty(row.integrated_evidence_quality_class)
                posture=pretty(row.get('credit_committee_posture'))
                pill='low' if evidence=='Low' else 'partial'
                company=row.company.replace('Private Limited','').replace('Limited','').strip()
                dot={'HIGH':'#ee8a16','ELEVATED':'#ee8a16','MODERATE':'#efc334','LOW':'#0c9f78'}.get(row.project_stress_vulnerability_class,'#9bacbf')
                rows.append(f'<tr><td>{escape(company)}</td><td>{escape(text(row.state))}</td><td><span class="ref-dot" style="background:{dot}"></span>{escape(pretty(row.project_stress_vulnerability_class))}</td><td><span class="ref-pill {pill}">{escape(evidence)}</span></td><td><span class="ref-pill">{escape(posture)}</span></td></tr>')
            st.markdown('<div class="ref-table-scroll"><table class="ref-table"><thead><tr><th>Project</th><th>State</th><th>Vulnerability</th><th>Evidence</th><th>Review status</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>',unsafe_allow_html=True)
    st.markdown(f'<div class="ref-meta">Universe cards: all {len(master)} ecosystem projects · Charts and evidence coverage: {len(d)} selected projects · Evidence coverage: {covered}/{len(d)} have a source-verified row, not complete underwriting.</div>',unsafe_allow_html=True)
    with st.expander('Full portfolio register & concentration'):
        a,b,c=st.columns(3)
        a.metric('Selected projects',len(d))
        b.metric('Disclosed investment',money(d.investment_crore.sum(min_count=1)))
        c.metric('Stress eligible',int(d.banking_eligible.sum()))
        table(d,['project_id','company','state','project_type','investment_crore','validated_cluster','project_stress_vulnerability_class','final_ews_status','integrated_evidence_quality_class'])
        amounts=d.dropna(subset=['investment_crore']).groupby('state',dropna=False).investment_crore.sum(min_count=1).reset_index()
        if not amounts.empty and amounts.investment_crore.sum()>0:
            amounts['share_pct']=100*amounts.investment_crore/amounts.investment_crore.sum()
            chart(px.bar(amounts,x='state',y='investment_crore',hover_data=['share_pct'],labels={'investment_crore':'Disclosed investment (₹ crore)','state':'State'},title='Geographic concentration of disclosed investment',color_discrete_sequence=['#0f766e']),'concentration')
            st.caption(f'State HHI: {((amounts.share_pct/100)**2).sum():.3f} (0–1). Project investment is not bank exposure. Investment missing for {d.investment_crore.isna().sum()} selected projects.')
        download(d,'Download selected portfolio','selected_portfolio.csv')

def explorer(d,data):
    labels=dict(zip(d.project_id,d.company+' · '+d.project_id))
    pid=st.selectbox('Project',d.project_id,format_func=labels.get)
    row=d.set_index('project_id').loc[pid]
    st.subheader(labels[pid])
    a,b,c=st.columns(3); a.metric('Investment',money(row.investment_crore)); b.metric('Structural cluster',text(row.validated_cluster)); c.metric('Research grade',text(row.indicative_model_risk_grade))
    fields=['project_scope','state','project_type','baseline_score','severe_score','project_stress_vulnerability_score','p95_score','p99_score','mean_simulated_score','monte_carlo_rank_stability','final_ews_status','monitoring_maturity','credit_committee_posture','integrated_evidence_quality_class','critical_review_flags']
    table(pd.DataFrame({'Measure':fields,'Saved value':[text(row.get(f)) for f in fields]}))
    st.info(text(row.get('integrated_credit_committee_explanation')))
    risks=subset(data,'stress',[pid])
    if not risks.empty:
        st.markdown('**Severe-stress score contributions**')
        con=contributions(risks.iloc[0],.5)
        chart(px.bar(con,x='scenario_points',y='driver',orientation='h',labels={'scenario_points':'Contribution (score points)'},color_discrete_sequence=['#2563eb']),'drivers')
        st.caption('Exact weighted contributions from the deterministic formula; these are not SHAP values or causal effects.')
    with st.expander('Borrower financial evidence and scope',expanded=True):
        st.caption('Statement scope and financial year must be read together. Parent/group evidence is not project-company financial evidence.')
        table(subset(data,'borrower',[pid]))
    with st.expander('Source evidence and information gaps'):
        table(subset(data,'evidence',[pid])); table(subset(data,'gaps',[pid]))
    summary=pd.DataFrame({'field':row.index,'value':[text(v) for v in row.values]})
    download(summary,'Download project review summary',f'{pid}_review.csv')
    compare=st.multiselect('Compare two or three projects',list(d.project_id),default=list(d.project_id[:min(2,len(d))]),max_selections=3,format_func=labels.get)
    if len(compare)>=2:
        table(d[d.project_id.isin(compare)],['project_id','company','investment_crore','validated_cluster','baseline_score','severe_score','p95_score','p99_score','indicative_model_risk_grade','final_ews_status','integrated_evidence_quality_class'])
    else: st.info('Select at least two projects for comparison.')

def structural(d,data):
    points=d.dropna(subset=['PC1','PC2']).copy()
    colors=['#0875e8','#0aab98','#8b5cf6','#f08b24','#df4968','#4396b5']
    palette={f'Segment {i}':colors[i] for i in range(6)}
    a,b,c=st.columns(3)
    a.metric('Mapped projects',f'{len(points)} / {len(d)}')
    b.metric('Segments in selection',points.validated_cluster.nunique())
    c.metric('Model approach','PCA + clustering')
    if len(points):
        points['Segment']=points.validated_cluster.map(lambda v:f'Segment {int(v)}' if pd.notna(v) else 'Not available')
        left,right=st.columns([2.1,1])
        with left,st.container(border=True,key='panel-structural'):
            card_title('Structural landscape','Each point is a project. Nearby projects share similar structural features.')
            fig=px.scatter(points,x='PC1',y='PC2',color='Segment',hover_name='company',hover_data={'project_id':True,'project_type':True,'state':True,'PC1':':.2f','PC2':':.2f'},color_discrete_map=palette,labels={'PC1':'Principal component 1','PC2':'Principal component 2','project_id':'Project','project_type':'Type','state':'State'})
            fig.update_traces(marker=dict(size=19,opacity=.95,line=dict(width=2,color='#fff')))
            fig.update_layout(height=430,margin=dict(l=55,r=20,t=60,b=50),paper_bgcolor='#fff',plot_bgcolor='#f8fbff',font=dict(family='Segoe UI, Arial',size=13,color='#344c73'),legend=dict(title=None,orientation='h',y=1.14,x=0),hoverlabel=dict(bgcolor='#102235',font_color='#fff'),xaxis=dict(gridcolor='#e4edf7',zeroline=False),yaxis=dict(gridcolor='#e4edf7',zeroline=False))
            st.plotly_chart(fig,key='pca',width='stretch',theme=None,config={'displayModeBar':False})
        with right,st.container(border=True,key='panel-composition'):
            card_title('Segment composition','Project counts within your current selection')
            counts=points.Segment.value_counts().sort_index().rename_axis('Segment').reset_index(name='Projects')
            fig=px.bar(counts,x='Projects',y='Segment',orientation='h',color='Segment',color_discrete_map=palette,text='Projects')
            fig.update_traces(textposition='outside',cliponaxis=False,marker_cornerradius=5)
            fig.update_layout(height=430,showlegend=False,paper_bgcolor='#fff',plot_bgcolor='#fff',margin=dict(l=80,r=30,t=40,b=50),font=dict(size=13,color='#344c73'),xaxis=dict(title='Projects',dtick=1,gridcolor='#eaf0f6',range=[0,counts.Projects.max()*1.3]),yaxis=dict(title=None))
            st.plotly_chart(fig,key='segment_counts',width='stretch',theme=None,config={'displayModeBar':False})
    else: st.info('PCA coordinates are unavailable for this selection.')
    variance=data['variance']
    if not variance.empty:
        with st.container(border=True,key='panel-variance'):
            card_title('What the components explain','Share of variation captured across the reference ecosystem')
            fig=px.bar(variance,x='component',y='explained_variance',hover_data={'cumulative_variance':':.1%'},color_discrete_sequence=['#0875e8'],labels={'component':'Component','explained_variance':'Explained variation'})
            fig.update_traces(marker_cornerradius=4); fig.update_yaxes(tickformat='.0%')
            chart(fig,'variance')
    with st.expander('Segment profiles & model quality'):
        st.caption('Segments describe structural similarity, not default risk. Quality measures refer to the full reference ecosystem; the model remains unchanged when filters are applied.')
        seg=data['segments']; table(seg[seg.cluster.isin(d.validated_cluster.dropna())] if not seg.empty else seg,['cluster','provisional_cluster_name','key_characteristics','project_count'])
        table(data['validation'],['k','silhouette','kmeans_hierarchical_ari','bootstrap_runs','mean_bootstrap_ari','validation_score'])

def stress_page(d,data,signature):
    card_title('Compare the impact of stress','Choose a scenario to see how manufacturing vulnerability changes.')
    preset=st.selectbox('Scenario',['Baseline','Mild','Moderate','Severe','Custom'],key='stress_preset')
    severity=st.slider('Macro risk severity (fraction of remaining headroom)',0.0,.5,.0,.01,key='severity') if preset=='Custom' else stress_engine.SCENARIOS[preset.lower()]
    st.button('Reset to baseline',on_click=reset_stress)
    with st.expander('Scenario assumptions'):
        st.caption(f'Shock severity: {severity:.2f} on a 0–0.50 research scale. The four macro/banking risk channels change; project size and geographic concentration remain fixed. This is not a forecast of GDP or interest rates.')
    try: out,gate=calculate_stress(data['stress'],tuple(d.project_id),severity)
    except (ValueError,RuntimeError,KeyError) as exc: st.error(str(exc)); return
    a,b,c=st.columns(3)
    change=round(float(out.score_change.mean()),1)
    a.metric('Scenario',preset); b.metric('Projects assessed',f'{len(out)} / {len(d)}'); c.metric('Average score change','0.0 points' if change==0 else f'{change:+.1f} points')
    labels=dict(zip(out.project_id,out.company.str.replace('Private Limited','',regex=False).str.replace('Limited','',regex=False).str.slice(0,22)))
    fig=go.Figure()
    for field,label,color in [('baseline_score','Baseline','#0875e8'),('scenario_score',f'{preset} scenario','#f09b28')]:
        fig.add_bar(x=out.project_id,y=out[field],name=label,marker_color=color,marker_cornerradius=4,customdata=out.company,hovertemplate='%{customdata}<br>'+label+': %{y:.2f}<extra></extra>')
    fig.update_xaxes(tickmode='array',tickvals=out.project_id,ticktext=list(labels.values()),tickangle=-25,title=None)
    fig.update_yaxes(title='Vulnerability score (0–100)',range=[0,105])
    with st.container(border=True,key='panel-stress'):
        card_title('Baseline vs scenario','Blue shows baseline · amber shows your selected scenario')
        chart(fig,'stress')
    if severity==0: st.caption('Baseline is selected, so both bars have the same value. Choose Mild, Moderate or Severe to compare a stressed scenario.')
    table(out,['project_id','company','baseline_score','scenario_score','score_change','baseline_rank_filtered','scenario_rank_filtered','rank_change'])
    st.caption('Ranks are recalculated within the supported filtered cohort. Positive rank change means movement toward a higher vulnerability rank. Saved grades and committee postures are not recomputed.')
    download(out,'Download calculated stress results','stress_scenario.csv')
    if st.button('Save stress scenario locally'):
        target=archive_scenario('stress',out,{'severity':severity,'scope':list(d.project_id)},signature); st.success(f'Saved separately: {target.relative_to(ROOT)}')

def monte(d,data):
    mc=subset(data,'mc',d.project_id)
    card_title('Explore simulated vulnerability','Results from completed simulations across the manufacturing portfolio')
    draws=data['draws']; available=[p for p in d.project_id if p in draws]
    if available:
        names=dict(zip(d.project_id,d.company+' · '+d.project_id))
        pid=st.selectbox('Project distribution',available,format_func=names.get)
        vals=pd.to_numeric(draws[pid],errors='coerce').dropna()
        if not vals.empty:
            a,b,c,e=st.columns(4)
            a.metric('Simulation draws',f'{len(vals):,}'); b.metric('Mean score',f'{vals.mean():.1f}'); c.metric('95th percentile',f'{vals.quantile(.95):.1f}'); e.metric('99th percentile',f'{vals.quantile(.99):.1f}')
            with st.container(border=True,key='panel-distribution'):
                card_title('Simulation distribution','Dashed lines mark the mean and the 95th-percentile score')
                fig=px.histogram(x=vals,nbins=45,labels={'x':'Simulated vulnerability score','y':'Simulation draws'},color_discrete_sequence=['#18ab9b'])
                fig.update_yaxes(title='Simulation draws')
                fig.update_traces(marker_line_color='#fff',marker_line_width=.7)
                fig.add_vline(x=vals.mean(),line_color='#0875e8',line_dash='dash',annotation_text='Mean',annotation_position='top left')
                fig.add_vline(x=vals.quantile(.95),line_color='#f09b28',line_dash='dash',annotation_text='95th percentile',annotation_position='top right')
                chart(fig,'mc_hist')
        download(draws[['simulation_id',pid]],'Download archived draws',f'{pid}_archived_draws.csv')
    else: st.info('No raw archived simulation scores available for the selected projects. A distribution cannot be reconstructed from summary percentiles.')
    with st.container(border=True,key='panel-simulation-results'):
        card_title('Portfolio simulation results',f'{len(mc)} of {len(d)} selected projects have completed simulation statistics')
        table(mc,['project_id','company','mean_simulated_score','p95_score','p99_score','monte_carlo_rank_stability'])
    with st.expander('About these simulations & availability'):
        st.write('These charts use the actual stored simulation draws from the project’s completed analysis. They are available for inspection and export. Starting a new simulation is currently unavailable because the original random seed and sampling method still need reproducibility checks.')
        st.caption('The 95th percentile is a score exceeded in 5% of the completed draws, not a default probability or a monetary loss. Ranking frequency is also not probability of default.')
    with st.expander('Ranking stability across methods'):
        table(data['cross_method'])

def allocation(d,data,signature):
    st.info('Saved allocation policy explorer. Budget scaling preserves archived shares; it does not rerun an optimizer. The original solver/objective implementation is unavailable, so no new optimization claim is made.')
    policies=data['policy']; allocations=data['allocations']
    if policies.empty or allocations.empty: st.error('Allocation sources unavailable. Restore the registered policy and allocation CSVs.'); return
    style=st.selectbox('Archived risk / scale policy',sorted(policies.weight_scenario.unique()))
    pool=policies[policies.weight_scenario.eq(style)]
    pid=st.selectbox('Archived policy scenario',pool.scenario_id.tolist())
    policy=pool[pool.scenario_id.eq(pid)].iloc[0]
    st.caption(f'Archived weights: risk {policy.risk_weight:.2f}, scale {policy.scale_weight:.2f}. Saved limits: project ≤ {policy.max_project_share_limit:.0%}; state ≤ {policy.max_state_share_limit:.0%}; project ≥ {policy.min_project_share_limit:.0%}. These weights describe the saved policy; the exact objective has not been recovered.')
    budget=st.number_input('Scenario budget (₹ crore)',min_value=1.0,max_value=10000000.0,value=10000.0,step=1000.0)
    with st.expander('Check tighter diversification limits'):
        st.caption('These review limits test the saved shares. They do not solve for a new allocation.')
        cap=st.number_input('Maximum project share',0.0,1.0,float(policy.max_project_share_limit),.01,key=f'cap_{pid}')
        state_cap=st.number_input('Maximum state share',0.0,1.0,float(policy.max_state_share_limit),.01,key=f'statecap_{pid}')
        floor=st.number_input('Minimum project share',0.0,1.0,float(policy.min_project_share_limit),.01,key=f'floor_{pid}')
    eligible=d[d.banking_eligible]
    try: out,checks=allocate_saved_policy(allocations,policy,budget,eligible.project_id,cap,state_cap,floor)
    except ValueError as exc: st.error(str(exc)); return
    st.success('New budget scaling calculated · all displayed constraints passed')
    a,b,c=st.columns(3); a.metric('Allocated',money(out.scenario_allocation_crore.sum())); b.metric('Unused budget',money(max(0,budget-out.scenario_allocation_crore.sum()))); c.metric('Project HHI',f'{(out.allocation_share**2).sum():.3f}')
    chart(px.bar(out,x='project_id',y='scenario_allocation_crore',hover_data=['company','state','allocation_share'],labels={'scenario_allocation_crore':'Scenario allocation (₹ crore)'},color_discrete_sequence=['#0f766e']),'allocation')
    table(out,['project_id','company','state','allocation_share','scenario_allocation_crore']); download(out,'Download budget scenario','allocation_scenario.csv')
    if st.button('Save allocation scenario locally'):
        target=archive_scenario('allocation',out,{'policy':int(pid),'budget_crore':budget,'maximum_project_share':cap,'maximum_state_share':state_cap,'minimum_project_share':floor},signature); st.success(f'Saved separately: {target.relative_to(ROOT)}')
    with st.expander('Archived policy sensitivity and constraint checks'):
        table(pd.DataFrame({'Check':[k.replace('_',' ').capitalize() for k in checks],'Result':['Passed' if v else 'Needs review' for v in checks.values()]}))
        st.caption('Historical sensitivity outputs below are saved results. Budget scaling leaves concentration and the weighted stress index unchanged.')
        table(pool,['scenario_id','budget_crore','max_project_share_limit','max_state_share_limit','min_project_share_limit','portfolio_stress_index','project_hhi','state_hhi'])

def committee(d,data):
    st.caption('Sortable research review register. Click a column heading to sort. Current EWS and committee posture come from integrated banking outputs; historic research grades remain separately labeled.')
    cols=['project_id','company','indicative_model_risk_grade','final_ews_status','monitoring_maturity','credit_committee_posture','committee_monitoring_tier','critical_review_flags','integrated_evidence_quality_class','integrated_risk_component_coverage_pct']
    register=d[[c for c in cols if c in d]].copy()
    gaps=subset(data,'gaps',d.project_id)
    register['reported_information_gaps']=register.project_id.map(gaps.groupby('project_id').size()) if not gaps.empty else np.nan
    table(register); download(register,'Download filtered review register','committee_register.csv')
    st.subheader('Evidence register'); table(subset(data,'evidence',d.project_id)); st.subheader('Information gaps'); table(gaps)
    st.caption('A missing gap count means no matching gap-register row; it does not certify complete underwriting evidence.')

def health_page(data,health,master,issues):
    validation=data['frozen_validation']; method=data['method']
    a,b,c=st.columns(3)
    a.metric('Data sources available',f'{health.status.eq("AVAILABLE").sum()} / {len(health)}')
    b.metric('Structural model','Checked' if validation.get('cluster_recovery_pass') is True else 'Review needed')
    deterministic=method.get('deterministic_stress',{}).get('deterministic_method_reproduction_pass')
    c.metric('Stress calculations','Checked' if deterministic is True else 'Review needed')
    with st.container(border=True,key='panel-readiness'):
        card_title('Analysis readiness','Readable summaries of the checks behind the dashboard')
        rows=[('Feature preparation',validation.get('raw_feature_contract_pass')),('Feature scaling',validation.get('stored_z_reconstruction_pass')),('PCA projection',validation.get('pca_reconstruction_pass')),('Segment assignment',validation.get('cluster_recovery_pass')),('Stress calculation',deterministic)]
        table(pd.DataFrame({'Analysis':[name for name,_ in rows],'Status':['Checked' if passed is True else 'Review needed' for _,passed in rows]}))
        st.caption('Checks confirm that the saved reference analysis can be reproduced; they do not establish predictive accuracy for defaults.')
        st.write('**Monte Carlo:** completed simulation results are available. New simulation runs await reproducibility checks.')
    with st.container(border=True,key='panel-coverage'):
        card_title('Evidence coverage','Coverage uses the relevant project universe for each measure')
        manufactured=master[master.project_scope.eq('Manufacturing')]
        specs=[('Project investment','investment_crore',manufactured),('Structural segments','validated_cluster',master),('Stress results','severe_score',manufactured),('Monte Carlo tail scores','p95_score',manufactured),('Early-warning signals','final_ews_status',manufactured),('Evidence quality','integrated_evidence_quality_class',manufactured)]
        coverage=pd.DataFrame([{'Measure':label,'Available':int(frame[field].notna().sum()),'Projects':len(frame),'Coverage':f'{frame[field].notna().mean():.0%}' if len(frame) else 'Not available'} for label,field,frame in specs])
        table(coverage)
        borrower=data['borrower']
        missing=manufactured[~manufactured.project_id.isin(borrower.get('project_id',pd.Series(dtype=str)))]
        if not missing.empty:
            names=[f'{r.company} · {r.state} ({r.project_id})' for _,r in missing.iterrows()]
            st.write('**Financial evidence to collect:** '+ '; '.join(names)+'. No borrower financial profile is available for '+str(len(missing))+' manufacturing project(s).')
            st.caption('This is a source-data gap. Financial figures from another project or company have not been substituted.')
        st.caption('A borrower-panel entry can still contain unavailable financial figures; profile coverage alone does not mean complete financial evidence.')
        other=[i for i in issues if not i.startswith('borrower:')]
        if other:
            st.warning(f'{len(other)} additional source relationships need review. See the downloadable data-quality report.')
            download(pd.DataFrame({'data_quality_issue':other}),'Download data-quality details','data_quality_details.csv')
    with st.expander('Source availability & update times'):
        sources=health[['source','status','rows','file_modified_utc']].copy()
        names={'ecosystem':'Ecosystem master','canonical':'Manufacturing master','master':'Integrated banking panel','committee':'Credit committee','final':'Research grades','stress':'Stress analysis','mc':'Simulation summaries','draws':'Simulation draws','borrower':'Borrower financial profiles','evidence':'Source evidence','gaps':'Information gaps','ews':'Early-warning panel','manifest':'Model reference','frozen_validation':'Structural checks','method':'Analysis checks','clusters':'Segment assignments','variance':'PCA explained variation','validation':'Cluster quality','segments':'Segment profiles','allocations':'Allocation results','policy':'Allocation policies','cross_method':'Ranking comparison','new_mc':'New-project simulation status'}
        sources['source']=sources.source.map(lambda v:names.get(v,v.replace('_',' ').capitalize()))
        sources['status']=sources.status.map({'AVAILABLE':'Available','UNAVAILABLE':'Needs attention'})
        table(sources)
        st.caption('Update times describe local source files, rather than verified publication dates.')
        download(health,'Download source health','source_health.csv')
