# 问渠 CAD

基于 FreeCAD 的自用发行版。方案：`docs/问渠CAD方案.md`；在 Windows 上构建：`使用说明.md`。

- `build-wqcad.ps1`：取 FreeCAD 1.1.4 → 打 `patches/` 里的 27 个补丁（来自《FreeCAD 内核解密、验证与修正》）→ pixi 编译安装 → 测试 → 桌面快捷方式。
- `tests/`：本书的 FreeCAD 测试；`run_book_tests.py`：在 FreeCADCmd 里逐个运行。
- `branding.xml`：窗口标题。
