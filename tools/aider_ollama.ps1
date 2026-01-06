param(
    [Parameter(Mandatory = $false)]
    [string]$Model = "qwen2.5-coder:7b-instruct",

    [Parameter(Mandatory = $false)]
    [string]$ApiBase = "http://127.0.0.1:11434",

    [Parameter(Mandatory = $false)]
    [int]$ContextLength = 8192,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AiderArgs
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command "aider" -ErrorAction SilentlyContinue)) {
    Write-Host "aider ist nicht installiert oder nicht im PATH."
    Write-Host "Installiere mit: python -m pip install aider-install" 
    exit 1
}

if (-not (Get-Command "ollama" -ErrorAction SilentlyContinue)) {
    Write-Host "ollama ist nicht installiert oder nicht im PATH."
    Write-Host "Installiere Ollama: https://ollama.com" 
    exit 1
}

if (-not $env:OLLAMA_API_BASE) {
    $env:OLLAMA_API_BASE = $ApiBase
}

if (-not $env:OLLAMA_CONTEXT_LENGTH) {
    $env:OLLAMA_CONTEXT_LENGTH = "$ContextLength"
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

Write-Host "OLLAMA_API_BASE=$env:OLLAMA_API_BASE"
Write-Host "OLLAMA_CONTEXT_LENGTH=$env:OLLAMA_CONTEXT_LENGTH"
Write-Host "Model=ollama_chat/$Model"

Push-Location $repoRoot
try {
    & aider --model "ollama_chat/$Model" @AiderArgs
} finally {
    Pop-Location
}
