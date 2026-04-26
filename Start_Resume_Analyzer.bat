@echo off
echo ----------------------------------------------------
echo Starting TalentLens AI Resume Analyzer Server
echo Please do not close this window while using the app!
echo ----------------------------------------------------
python -m uvicorn main:app --reload
pause
