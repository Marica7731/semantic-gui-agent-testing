# 架构设计

## 分层

```
Agent (LLM / MCP client)
        │  JSON-RPC over stdio (MCP)
        ▼
sgat.mcp.server          工具面：find / tap / input_text / back / wait / assert
        ▼
sgat.session             多 Agent 会话隔离（每会话独立 executor 实例与缓存）
        ▼
sgat.executor.GUIExecutor  平台无关管线：locate → act → wait → assert
        ├── sgat.semantic.matcher      语义匹配（纯 Python，0 次模型调用）
        ├── sgat.semantic.incremental  Merkle 哈希增量 UI 更新
        ├── sgat.visual.fallback       视觉兜底（可插拔 OCR，仅最后手段）
        ├── sgat.waiting / assertions / batch  状态等待 / 自动断言 / 批量隔离
        ▼
平台执行器
        ├── sgat.android.executor   adb + uiautomator2（懒加载）
        ├── sgat.windows.executor   UI Automation + pywinauto（懒加载）
        └── sgat.stub               内存执行器（无设备冒烟/测试/压测用）
```

## 语义定位管线

1. **dump**：执行器从设备拉取控件树（Android `dump_hierarchy()` XML / Windows
   UIA ElementInfo 递归），转成统一的 `UINode` 树。
2. **match**：`SemanticMatcher` 对每个节点打分，字段优先级为
   resource_id（精确 1.0 / 包含 0.8）＞ text（精确 1.0 / 子串 0.75 / 模糊）＞
   content_desc ＞ description（对节点全部文本面做比率 + 词重叠）；
   `class_name` 作为加权修正。低于 0.5 的候选被丢弃。
3. **act**：取最高分节点中心坐标执行动作；前两名分差 < 0.05 时在结果中标记
   `ambiguous`，供上层 Agent 决策（不静默二选一）。
4. **wait + assert**：动作后轮询目标出现/断言状态，全部本地判定，不消耗模型。

关键设计：**定位是确定性的**。同一个界面、同一个目标，结果可复现；Agent 只需
输出语义目标（"找到写着 OK 的按钮"），定位开销与模型无关。

## UI 增量更新

`UITreeCache` 为每个节点计算覆盖自身与全部子孙的内容哈希（`node_id` 不参与，
身份由内容决定）：

- 根哈希未变 → 缓存命中，直接复用（Agent 可跳过重新定位与重新截图）；
- 根哈希变化 → 记录本次 dump 与旧索引复用的子树数量，用于评估界面变化幅度。

这样 agent loop 里"界面没变就别折腾"成为一次哈希比较的成本。

## 视觉兜底

语义匹配失败且配置了 OCR provider 时，才走 `VisualFallback.resolve()`：
截图 → OCR 出文本框列表 → 找包含目标文本的最紧框。未配置 provider 时
`NullOcrProvider` 显式报错——兜底缺失必须可诊断，不允许静默吞掉。

## 多 Agent 隔离

`SessionManager` 为每个 Agent 会话创建独立 `AgentSession`：executor 实例、
UI 缓存、会话标签互不共享。两个 Agent 驱动同一台设备时，一处点击不会污染
另一处的状态视图。

## MCP 工具面

stdio 上跑 newline-delimited JSON-RPC 2.0，实现 `initialize` / `tools/list` /
`tools/call` 最小子集，不依赖第三方 SDK。断言失败与等待超时按 MCP 约定返回
`isError: true` 的工具结果，协议错误与工具错误分离，服务器循环永不因单个
工具调用崩溃。
