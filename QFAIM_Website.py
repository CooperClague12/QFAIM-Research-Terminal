"""QFAIM Academic Edition — four-block research studio and refreshable screener."""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import streamlit as st
from qfaim_engine import METRICS, fetch
from openai import OpenAI

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
 'single_ticker':'', 'single_stock_result':None, 'single_stock_checked':None,
 'ai_answer':None,'ai_prompt':None,'ai_model':'gpt-4.1-mini','ai_web':True,
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

def get_api_key():
 # The owner can configure OPENAI_API_KEY in Streamlit Secrets; visitors never see it.
 try:
  secret = st.secrets.get('OPENAI_API_KEY', '')
  if secret: return str(secret)
 except Exception:
  pass
 return os.environ.get('OPENAI_API_KEY', '') or st.session_state.get('visitor_api_key', '')

def run_ai_research(prompt, model, use_web):
 key = get_api_key()
 if not key:
  raise ValueError('No OpenAI API key configured. Add OPENAI_API_KEY to Streamlit app secrets, or enter your own key in the research panel.')
 client = OpenAI(api_key=key, timeout=120.0, max_retries=1)
 instructions = ("You are the research analyst for QFAIM, an educational equity-research website. "
  "Fulfill the four-block research request. Be understandable to the user's stated experience level. "
  "When a request is broad, choose a reasonable, explicitly stated scope rather than refusing. "
  "Use clear section headings, comparisons and risk factors. Separate facts, estimates and opinion. "
  "Never invent live prices, valuations, source citations, company financials, or screening coverage. "
  "If data cannot be verified, say so and offer a research method instead. "
  "For country-specific and sector screens, describe how candidates were selected and don't claim exhaustive coverage. "
  "If web search is available, cite the underlying sources with dates and links in the report. "
  "This is general educational research, not personalized investment advice.")
 kwargs = {'model': model, 'instructions': instructions, 'input': prompt, 'max_output_tokens': 3800}
 if use_web: kwargs['tools'] = [{'type': 'web_search_preview'}]
 response = client.responses.create(**kwargs)
 result = (response.output_text or '').strip()
 if not result: raise RuntimeError('The AI returned no readable report. Please try again.')
 return result

st.markdown('<div class="brandline">▥ &nbsp; QFAIM <span style="font:500 .78rem DM Sans,sans-serif;color:#789082">/ RESEARCH TERMINAL</span></div>',unsafe_allow_html=True)
st.markdown('''<div class="hero"><div class="eyebrow">Independent equity research · Academic edition</div><div class="hero-title">Learn the market.<br>Research with confidence.</div><div class="hero-sub">A guided stock research workspace for curious beginners and experienced investors. Choose how your analyst thinks, explore 133 ready-made research ideas, and compare companies with transparent data.</div><div class="hero-foot">FOUR-BLOCK RESEARCH SYSTEM &nbsp; · &nbsp; 133 CURATED PROMPTS &nbsp; · &nbsp; REFRESHABLE STOCK SCREENING</div></div>''',unsafe_allow_html=True)

cols=st.columns(4,gap='small')
for c,(n,title,desc) in zip(cols,[('01','Your profile','Set your experience and learning goals.'),('02','Analyst style','Choose how research is explained.'),('03','Research question','Pick from 133 ideas or write your own.'),('04','Financial factors','Select and weight the metrics that matter.')]):
 with c:st.markdown(f'<div class="step-card"><div class="step-num">BLOCK {n}</div><div class="step-title">{title}</div><div class="step-copy">{desc}</div></div>',unsafe_allow_html=True)

