# AGENTS.md — AI 编程 Agent 实施任务书

本仓库是 LLM 驱动 GUI 测试的通用框架（Android + Windows + MCP 接口）。
任何 AI 编程 Agent 在本仓库工作时，先读完本文，再动手。

## 1. 项目定位

解决的问题：GUI Agent 直接用「截图 + 坐标 + VLM」跑真实界面时，脚本脆、成本高、结果不可复现。

本框架的路线：**控件树语义定位为主（零模型调用），视觉 OCR 兜底为辅**，
通过 MCP 把执行器暴露给任意 Agent。技术选型的完整依据见
`docs/selection-rationale.md`，架构见 `docs/architecture.md`。

## 2. 当前状态（接手前必读）

| 项 | 状态 |
| --- | --- |
| 核心层（模型/匹配/增量/等待/断言/批量/会话/注册表） | 已实现，16 项单元测试通过（stub 层面） |
| Android 解析层（uiautomator XML → UINode） | 已实现并有单元测试；**未连真机验证** |
| Windows 执行器（pywinauto） | 已实现；**未连真机验证** |
| MCP Server（stdio JSON-RPC，initialize/tools.list/tools.call） | 已实现并有单元测试；**未与真实 MCP 客户端联调** |
| 性能数据 | **无**。`docs/benchmarks.md` 只有指标定义和模板，不许预填数字 |
| CI | GitHub Actions 矩阵（Ubuntu/Windows × 3.10/3.12），只跑无设备单测 |

即：**本仓库当前是"链路完整、未经实机验证"的状态。** 任何"已完成"的表述
只允许指向已验证的范围，实机相关结论必须有证据后才能写。

## 3. 实施任务（按优先级）

### P0 实机验证（先做，别跳过）
1. Windows：`pip install -e ".[windows]"`，对记事本/计算器执行
   `tap(SemanticTarget(...))` → `assert_state(...)`，记录真实控件树形态与坑
   （UWP/Win32/WebView 差异）。
2. Android：`adb devices` → `python -m uiautomator2 init` → 对设置页执行定位
   与点击，确认 `dump_hierarchy` 在目标 App 上不被屏蔽。
3. MCP 联调：任一真实 MCP 客户端连 `python -m sgat.mcp.server --executor ...`，
   走通 initialize → tools/list → tools/call 全链路。
4. 把验证结果（含失败样本）写回 `docs/`，并在本文第 2 节更新状态表。

### P1 性能基线
按 `docs/benchmarks.md` 的指标定义与对比基线（语义定位 vs 纯视觉 vs 固定
sleep）实测三组数据，填入结果模板，注明设备与日期。

### P2 视觉兜底落地
实现一个真实 `OcrProvider`（如 PaddleOCR / Windows OCR），接入
`VisualFallback`，验证「控件树找不到 → OCR 找到」的完整链路。注意
`screenshot()` 目前在基类是显式 NotImplementedError，平台执行器需各自实现。

### P3 增强项（实机验证后再做）
Windows 截图（`screenshot()`）、批量 MCP 工具、会话级 MCP 工具（多 Agent
并行驱动）、元素等待事件的日志面。

## 4. 铁律

- **禁止编造 API**。不确定的接口参数先实测或查文档，抓不到就明说没有依据；
  HTTP/调用成功不等于参数正确，必须比对返回内容。
- **禁止无证据声称完成**。实机没跑过就说"已验证"、benchmark 没跑就填数字，
  都属于事故。
- **错误要可诊断**。禁止用静默兜底掩盖失败（参考 `NullOcrProvider` 的做法：
  显式报错而不是返回空）。
- **保持分层**。平台相关代码只允许出现在 `sgat.android` / `sgat.windows`，
  核心层保持无第三方依赖、可无设备测试。
- **测试边界**。单元测试不许依赖设备、网络和真实 sleep（用注入时钟）；设备
  相关验证写进文档记录，不塞进 CI。
- **仓库卫生**。不提交 secret、数据库、日志、构建产物；`CODEX_GOAL.md` 类
  本地规划文件不入库。

## 5. 验收清单（对任何一轮改动）

- [ ] `pytest -q` 全绿
- [ ] 新代码有对应单元测试；解析/匹配类逻辑保持纯函数
- [ ] `git status` 干净，只提交本轮相关文件
- [ ] 若声称"实机可用"：附设备输出或截图证据
- [ ] 若修改了对外行为：同步更新 README / docs / AGENTS.md 状态表
