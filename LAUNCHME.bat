@echo off

cd /d "%~dp0"

call .\venv\Scripts\activate

python __src__/main.py