studio, screener, guide = st.tabs(['✦  Research studio','▥  Stock snapshot','ⓘ  About & deployment'])
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
   st.divider()
   st.markdown('#### ✦ Run your research here')
   st.write('Generate a complete AI research report from the four blocks above, without leaving QFAIM.')
   st.selectbox('AI model', ['gpt-4.1-mini', 'gpt-4.1'], key='ai_model', help='The mini model generally costs less; the larger model can be more thorough. Both use paid API usage.')
   st.checkbox('Search the web for current sources', key='ai_web', help='Web search may increase API usage charges. It can improve factual freshness but does not guarantee complete market coverage.')
   if not get_api_key():
    st.text_input('OpenAI API key (this session only)', type='password', key='visitor_api_key', placeholder='sk-...', help='For personal testing. For a public site, configure OPENAI_API_KEY in Streamlit Community Cloud Secrets instead. Do not put keys in GitHub.')
   if st.button('✦ Run AI Research', type='primary', use_container_width=True):
    st.session_state.ai_answer = None
    st.session_state.ai_prompt = None
    if not st.session_state.profile.strip() or not st.session_state.task.strip():
     st.error('Complete your profile and research question first.')
    else:
     with st.spinner('Researching your question and writing the report… this may take a minute.'):
      try:
       answer = run_ai_research(prompt, st.session_state.ai_model, st.session_state.ai_web)
       st.session_state.ai_answer = answer
       st.session_state.ai_prompt = prompt
      except Exception as exc:
       st.error(f'Unable to generate the report: {exc}')
   if st.session_state.ai_answer:
    if st.session_state.ai_prompt != prompt:
     st.warning('The report below was generated from an earlier version of your four blocks. Click Run AI Research again to update it.')
    st.markdown('#### Your AI research report')
    st.markdown(st.session_state.ai_answer)
    st.download_button('↓ Download AI report', st.session_state.ai_answer, 'QFAIM_AI_research_report.md', 'text/markdown', use_container_width=True)
   st.caption('AI research can contain errors. Verify figures and cited sources before making investment decisions. API usage is billed by the API provider.')
   st.markdown('<div class="soft-note">Tip: Choose <b>Beginner-friendly teacher</b> if you are new to the market. You can always switch to a more technical analyst later.</div>',unsafe_allow_html=True)
  with st.container(border=True):
   st.markdown('#### How the four blocks fit together')
   st.write('**Profile** sets the audience. **Analyst style** sets the tone and rigor. **Research question** sets the task. **Financial factors** define the measurements.')
   st.caption('Run AI Research generates a report using an OpenAI API key. The stock snapshot shows available metrics for one ticker at a time; AI research does not guarantee an exhaustive sector screen.')

@st.cache_data(ttl=240, show_spinner=False)
def get_single_stock(ticker: str):
    return fetch(ticker, 'SPY')


def metric_display(name, value):
    if value is None or pd.isna(value):
        return 'Not available'
    value = float(value)
    if name in {'ROE', 'ROA', 'Operating Margin', 'Revenue Growth', 'Earnings Growth',
                'Dividend Yield', 'FCF Yield', 'Relative Strength 6M', '1Y Return'}:
        return f'{value * 100:,.2f}%'
    if name == 'MACD Histogram':
        return f'{value:+,.2f}% of price'
    if name in {'Trailing P/E', 'Forward P/E', 'P/B', 'PEG', 'EV/EBITDA'}:
        return f'{value:,.2f}x'
    if name == 'Debt/Equity':
        return f'{value:,.1f}%'  # Yahoo Finance reports this ratio in percentage points
    return f'{value:,.2f}'


def compact_amount(value, currency='USD'):
    if value is None or pd.isna(value):
        return 'Not available'
    value = float(value)
    prefix = '$' if currency == 'USD' else f'{currency} '
    for scale, suffix in [(1e12, 'T'), (1e9, 'B'), (1e6, 'M')]:
        if abs(value) >= scale:
            return f'{prefix}{value / scale:,.2f}{suffix}'
    return f'{prefix}{value:,.2f}'


