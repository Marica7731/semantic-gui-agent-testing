# 性能评测

## 指标定义

| 指标 | 含义 | 采集方式 |
| --- | --- | --- |
| 定位耗时 (p50/p95) | 从发起匹配到选出目标节点的毫秒数 | `ActionResult.elapsed_ms` |
| 操作成功率 | 批量步骤中 `success=true` 的比例 | `batch.summarize` |
| 模型调用次数 | 定位消耗的模型调用数（本框架恒为 0） | 设计保证，非测量值 |
| 缓存命中率 | UI 树根哈希未变化的比例 | `executor.cache.stats` |
| 整任务耗时 | 场景端到端毫秒数 | CSV 按场景聚合 |

## 当前状态

**无实机数据。** 仓库不预填任何编造数字。

`benchmarks/run_benchmarks.py` 默认对内存 stub 执行，仅验证链路与输出格式；
真实结论必须来自实机运行：

```bash
# stub 冒烟（任何机器可跑）
python benchmarks/run_benchmarks.py

# Android 实机
python benchmarks/run_benchmarks.py --executor android --serial <serial> --repeat 20

# Windows 实机
python benchmarks/run_benchmarks.py --executor windows --window-title "Notepad" --repeat 20
```

## 结果记录模板

实机跑完后，把 `benchmarks/results/*.csv` 对应的 Markdown 汇总贴到下面，
并注明：设备型号 / 系统版本 / 被测应用 / 日期。

| 场景 | 设备 | p50 (ms) | p95 (ms) | 成功率 | 缓存命中率 | 日期 |
| --- | --- | --- | --- | --- | --- | --- |
| （待实机填充） | | | | | | |

对比基线（建议同环境各测一组）：

1. 本框架语义定位；
2. 纯视觉定位（截图 + VLM 每步定位）——预期差距即本框架的核心收益；
3. 固定 sleep 脚本——预期在等待类场景上差距最大。
