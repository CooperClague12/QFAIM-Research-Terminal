#!/bin/bash
cd "$(dirname "$0")"
python3 -m pip install -r requirements.txt || { echo 'Dependency installation failed'; read -r; exit 1; }
python3 -m streamlit run QFAIM_Live_App.py
