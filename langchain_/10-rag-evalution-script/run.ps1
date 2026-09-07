# main.py를 올바른 인터프리터로 실행하는 헬퍼.
#
# PATH의 python은 pyenv shim(3.13.13)이고 거기엔 langchain이 없다.
# 패키지는 시스템 Python 3.13.15에 설치돼 있으므로 그쪽으로 넘긴다.
#
#   .\run.ps1 --config chunk_700 --retrieval-only --limit 3
#   .\run.ps1 --compare

$ErrorActionPreference = "Stop"

$python = "C:\Users\snail\AppData\Local\Programs\Python\Python313\python.exe"

if (-not (Test-Path $python)) {
    Write-Error "인터프리터를 찾지 못했습니다: $python`n경로가 바뀌었다면 run.ps1의 `$python 값을 고치세요."
    exit 1
}

& $python (Join-Path $PSScriptRoot "main.py") @args
exit $LASTEXITCODE
