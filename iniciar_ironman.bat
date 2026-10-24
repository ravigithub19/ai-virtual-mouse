@echo off
title Ironman Touchless Pro - JARVIS HUD
echo ========================================================
echo   Iniciando Ironman Touchless Pro (JARVIS HUD)...
echo   Webcam USB: Logitech C922
echo   Pressione 'q' na janela de video para sair.
echo ========================================================
python ironman_touchless_pro.py
if errorlevel 1 (
    echo.
    echo Ocorreu um erro ao executar a aplicacao.
    pause
)
