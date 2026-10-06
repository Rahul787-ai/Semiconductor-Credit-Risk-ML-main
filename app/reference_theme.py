"""Reference-inspired presentation layer; no external fonts or image services."""
from html import escape
from urllib.parse import quote
import streamlit as st

PATHS = {
    'home': '<path d="m3 10 9-7 9 7v11h-6v-7H9v7H3z"/>',
    'file': '<path d="M6 3h8l4 4v14H6zM14 3v5h5"/>',
    'bars': '<path d="M5 21V11m7 10V3m7 18V8"/>',
    'pulse': '<path d="M2 12h5l3-9 4 18 3-9h5"/>',
    'network': '<circle cx="5" cy="18" r="3"/><circle cx="19" cy="5" r="3"/><path d="m7 16 10-9"/>',
    'pie': '<path d="M12 3v9h9A9 9 0 1 1 12 3zM16 3a7 7 0 0 1 5 5h-5z"/>',
    'users': '<circle cx="9" cy="7" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3m1-17a3 3 0 0 1 0 6m2 5a5 5 0 0 1 3 4v2"/>',
    'shield': '<path d="m12 3 9 4v6c0 5-9 9-9 9s-9-4-9-9V7z"/>',
    'chip': '<rect x="5" y="5" width="14" height="14" rx="1"/><rect x="9" y="9" width="6" height="6"/><path d="M8 1v4m8-4v4M8 19v4m8-4v4M1 8h4m-4 8h4m14-8h4m-4 8h4"/>',
    'factory': '<path d="M3 21V10l6 3V8l7 4V3h4v18zM7 17h1m4 0h1m4 0h1"/>',
    'gear': '<path d="m9 3-1 3-3 1-2 3 2 2-1 4 3 2 3-1 2 3 4-1 1-3 3-1 1-4-3-2 1-3-4-2-2 2z"/><circle cx="12" cy="12" r="3"/>',
    'flask': '<path d="M9 3h6m-5 0v6l-6 11h16L14 9V3M8 15h8"/>',
}

def icon(name, color='currentColor'):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{PATHS[name]}</svg>'

