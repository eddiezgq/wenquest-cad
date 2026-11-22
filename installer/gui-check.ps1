# 装好以后真把界面打开（11-22：之前只在打包机上检查，打包机上路径正好存在，“找不到 Qt 界面插件”没查出来）。
# 静默安装 → 按启动器的办法设环境 → FreeCAD.exe 跑一个小宏（8 秒后写一个文件、关窗口）→ 等那个文件。
#   pwsh installer/gui-check.ps1 -Setup <安装包.exe> [-Dir <装到哪里>] [-Hide <打包机环境目录：检查时先改名藏起来>]
param(
  [Parameter(Mandatory = $true)][string]$Setup,
  [string]$Dir = "",
  [string]$Hide = "",
  [switch]$SoftGL          # GitHub 的 Windows 机器没有显卡驱动（只有 OpenGL 1.1）：检查时临时放 Mesa 软件渲染，查完删掉
)
$ErrorActionPreference = "Stop"
$sargs = @("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/LOG=$env:RUNNER_TEMP\gui-setup.log")
if ($Dir) { $sargs += "/DIR=$Dir" }
$p = Start-Process -FilePath $Setup -ArgumentList $sargs -Wait -PassThru
if ($p.ExitCode -ne 0) { Get-Content "$env:RUNNER_TEMP\gui-setup.log" -Tail 30; throw "安装失败 $($p.ExitCode)" }
if (-not $Dir) {
  $Dir = @("WenQuestCAD", "WenQuest FEA", "WenQuest MBD") | ForEach-Object { Join-Path $env:ProgramFiles $_ } | Where-Object { Test-Path $_ } | Select-Object -First 1
}
Write-Host "装在：$Dir"
$bin = Join-Path $Dir "bin"
if (Test-Path "$Dir\WenQuestCAD.cmd") {          # 问渠 CAD：照启动器设环境
  $cp = "$Dir\env"; $bin = "$cp\Library\bin"
  $env:CONDA_PREFIX = $cp; $env:PYTHONHOME = $cp; $env:PYTHONUTF8 = "1"
  $env:PATH = "$cp;$cp\Library\mingw-w64\bin;$cp\Library\usr\bin;$cp\Library\bin;$cp\Scripts;$cp\bin;$env:PATH"
  $line = Select-String -Path "$Dir\WenQuestCAD.cmd" -Pattern 'set "QT_PLUGIN_PATH=' -List
  if ($line) { $env:QT_PLUGIN_PATH = "$cp\Library\lib\qt6\plugins" }
}
Get-ChildItem $Dir -Recurse -Include qt.conf, qt6.conf, qt5.conf -ErrorAction SilentlyContinue | ForEach-Object {
  Write-Host "--- $($_.FullName)"; Get-Content $_.FullName | Select-Object -First 4 | ForEach-Object { Write-Host "  $_" }
}
$added = @()
if ($SoftGL) {
  $h = @{}; if ($env:GH_TOKEN) { $h.Authorization = "Bearer $env:GH_TOKEN" }
  $rel = Invoke-RestMethod -Headers $h https://api.github.com/repos/pal1000/mesa-dist-win/releases/latest
  $a = $rel.assets | Where-Object { $_.name -match '^mesa3d-.*-release-msvc\.7z$' } | Select-Object -First 1
  if (-not $a) { throw "没找到 Mesa 软件渲染包" }
  $z = "$env:RUNNER_TEMP\mesa.7z"; Invoke-WebRequest -UseBasicParsing $a.browser_download_url -OutFile $z
  & 7z x $z "-o$env:RUNNER_TEMP\mesa" -y | Out-Null
  foreach ($f in Get-ChildItem "$env:RUNNER_TEMP\mesa\x64" -Filter *.dll) {
    if (-not (Test-Path (Join-Path $bin $f.Name))) { Copy-Item $f.FullName $bin; $added += (Join-Path $bin $f.Name) }
  }
  $env:GALLIUM_DRIVER = "llvmpipe"
  Write-Host "临时放了 Mesa（$($a.name)）：$($added.Count) 个 dll"
}
$hidden = $null
if ($Hide -and (Test-Path $Hide)) { $hidden = "$Hide.hidden-for-gui-check"; Rename-Item $Hide $hidden; Write-Host "暂时藏起：$Hide" }
try {
  $flag = "$env:RUNNER_TEMP\gui_ok.txt"
  Remove-Item $flag -ErrorAction SilentlyContinue
  $macro = "$env:RUNNER_TEMP\guicheck.FCMacro"
  $py = @(
    "import FreeCAD, FreeCADGui",
    "from PySide import QtCore",
    "def done():",
    "    open(r'$flag', 'w').write('ok ' + '.'.join(FreeCAD.Version()[:3]))",
    "    FreeCADGui.getMainWindow().close()",
    "QtCore.QTimer.singleShot(8000, done)"
  )
  [IO.File]::WriteAllLines($macro, $py, (New-Object Text.UTF8Encoding $false))
  $fc = Start-Process -FilePath "$bin\FreeCAD.exe" -ArgumentList "`"$macro`"" -WorkingDirectory $bin -PassThru `
        -RedirectStandardOutput "$env:RUNNER_TEMP\fc_out.txt" -RedirectStandardError "$env:RUNNER_TEMP\fc_err.txt"
  $t = 0
  while (-not (Test-Path $flag) -and -not $fc.HasExited -and $t -lt 300) { Start-Sleep 2; $t += 2 }
  Start-Sleep 3
  if (-not $fc.HasExited) { Stop-Process -Id $fc.Id -Force -ErrorAction SilentlyContinue }
  Write-Host "--- stderr"; Get-Content "$env:RUNNER_TEMP\fc_err.txt" -Tail 30 -ErrorAction SilentlyContinue
  if (-not (Test-Path $flag)) { throw "界面没打开（$t 秒）" }
  Write-Host "界面打开了：$(Get-Content $flag)"
} finally {
  if ($hidden) { Rename-Item $hidden (Split-Path $Hide -Leaf); Write-Host "已放回：$Hide" }
  foreach ($f in $added) { Remove-Item $f -Force -ErrorAction SilentlyContinue }
}
