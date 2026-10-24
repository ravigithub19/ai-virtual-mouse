@echo off
title AI Virtual Mouse Studio
echo ========================================================
echo   Iniciando AI Virtual Mouse Studio & Test Lab...
echo ========================================================
python main_gui.py
if errorlevel 1 (
    echo.
    echo Ocorreu um erro ao executar a aplicacao.
    pause
)
