import streamlit as st
import pandas as pd
from qfaim_engine import METRICS,fetch,score

st.set_page_config(page_title='QFAIM | Live Stock Screener',page_icon='📈',layout='wide')
st.title('QFAIM · Live Stock Screener')
st.caption('Cooper Clague MS Intern 2025 QFAIM | Enhanced quantitative engine')
st.warning('Research only. Yahoo Finance data may be delayed, incomplete or inaccurate. Validate important figures against filings. No API or live connection exists until this app is run on your computer.')
with st.sidebar:
 st.header('Research configuration')
 profile=st.text_area('Block 1 · Profile','Wealth management research analyst with an economics background.')
 behavior=st.text_area('Block 2 · Response behavior','Data-first, concise, source-aware investment research.')
 task=st.text_area('Block 3 · Research task','Rank a selected universe of financial stocks.')
 benchmark=st.text_input('Benchmark ticker','XLF').upper().strip()
 universe=st.text_area('Stock tickers (comma separated)','TBBK, HBT, SBSI, JPM, GS, MS, V, MA')
 selected=st.multiselect('Block 4 · Factors',list(METRICS),default=['Trailing P/E','P/B','ROE','Revenue Growth','Earnings Growth','Relative Strength 6M','RSI 14'])
 st.caption('The original factor library includes additional metrics that require a paid or alternative data source. Only directly supported factors appear here.')
 st.subheader('Factor weights')
 weights={m:st.number_input(m,min_value=0.,max_value=100.,value=1.,step=0.5,key=m) for m in selected}
 bank_adjust=st.checkbox('Exclude structurally unsuitable bank ratios',value=True)
 mincoverage=st.slider('Minimum factor coverage (%)',0,100,50,5)
 run=st.button('Fetch data and rank stocks',type='primary',use_container_width=True)

st.info('Enter your own universe. This app does not discover all constituents of an index or automatically identify every small-cap stock.')
if run:
 tickers=list(dict.fromkeys(t.strip().upper() for t in universe.replace('\n',',').split(',') if t.strip()))
 if not tickers or not selected:st.error('Choose tickers and at least one factor.');st.stop()
 if len(tickers)>30:st.error('Limit a single run to 30 tickers to reduce provider throttling.');st.stop()
 records=[]; errors=[]; bar=st.progress(0)
 for i,ticker in enumerate(tickers):
  try:records.append(fetch(ticker,benchmark))
  except Exception as exc:errors.append(f'{ticker}: {exc}')
  bar.progress((i+1)/len(tickers))
 if errors:st.warning('Some tickers could not be loaded: '+' | '.join(errors))
 if not records:st.error('No data retrieved. Check connection or provider availability.');st.stop()
 raw=pd.DataFrame(records)
 ranked=score(raw,selected,weights,bank_adjust)
 eligible=ranked[ranked['Coverage %']>=mincoverage].copy()
 st.subheader('Ranked results')
 st.caption('Scores are within this user-selected peer universe, not the entire market. Missing factors are excluded and reported through coverage. Scores are not investment return forecasts.')
 display=['Ticker','Company','Market Cap','Price','Price Date','Composite Score','Coverage %']+selected
 st.dataframe(eligible[display].style.format({'Composite Score':'{:.1f}','Coverage %':'{:.0f}','Price':'${:,.2f}','Market Cap':'{:,.0f}'},na_rep='N/A'),use_container_width=True,hide_index=True)
 st.bar_chart(eligible.set_index('Ticker')['Composite Score'])
 st.download_button('Download ranked CSV',ranked.to_csv(index=False).encode(),'QFAIM_ranked.csv','text/csv')
 st.download_button('Download raw observations CSV',raw.to_csv(index=False).encode(),'QFAIM_raw.csv','text/csv')
 with st.expander('Scoring methodology and audit notes'):
  st.markdown('Each factor is ranked by percentile across the available peer universe. Lower is better for positive valuation multiples; higher is better for profitability, growth and momentum. RSI favors values near 55 and beta favors values near 1 as explicit neutral assumptions. Scores are weighted averages of available percentiles. Ratios that are structurally unsuitable for banks can be excluded. If only one ticker has a usable observation for a metric, that metric is not scored. Missing data is never scored as zero.')
  st.dataframe(ranked[['Ticker','Industry','Composite Score','Coverage %']+[f'Score: {m}' for m in selected]],hide_index=True,use_container_width=True)
 st.subheader('Reusable research prompt')
 st.code(f'USER: {profile}\nBEHAVIOR: {behavior}\nTASK: {task}\nBENCHMARK: {benchmark}\nFACTORS: {", ".join(selected)}\nUse attached CSV results, verify data against filings, explain risks and distinguish facts from opinions.',language='text')
else:
 st.markdown('### How to use\n1. Choose a stock universe and factors in the sidebar.\n2. Click **Fetch data and rank stocks**.\n3. Review factor coverage and download the audit-ready CSV.\n4. Bring the CSV into your ChatGPT QFAIM Project for a sourced qualitative report.')