def quick_take(stock):
    def num(k):
        value = stock.get(k)
        return float(value) if value is not None and pd.notna(value) else None
    name = stock.get('Company') or stock['Ticker']
    sector = stock.get('Sector') or 'an unspecified sector'
    industry = stock.get('Industry')
    cap = num('Market Cap')
    intro = f"**{name} ({stock['Ticker']})** operates in {sector}"
    if industry:
        intro += f' ({industry})'
    intro += '.'
    if cap is not None:
        intro += f" Its reported market capitalization is {compact_amount(cap, stock.get('Currency') or 'USD')}."
    details = []
    pe = num('Trailing P/E')
    if pe is not None and pe > 0:
        details.append(f'It trades at roughly **{pe:.1f} times trailing earnings**; this is a valuation multiple, not a standalone verdict on whether the stock is cheap.')
    growth = num('Revenue Growth')
    if growth is not None:
        details.append(f"Reported revenue growth is **{growth * 100:+.1f}%** ({'positive' if growth >= 0 else 'negative'}), based on the data provider’s reporting period.")
    roe = num('ROE')
    if roe is not None:
        details.append(f'Its return on equity is **{roe * 100:.1f}%**, although comparisons should account for industry and leverage.')
    ret = num('1Y Return')
    if ret is not None:
        details.append(f'The adjusted one-year price return is approximately **{ret * 100:+.1f}%**; past performance does not predict future results.')
    if not details:
        details.append('Several key financial figures are unavailable from the data provider, so a meaningful valuation assessment is limited.')
    return ' '.join([intro] + details[:3]) + ' **Research takeaway:** Compare these figures with similar companies, check the latest filings, and consider business risks before drawing a conclusion.'


with screener:
    st.markdown('### Stock snapshot')
    st.caption('Enter one ticker to see its available quantitative factors and a plain-English company breakdown. No factor selection or API key required.')
    with st.form('single_ticker_lookup', clear_on_submit=False):
        entry, action = st.columns([4, 1], vertical_alignment='bottom')
        with entry:
            ticker_input = st.text_input('Stock ticker', placeholder='e.g., AAPL, JPM, MSFT, TBBK', max_chars=20, key='single_ticker')
        with action:
            submitted = st.form_submit_button('Analyze stock', type='primary', use_container_width=True)
    if submitted:
        import re
        ticker = ticker_input.strip().upper()
        if not re.fullmatch(r'[A-Z0-9^.=\-]{1,15}', ticker):
            st.error('Please enter one valid ticker symbol, such as AAPL or BRK-B.')
        else:
            try:
                with st.spinner(f'Loading financial data for {ticker}…'):
                    get_single_stock.clear()
                    stock = get_single_stock(ticker)
                st.session_state.single_stock_result = stock
                st.session_state.single_stock_checked = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
            except Exception as exc:
                st.session_state.single_stock_result = None
                st.error(f'Unable to retrieve {ticker}: {str(exc)[:220]}. Please try again later.')
    stock = st.session_state.get('single_stock_result')
    if stock:
        st.markdown(f"### {stock.get('Company') or stock['Ticker']} · {stock['Ticker']}")
        st.caption(f"{stock.get('Sector') or 'Sector unavailable'} · {stock.get('Industry') or 'Industry unavailable'} · Price date: {stock.get('Price Date') or 'unknown'} · Retrieved: {st.session_state.get('single_stock_checked', 'unknown')}")
        currency = stock.get('Currency') or 'USD'
        p1, p2, p3 = st.columns(3)
        p1.metric('Last available price', compact_amount(stock.get('Price'), currency))
        p2.metric('Market capitalization', compact_amount(stock.get('Market Cap'), currency))
        p3.metric('1-year adjusted return', metric_display('1Y Return', stock.get('1Y Return')))
        with st.container(border=True):
            st.markdown('#### In plain English')
            st.markdown(quick_take(stock))
        st.markdown('#### Quantitative factor breakdown')
        st.caption('All 18 factors currently calculated by the QFAIM data engine are shown below, including unavailable values. This is not the entire 60+ factor idea library.')
        sections = {
            'Valuation': ['Trailing P/E', 'Forward P/E', 'P/B', 'PEG', 'EV/EBITDA', 'FCF Yield'],
            'Profitability & growth': ['ROE', 'ROA', 'Operating Margin', 'Revenue Growth', 'Earnings Growth'],
            'Financial strength & income': ['Debt/Equity', 'Dividend Yield'],
            'Price trends & risk': ['Beta', 'Relative Strength 6M', 'RSI 14', 'MACD Histogram', '1Y Return'],
        }
        for section, factors in sections.items():
            st.markdown(f'**{section}**')
            rows = [{'Factor': factor, 'Value': metric_display(factor, stock.get(factor))} for factor in factors]
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        st.download_button('↓ Download all factor values (CSV)',
            pd.DataFrame([{'Ticker': stock['Ticker'], 'Company': stock.get('Company'), 'Factor': m,
                           'Raw value': stock.get(m), 'Display value': metric_display(m, stock.get(m))}
                          for m in METRICS]).to_csv(index=False).encode('utf-8'),
            file_name=f"QFAIM_{stock['Ticker']}_factors.csv", mime='text/csv')
        st.info('Figures are supplied through an unofficial Yahoo Finance interface and may be delayed, stale, missing, or inconsistent across industries. The blurb is a rules-based summary of available data, not an AI-generated investment recommendation. Verify important numbers against company filings.')
    else:
        st.markdown('<div class="soft-note">Try <b>AAPL</b> for Apple, <b>JPM</b> for JPMorgan, or <b>MS</b> for Morgan Stanley. You will see a short company overview and a table of financial factors.</div>', unsafe_allow_html=True)

