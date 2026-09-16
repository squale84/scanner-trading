@echo off
title Scanner Trading
cd /d "%~dp0"

echo Lancement du serveur local...
start "Serveur FastAPI" cmd /k python -m uvicorn server:app --reload --port 8000

timeout /t 3 >nul

echo Lancement du tunnel Cloudflare...
start "Tunnel Cloudflare" cmd /k cloudflared.exe tunnel --url http://localhost:8000

echo Ouverture de la page web...
timeout /t 2 >nul
start http://localhost:8000