CSS = '''<style>
:root {--ink:#0b1534;--muted:#7083a3;--line:#dce5ef;--blue:#0875e8;}
.stApp {background:#f2f6fa;}
.stApp, input, button, select {font-family:Inter,"Segoe UI",Arial,sans-serif;}
[data-testid="stHeader"] {background:transparent;height:2.3rem;}
[data-testid="stAppDeployButton"],[data-testid="stMainMenu"] {display:none;}
.block-container {max-width:1600px;padding:2rem 1.55rem 2rem;}
[data-testid="stVerticalBlock"] {gap:1rem;}
[data-testid="stElementContainer"]:has(style) {display:none;}
h1,h2,h3,h4 {color:var(--ink)!important;letter-spacing:-.035em;}
[data-testid="stSidebar"] {background:#102235;border-right:1px solid #1b3046;min-width:250px!important;max-width:250px!important;}
[data-testid="stSidebarUserContent"] {padding:1.6rem .65rem;}
[data-testid="stSidebarHeader"] {height:32px;min-height:32px;padding:0;}
.ref-brand {display:flex;align-items:center;gap:15px;padding:0 12px 26px;color:#acd0ed;font-size:15px;font-weight:500;line-height:1.35;letter-spacing:.01em;}
.ref-brand svg {width:36px;height:36px;color:#2497ff;flex-shrink:0;}
[data-testid="stSidebar"] [role="radiogroup"] {gap:9px;}
[data-testid="stSidebar"] [role="radiogroup"]>div {width:100%;}
[data-testid="stSidebar"] [role="radiogroup"] label {width:100%;box-sizing:border-box;display:flex;}
[data-testid="stSidebar"] [role="radiogroup"] label>div>div:first-child {display:none;}
[data-testid="stSidebar"] [role="radiogroup"] label {margin:0!important;padding:13px 12px!important;min-height:49px;border-radius:7px;position:relative;border-left:3px solid transparent;gap:14px;}
[data-testid="stSidebar"] [role="radiogroup"] label>div:first-child {display:none;}
[data-testid="stSidebar"] [role="radiogroup"] label:before {content:"";width:23px;height:23px;background-size:contain;background-repeat:no-repeat;flex-shrink:0;}
[data-testid="stSidebar"] [role="radiogroup"] label p {color:#afc6df!important;font-size:15px!important;white-space:nowrap;}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {background:#174f87;border-left-color:#2c9afa;}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {color:#fff!important;font-weight:600;}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {background:#1a3b5c;}
[data-testid="stSidebar"] input {background:#19344d!important;color:#fff!important;}
[data-testid="stSidebar"] [data-testid="stExpander"] {background:transparent;border-color:#294158;}
.ref-heading {font-size:clamp(30px,3.3vw,43px);line-height:1.1;font-weight:750;letter-spacing:-.045em;color:var(--ink);margin:0 0 4px;}
.ref-subtitle {font-size:20px;color:var(--muted);line-height:1.4;}
.ref-badge {display:inline-flex;gap:8px;align-items:center;background:#e3f1ff;border:1px solid #d4e9ff;border-radius:7px;color:#0875e8;font-size:13px;padding:10px 12px;white-space:nowrap;}
.ref-badge svg {width:19px;height:19px;}
[data-testid="stMetric"] {background:#fff;border:1px solid var(--line);box-shadow:0 1px 1px #162f5010;border-radius:8px;padding:17px 18px;min-height:112px;}
[data-testid="stMetricLabel"] p {color:#364d73!important;font-weight:500;font-size:14px;}
[data-testid="stMetricValue"] {color:var(--ink)!important;font-size:43px!important;line-height:1.25;font-weight:750;letter-spacing:-.05em;}
.ref-kpi {height:112px;background:#fff;border:1px solid var(--line);border-radius:8px;padding:17px 18px;margin-bottom:16px;box-sizing:border-box;position:relative;}
.ref-kpi-label {color:#364d73;font-size:14px;font-weight:500;}
.ref-kpi-value {font-size:43px;line-height:1.35;font-weight:750;letter-spacing:-.05em;color:var(--ink);}
.ref-kpi-icon {position:absolute;right:16px;top:31px;background:#e9f4ff;color:#0875e8;width:52px;height:52px;border-radius:50%;display:grid;place-items:center;}
.ref-kpi-icon.teal {background:#e6f6f1;color:#078982;}
.ref-kpi-icon svg {width:28px;height:28px;}
[data-testid="stLayoutWrapper"]:has(>.st-key-ref-filters), .st-key-ref-filters {background:#fff;border-radius:8px;}
[data-testid="stVerticalBlockBorderWrapper"]>div, [data-testid="stVerticalBlock"] [data-testid="stVerticalBlockBorderWrapper"] {border-color:var(--line)!important;border-radius:8px!important;}
[data-testid="stVerticalBlock"] [data-testid="stVerticalBlockBorderWrapper"] {background:#fff;}
.st-key-ref-risk,.st-key-ref-ews,.st-key-ref-review {background:#fff!important;}
[class*="st-key-panel-"] {background:#fff!important;}
@media(max-width:1100px){[data-testid="stHorizontalBlock"]:has(.st-key-panel-structural){flex-wrap:wrap}[data-testid="stHorizontalBlock"]:has(.st-key-panel-structural)>[data-testid="stColumn"]{flex:1 1 100%;width:100%}}
[data-testid="stSelectbox"] [data-baseweb="select"]>div {border-color:var(--line);border-radius:6px;background:#fbfdff;min-height:40px;}
.ref-card-title {font-size:18px;line-height:1.3;letter-spacing:-.025em;font-weight:700;color:var(--ink);}
.ref-card-note {font-size:13px;color:var(--muted);margin-top:3px;}
.ref-meta {font-size:11px;color:#7890aa;line-height:1.5;}
.stDownloadButton>button {background:#0875e8!important;color:#fff!important;border:1px solid #0875e8!important;border-radius:7px;padding:9px 14px;white-space:nowrap;}
.stDownloadButton>button p {color:#fff!important;font-size:14px!important;font-weight:600;}
.stButton>button {border-radius:7px;}
[data-testid="stDataFrame"] {border-radius:7px;border:1px solid var(--line);}
.ref-table-scroll {overflow-x:auto;}
.ref-table {width:100%;border-collapse:collapse;font-size:13px;color:#15264a;}
.ref-table th {text-align:left;background:#eef3f8;color:#3b5173;font-size:12px;font-weight:600;padding:10px 12px;white-space:nowrap;}
.ref-table th,.ref-table td {border-left:0!important;border-right:0!important;}
.ref-table td {border-bottom:1px solid #edf1f6;padding:12px;vertical-align:middle;}
.ref-table td:first-child {font-weight:600;max-width:280px;}
.ref-table tr:last-child td {border-bottom:0;}
.ref-pill {display:inline-block;padding:4px 10px;border-radius:4px;background:#e2efff;color:#075fc9;font-size:12px;}
.ref-pill.low {background:#ffe1e7;color:#86283f;}.ref-pill.partial {background:#fff4d3;color:#7d601c;}
.ref-dot {display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:8px;background:#eb9a17;}
.ref-legend {font-size:13px;color:#15264a;margin:19px 0;line-height:1.6;}.ref-legend small {display:block;color:#7184a1;margin-left:19px;font-size:11px;}
.ref-footer {color:#7d90aa;font-size:11px;text-align:right;padding:4px 0;}
@media(max-width:1000px){.ref-heading{font-size:32px}.ref-subtitle{font-size:16px}.ref-kpi-icon{width:40px;height:40px;right:10px}.ref-kpi-value{font-size:36px}.ref-kpi{padding:14px 12px}}
@media(min-width:701px) and (max-width:1100px){[data-testid="stHorizontalBlock"]:has(.st-key-ref-risk),[data-testid="stHorizontalBlock"]:has(.ref-heading){flex-wrap:wrap}[data-testid="stHorizontalBlock"]:has(.st-key-ref-risk)>[data-testid="stColumn"]{width:100%;flex:1 1 100%}[data-testid="stHorizontalBlock"]:has(.ref-heading)>[data-testid="stColumn"]:first-child{flex:1 1 100%}[data-testid="stHorizontalBlock"]:has(.ref-kpi){flex-wrap:wrap}[data-testid="stHorizontalBlock"]:has(.ref-kpi)>[data-testid="stColumn"]{flex:1 1 45%}}
@media(max-width:700px){.block-container{padding:2rem .8rem 1rem}[data-testid="stHorizontalBlock"]{flex-wrap:wrap}[data-testid="stColumn"]{min-width:240px}.ref-heading{font-size:30px}.ref-kpi{height:100px}.ref-table{min-width:640px}}
</style>'''

def apply_reference_theme():
    nav=['home','file','bars','pulse','network','pie','users','shield']
    rules=''
    for i,name in enumerate(nav,1):
        svg=quote(icon(name,'#afc6df'))
        rules+=f'[data-testid="stSidebar"] [role="radiogroup"]>div:nth-child({i}) label:before {{background-image:url("data:image/svg+xml,{svg}");}}'
    st.markdown(CSS+f'<style>{rules}</style>',unsafe_allow_html=True)

def card_title(title,note=''):
    st.markdown(f'<div class="ref-card-title">{escape(title)}</div><div class="ref-card-note">{escape(note)}</div>',unsafe_allow_html=True)

def kpi(label,value,name,teal=False):
    st.markdown(f'<div class="ref-kpi"><div class="ref-kpi-label">{escape(label)}</div><div class="ref-kpi-value">{escape(str(value))}</div><div class="ref-kpi-icon {"teal" if teal else ""}">{icon(name)}</div></div>',unsafe_allow_html=True)
