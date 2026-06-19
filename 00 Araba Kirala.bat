@echo off
:: Change directory to the folder where this batch file is located


:: Run the Streamlit application
python -m streamlit run app.py

:: Keep the command window open if the application crashes or stops
pause