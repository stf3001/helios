@echo off
rem ============================================================
rem  HELIOS — demarrage complet en un double-clic (dev local)
rem  Lance : Postgres (Docker) + API FastAPI + frontend Vite
rem ============================================================
setlocal
set "ROOT=%~dp0"
set "PATH=%PATH%;C:\Program Files\Docker\Docker\resources\bin"

echo.
echo  ☀ HELIOS — demarrage...
echo.

rem --- 1. Postgres (Docker) ---
docker ps >nul 2>&1
if errorlevel 1 (
    echo  [1/4] Docker ne repond pas — lancement de Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo        Attente du demarrage de Docker ^(jusqu'a 60 s^)...
    for /l %%i in (1,1,30) do (
        timeout /t 2 /nobreak >nul
        docker ps >nul 2>&1 && goto docker_ok
    )
    echo  [ERREUR] Docker n'a pas demarre. Ouvrez Docker Desktop puis relancez ce script.
    pause
    exit /b 1
)
:docker_ok
echo  [1/4] Docker OK — demarrage de Postgres...
cd /d "%ROOT%"
docker compose up -d postgres >nul 2>&1

rem --- 2. API FastAPI (fenetre dediee) ---
echo  [2/4] Lancement de l'API (port 8000)...
start "HELIOS API" cmd /k "cd /d %ROOT%api && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

rem --- 3. Frontend Vite (fenetre dediee) ---
echo  [3/4] Lancement du frontend (port 5173)...
start "HELIOS Frontend" cmd /k "cd /d %ROOT%frontend && npm run dev"

rem --- 4. Navigateur ---
echo  [4/4] Ouverture du navigateur dans 8 secondes...
timeout /t 8 /nobreak >nul
start "" "http://localhost:5173"

echo.
echo  ☀ HELIOS est lance. Deux fenetres restent ouvertes (API + Frontend) :
echo    les fermer arrete le site. Postgres continue en arriere-plan (Docker).
echo.
pause
