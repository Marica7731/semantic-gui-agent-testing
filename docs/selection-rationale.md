# 选型依据

## 定位策略：语义优先，视觉兜底

| 方案 | 结论 | 理由 |
| --- | --- | --- |
| 坐标硬编码 | 否决 | 分辨率/DPI/语言/版本任一变化即碎；无法审计"点了什么" |
| 纯视觉（截图 + VLM 每步定位） | 否决为主定位 | 每步一次模型调用，延迟与成本高；输出坐标有抖动，不可复现 |
| 控件树语义定位 | **采用（主）** | 可访问性树稳定、确定性、零模型调用；resource-id/content-desc/AutomationId 是应用自己的语义 |
| 视觉 OCR 兜底 | **采用（最后手段）** | 游戏画布/自绘控件无控件树时唯一路径；必须显式配置，失败要可诊断 |

## Android 执行器：uiautomator2

对比 Appium、裸 adb：

- **Appium**：能力全但重——WebDriver 协议、独立 server、多一整层抽象，调试
  链路长。适合大规模跨平台设备农场，不适合轻量 agent 执行器。
- **裸 adb + uiautomator dump**：每次 dump 拉全量 XML、走 shell，慢且超时多。
- **uiautomator2**（采用）：纯 Python 客户端 + 设备端 atx-agent，HTTP 直连，
  API 直接（`dump_hierarchy / click / send_keys / press`），部署一条
  `python -m uiautomator2 init`。与本项目"轻执行器 + 语义层在上"的分层最匹配。

## Windows 执行器：pywinauto（uia backend）

- **WinAppDriver**：微软已停止积极维护（仓库归档），新项目不应押注。
- **直接写 UIA COM 互操作**：无额外依赖但样板代码量大，维护成本转嫁给自己。
- **pywinauto**（采用）：维护活跃、纯 Python、`backend="uia"` 暴露
  AutomationId/ControlType，`Desktop.window(title_re=...)` 定窗口，
  `mouse.click` / `keyboard.send_keys` 覆盖输入原语。

## Agent 接口：MCP（stdio）

- **自管 REST 服务**：要自己处理端口、鉴权、生命周期，还引入网络暴露面。
- **MCP**（采用）：面向工具调用的开放协议，主流 agent 客户端原生支持；
  stdio 传输零端口、零网络配置，进程生命周期跟随客户端。本项目实现了
  `initialize / tools/list / tools/call` 最小子集，不依赖 SDK，避免协议库
  版本漂移带来的维护负担。

## 状态同步：Merkle 哈希增量更新 + 轮询等待

- 每步全量重新解析控件树简单但浪费；**内容哈希**让"界面没变"变成一次比较，
  并能量化"变了多少"（复用子树计数）。
- 固定 sleep 是竞态来源；**谓词轮询 + 可注入时钟**既消除竞态又让测试零等待。

## 测试与 CI：pytest + GitHub Actions 矩阵

- 设备相关代码用**纯函数解析层**（XML → UINode）隔离，单测无设备可跑；
- CI 只装 `.[dev]`，Ubuntu + Windows × 3.10/3.12，保证核心层跨平台；
- 平台 extras 用 environment marker 隔离（pywinauto 仅 Windows 安装），
  避免 CI 在 Linux 上装不上原生依赖。
