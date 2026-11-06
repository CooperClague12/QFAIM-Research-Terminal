# Cooper Clague QFAIM — Reconstructed and Upgraded

This is a **reconstruction**, not a byte-for-byte recovery of the 2025 GPT or its PDF. The four original blocks and sector research concept are preserved. The factor list and dashboard are expanded implementations.

## Files
- `PROJECT_INSTRUCTIONS.md` — copy all text into ChatGPT Project instructions.
- `QFAIM_Dashboard.html` — open locally in a browser; customize the four blocks, factor selection and weights; copy a research prompt or download the configuration as JSON.
- `FACTOR_LIBRARY.csv` — factor definitions, favorable direction and applicability notes.
- `RESEARCH_TEMPLATE.md` — report format and reproducibility checklist.
- `SAMPLE_CONFIG.json` — starting configuration.

## Put it in ChatGPT Projects
1. In ChatGPT's sidebar, select **Projects** then **New project**. Name it `Cooper Clague QFAIM | Stock Research Modular`.
2. Open the project, locate **Project instructions** (usually in the project menu), and paste the complete text of `PROJECT_INSTRUCTIONS.md`.
3. Upload `FACTOR_LIBRARY.csv`, `RESEARCH_TEMPLATE.md`, `SAMPLE_CONFIG.json`, and optionally `README_START_HERE.md` as project files. The HTML dashboard is best opened on your own computer; if Projects accepts HTML, you can also upload it as a reference, but ChatGPT Projects does not run its interface as an embedded app.
4. Start a new chat inside that project and say: `Run QFAIM using the uploaded configuration. Screen U.S. small-cap financial stocks using current verifiable data.`
5. To use the dashboard, unzip the package and double-click `QFAIM_Dashboard.html`. It runs offline; it **does not** fetch live market data. Copy the generated prompt into your project chat for researched analysis.

## Important limitations
The dashboard is a **configuration and scoring workbench**, not a live financial-data terminal. Its scoring tab uses user-entered observations; it will not manufacture financial figures. It does not save changes permanently between browser sessions, so export JSON to retain a configuration. The ChatGPT Project is the persistent research workspace, not the dashboard itself.

## NEW: Live screening engine (November 2026)
The original `QFAIM_Dashboard.html` remains the offline modular prompt builder. `QFAIM_Live_App.py` adds automatic financial data retrieval and ranking when run locally.

### Launch on Mac or Windows
1. Install Python 3.10 or newer from python.org (with pip).
2. Open a terminal in this extracted folder.
3. Run `python3 -m pip install -r requirements.txt` (Windows: `py -m pip install -r requirements.txt`).
4. Run `python3 -m streamlit run QFAIM_Live_App.py` (Windows: `py -m streamlit run QFAIM_Live_App.py`).
5. Open the local URL printed in your terminal (usually http://localhost:8501).
Mac users can alternatively double-click `START_LIVE_DASHBOARD.command` if permitted by macOS security settings.

The application requires internet access. It uses unofficial Yahoo Finance data via yfinance and may be rate-limited, stale or missing. The model ranks only the tickers entered, not an automatically discovered entire sector. It does not provide full EPS revision histories, consensus estimates, or live options data. Use company filings to verify figures before decisions. The app does not run inside ChatGPT Projects: upload exported CSVs to the project for analysis.


## Expanded Block 3 prompt library
The website now has **133** ready-made Block 3 research prompts, including 55 U.S. sector-by-size combinations, 48 country/theme combinations, and 30 beginner education and thematic prompts. Search and category filters are in the sidebar. Choose **Custom — write my own** for completely free-form instructions. Presets do not guarantee that all requested stocks can be automatically discovered; the live screener still requires tickers and supports up to 30 per run.

Deploy with `BLOCK3_PROMPT_LIBRARY.json` alongside `QFAIM_Website.py`.
