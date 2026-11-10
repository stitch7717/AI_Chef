# loadkit —— 通用并发压测框架

与具体业务完全解耦，**复制 `loadkit.py` 单文件到任何工程即可用**（仅依赖 httpx）。

## 四个测量原语

| 原语 | 用途 | 验证什么 |
|---|---|---|
| `timed()` | 阶梯并发（总量+并发上限） | 吞吐基线：QPS / P95 / 错误率 |
| `spike()` | 瞬时冲击（全部同时发出） | 过载保护：是否 5xx 雪崩 |
| `soak()` | 持续匀速打流 + 内存采样 | 稳定性：5xx、内存泄漏 |
| `report()` | 汇总判定 | 自动区分「真实失败」与「限流/保护触发(429/503)」 |

## 在新项目中使用（三步）

1. 复制 `loadkit.py` 到你的 `scripts/` 目录
2. 写场景文件（参考 `load_test.py`），每个场景就是一个小异步函数：

```python
from loadkit import timed, report

async def my_request(i):
    r = await client.get("/your/api")          # 你的接口
    return r.status_code                        # 框架自动分类 2xx/429/5xx

results = [await timed("我的场景", my_request, total=200, concurrency=50)]
report(results)
```

3. 业务正确性校验用 `on_result` 回调或手动构造 `Result`（参考 `load_test_pro.py` 的场景 H：
   压完之后**查库验证数据符合业务语义**，这是业务级压测和普通压测的本质区别）

## 分类规则

- 2xx/3xx → 成功
- **429 / 503 → 「保护触发」**：限流、过载保护生效是安全特性，汇总时单独列出、不计失败
- 其他 4xx/5xx → 真实失败
- soak 场景内存增长 ≥100MB → 判定疑似泄漏

## 本项目脚本分工

- `load_test.py` —— 吞吐基线（入口/DB读/DB写/多用户流程/真实LLM并发）
- `load_test_pro.py` —— 业务级硬指标（尖峰/SSE流式/并发写一致性/浸泡）
