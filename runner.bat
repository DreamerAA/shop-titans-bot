@echo off
REM Активация виртуального окружения
call ..\env-stb\Scripts\Activate.bat

REM Запуск бота с конфигурацией
python -m bot.run.main --config .\configs\my_config.yaml
