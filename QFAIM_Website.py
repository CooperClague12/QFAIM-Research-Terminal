"""QFAIM website: modular prompt studio + refreshable stock screening."""
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import streamlit as st
from qfaim_engine import METRICS, fetch, score

st.set_page_config(page_title='QFAIM | Research Terminal',page_icon='📈',layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>.block-container{padding-top:1.6rem;max-width:1450px}div[data-testid="stMetric"]{border:1px solid #d5dce7;border-radius:12px;padding:12px}h1{letter-spacing:-.04em}.stButton button[kind="primary"]{border-radius:10px}</style>''',unsafe_allow_html=True)

BEHAVIOR_PRESETS={
 'Institutional equity analyst': 'Act as a rigorous institutional equity research analyst. Prioritize primary filings and dated verifiable sources. Separate facts, estimates and judgment. Show valuation and operating comparisons, explain every scoring decision, discuss catalysts and downside risks, and never invent missing data.',
 'Financial advisor / client ready': 'Act as a fiduciary-minded wealth management research assistant. Explain financial metrics clearly, connect findings to risk tolerance and diversification, present balanced bull/base/bear cases, cite dated sources, and avoid presenting research rankings as personal investment advice.',
 'Deep value investor': 'Focus on price versus conservative intrinsic value, normalized earnings, quality of assets, capital allocation, downside protection and margin of safety. Test accounting quality and explain value traps. Use verifiable sources and explicit assumptions.',
 'Growth and quality investor': 'Prioritize durable competitive advantages, revenue and EPS growth, profitability, reinvestment opportunities, management execution and valuation discipline. Compare against close peers; quantify risks and use dated sources.',
 'Quantitative factor researcher': 'Use a reproducible factor-screening process. Define universe, factor direction, data dates, normalization, peer group, weights and missing-data policy. Show factor-level scores and coverage. Never imply unverified whole-market coverage.',
 'Beginner-friendly explainer': 'Explain results in straightforward language with short examples. Define each metric on first use, distinguish company quality from stock valuation, cite reliable sources, and explain uncertainty without jargon.',
}
PROMPT_LIBRARY=json.loads((Path(__file__).parent/'BLOCK3_PROMPT_LIBRARY.json').read_text(encoding='utf-8'))
PROMPTS_BY_TITLE={x['title']:x for x in PROMPT_LIBRARY}
TASK_PRESETS={x['title']:{'task':x['task'],'tickers':'','benchmark':x['benchmark']} for x in PROMPT_LIBRARY}
TASK_PRESETS['Custom — write my own']={'task':'','tickers':'','benchmark':'SPY'}
DEFAULT_TASK='Small-cap Financials stocks'

FACTOR_DEFAULT=['Trailing P/E','P/B','ROE','Revenue Growth','Earnings Growth','Relative Strength 6M','RSI 14']

def init(name,value):
 if name not in st.session_state:st.session_state[name]=value
init('profile','Economics graduate with wealth management internship experience; interested in evidence-based stock research.')
init('behavior_preset','Institutional equity analyst')
init('task_preset',DEFAULT_TASK)
init('behavior',BEHAVIOR_PRESETS['Institutional equity analyst'])
init('task',TASK_PRESETS[DEFAULT_TASK]['task'])
init('tickers',TASK_PRESETS[DEFAULT_TASK]['tickers'])
init('benchmark','XLF')
init('selected',FACTOR_DEFAULT)
init('refresh_mins',5)
init('auto_refresh',False)
init('last_results',None)
init('last_raw',None)
init('last_fetch',None)
init('min_coverage',50)
init('bank_adjust',True)

def behavior_changed(): st.session_state.behavior=BEHAVIOR_PRESETS[st.session_state.behavior_preset]
def task_changed():
 p=TASK_PRESETS[st.session_state.task_preset]
 for k in ('task','tickers','benchmark'):st.session_state[k]=p[k]

st.title('QFAIM  /  Research Terminal')
st.caption('Cooper Clague MS Intern 2025 QFAIM · Modular prompt studio + live-data stock screening')
with st.sidebar:
 st.header('The four blocks')
 st.text_area('01  ·  User profile',key='profile',height=105)
 st.selectbox('02  ·  AI response preset',list(BEHAVIOR_PRESETS),key='behavior_preset',on_change=behavior_changed)
 st.text_area('Edit Block 2 instructions',key='behavior',height=150)
 st.markdown('### 03 · Research assignment')
 st.caption(f'{len(PROMPT_LIBRARY)} ready-made ideas, plus a completely custom option. Browse by topic or search for words like media, small-cap, Japan, or dividends.')
 categories=['All categories']+sorted({x['category'] for x in PROMPT_LIBRARY})
 category=st.selectbox('Browse Block 3 topics',categories,key='prompt_category')
 search=st.text_input('Search prompts',placeholder='Try: healthcare, micro-cap, Brazil, beginner',key='prompt_search')
 candidates=[x['title'] for x in PROMPT_LIBRARY if (category=='All categories' or x['category']==category) and (not search or search.lower() in (' '.join([x['title'],x['task'],*x['tags']])).lower())]
 choices=['Custom — write my own']+candidates
 if st.session_state.task_preset not in choices:
  choices.insert(1,st.session_state.task_preset)
 st.selectbox('03  ·  Choose a research prompt',choices,key='task_preset',on_change=task_changed)
 if st.session_state.task_preset in PROMPTS_BY_TITLE:
  item=PROMPTS_BY_TITLE[st.session_state.task_preset]
  st.caption(f"{item['id']} · {item['category']} · {item['level']}")
 else: st.caption('Custom mode: write anything you want below. You can specify sector, market cap, country, research goal, and output style.')
 st.text_area('Block 3 — edit or write your own research prompt',key='task',height=210)
 st.caption('Stock tickers are optional for research prompts. For the live screener, enter actual ticker symbols in its tab.')
 st.multiselect('04  ·  Financial factors',list(METRICS),key='selected')
 st.caption('The full 60+ factor library is in FACTOR_LIBRARY.csv. Only factors supported by the live data engine can be calculated here.')

weights={}
with st.expander('Factor weights and screening rules',expanded=False):
 c1,c2=st.columns(2)
 with c1:
  for m in st.session_state.selected[:(len(st.session_state.selected)+1)//2]:weights[m]=st.number_input(f'Weight · {m}',min_value=0.,max_value=100.,value=1.,step=0.5,key='weight_'+m)
 with c2:
  for m in st.session_state.selected[(len(st.session_state.selected)+1)//2:]:weights[m]=st.number_input(f'Weight · {m}',min_value=0.,max_value=100.,value=1.,step=0.5,key='weight_'+m)
 st.checkbox('Exclude unsuitable bank ratios',key='bank_adjust',help='For banks, omit EV/EBITDA, FCF Yield, Debt/Equity and Operating Margin from scoring.')
 st.slider('Minimum weighted factor coverage (%)',0,100,key='min_coverage',step=5)

prompt=f'''QFAIM EQUITY RESEARCH REQUEST\n\nBLOCK 1 — USER PROFILE\n{st.session_state.profile}\n\nBLOCK 2 — ANALYST BEHAVIOR\n{st.session_state.behavior}\n\nBLOCK 3 — RESEARCH ASSIGNMENT\n{st.session_state.task}\nUniverse: {st.session_state.tickers}\nBenchmark: {st.session_state.benchmark}\n\nBLOCK 4 — FACTORS AND WEIGHTS\n'''+('\n'.join(f'- {m}: weight {weights.get(m,1):g}' for m in st.session_state.selected) or '(none selected)')+f'''\n\nMETHODOLOGY\nScore against the supplied universe, not the entire market. State data dates and sources. Normalize factors transparently, show factor coverage and missing observations, and explain bank/nonbank applicability. Minimum coverage: {st.session_state.min_coverage}%. Do not invent data or claim real-time quotes without verification. Distinguish preliminary screen results from investment recommendations.'''

t1,t2,t3=st.tabs(['Research prompt studio','Live stock screener','How to use / deploy'])
with t1:
 a,b=st.columns([1,1.2],gap='large')
 with a:
  st.subheader('Your current research setup')
  st.metric('Selected factors',len(st.session_state.selected))
  st.write('**AI preset:**',st.session_state.behavior_preset)
  st.write('**Research preset:**',st.session_state.task_preset)
  st.caption('The preset is a starting point: you can edit every word of Block 3, or choose Custom — write my own.')
  st.write('**Tickers:**',st.session_state.tickers)
  st.write('**Benchmark:**',st.session_state.benchmark)
  st.info('Change any of the four blocks in the sidebar. The generated prompt updates immediately; no market-data request is needed.')
  config={'profile':st.session_state.profile,'behavior_preset':st.session_state.behavior_preset,'behavior':st.session_state.behavior,'task_preset':st.session_state.task_preset,'task':st.session_state.task,'tickers':st.session_state.tickers,'benchmark':st.session_state.benchmark,'factors':st.session_state.selected,'weights':weights,'min_coverage':st.session_state.min_coverage}
  st.download_button('Download setup (JSON)',json.dumps(config,indent=2),'QFAIM_configuration.json','application/json')
 with b:
  st.subheader('Live-updating prompt preview')
  st.code(prompt,language='text',wrap_lines=True)
  st.download_button('Download prompt (.txt)',prompt,'QFAIM_research_prompt.txt','text/plain',type='primary')

@st.cache_data(ttl=240,show_spinner=False)
def load_tickers(tickers,benchmark):
 rows=[];errors=[]
 for ticker in tickers:
  try: rows.append(fetch(ticker,benchmark))
  except Exception as e: errors.append(f'{ticker}: {str(e)[:160]}')
 return pd.DataFrame(rows),errors

def refresh_results():
 tickers=list(dict.fromkeys(t.strip().upper() for t in st.session_state.tickers.replace('\n',',').split(',') if t.strip()))
 if not tickers: st.error('Enter at least one ticker.');return
 if len(tickers)>30:st.error('Maximum 30 tickers per run.');return
 if not st.session_state.selected:st.error('Choose at least one factor.');return
 if not any(weights.get(m,1)>0 for m in st.session_state.selected):st.error('At least one factor weight must be positive.');return
 raw,errors=load_tickers(tuple(tickers),st.session_state.benchmark.strip().upper())
 if errors:st.warning('Data retrieval issues: '+' | '.join(errors))
 if raw.empty:st.error('No usable market data was returned. Check tickers, network access, or provider limits.');return
 ranked=score(raw,st.session_state.selected,weights,st.session_state.bank_adjust)
 st.session_state.last_results=ranked
 st.session_state.last_raw=raw
 st.session_state.last_fetch=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

with t2:
 st.subheader('Stock screening engine')
 st.text_area('Tickers to compare (comma-separated)',key='tickers',height=75)
 st.text_input('Benchmark ticker',key='benchmark')
 st.caption('Prices are retrieved when a screen runs. Data may be delayed, unavailable, or inaccurate. This is not an exchange-connected real-time price feed.')
 x,y,z=st.columns([1,1,2])
 with x: run=st.button('Fetch / refresh stock data',type='primary',use_container_width=True)
 with y: st.selectbox('Refresh interval',options=[5,10,15,30,60],format_func=lambda n:f'{n} minutes',key='refresh_mins')
 with z: st.toggle('Auto-refresh while this page is open',key='auto_refresh')
 if run:
  load_tickers.clear()
  with st.spinner('Retrieving prices and company fundamentals…'):refresh_results()

 @st.fragment(run_every=(f'{st.session_state.refresh_mins}m' if st.session_state.auto_refresh else None))
 def live_panel():
  if st.session_state.auto_refresh:
   # Cache expiry avoids unnecessary repeat calls during rerenders.
   refresh_results()
  ranked=st.session_state.last_results
  if ranked is None:
   st.info('Click **Fetch / refresh stock data** to calculate the first ranking. You can optionally enable periodic refresh.')
   return
  st.caption(f'Last retrieval: {st.session_state.last_fetch} · Ranked only among your entered tickers · Cached data may be up to four minutes old')
  eligible=ranked[ranked['Coverage %']>=st.session_state.min_coverage].copy()
  if eligible.empty:st.warning('No stocks meet your minimum coverage threshold. Try lowering it or choosing factors with better data availability.')
  else:
   a,b,c=st.columns(3)
   a.metric('Companies with sufficient data',len(eligible))
   b.metric('Highest ranked',str(eligible.iloc[0]['Ticker']))
   c.metric('Top composite score',f"{eligible.iloc[0]['Composite Score']:.1f}/100")
   columns=['Ticker','Company','Market Cap','Price','Price Date','Composite Score','Coverage %']+st.session_state.selected
   st.dataframe(eligible[columns],hide_index=True,use_container_width=True)
   st.bar_chart(eligible.set_index('Ticker')['Composite Score'])
  st.download_button('Export ranked results (CSV)',ranked.to_csv(index=False).encode(),'QFAIM_ranked.csv','text/csv')
  st.download_button('Export raw data (CSV)',st.session_state.last_raw.to_csv(index=False).encode(),'QFAIM_raw.csv','text/csv')
  with st.expander('Audit: per-factor scores and missing data'):
   st.dataframe(ranked[['Ticker','Industry','Composite Score','Coverage %']+[f'Score: {m}' for m in st.session_state.selected]],hide_index=True,use_container_width=True)
   st.write('Scores are weighted peer percentiles for available observations. Missing values are excluded, not set to zero. Valuation multiples must be positive. Bank-inapplicable factors are omitted when enabled. RSI is scored for closeness to 55; beta for closeness to 1. A factor with fewer than two valid observations is not scored.')
 live_panel()

with t3:
 st.markdown('''### What this website does
**Block 1:** Your background. **Block 2:** Choose a premade analyst style and edit it. **Block 3:** Browse 133 premade research assignments by sector, company size, country, or learning topic. Search them or select **Custom — write my own** and edit freely. **Block 4:** Choose and weight the financial metrics.

The **Research prompt studio** updates as you type. Download the prompt and paste it into your ChatGPT QFAIM Project. The **Live stock screener** requests current available data for up to 30 tickers and ranks them. Optional auto-refresh checks for updates while the page is open.

### Put the website online
1. Upload the project files to a private or public GitHub repository (at minimum `QFAIM_Website.py`, `qfaim_engine.py`, `requirements.txt`, and `.streamlit/config.toml`).
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) and select **Create app**.
3. Choose the GitHub repository and set the main file to `QFAIM_Website.py`, then deploy.
4. Share the resulting URL. You can also run it locally with `python3 -m streamlit run QFAIM_Website.py`.

**Important:** A hosted URL is not created by this download. You must deploy it. The Yahoo Finance interface is unofficial and can be rate-limited or return missing data. The app does not search every stock in the market, stream exchange quotes tick-by-tick, or execute trades. Verify material facts with issuer filings.''')
