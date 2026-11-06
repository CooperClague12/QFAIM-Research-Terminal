# QFAIM — Academic Edition

A cream-and-forest-green redesign of the Cooper Clague QFAIM research terminal.

## Features
- Four-block research workflow: profile, editable analyst presets, research assignments, selected factors.
- 133 curated Block 3 prompts, searchable and filterable by category; fully editable custom mode.
- Six Block 2 analyst styles, with editable instructions.
- A separate stock screener for up to 30 user-entered ticker symbols, using yfinance and the bundled scoring engine.
- Adjustable factor weights, minimum coverage setting, and bank-specific metric exclusions.
- Optional periodic refresh while the page is open; CSV downloads and prompt/configuration exports.

## Deploy to your existing Streamlit website
1. Unzip the package.
2. Open your GitHub repository that currently powers https://qfaimwebsite.streamlit.app/.
3. Replace `QFAIM_Website.py`, `qfaim_engine.py`, `BLOCK3_PROMPT_LIBRARY.json`, `requirements.txt`, and `.streamlit/config.toml` with the versions here. Make sure these are in the same directory as the deployed main file.
4. Commit the changes to the branch connected to Streamlit Community Cloud.
5. Streamlit will usually rebuild the app at the **same URL**. Check app logs if there is an error.

If you upload the entire `QFAIM_Academic_Website` directory as a nested folder instead of replacing root files, change the app's entrypoint to `QFAIM_Academic_Website/QFAIM_Website.py`.

## Local preview
```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run QFAIM_Website.py
```

## Notes
- The prompt builder updates immediately, but it does not execute an AI model by itself.
- The screener retrieves financial data only for the tickers entered. It does not search all listed companies.
- Yahoo Finance through yfinance is an unofficial data source and may be delayed, rate-limited, or incomplete.
- Factor scores are relative to the supplied comparison group, not forecasts or investment recommendations.
- This package has been syntax-checked, but a full live deployment and provider fetch have not been verified.