with guide:
 st.markdown('### About QFAIM')
 st.write('QFAIM began as a modular equity research workflow and now combines a guided prompt builder with a single-stock quantitative snapshot. It is designed to make financial research more approachable without hiding uncertainty.')
 st.markdown('### AI research setup')
 st.write('The **Run AI Research** button calls the OpenAI API to generate a report from your four blocks. It can optionally search the web for current sources. API billing is separate from ChatGPT subscriptions.')
 st.code('OPENAI_API_KEY = \"your-api-key-here\"', language='toml')
 st.caption('In Streamlit Community Cloud: open your app → Settings → Secrets, paste the key in TOML format, save, and reboot if prompted. Never commit an API key to GitHub. Alternatively, visitors can enter their own key for the current session.')
 st.markdown('### Publish this Academic Edition')
 st.markdown('''1. Extract the ZIP package and open the `QFAIM_Academic_Website` folder.
2. In your existing GitHub repository, replace the old `QFAIM_Website.py` and `.streamlit/config.toml` with the new files. Upload the remaining project files if missing. Keep the same folder structure.
3. Commit the changes to the branch connected to Streamlit Community Cloud.
4. Streamlit should redeploy the app at the **same website address**. Check deployment logs if the site shows an error.

To run locally: `python3 -m pip install -r requirements.txt` then `python3 -m streamlit run QFAIM_Website.py`.''')
 st.warning('Market data is not guaranteed live or complete. The stock snapshot does not scan the entire market, execute trades, or provide individualized financial advice. Confirm key figures using issuer filings.')

# Persistent site-wide footer: displayed below every workspace tab.
st.divider()
st.markdown('''
<div style="text-align:center; padding: 1.15rem 1rem 2rem; color:#46604d; font-size:0.88rem; line-height:1.65;">
<strong>School Project Disclaimer</strong><br>
QFAIM is an educational school project created to explore financial research,
quantitative analysis, and AI-assisted learning. It is not a professional investment
advisory service. Information and AI-generated responses may be inaccurate,
incomplete, or outdated and should not be treated as personalized financial advice.
Always verify financial data with reliable primary sources before making investment decisions.
</div>
''', unsafe_allow_html=True)
