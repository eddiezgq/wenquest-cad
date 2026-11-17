# 问渠 CAD 0.1 构建脚本：FreeCAD 1.1.4 + 本书 27 个补丁（方案：本书仓库 docs/问渠CAD方案.md）
# 用法（在本文件所在文件夹里打开 PowerShell）：
#   powershell -ExecutionPolicy Bypass -File .\build-wqcad.ps1
# 可重复运行：已下载的源码与依赖不重下；每次都先回到 1.1.4 原样再打补丁。
param([string]$Root = "C:\wqcad")

# 外部程序的成败一律看退出码（Run 函数）；不用 Stop，免得 PowerShell 5 把程序写到 stderr 的普通输出当成错误
$ErrorActionPreference = "Continue"
$Kit = $PSScriptRoot
$Logs = Join-Path $Kit "logs"
New-Item -ItemType Directory -Force $Logs | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
Start-Transcript -Path (Join-Path $Logs "build-$Stamp.log") | Out-Null
$Summary = Join-Path $Logs "summary-$Stamp.txt"
function Step($msg) { $line = "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $msg; Write-Host $line -ForegroundColor Cyan; Add-Content -Path $Summary -Value $line -Encoding UTF8 }
function Stop-Build($msg) { Step "失败：$msg"; Stop-Transcript | Out-Null; exit 1 }
function Run($what) { if ($LASTEXITCODE -ne 0) { Stop-Build "$what（退出码 $LASTEXITCODE）" } }

# ---------- 1 检查工具 ----------
Step "1/7 检查工具"
$env:Path = "$env:USERPROFILE\.pixi\bin;$env:Path"
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Stop-Build "没有找到 git，请先装 Git for Windows" }
if (-not (Get-Command pixi -ErrorAction SilentlyContinue)) { Stop-Build "没有找到 pixi，请先装 pixi" }
$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
$vs = $null
if (Test-Path $vswhere) { $vs = & $vswhere -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath }
if (-not $vs) { Stop-Build "没有找到 Visual Studio 2022 的 C++ 生成工具" }
Step ("git {0}；pixi {1}；VS {2}" -f (git --version), (pixi --version), $vs)
$freeGB = [math]::Round((Get-PSDrive -Name ($Root.Substring(0,1))).Free / 1GB)
Step "磁盘剩余 $freeGB GB"
if ($freeGB -lt 40) { Stop-Build "磁盘剩余不足 40 GB" }

# ---------- 2 取源码 ----------
Step "2/7 取 FreeCAD 1.1.4 源码到 $Root\FreeCAD"
$Src = Join-Path $Root "FreeCAD"
New-Item -ItemType Directory -Force $Root | Out-Null
if (-not (Test-Path (Join-Path $Src ".git"))) {
    git -c core.autocrlf=false clone --branch 1.1.4 --depth 1 --recurse-submodules --shallow-submodules https://github.com/FreeCAD/FreeCAD.git $Src
    Run "下载源码"
}
Set-Location $Src
git config core.autocrlf false

# ---------- 3 打补丁 ----------
Step "3/7 回到 1.1.4 原样，按序打 27 个补丁"
git reset --hard HEAD | Out-Null; Run "git reset"
git clean -fd | Out-Null; Run "git clean"
$n = 0
foreach ($line in Get-Content (Join-Path $Kit "patches\series.txt") -Encoding UTF8) {
    $file = $line.Split("`t")[0]
    git apply --index --whitespace=nowarn (Join-Path $Kit "patches\$file")
    Run "补丁打不上：$file"
    $n++
    Step "  已打 $file"
}
Step "共打上 $n 个补丁"

# ---------- 4 编译、安装 ----------
$memGB = [math]::Floor((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB)
$jobs = [math]::Max(1, [math]::Min([Environment]::ProcessorCount, [math]::Floor($memGB / 2)))
$env:CMAKE_BUILD_PARALLEL_LEVEL = "$jobs"
Step "4/7 编译（内存 $memGB GB，CPU $([Environment]::ProcessorCount) 线程，并行 $jobs）"
# 部分 conda 包（如 Qt、PySide）安装后要运行自带的设置脚本，pixi 默认不运行
pixi config set --local run-post-link-scripts insecure; Run "pixi 设置 run-post-link-scripts"
pixi install --force-reinstall; Run "重装依赖（让设置脚本生效）"
pixi run configure-release; Run "配置（configure-release）"
Step "  配置完成"
pixi run build-release; Run "编译（build-release）"
Step "  编译完成"
pixi run install-release; Run "安装（install-release）"
$Bin = Join-Path $Src ".pixi\envs\default\Library\bin"
$Exe = Join-Path $Bin "FreeCAD.exe"
$Cmd = Join-Path $Bin "FreeCADCmd.exe"
if (-not (Test-Path $Exe)) { Stop-Build "安装后没有找到 $Exe" }
Step "  安装完成：$Exe"

# ---------- 5 品牌 ----------
Step "5/7 窗口标题"
Copy-Item (Join-Path $Kit "branding.xml") (Join-Path $Bin "branding.xml") -Force

# ---------- 6 测试 ----------
Step "6/7 测试"
foreach ($t in "TestPartApp", "TestSketcherApp", "TestPartDesignApp", "MeshTestsApp") {
    $log = Join-Path $Logs "$t.log"
    Start-Process -FilePath $Cmd -ArgumentList "-t", $t -RedirectStandardOutput $log -RedirectStandardError "$log.err" -Wait -NoNewWindow
    $tail = (Get-Content $log, "$log.err" | Select-String -Pattern "^(Ran \d+ tests|OK|FAILED)" | ForEach-Object { $_.Line }) -join "；"
    Step "  $t：$tail"
}
foreach ($f in Get-ChildItem (Join-Path $Kit "tests") -Filter *.py) {
    $env:WQCAD_TEST_FILE = $f.FullName
    $env:WQCAD_OUT = Join-Path $Logs ($f.BaseName + ".json")
    $log = Join-Path $Logs ($f.BaseName + ".log")
    Start-Process -FilePath $Cmd -ArgumentList ("`"" + (Join-Path $Kit "run_book_tests.py") + "`"") -RedirectStandardOutput $log -RedirectStandardError "$log.err" -Wait -NoNewWindow
    $res = Get-Content $log, "$log.err" | Select-String -Pattern "^WQCAD " | ForEach-Object { $_.Line }
    if (-not $res) { $res = "没有结果（崩溃？见 $log）" }
    Step "  本书测试 $($f.BaseName)：$res"
}

# ---------- 7 快捷方式 ----------
Step "7/7 桌面快捷方式“问渠 CAD”"
$lnk = Join-Path ([Environment]::GetFolderPath("Desktop")) "问渠 CAD.lnk"
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($lnk)
$sc.TargetPath = $Exe
$sc.WorkingDirectory = $Bin
$sc.Save()
Step "完成。双击桌面上的“问渠 CAD”启动。"
Stop-Transcript | Out-Null
