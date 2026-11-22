# 环境搬家：pixi 环境里有的文件写死了打包机上的绝对路径（D:/wqcad/FreeCAD/.pixi/envs/default）。
# 11-22：qt6.conf 里的 Plugins 指向打包机，装到用户电脑上界面插件找不到，启动报
# “no Qt platform plugin could be initialized”。这里把 qt6.conf 改成相对路径（Qt 按程序所在目录解析），
# 再列出其余还含打包机路径的文本文件（只报告，供下一步判断）。
#   pwsh installer/relocate.ps1 -Env <环境目录> [-Old <打包机上的环境路径>]
param(
  [Parameter(Mandatory = $true)][string]$Env,
  [string]$Old = "D:/wqcad/FreeCAD/.pixi/envs/default"
)
$ErrorActionPreference = "Stop"
$keys = [ordered]@{
  Documentation = "Library/share/doc/qt6"; Headers = "Library/include/qt6"; Libraries = "Library/lib"
  LibraryExecutables = "Library/lib/qt6"; Binaries = "Library/lib/qt6/bin"; Plugins = "Library/lib/qt6/plugins"
  QmlImports = "Library/lib/qt6/qml"; ArchData = "Library/lib/qt6"; Data = "Library/share/qt6"
  Translations = "Library/share/qt6/translations"; Examples = "Library/share/doc/qt6/examples"; Tests = "Library/tests"
}
# qt6.conf 所在目录 → 到环境根目录的相对路径（Prefix）
$confs = @{ "Library\bin\qt6.conf" = "../.."; "qt6.conf" = "." }
foreach ($rel in $confs.Keys) {
  $f = Join-Path $Env $rel
  if (-not (Test-Path $f)) { Write-Host "没有 $rel（跳过）"; continue }
  $lines = @("[Paths]", "Prefix = $($confs[$rel])") + ($keys.Keys | ForEach-Object { "$_ = $($keys[$_])" })
  [IO.File]::WriteAllLines($f, $lines, (New-Object Text.UTF8Encoding $false))
  Write-Host "改好 $rel"
  Get-Content $f | ForEach-Object { Write-Host "  $_" }
}
if (-not (Test-Path (Join-Path $Env "Library\lib\qt6\plugins\platforms\qwindows.dll"))) { throw "环境里没有 Library\lib\qt6\plugins\platforms\qwindows.dll" }
# 其余还含打包机路径的文件（报告）
$pat = [regex]::Escape($Old) + "|" + [regex]::Escape($Old.Replace("/", "\"))
$hits = Get-ChildItem -Recurse -File $Env -Include *.conf, *.cfg, *.ini, *.pth, *.json, *.bat, *.cmd, *.txt, *.py, *.xml -ErrorAction SilentlyContinue |
  Where-Object { $_.Length -lt 2MB } | Select-String -Pattern $pat -List | Select-Object -ExpandProperty Path
Write-Host "还含打包机路径的文本文件：$(@($hits).Count) 个"
$hits | Select-Object -First 40 | ForEach-Object { Write-Host "  $_" }
