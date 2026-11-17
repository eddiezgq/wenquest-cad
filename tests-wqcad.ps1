# 问渠 CAD：窗口标题、测试、启动器与桌面快捷方式（build-wqcad.ps1 编译完成后调用；也可单独运行）
#   powershell -ExecutionPolicy Bypass -File .\tests-wqcad.ps1
# FreeCAD 要在 pixi 环境里启动（Python、Qt 等 DLL 在环境的其他目录），所以一律经 "pixi run" 启动。
param([string]$Root = "C:\wqcad")

$ErrorActionPreference = "Continue"
$Kit = $PSScriptRoot
$Logs = Join-Path $Kit "logs"
New-Item -ItemType Directory -Force $Logs | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Summary = Join-Path $Logs "tests-$Stamp.txt"
function Step($msg) { $line = "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $msg; Write-Host $line -ForegroundColor Cyan; Add-Content -Path $Summary -Value $line -Encoding UTF8 }

$env:Path = "$env:USERPROFILE\.pixi\bin;$env:Path"
$Pixi = (Get-Command pixi).Source
$Src = Join-Path $Root "FreeCAD"
$Manifest = Join-Path $Src "pixi.toml"
$Bin = Join-Path $Src ".pixi\envs\default\Library\bin"
$Exe = Join-Path $Bin "FreeCAD.exe"
$Cmd = Join-Path $Bin "FreeCADCmd.exe"
if (-not (Test-Path $Exe)) { Step "没有找到 $Exe，请先运行 build-wqcad.ps1"; exit 1 }

function Invoke-FreeCADCmd($argList, $log) {
    $a = @("run", "--frozen", "--manifest-path", "`"$($Manifest -replace '\\','/')`"", "`"$($Cmd -replace '\\','/')`"") + $argList
    $p = Start-Process -FilePath $Pixi -ArgumentList $a -WorkingDirectory $Src -RedirectStandardOutput $log -RedirectStandardError "$log.err" -Wait -NoNewWindow -PassThru
    return $p.ExitCode
}

Step "1/3 窗口标题"
Copy-Item (Join-Path $Kit "branding.xml") (Join-Path $Bin "branding.xml") -Force

Step "2/3 测试"
$code = Invoke-FreeCADCmd @("--version") (Join-Path $Logs "version.log")
$ver = (Get-Content (Join-Path $Logs "version.log"), (Join-Path $Logs "version.log.err") -ErrorAction SilentlyContinue) -join " "
Step "  FreeCADCmd --version：$ver（退出码 $code）"
foreach ($t in "TestPartApp", "TestSketcherApp", "TestPartDesignApp", "MeshTestsApp") {
    $log = Join-Path $Logs "$t.log"
    $code = Invoke-FreeCADCmd @("-t", $t) $log
    $tail = (Get-Content $log, "$log.err" | Select-String -Pattern "^(Ran \d+ tests|OK|FAILED)" | ForEach-Object { $_.Line }) -join "；"
    Step "  $t：$tail（退出码 $code）"
}
foreach ($f in Get-ChildItem (Join-Path $Kit "tests") -Filter *.py) {
    $env:WQCAD_TEST_FILE = $f.FullName
    $env:WQCAD_OUT = Join-Path $Logs ($f.BaseName + ".json")
    $log = Join-Path $Logs ($f.BaseName + ".log")
    $code = Invoke-FreeCADCmd @("`"$(Join-Path $Kit "run_book_tests.py")`"") $log
    $res = Get-Content $log, "$log.err" | Select-String -Pattern "^WQCAD " | ForEach-Object { $_.Line }
    if (-not $res) { $res = "没有结果（见 $log）" }
    Step "  本书测试 $($f.BaseName)：$res（退出码 $code）"
}

Step "3/3 启动器与桌面快捷方式"
$Launcher = Join-Path $Root "WenQuestCAD.cmd"
# pixi run 把命令里的反斜杠当转义符吃掉，所以传给它的路径一律用正斜杠
$cmdText = "@echo off`r`ncd /d `"$Src`"`r`n`"$Pixi`" run --frozen --manifest-path `"$($Manifest -replace '\\','/')`" `"$($Exe -replace '\\','/')`" %*`r`n"
[System.IO.File]::WriteAllText($Launcher, $cmdText, (New-Object System.Text.UTF8Encoding($false)))
# WScript.Shell 处理不了中文文件名：先用英文名建快捷方式，再改名
$desk = [Environment]::GetFolderPath("Desktop")
$tmpLnk = Join-Path $desk "WenQuestCAD.lnk"
$lnk = Join-Path $desk "问渠 CAD.lnk"
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($tmpLnk)
$sc.TargetPath = $Launcher
$sc.WorkingDirectory = $Src
$sc.WindowStyle = 7
$sc.IconLocation = "$Exe,0"
$sc.Save()
if (Test-Path -LiteralPath $lnk) { Remove-Item -LiteralPath $lnk -Force }
Move-Item -LiteralPath $tmpLnk -Destination $lnk -Force
Step "完成。双击桌面上的“问渠 CAD”启动（首次启动约需半分钟）。"
