@echo off
echo Hosting update: Hugging Face Docker Spaces now require a paid plan.
echo Use the Render Free Docker instructions that will open now.
start "" notepad.exe "%~dp0DEPLOY-RENDER.md"
start "" "https://dashboard.render.com/register"
pause
