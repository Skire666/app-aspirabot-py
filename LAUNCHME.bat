@echo off
setlocal

set PROJECT=app-aspirabot-py

for %%D in (D E F) do (
    if exist "%%D:\%PROJECT%\__src__\main.py" (
        cd /d "%%D:\%PROJECT%"

        call .\venv\Scripts\activate

        python __src__\main.py
        exit /b
    )
)

echo Projet introuvable sur D:, E: ou F:.
pause