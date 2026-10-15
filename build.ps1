Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Сборка EXE для РАНХиГС (PowerShell)   " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python не найден! Установите Python 3.10+" -ForegroundColor Red
    pause
    exit
}

Write-Host "Устанавливаю зависимости..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install --upgrade selenium pyinstaller

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка при установке зависимостей!" -ForegroundColor Red
    pause
    exit
}

Write-Host "Очищаю предыдущие сборки..." -ForegroundColor Yellow
Remove-Item -Path "build", "dist" -Recurse -ErrorAction SilentlyContinue
Remove-Item -Path "*.spec" -ErrorAction SilentlyContinue

Write-Host "Собираю EXE..." -ForegroundColor Yellow
python -m PyInstaller --onefile --windowed `
  --collect-all=selenium `
  --name "ranepa_automation" `
  main.py

if (-not (Test-Path "dist\ranepa_automation.exe")) {
    Write-Host "❌ Ошибка при сборке!" -ForegroundColor Red
    pause
    exit
}

Write-Host "Готовлю шаблоны..." -ForegroundColor Yellow

@"
your_login
your_password
"@ | Out-File -FilePath "dist\login.txt.example" -Encoding UTF8

@"
Название_группы
ФИО_сотрудника
ФИО_заявителя
"@ | Out-File -FilePath "dist\data.txt.example" -Encoding UTF8

@"
========================================
  РАНХиГС — автоматизация заявок
========================================

ПОДГОТОВКА:
1. Установите Google Chrome
2. Скачайте папку целиком

НАСТРОЙКА:
1. Переименуйте 'login.txt.example' в 'login.txt'
   строка 1: логин
   строка 2: пароль

2. Переименуйте 'data.txt.example' в 'data.txt'
   строка 1: группа
   строка 2: кому назначить
   строка 3: заявитель

ЗАПУСК:
Запустите 'ranepa_automation.exe'

ПАРАЛЛЕЛЬНЫЙ ЗАПУСК:
Можно запускать несколько копий одновременно.
Каждый процесс — своя чистая сессия Chrome.
Одновременно работают не более MAX_PARALLEL (см. config.py).

ЛОГИ: выводятся в консоль.
"@ | Out-File -FilePath "dist\README.txt" -Encoding UTF8

$fileSize = [math]::Round((Get-Item "dist\ranepa_automation.exe").Length / 1MB, 2)

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ СБОРКА УСПЕШНО ЗАВЕРШЕНА!" -ForegroundColor Green
Write-Host "   EXE: dist\ranepa_automation.exe ($fileSize MB)" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
pause