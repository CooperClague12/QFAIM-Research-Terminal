"""QFAIM live data and transparent cross-sectional scoring."""
from __future__ import annotations
import numpy as np
import pandas as pd
import yfinance as yf

METRICS = {
 'Trailing P/E':('trailingPE','low'), 'Forward P/E':('forwardPE','low'),
 'P/B':('priceToBook','low'), 'PEG':('trailingPegRatio','low'),
 'EV/EBITDA':('enterpriseToEbitda','low'), 'FCF Yield':('freeCashflow','special'),
 'ROE':('returnOnEquity','high'), 'ROA':('returnOnAssets','high'),
 'Operating Margin':('operatingMargins','high'), 'Revenue Growth':('revenueGrowth','high'),
 'Earnings Growth':('earningsGrowth','high'), 'Debt/Equity':('debtToEquity','low'),
 'Dividend Yield':('dividendYield','high'), 'Beta':('beta','neutral'),
 'Relative Strength 6M':('relative_strength_6m','high'), 'RSI 14':('rsi_14','neutral'),
 'MACD Histogram':('macd_histogram','high'), '1Y Return':('return_1y','high'),
}
BANK_INAPPLICABLE={'EV/EBITDA','FCF Yield','Debt/Equity','Operating Margin'}

def rsi(close, window=14):
    delta=close.diff(); gains=delta.clip(lower=0); losses=-delta.clip(upper=0)
    ag=gains.ewm(alpha=1/window,adjust=False,min_periods=window).mean()
    al=losses.ewm(alpha=1/window,adjust=False,min_periods=window).mean()
    ratio=ag/al.replace(0,np.nan)
    result=100-100/(1+ratio)
    if len(result) and al.iloc[-1]==0 and ag.iloc[-1]>0: return 100.0
    return float(result.iloc[-1]) if len(result) else np.nan

def fetch(ticker, benchmark='XLF'):
    ticker=ticker.strip().upper(); stock=yf.Ticker(ticker)
    info=stock.info or {}; hist=stock.history(period='18mo',auto_adjust=True)
    if hist.empty or len(hist)<40: raise ValueError(f'Insufficient price history for {ticker}')
    close=hist['Close'].dropna(); price=float(close.iloc[-1]); result={'Ticker':ticker,'Company':info.get('shortName') or ticker,'Sector':info.get('sector'),'Industry':info.get('industry'),'Market Cap':info.get('marketCap'),'Price':price,'Price Date':str(close.index[-1].date()),'Currency':info.get('currency','USD')}
    for label,(field,_) in METRICS.items():
        if field in ['relative_strength_6m','rsi_14','macd_histogram','return_1y']:continue
        v=info.get(field)
        if label=='FCF Yield':v=(v/info.get('marketCap')) if isinstance(v,(int,float)) and info.get('marketCap') else None
        result[label]=v
    result['RSI 14']=rsi(close)
    e12=close.ewm(span=12,adjust=False).mean();e26=close.ewm(span=26,adjust=False).mean();macd=e12-e26
    result['MACD Histogram']=float((macd-macd.ewm(span=9,adjust=False).mean()).iloc[-1]/price)*100
    result['1Y Return']=float(price/close.iloc[-253]-1) if len(close)>=253 else np.nan
    if len(close)>=127:
        bench=yf.Ticker(benchmark).history(period='18mo',auto_adjust=True)['Close'].dropna()
        common=close.index.intersection(bench.index)
        if len(common)>=127:
            c=close.loc[common]; b=bench.loc[common]
            result['Relative Strength 6M']=float(c.iloc[-1]/c.iloc[-127]-b.iloc[-1]/b.iloc[-127])
        else: result['Relative Strength 6M']=np.nan
    else: result['Relative Strength 6M']=np.nan
    return result

def score(frame, selected, weights=None, bank_adjust=True):
    """Percentile scores within supplied universe; non-positive multiples excluded."""
    df=frame.copy(); weights=weights or {k:1 for k in selected}
    for metric in selected:
        s=pd.to_numeric(df.get(metric,pd.Series(np.nan,index=df.index)),errors='coerce')
        if metric in ['Trailing P/E','Forward P/E','P/B','PEG','EV/EBITDA']:s=s.where(s>0)
        if bank_adjust and metric in BANK_INAPPLICABLE and 'Industry' in df:
            bank=df['Industry'].fillna('').str.contains('Banks|Banking',case=False,regex=True)
            s=s.mask(bank)
        if metric=='RSI 14':
            # Reward constructive momentum, penalize overbought/oversold extremes.
            raw=-(s-55).abs()
        elif metric=='Beta':
            raw=-(s-1).abs()
        else: raw=-s if METRICS[metric][1]=='low' else s
        n=raw.notna().sum()
        df[f'Score: {metric}']=raw.rank(pct=True,method='average')*100 if n>=2 else np.nan
    cols=[f'Score: {m}' for m in selected]
    w=pd.Series({f'Score: {m}':max(0,float(weights.get(m,1))) for m in selected})
    if w.sum()==0:raise ValueError('Select at least one positive weight')
    valid=df[cols].notna()
    df['Coverage %']=valid.mul(w,axis=1).sum(axis=1)/w.sum()*100
    numerator=df[cols].mul(w,axis=1).sum(axis=1,min_count=1)
    denom=valid.mul(w,axis=1).sum(axis=1).replace(0,np.nan)
    df['Composite Score']=numerator/denom
    return df.sort_values(['Composite Score','Coverage %'],ascending=False,na_position='last')
