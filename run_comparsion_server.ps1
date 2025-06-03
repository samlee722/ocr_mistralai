# 두 OCR 서버를 동시에 실행하는 스크립트

# 0. 가상 환경 활성화 경로 설정
# Windows PowerShell에서는 .venv\Scripts\Activate.ps1을 실행합니다.
$venvPath = ".\.venv\Scripts\Activate.ps1"

# 가상 환경 활성화 스크립트가 있는지 확인
if (-not (Test-Path $venvPath)) {
    Write-Host "❌ 오류: 가상 환경 활성화 스크립트를 찾을 수 없습니다."
    Write-Host "   경로: $venvPath"
    Write-Host "   스크립트와 같은 디렉토리에 '.venv' 가상 환경이 있는지 확인하세요."
    # PowerShell 스크립트 실행을 위해 Enter 키를 누를 때까지 대기
    Read-Host "Press Enter to exit"
    exit
}

# 가상 환경 활성화 시도
try {
    . $venvPath
    Write-Host "✅ Virtual environment activated."
}
catch {
    Write-Host "❌ 오류: 가상 환경을 활성화하지 못했습니다."
    Write-Host "   PowerShell 실행 정책(Execution Policy) 문제일 수 있습니다."
    Write-Host "   PowerShell을 관리자 권한으로 열고 아래 명령어를 실행해 보세요."
    Write-Host "   Set-ExecutionPolicy RemoteSigned"
    Read-Host "Press Enter to exit"
    exit
}

Write-Host "🚀 Starting OCR Comparison Servers..."
Write-Host "=================================="

# try...finally 블록을 사용하여 스크립트가 종료될 때(Ctrl+C 포함)
# finally 블록이 항상 실행되도록 보장합니다.
try {
    # 1. OCR API 서버 시작
    Write-Host "1️⃣ Starting OCR API Server (port 8002)..."
    # -WindowStyle Hidden # 주석 해제 시 새 창이 뜨지 않음
    $proc1 = Start-Process uvicorn -ArgumentList "main_ocr_only:app --reload --port 8002" -PassThru

    # 잠시 대기
    Start-Sleep -Seconds 2

    # 2. Vision 모델 서버 시작
    Write-Host "2️⃣ Starting Vision Model Server (port 8003)..."
    $proc2 = Start-Process uvicorn -ArgumentList "main_vision_only:app --reload --port 8003" -PassThru

    Write-Host ""
    Write-Host "✅ Both servers are running!"
    Write-Host ""
    Write-Host "📍 Endpoints:"
    Write-Host "  - OCR API: http://localhost:8002/ocr/extract-text"
    Write-Host "  - Vision: http://localhost:8003/ocr/vision-extract"
    Write-Host ""
    Write-Host "🧪 To test:"
    Write-Host "  python test_ocr_comparison.py <image_file>"
    Write-Host ""
    Write-Host "Press Ctrl+C to stop all servers..."

    # 스크립트가 바로 종료되지 않고 서버들이 실행되도록 무한 대기
    while ($true) {
        Start-Sleep -Seconds 1
    }
}
finally {
    # 이 블록은 스크립트가 정상 종료되거나, 오류가 발생하거나, 사용자가 Ctrl+C를 눌렀을 때 실행됩니다.
    Write-Host "`n🛑 Stopping servers..."
    
    # 실행된 프로세스들이 있으면 종료시킴
    if ($proc1) {
        Stop-Process -Id $proc1.Id -Force -ErrorAction SilentlyContinue
    }
    if ($proc2) {
        Stop-Process -Id $proc2.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "All servers stopped."
}