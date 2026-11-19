# 问渠 CAD 0.2a / 0.3c：把 freecad-ai-parts 的 AI Parts 工作台装进问渠 CAD（细则见 docs\细则-0.2.md、docs\细则-0.3.md 的 0.3c）
#   powershell -ExecutionPolicy Bypass -File .\ai-wqcad.ps1
# 可重复运行。不调用 AI 模型，不读写密钥。
param(
    [string]$Root = "C:\wqcad",
    [string]$Commit = "c5cb1c278502e159bd2dc255806f377fa7366591"
)

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$Kit = $PSScriptRoot
$Logs = Join-Path $Kit "logs"
New-Item -ItemType Directory -Force $Logs | Out-Null
$Summary = Join-Path $Logs ("ai-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".txt")
function Step($msg) { $line = "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $msg; Write-Host $line -ForegroundColor Cyan; Add-Content -Path $Summary -Value $line -Encoding UTF8 }
function Fail($msg) { Step "失败：$msg"; exit 1 }

$env:Path = "$env:USERPROFILE\.pixi\bin;$env:Path"
$Pixi = (Get-Command pixi -ErrorAction SilentlyContinue).Source
if (-not $Pixi) { Fail "找不到 pixi" }
$Src = Join-Path $Root "FreeCAD"
$Manifest = Join-Path $Src "pixi.toml"
$PyEnv = Join-Path $Src ".pixi\envs\default"
$Py = Join-Path $PyEnv "python.exe"
$Cmd = Join-Path $PyEnv "Library\bin\FreeCADCmd.exe"
$ModDir = Join-Path $PyEnv "Library\Mod"
$Repo = Join-Path $Root "freecad-ai-parts"
if (-not (Test-Path $Cmd)) { Fail "没有找到 $Cmd，请先完成 0.1（build-wqcad.ps1）" }

# pixi run 会吃掉反斜杠，路径一律换成正斜杠
function Fwd($p) { return ($p -replace '\\', '/') }
function Invoke-Env($exe, $argList, $log) {
    $a = @("run", "--frozen", "--manifest-path", "`"$(Fwd $Manifest)`"", "`"$(Fwd $exe)`"") + $argList
    $p = Start-Process -FilePath $Pixi -ArgumentList $a -WorkingDirectory $Src -RedirectStandardOutput $log -RedirectStandardError "$log.err" -Wait -NoNewWindow -PassThru
    return $p.ExitCode
}

Step "1/5 取 freecad-ai-parts（固定提交 $($Commit.Substring(0,7))）"
if (-not (Test-Path (Join-Path $Repo ".git"))) {
    git clone --no-checkout https://github.com/eddiezgq/freecad-ai-parts.git $Repo 2>&1 | Write-Host
    if (-not (Test-Path (Join-Path $Repo ".git"))) { Fail "git clone 失败（这个仓库是私有的，需要用你的 GitHub 账号登录）" }
}
# 仓库的 factory/ 里有 aux.kicad_sch 这类 Windows 保留的文件名：git 默认连登记都拒绝（invalid path）。
# 只对这个仓库关掉这项检查，并且只取工作台用到的目录，factory/ 不写到硬盘上
git -C $Repo config core.protectNTFS false
git -C $Repo sparse-checkout set freecad_addon engine kb analysis mcp_server llm_gateway ingest licensing schema data tests 2>&1 | Write-Host
git -C $Repo fetch --quiet origin 2>&1 | Write-Host
git -C $Repo -c advice.detachedHead=false checkout --quiet --force $Commit 2>&1 | Write-Host
$head = (git -C $Repo rev-parse HEAD).Trim()
if ($head -ne $Commit) { Fail "切换到 $Commit 失败（现在是 $head）" }
Step "  已在 $head"

Step "2/5 用问渠 CAD 的 Python 装依赖（基本依赖 + 对话 + 网格）"
$reqPy = Join-Path $Logs "ai-req.py"
$req = Join-Path $Logs "ai-requirements.txt"
$code = @"
import sys, tomllib
p = tomllib.load(open(sys.argv[1], 'rb'))['project']
reqs = list(p['dependencies']) + list(p['optional-dependencies']['llm']) + list(p['optional-dependencies']['fea'])
open(sys.argv[2], 'w', encoding='ascii').write('\n'.join(r.split('#')[0].strip() for r in reqs if r.strip()) + '\n')
"@
[IO.File]::WriteAllText($reqPy, $code, (New-Object Text.UTF8Encoding $false))
$rc = Invoke-Env $Py @("`"$(Fwd $reqPy)`"", "`"$(Fwd (Join-Path $Repo 'pyproject.toml'))`"", "`"$(Fwd $req)`"") (Join-Path $Logs "ai-req.log")
if ($rc -ne 0 -or -not (Test-Path $req)) { Fail "读取依赖清单失败（见 logs\ai-req.log.err）" }
Step ("  " + ((Get-Content $req) -join "，"))
$pipLog = Join-Path $Logs "ai-pip.log"
$rc = Invoke-Env $Py @("-m", "pip", "install", "--disable-pip-version-check", "--no-warn-script-location", "--progress-bar", "off", "-r", "`"$(Fwd $req)`"") $pipLog
if ($rc -ne 0) { Fail "依赖安装失败（见 logs\ai-pip.log.err）" }
Step "  依赖已装好"

Step "3/5 检查 CalculiX（AI 设计零件算台阶圆角的应力集中要用，本机计算、不联网）"
$ccx = $null
$cands = @([Environment]::GetEnvironmentVariable("FAP_CCX", "User"), (Join-Path $PyEnv "Library\bin\ccx.exe"),
           (Join-Path $env:USERPROFILE ".pixi\bin\ccx.exe"), (Join-Path $env:USERPROFILE ".pixi\bin\ccx.bat"))
foreach ($c in $cands) { if ($c -and (Test-Path $c)) { $ccx = $c; break } }
if (-not $ccx) {
    Step "  没有找到，从 conda-forge 装 calculix（pixi global，单独的环境，不动问渠 CAD 的环境）"
    & $Pixi global install calculix 2>&1 | Write-Host
    foreach ($c in $cands[2..3]) { if (Test-Path $c) { $ccx = $c; break } }
}
if (-not $ccx) { Fail "装不上 CalculiX（ccx），把屏幕上的输出发给 Claude" }
[Environment]::SetEnvironmentVariable("FAP_CCX", $ccx, "User")
$env:FAP_CCX = $ccx
Step "  CalculiX：$ccx（已记进用户环境变量 FAP_CCX）"

Step "4/5 把工作台装进问渠 CAD（$ModDir\FreeCADAIParts）"
$env:PYTHONPATH = $Repo
$rc = Invoke-Env $Py @("-m", "freecad_addon.install", "--standalone", "--mod-dir", "`"$(Fwd $ModDir)`"") (Join-Path $Logs "ai-install.log")
Remove-Item Env:\PYTHONPATH
$lib = Join-Path $ModDir "FreeCADAIParts\lib"
if ($rc -ne 0 -or -not (Test-Path (Join-Path $ModDir "FreeCADAIParts\InitGui.py"))) { Fail "工作台安装失败（见 logs\ai-install.log 与 .err）" }
Step "  已装好"

Step "5/5 冒烟检查（不调用 AI 模型）"
$env:WQCAD_AI_LIB = $lib
$env:WQCAD_OUT = Join-Path $Logs "ai-smoke.json"
$smokeLog = Join-Path $Logs "ai-smoke.log"
$rc = Invoke-Env $Cmd @("`"$(Fwd (Join-Path $Kit 'run_ai_smoke.py'))`"") $smokeLog
$res = Get-Content $smokeLog, "$smokeLog.err" -ErrorAction SilentlyContinue | Select-String -Pattern "^WQCAD-AI " | ForEach-Object { $_.Line }
if (-not $res) { $res = "没有结果（见 logs\ai-smoke.log）" }
Step "  $res"
if (-not ($res -match " OK$")) { Fail "冒烟检查没过，把 logs\ai-smoke.json 发给 Claude" }

$hasKey = [Environment]::GetEnvironmentVariable("ANTHROPIC_API_KEY", "User") -or [Environment]::GetEnvironmentVariable("DEEPSEEK_API_KEY", "User")
Step "冒烟检查通过。"
if (-not $hasKey) {
    Step "还差密钥：在 PowerShell 里自己输入下面这行（把 sk-ant-... 换成你的 Claude 密钥），然后重开问渠 CAD："
    Write-Host '  setx ANTHROPIC_API_KEY "sk-ant-..."' -ForegroundColor Yellow
    Write-Host "  （到国内用时再设 DEEPSEEK_API_KEY，用国内部署现有的那个；软件会按地区自动切换）" -ForegroundColor Yellow
} else {
    Step "已设好密钥。重开问渠 CAD，在工作台下拉框里选 AI Parts。"
}
