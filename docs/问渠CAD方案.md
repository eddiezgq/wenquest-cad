# 问渠 CAD 方案 v0.1（2026-11-16，Eddie 已确认；同日按构建方式细化，见第三、四节）

## 一、定位

- **是什么**：基于 FreeCAD 的自用发行版，名称“问渠 CAD（基于 FreeCAD）”。不另写几何内核。
- **给谁用**：先给 Eddie 自己和公司内部用。不对外发放，因此没有公开源码的义务，本书的补丁也不因此公开。
- **为什么比官方 FreeCAD 好**：带上本书验证过的修正（27 个 FreeCAD 补丁），以本书的测试做回归；以后加 AI 工作台。
- **许可**：FreeCAD、OCCT 都是 LGPL。以后若发给学员或客户，须随附改过的源码并允许替换库——到那一步再单独定。名称里不用“FreeCAD”字样作为产品名（FreeCAD 的商标规定），只写“基于 FreeCAD”。

## 二、分三个版本

| 版本 | 内容 | 验收 |
| --- | --- | --- |
| **0.1** | FreeCAD 1.1.4 + 27 个 FreeCAD 补丁（`patches/series/freecad-1.1.4/`）+ 本书测试；装在 Eddie 的 Windows 电脑上，桌面快捷方式“问渠 CAD” | 见第四节 |
| 0.2 | AI 工作台：freecad-ai-parts 的零件选型与确定性校验接进来；AI 只起草，人确认；国内用 DeepSeek，Claude 只在美国用 | 另写细则 |
| 0.3 | 结合业务：夹具设计（配《夹具设计与制造》）、问渠平台课程与虚拟实验、机器人关节选型 | 另写细则 |

0.1 **不含** 6 个 OCCT 补丁：FreeCAD 1.1.4 的构建配置用的是 OCCT 7.8 系列，本书的 OCCT 补丁针对 8.0.1，移植放到 0.2 再做。

## 三、怎么构建（在 Eddie 的 Windows 电脑上，C 盘）

本会话不能直接在 Windows 上编译（能用的 shell 是一台 Linux 虚拟机），所以由 Eddie 运行脚本，我读日志。

1. **构建包**放在 `C:\Users\<你>\Projects\wenquest-cad`（本会话可读写，便于我看日志）：`build-wqcad.ps1`、`patches\`（27 个补丁 + `series.txt`）、`tests\`（本书 16 组 FreeCAD 测试）、`run_book_tests.py`、`branding.xml`、`logs\`。构建包的源文件就是本仓库根目录。
2. **一次性装三样工具**：Git for Windows；Visual Studio 2022 生成工具（“使用 C++ 的桌面开发”）；pixi。
3. **脚本做的事**：
   1. 检查三样工具；
   2. 在 `C:\wqcad\FreeCAD` 取 FreeCAD 1.1.4 源码（含子模块，关闭换行转换）；
   3. 回到 1.1.4 原样，按 `series.txt` 逐个打补丁，打不上立即停；
   4. `pixi run configure-release` → `build-release` → `install-release`（FreeCAD 官方的构建任务；并行数按内存定，每 2 GB 一个）；
   5. 把 `branding.xml` 放进程序目录：窗口标题显示“问渠 CAD 0.1（基于 FreeCAD 1.1.4）”；
   6. 跑测试（第四节），结果写进 `logs\`；
   7. 桌面建快捷方式“问渠 CAD”。
   全过程写日志 `logs\build-日期时间.log`。脚本可重复运行：已下载的源码与依赖不重下。
4. **安装位置**：程序就在 `C:\wqcad\FreeCAD\.pixi\envs\default\Library\bin\FreeCAD.exe`（pixi 环境本身就是运行环境），不另做安装包。自用够了；发给别人用的安装包放到以后。
5. **磁盘**：C 盘预留 40 GB。
6. **Windows 智能应用控制**（11-17 首次运行发现）：它会拦下 pixi 装的 cmake 等未签名程序，自己编的问渠 CAD 也会被拦。处理：先查状态；若为“开”，关掉它（Windows 安全中心 → 应用和浏览器控制 → 智能应用控制 → 关）。关掉后不能再打开（除非重装 Windows），杀毒（Defender）不受影响。若是公司管控的电脑，不改策略，改在 WSL（Windows 自带的 Linux）里构建运行。
8. **启动方式**（11-17 发现）：FreeCAD.exe 要在 pixi 环境里启动（Python、Qt 的 DLL 在环境的其他目录），直接双击会静默退出。所以桌面快捷方式指向 `C:\wqcad\问渠CAD.cmd`，由它经 `pixi run` 启动；测试也经 `pixi run` 运行（`tests-wqcad.ps1`）。
9. **编译时间**：第一次编译约 8 小时（8 线程、31 GB 内存；比原估计长得多，主要是 Defender 扫描新文件，且默认连 FreeCAD 自带的 C++ 单元测试一起编）。补丁不变时重跑脚本跳过打补丁，只增量编译。
7. **pixi 设置**：允许 conda 包运行安装后脚本（`run-post-link-scripts`），Qt、PySide 需要；脚本第一次会重装一遍环境。

## 四、0.1 的验收

1. 27 个补丁全部打上，编译、安装无错误。
2. FreeCAD 自带测试：TestPartApp（其中已含本书登记进去的测试）、TestSketcherApp、TestPartDesignApp、MeshTestsApp 全部通过。
3. 本书的 16 组 FreeCAD 测试：除第 6 章那组（问题在 OCCT）外全部通过。
4. 打开图形界面，手工检查两处只在界面里的修正：第 5 章“展开面”命令、第 26 章“检查几何”对话框（我给检查步骤）。
5. 窗口标题显示“问渠 CAD 0.1（基于 FreeCAD 1.1.4）”。

验收结果写回本文件。

## 五、仓库

- 本仓库 `eddiezgq/wenquest-cad`（私有，11-16 建）：构建包（根目录）与本方案。
- 补丁的“源头”是本书仓库 `cad-kernel-ai-textbook`（`patches/series/freecad-1.1.4/`）；补丁有改动时同步到本仓库 `patches/`。

## 六、需要 Eddie 做的

1. ~~确认本方案~~（11-16 已确认；只有一个 C 盘，空间足够；书的仓库已改私有）。
2. 允许本会话读写 `Projects` 文件夹（放构建包、看日志）。
3. 按 `使用说明.md` 装三样工具，运行一次脚本。
