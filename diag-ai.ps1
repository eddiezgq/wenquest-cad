# 诊断 AI 对话面板连不上模型的原因（不显示密钥，不调用模型）
#   powershell -ExecutionPolicy Bypass -File .\diag-ai.ps1
param([string]$Root = "C:\wqcad")
$env:Path = "$env:USERPROFILE\.pixi\bin;$env:Path"
$env:PYTHONUTF8 = "1"
foreach ($k in "ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY") {
    if (-not (Get-Item "Env:$k" -ErrorAction SilentlyContinue)) {
        $v = [Environment]::GetEnvironmentVariable($k, "User")
        if ($v) { Set-Item "Env:$k" $v }
    }
}
$Src = Join-Path $Root "FreeCAD"
$m = (Join-Path $Src "pixi.toml") -replace '\\', '/'
$py = (Join-Path $Src ".pixi\envs\default\python.exe") -replace '\\', '/'
$d = (Join-Path $PSScriptRoot "diag_ai.py") -replace '\\', '/'
$log = Join-Path $PSScriptRoot "logs\diag-ai.txt"
Push-Location $Src
& pixi run --frozen --manifest-path $m $py $d 2>&1 | Tee-Object -FilePath $log
Pop-Location
Write-Host "结果也存在 logs\diag-ai.txt"
