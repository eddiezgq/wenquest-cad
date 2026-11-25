# 问渠 CAD 0.2b：给 OCCT 7.8.1 打上本书的修正（细则见 docs\细则-0.2.md）
#   powershell -ExecutionPolicy Bypass -File .\build-occt.ps1            # 编译并替换（约 1 小时）
#   powershell -ExecutionPolicy Bypass -File .\build-occt.ps1 -Restore   # 换回原来的 OCCT
#   pwsh -File .\build-occt.ps1 -Root D:\wqcad -OutDir D:\occt-out      # 只编不换：3 个库放到 OutDir（安装包工作流用，0.3.7）
# 只重编受补丁影响的 3 个程序库（TKMath、TKGeomAlgo、TKTopAlgo），补丁不改头文件，FreeCAD 不用重编。
param(
    [string]$Root = "C:\wqcad",
    [switch]$Restore,
    [string]$OutDir = ""
)

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"
$Kit = $PSScriptRoot
$Logs = Join-Path $Kit "logs"
New-Item -ItemType Directory -Force $Logs | Out-Null
$Summary = Join-Path $Logs ("occt-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".txt")
function Step($msg) { $line = "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $msg; Write-Host $line -ForegroundColor Cyan; Add-Content -Path $Summary -Value $line -Encoding UTF8 }
function Fail($msg) { Step "失败：$msg"; exit 1 }
function Fwd($p) { return ($p -replace '\\', '/') }

$env:Path = "$env:USERPROFILE\.pixi\bin;$env:Path"
$Pixi = (Get-Command pixi -ErrorAction SilentlyContinue).Source
if (-not $Pixi) { Fail "找不到 pixi" }
$Src = Join-Path $Root "FreeCAD"
$Manifest = Join-Path $Src "pixi.toml"
$Bin = Join-Path $Src ".pixi\envs\default\Library\bin"
$Occt = Join-Path $Root "occt-7.8.1"
$Build = Join-Path $Root "occt-7.8.1-build"
$Backup = Join-Path $Root "occt-7.8.1-original"
$Dlls = @("TKMath.dll", "TKGeomAlgo.dll", "TKTopAlgo.dll")
if (-not $OutDir -and -not (Test-Path (Join-Path $Bin "FreeCAD.exe"))) { Fail "没有找到问渠 CAD（先完成 0.1）" }
if (-not (Get-ChildItem (Join-Path $Src ".pixi\envs\default\conda-meta") -Filter "occt-7.8.1-*.json" -ErrorAction SilentlyContinue)) { Fail "环境里的 OCCT 不是 7.8.1，补丁对不上" }

if ($Restore) {
    foreach ($d in $Dlls) {
        $b = Join-Path $Backup $d
        if (-not (Test-Path $b)) { Fail "没有备份 $b，无法换回" }
        Copy-Item $b (Join-Path $Bin $d) -Force
    }
    Step "已换回原来的 OCCT 程序库（$($Dlls -join '、')）。"
    exit 0
}

function Invoke-Env($argList, $log) {
    $a = @("run", "--frozen", "--manifest-path", "`"$(Fwd $Manifest)`"") + $argList
    $p = Start-Process -FilePath $Pixi -ArgumentList $a -WorkingDirectory $Src -RedirectStandardOutput $log -RedirectStandardError "$log.err" -Wait -NoNewWindow -PassThru
    return $p.ExitCode
}

Step "1/5 取 OCCT 7.8.1 源码"
if (-not (Test-Path (Join-Path $Occt ".git"))) {
    git clone --quiet --depth 1 --branch V7_8_1 https://github.com/Open-Cascade-SAS/OCCT.git $Occt 2>&1 | Write-Host
    if (-not (Test-Path (Join-Path $Occt "CMakeLists.txt"))) { Fail "下载 OCCT 源码失败" }
}

Step "2/5 打补丁（patches\occt-7.8.1，5 个）"
$patches = Get-ChildItem (Join-Path $Kit "patches\occt-7.8.1") -Filter *.patch | Sort-Object Name
$hash = ($patches | ForEach-Object { (Get-FileHash $_.FullName -Algorithm SHA256).Hash }) -join ","
$stamp = Join-Path $Occt "wqcad-patched.txt"
if (-not (Test-Path $stamp) -or (Get-Content $stamp -Raw).Trim() -ne $hash) {
    git -C $Occt checkout --quiet -- . 2>&1 | Write-Host
    foreach ($p in $patches) {
        git -C $Occt apply --whitespace=nowarn $p.FullName 2>&1 | Write-Host
        if ($LASTEXITCODE -ne 0) { Fail "补丁打不上：$($p.Name)" }
        Step "  $($p.Name)"
    }
    Set-Content -Path $stamp -Value $hash -Encoding ascii
} else { Step "  已打过，跳过" }

Step "3/5 配置（只要 3 个程序库用到的模块）"
$cfg = @("cmake", "-G", "Ninja", "-S", "`"$(Fwd $Occt)`"", "-B", "`"$(Fwd $Build)`"",
    "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_POLICY_VERSION_MINIMUM=3.5",
    "-DBUILD_MODULE_FoundationClasses=ON", "-DBUILD_MODULE_ModelingData=ON", "-DBUILD_MODULE_ModelingAlgorithms=ON",
    "-DBUILD_MODULE_Visualization=OFF", "-DBUILD_MODULE_ApplicationFramework=OFF", "-DBUILD_MODULE_DataExchange=OFF",
    "-DBUILD_MODULE_DETools=OFF", "-DBUILD_MODULE_Draw=OFF", "-DBUILD_DOC_Overview=OFF",
    "-DUSE_FREETYPE=OFF", "-DUSE_TK=OFF", "-DUSE_TBB=OFF", "-DUSE_VTK=OFF", "-DUSE_FREEIMAGE=OFF", "-DUSE_RAPIDJSON=OFF",
    "-DUSE_OPENGL=OFF", "-DUSE_GLES2=OFF", "-DUSE_D3D=OFF")
$rc = Invoke-Env $cfg (Join-Path $Logs "occt-configure.log")
if ($rc -ne 0) { Fail "配置失败（见 logs\occt-configure.log 与 .err）" }

Step "4/5 编译 TKMath、TKGeomAlgo、TKTopAlgo（约 1 小时，电脑不要睡眠）"
$rc = Invoke-Env @("cmake", "--build", "`"$(Fwd $Build)`"", "--target", "TKMath", "TKGeomAlgo", "TKTopAlgo") (Join-Path $Logs "occt-build.log")
if ($rc -ne 0) { Fail "编译失败（见 logs\occt-build.log 与 .err）" }

if ($OutDir) {
    New-Item -ItemType Directory -Force $OutDir | Out-Null
    foreach ($d in $Dlls) {
        $new = Get-ChildItem $Build -Recurse -Filter $d | Where-Object { $_.FullName -notmatch "\\CMakeFiles\\" } | Select-Object -First 1
        if (-not $new) { Fail "编译结果里找不到 $d" }
        Copy-Item $new.FullName (Join-Path $OutDir $d) -Force
        Step "  已放到 $OutDir：$d"
    }
    exit 0
}

Step "5/5 备份原来的程序库并替换"
New-Item -ItemType Directory -Force $Backup | Out-Null
foreach ($d in $Dlls) {
    $new = Get-ChildItem $Build -Recurse -Filter $d | Where-Object { $_.FullName -notmatch "\\CMakeFiles\\" } | Select-Object -First 1
    if (-not $new) { Fail "编译结果里找不到 $d" }
    $orig = Join-Path $Bin $d
    $b = Join-Path $Backup $d
    if (-not (Test-Path $b)) { Copy-Item $orig $b -Force; Step "  已备份 $d" }
    Copy-Item $new.FullName $orig -Force
    Step "  已替换 $d（$($new.FullName)）"
}
Step "完成。接着运行 tests-wqcad.ps1 验收；要换回原来的 OCCT，运行 build-occt.ps1 -Restore。"
