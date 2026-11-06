"""QFAIM Academic Edition — four-block research studio and refreshable screener."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import streamlit as st
from qfaim_engine import METRICS, fetch, score

ROOT = Path(__file__).resolve().parent
LIBRARY = json.loads((ROOT / 'BLOCK3_PROMPT_LIBRARY.json').read_text(encoding='utf-8'))
LOOKUP = {p['title']: p for p in LIBRARY}
CUSTOM = '✍️ Custom — write my own'
BEHAVIORS = {
    'Beginner-friendly teacher': 'Explain everything in straightforward language suitable for someone new to investing. Define each financial term when first used, use simple examples, compare risks fairly, cite dated sources, and never make up numbers.',
    'Institutional equity analyst': 'Act as a rigorous institutional equity analyst. Prefer dated company filings and primary sources. Separate facts, estimates and opinions. Compare peers, explain valuation and scoring methodology, show downside risks and catalysts, and never invent missing data.',
    'Financial advisor / client-ready': 'Explain the research in clear, client-ready language. Emphasize diversification, uncertainty, investment time horizon and downside risk. Use reliable dated sources. Do not imply personalized financial advice.',
    'Long-term value investor': 'Analyze price versus normalized earnings, asset quality, capital allocation, financial strength, margin of safety, and possible value traps. Use explicit assumptions and reliable dated sources.',
    'Growth and quality investor': 'Focus on durable business advantages, revenue and earnings growth, margins, reinvestment, management execution, and reasonable valuation. Compare peers and disclose risks.',
    'Quantitative researcher': 'Define the investable universe, factors, data dates, normalization, weights, missing-data treatment and factor coverage. Provide auditable comparisons and do not imply full-market coverage unless actually verified.',
}
DEFAULT_FACTORS = ['Trailing P/E', 'P/B', 'ROE', 'Revenue Growth', 'Earnings Growth', 'Relative Strength 6M', 'RSI 14']

st.set_page_config(page_title='QFAIM | Academic Research Terminal', page_icon='🎓', layout='wide', initial_sidebar_state='collapsed')
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Libre+Baskerville:wght@400;700&display=swap');
:root {--forest:#174e3a;--deep:#12382b;--cream:#f8f6f0;--border:#d9d8cb;--muted:#6b766d;}
html,body,[class*="css"],.stApp {font-family:'DM Sans',sans-serif;}
.stApp {background:var(--cream);}
.block-container {max-width:1370px;padding-top:1.1rem;padding-bottom:5rem;}
h1,h2,h3 {font-family:'Libre Baskerville',Georgia,serif;letter-spacing:-.025em;color:#173d2f;}
h1 {font-size:2.4rem!important;line-height:1.22!important;} h2 {font-size:1.45rem!important;}
p,li {line-height:1.55;}
[data-testid="stHeader"] {background:transparent;}
[data-testid="stSidebar"] {background:#eeeae0;}
[data-testid="stTabs"] button {font-weight:650;}
[data-testid="stMetric"] {background:#fffefa;border:1px solid var(--border);border-radius:12px;padding:13px 17px;}
[data-testid="stMetricLabel"] {color:#68766d;}
[data-testid="stExpander"] {background:#fffefa;border:1px solid var(--border);border-radius:12px;}
[data-testid="stVerticalBlockBorderWrapper"] {border-color:var(--border)!important;}
.stButton>button[kind="primary"],.stDownloadButton>button[kind="primary"] {background:#174e3a;color:white;border-radius:9px;border:1px solid #174e3a;}
.stButton>button,.stDownloadButton>button {border-radius:9px;}
.stTextInput input,.stTextArea textarea {background:#fffefa;}
.hero {border:1px solid #d7d4c4;border-radius:18px;background:linear-gradient(112deg,rgba(250,249,244,.97) 0%,rgba(250,249,244,.95) 58%,rgba(216,229,212,.72) 100%);padding:30px 34px 25px;margin:12px 0 22px;position:relative;overflow:hidden;}
.hero:after {content:'✦';position:absolute;right:5%;top:-53px;font-size:230px;color:rgba(23,78,58,.065);font-family:Georgia;pointer-events:none;}
.eyebrow {text-transform:uppercase;font-size:.69rem;font-weight:800;letter-spacing:.16em;color:#547c66;margin-bottom:9px;}
.hero-title {font-family:'Libre Baskerville',Georgia,serif;font-size:2.45rem;font-weight:700;color:#173e2e;letter-spacing:-.05em;line-height:1.2;max-width:900px;}
.hero-sub {max-width:780px;color:#536b5e;font-size:1.02rem;margin-top:10px;line-height:1.65;}
.hero-foot {font-size:.78rem;color:#647a6d;margin-top:18px;font-weight:600;}
.step-card {background:#fffefa;border:1px solid #dedbcf;border-radius:14px;padding:17px 16px;min-height:154px;box-shadow:0 2px 10px rgba(30,54,36,.035);}
.step-num {font-size:.72rem;font-weight:800;color:#718b77;letter-spacing:.08em;}
.step-title {font-family:'Libre Baskerville',Georgia,serif;color:#174e3a;font-size:1.05rem;margin:9px 0 7px;}
.step-copy {font-size:.84rem;line-height:1.48;color:#637168;}
.section-eyebrow {text-transform:uppercase;letter-spacing:.14em;color:#738478;font-size:.72rem;font-weight:800;margin:8px 0 8px;}
.soft-note {padding:12px 16px;border-left:3px solid #537c5b;background:#edf2e9;border-radius:0 9px 9px 0;color:#395c49;font-size:.9rem;}
.brandline {font-family:'Libre Baskerville',Georgia,serif;font-size:1.1rem;color:#173e2e;font-weight:700;}
hr {border-color:#d8d9ce;}
@media(max-width:700px){.hero{padding:20px}.hero-title{font-size:1.8rem}.block-container{padding-left:1rem;padding-right:1rem}}
</style>''', unsafe_allow_html=True)

for key, value in {
 'profile':'Recent college graduate exploring financial markets. Explain important ideas clearly.',
 'behavior_preset':'Beginner-friendly teacher', 'behavior':BEHAVIORS['Beginner-friendly teacher'],
 'task_choice':LIBRARY[0]['title'], 'task':LIBRARY[0]['task'],
 'category':'All topics', 'search':'', 'selected':DEFAULT_FACTORS,
 'tickers':'JPM, GS, MS', 'benchmark':'XLF', 'refresh_mins':10,
 'auto_refresh':False, 'min_coverage':50, 'bank_adjust':True,
 'last_results':None,'last_raw':None,'last_fetch':None,
}.items():
 if key not in st.session_state: st.session_state[key] = value

def choose_behavior(): st.session_state.behavior = BEHAVIORS[st.session_state.behavior_preset]
def choose_task():
 if st.session_state.task_choice != CUSTOM and st.session_state.task_choice in LOOKUP:
  st.session_state.task = LOOKUP[st.session_state.task_choice]['task']

def weights():
 return {m:st.session_state.get('weight_'+m,1.) for m in st.session_state.selected}

def build_prompt():
 w=weights()
 return '\n\n'.join([
  'QFAIM | EQUITY RESEARCH REQUEST',
  'BLOCK 1 — USER PROFILE\n'+st.session_state.profile,
  'BLOCK 2 — RESEARCH ASSISTANT INSTRUCTIONS\n'+st.session_state.behavior,
  'BLOCK 3 — RESEARCH ASSIGNMENT\n'+st.session_state.task,
  'BLOCK 4 — FINANCIAL FACTORS\n'+ ('\n'.join(f'• {m} (weight {w[m]:g})' for m in st.session_state.selected) or 'No factors selected.'),
  'RESEARCH STANDARDS\nUse dated, verifiable sources. Define unfamiliar terms. State universe, peer set, benchmark and data availability. Do not fabricate factor values or claim whole-market coverage without verification. Show risks and explain any normalization or missing-data handling. This is educational research, not individualized investment advice.'
 ])

st.markdown('<div class="brandline">▥ &nbsp; QFAIM <span style="font:500 .78rem DM Sans,sans-serif;color:#789082">/ RESEARCH TERMINAL</span></div>',unsafe_allow_html=True)
st.markdown('''<div class="hero"><div class="eyebrow">Independent equity research · Academic edition</div><div class="hero-title">Learn the market.<br>Research with confidence.</div><div class="hero-sub">A guided stock research workspace for curious beginners and experienced investors. Choose how your analyst thinks, explore 133 ready-made research ideas, and compare companies with transparent data.</div><div class="hero-foot">FOUR-BLOCK RESEARCH SYSTEM &nbsp; · &nbsp; 133 CURATED PROMPTS &nbsp; · &nbsp; REFRESHABLE STOCK SCREENING</div></div>''',unsafe_allow_html=True)

cols=st.columns(4,gap='small')
for c,(n,title,desc) in zip(cols,[('01','Your profile','Set your experience and learning goals.'),('02','Analyst style','Choose how research is explained.'),('03','Research question','Pick from 133 ideas or write your own.'),('04','Financial factors','Select and weight the metrics that matter.')]):
 with c:st.markdown(f'<div class="step-card"><div class="step-num">BLOCK {n}</div><div class="step-title">{title}</div><div class="step-copy">{desc}</div></div>',unsafe_allow_html=True)

studio, screener, guide = st.tabs(['✦  Research studio','▥  Stock screener','ⓘ  About & deployment'])
with studio:
 st.markdown('### Build your research assignment')
 st.caption('Complete the four blocks below. Your research prompt updates instantly as you edit.')
 left,right=st.columns([1.04,.96],gap='large')
 with left:
  with st.container(border=True):
   st.markdown('#### 01 / Who is this for?')
   st.text_area('Your background and goals',key='profile',height=94,help='For example: I am a media studies graduate and a beginner at investing.')
  with st.container(border=True):
   st.markdown('#### 02 / Choose your analyst')
   st.selectbox('Premade instruction style',list(BEHAVIORS),key='behavior_preset',on_change=choose_behavior)
   with st.expander('Customize these instructions'):
    st.text_area('Edit Block 2',key='behavior',height=155,label_visibility='collapsed')
  with st.container(border=True):
   st.markdown('#### 03 / What would you like to research?')
   st.caption('Browse by sector and company size, country, or beginner learning topic.')
   cat_options=['All topics']+sorted({p['category'] for p in LIBRARY})
   st.selectbox('Research category',cat_options,key='category')
   st.text_input('Find a research idea',key='search',placeholder='Try: media, Brazil, micro-cap, dividends…')
   q=st.session_state.search.lower().strip()
   filtered=[p for p in LIBRARY if (st.session_state.category=='All topics' or p['category']==st.session_state.category) and (not q or q in ' '.join([p['title'],p['task'],*p.get('tags',[])]).lower())]
   titles=[CUSTOM]+[p['title'] for p in filtered]
   if st.session_state.task_choice not in titles: titles.insert(1,st.session_state.task_choice)
   st.selectbox(f'Research prompt · {len(filtered)} matching ideas',titles,key='task_choice',on_change=choose_task)
   if st.session_state.task_choice==CUSTOM:
    st.info('Custom mode: type any research question below. Nothing is restricted to the premade library.')
   elif st.session_state.task_choice in LOOKUP:
    p=LOOKUP[st.session_state.task_choice]
    st.caption(f"{p['id']} · {p['category']} · {p.get('level','All levels')}")
   st.text_area('Research question — always editable',key='task',height=180)
  with st.container(border=True):
   st.markdown('#### 04 / What should we measure?')
   st.multiselect('Select financial factors',list(METRICS),key='selected',help='These are metrics supported by the stock screener. The downloadable full factor library contains 60+ ideas.')
   st.caption('The live screener calculates supported metrics only. For broader research, the AI can discuss additional metrics when sourced.')
   with st.expander('Adjust factor weights and quality rules'):
    for metric in st.session_state.selected:
     st.number_input(f'{metric} weight',min_value=0.,max_value=100.,value=1.,step=.5,key='weight_'+metric)
    st.checkbox('Exclude unsuitable bank ratios',key='bank_adjust')
    st.slider('Minimum factor coverage (%)',0,100,key='min_coverage',step=5)
 with right:
  with st.container(border=True):
   st.markdown('#### Your research brief')
   st.caption('Updates automatically. Paste it into your QFAIM ChatGPT Project to run the research.')
   st.metric('Available research ideas',len(LIBRARY))
   a,b=st.columns(2)
   a.metric('Selected factors',len(st.session_state.selected))
   b.metric('Current analyst',st.session_state.behavior_preset.split(' ')[0])
   prompt=build_prompt()
   st.text_area('Generated research instructions',value=prompt,height=420,disabled=True)
   st.download_button('↓ Download research prompt',prompt,'QFAIM_research_prompt.txt','text/plain',type='primary',use_container_width=True)
   config={'profile':st.session_state.profile,'behavior':st.session_state.behavior,'behavior_preset':st.session_state.behavior_preset,'task':st.session_state.task,'task_choice':st.session_state.task_choice,'factors':st.session_state.selected,'weights':weights()}
   st.download_button('↓ Save configuration (JSON)',json.dumps(config,indent=2),'QFAIM_configuration.json','application/json',use_container_width=True)
   st.markdown('<div class="soft-note">Tip: Choose <b>Beginner-friendly teacher</b> if you are new to the market. You can always switch to a more technical analyst later.</div>',unsafe_allow_html=True)
  with st.container(border=True):
   st.markdown('#### How the four blocks fit together')
   st.write('**Profile** sets the audience. **Analyst style** sets the tone and rigor. **Research question** sets the task. **Financial factors** define the measurements.')
   st.caption('The research studio creates instructions. It does not itself execute a language model or automatically discover all stocks in a sector.')

@st.cache_data(ttl=240,show_spinner=False)
def retrieve(tickers:tuple[str,...],benchmark:str):
 rows,errors=[],[]
 for t in tickers:
  try:rows.append(fetch(t,benchmark))
  except Exception as exc:errors.append(f'{t}: {str(exc)[:130]}')
 return pd.DataFrame(rows),errors

def do_screen(force=False):
 names=list(dict.fromkeys(t.strip().upper() for t in st.session_state.tickers.replace('\n',',').split(',') if t.strip()))
 if not names:st.warning('Enter at least one ticker to start.');return
 if len(names)>30:st.error('Please enter no more than 30 tickers.');return
 if not st.session_state.selected:st.warning('Choose at least one factor in Block 4 first.');return
 w=weights()
 if not any(v>0 for v in w.values()):st.warning('Choose at least one factor with a positive weight.');return
 if force:retrieve.clear()
 raw,errors=retrieve(tuple(names),st.session_state.benchmark.strip().upper() or 'SPY')
 if errors:st.warning('Some data could not be retrieved: '+' | '.join(errors))
 if raw.empty:st.error('No usable data returned. Check ticker symbols and provider availability.');return
 st.session_state.last_raw=raw
 st.session_state.last_results=score(raw,st.session_state.selected,w,st.session_state.bank_adjust)
 st.session_state.last_fetch=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

with screener:
 st.markdown('### Compare publicly traded companies')
 st.caption('Enter up to 30 ticker symbols. QFAIM fetches available financial data, calculates selected factors, and ranks only the stocks you provide.')
 sleft,sright=st.columns([1.15,.85],gap='large')
 with sleft:
  with st.container(border=True):
   st.text_area('Ticker symbols, separated by commas',key='tickers',height=82)
   st.text_input('Comparison benchmark (ticker)',key='benchmark',help='For example: SPY for the broad U.S. market or XLF for financials.')
   a,b=st.columns(2)
   with a: run=st.button('↻  Refresh market data',type='primary',use_container_width=True)
   with b:st.selectbox('Auto-refresh interval',options=[5,10,15,30,60],format_func=lambda n:f'{n} minutes',key='refresh_mins')
   st.toggle('Auto-refresh while this page is open',key='auto_refresh')
   st.caption('Quotes may be delayed. Data is provided by an unofficial Yahoo Finance interface and can be missing or rate-limited.')
  if run:
   with st.spinner('Collecting prices and financial metrics…'):do_screen(force=True)
 with sright:
  st.markdown('#### Before you screen')
  st.markdown('<div class="soft-note">Your <b>Block 4 factor selection</b> controls the scoring. To change factors or weights, visit the Research studio tab. A score of 80/100 means relatively strong performance <b>within your chosen ticker list</b>, not an 80% chance of success.</div>',unsafe_allow_html=True)
  st.write('**Example tickers:** JPM, GS, MS, TBBK, HBT, SBSI')
  st.write('**Available metrics:** valuation, growth, profitability, momentum and risk.')
  st.write('**Outputs:** ranking table, comparison chart and downloadable CSV.')
 @st.fragment(run_every=(f'{st.session_state.refresh_mins}m' if st.session_state.auto_refresh else None))
 def results():
  if st.session_state.auto_refresh:do_screen()
  ranked=st.session_state.last_results
  if ranked is None:
   st.info('Your results will appear here after you click **Refresh market data**.')
   return
  st.markdown('### Research results')
  st.caption(f"Last checked: {st.session_state.last_fetch} · Data may be cached up to 4 minutes · Peer rankings, not buy recommendations")
  eligible=ranked[ranked['Coverage %']>=st.session_state.min_coverage].copy()
  if eligible.empty:st.warning('No stocks meet the minimum data-coverage setting. Try fewer factors or a lower threshold.')
  else:
   c1,c2,c3=st.columns(3)
   c1.metric('Companies scored',len(eligible))
   c2.metric('Highest ranked',str(eligible.iloc[0]['Ticker']))
   c3.metric('Top composite score',f"{eligible.iloc[0]['Composite Score']:.1f}/100")
   cols=['Ticker','Company','Market Cap','Price','Price Date','Composite Score','Coverage %']+st.session_state.selected
   st.dataframe(eligible[cols],hide_index=True,use_container_width=True)
   st.bar_chart(eligible.set_index('Ticker')['Composite Score'],color='#287050')
  st.download_button('↓ Download rankings (CSV)',ranked.to_csv(index=False).encode(),'QFAIM_rankings.csv','text/csv')
  st.download_button('↓ Download raw data (CSV)',st.session_state.last_raw.to_csv(index=False).encode(),'QFAIM_raw_data.csv','text/csv')
  with st.expander('Review factor scores and missing data'):
   cols=['Ticker','Industry','Composite Score','Coverage %']+[f'Score: {m}' for m in st.session_state.selected]
   st.dataframe(ranked[cols],hide_index=True,use_container_width=True)
   st.caption('Scores are weighted peer percentiles. Missing values are excluded. Ratios unsuitable for banks can be omitted. Factors with fewer than two usable observations are not scored.')
 results()

with guide:
 st.markdown('### About QFAIM')
 st.write('QFAIM began as a modular equity research workflow and now combines a guided prompt builder with a small-universe stock screener. It is designed to make financial research more approachable without hiding uncertainty.')
 st.markdown('### Publish this Academic Edition')
 st.markdown('''1. Extract the ZIP package and open the `QFAIM_Academic_Website` folder.
2. In your existing GitHub repository, replace the old `QFAIM_Website.py` and `.streamlit/config.toml` with the new files. Upload the remaining project files if missing. Keep the same folder structure.
3. Commit the changes to the branch connected to Streamlit Community Cloud.
4. Streamlit should redeploy the app at the **same website address**. Check deployment logs if the site shows an error.

To run locally: `python3 -m pip install -r requirements.txt` then `python3 -m streamlit run QFAIM_Website.py`.''')
 st.warning('Market data is not guaranteed live or complete. The screener does not scan the entire market, execute trades, or provide individualized financial advice. Confirm key figures using issuer filings.')
