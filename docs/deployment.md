# 部署说明

## Windows

1. Python 3.10+（建议用 pwsh 7）：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[windows,dev]"
pytest -q
```

2. 冒烟（无设备依赖）：

```powershell
python -m sgat.mcp.server --executor stub
# 另开一个终端手动发一条 initialize 的 JSON-RPC 行即可看到响应
```

3. 实机驱动（以记事本为例）：

```powershell
python -m sgat.mcp.server --executor windows --window-title "Notepad"
```

说明：pywinauto 使用 `uia` backend（UI Automation），元素带 AutomationId /
ControlType，这是语义定位在 Windows 上可用的前提。个别老应用只支持 `win32`
backend，定位能力会退化为窗口/控件文本。

## Android

1. 安装 platform-tools（adb）并确认设备：

```bash
adb devices        # 记下 serial
```

2. 安装并初始化：

```bash
pip install -e ".[android,dev]"
python -m uiautomator2 init    # 首次需要，向设备部署 atx-agent
```

3. 运行：

```bash
python -m sgat.mcp.server --executor android --serial <serial>
```

说明：`uiautomator2` 通过设备端 atx-agent 抓取控件树（等价 `uiautomator dump`），
部分银行/金融类 App 屏蔽 accessibility dump，属于已知边界，视觉兜底是唯一路径。

## WSL2

WSL2 默认无法直接访问 USB 设备，两条路线：

- **推荐：执行器放 Windows 侧，MCP 走 stdio**。MCP server 进程由客户端在
  Windows 上启动（`python -m sgat.mcp.server ...`），WSL2 里的 Agent 只消费
  MCP 工具结果，不接触设备层。零 USB 配置。
- **usbipd-win**：把 adb 设备 attach 进 WSL2（`usbipd bind/attach`），在
  WSL2 内跑完整链路。适合强依赖 Linux 工具链的场景，但多一层驱动转发，
  设备热插拔后需要重新 attach。

## MCP 客户端接入示例（Claude Desktop 形式）

```json
{
  "mcpServers": {
    "semantic-gui": {
      "command": "python",
      "args": ["-m", "sgat.mcp.server", "--executor", "windows", "--window-title", "Notepad"],
      "env": {}
    }
  }
}
```

## 持续集成

GitHub Actions（`.github/workflows/ci.yml`）：Ubuntu + Windows × Python
3.10/3.12 矩阵，只装 `.[dev]` 跑单元测试（不依赖任何设备）。设备相关测试
留给实机环境，不要塞进 CI 矩阵。
