"""
loadkit —— 通用并发压测框架（与任何具体项目解耦，可整体复制到其他工程）

提供四类测量原语，全部只关心「发请求、量时间、数错误」：
  timed()   阶梯并发：total 个请求、最多 concurrency 个同时在飞（吞吐基线）
  spike()   尖峰冲击：total 个请求同一瞬间全部发出（验证过载保护）
  soak()    持续浸泡：目标 QPS 匀速打流，支持内存采样回调（验证稳定性/泄漏）
  report()  汇总打印

依赖：仅 httpx + 标准库。使用方式见同目录 load_test.py / load_test_pro.py。
"""

from __future__ import annotations

import asyncio
import random
import statistics
import string
import subprocess
import time
from dataclasses import dataclass, field


# ==================== 数据结构 ====================

@dataclass
class Result:
    name: str
    total: int = 0
    wall: float = 0.0            # 总耗时（秒）
    latencies: list = field(default_factory=list)   # 毫秒
    errors: list = field(default_factory=list)      # 真实失败
    rate_limited: int = 0        # 429 次数（安全特性，不算失败）
    extra: dict = field(default_factory=dict)       # 场景自定义指标

    @property
    def qps(self) -> float:
        return self.total / self.wall if self.wall else 0.0

    def percentile(self, q: float) -> float:
        if not self.latencies:
            return 0.0
        lat = sorted(self.latencies)
        return lat[min(int(len(lat) * q), len(lat) - 1)]

    @property
    def ok(self) -> bool:
        return not self.errors


# ==================== 工具 ====================

def rand_name(prefix="lu", n=8):
    return f"{prefix}_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def classify(status: int) -> str:
    """把 HTTP 状态码归类为 ok / limited / error。"""
    if status == 429:
        return "limited"
    if status >= 500:
        # 503 过载保护视为"被正确拒绝"，不算服务错误
        return "limited" if status == 503 else "error"
    if status >= 400:
        return "error"
    return "ok"


def docker_mem_mb(container: str) -> float | None:
    """读取 docker 容器内存（MB），非 docker 环境返回 None。"""
    try:
        out = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", "{{.MemUsage}}", container],
            capture_output=True, text=True, timeout=15,
        ).stdout.strip()
        return float(out.split("/")[0].strip().rstrip("MiB"))
    except Exception:
        return None


# ==================== 测量原语 ====================

async def timed(name, request, total, concurrency, on_result=None) -> Result:
    """阶梯并发压测。

    request: 异步函数 `async def request(i) -> int|tuple`，返回 HTTP 状态码；
             或返回 (status, extra_dict) 附加自定义指标。
    on_result: 可选回调 `def on_result(result: Result)`，用于场景收尾校验
               （如一致性检查），可向 result.errors 里追加业务错误。
    """
    sem = asyncio.Semaphore(concurrency)
    r = Result(name=name, total=total)

    async def one(i):
        async with sem:
            t0 = time.perf_counter()
            try:
                out = await request(i)
                status = out[0] if isinstance(out, tuple) else out
                if isinstance(out, tuple):
                    r.extra.update(out[1])
                kind = classify(status)
                if kind == "error":
                    r.errors.append(f"HTTP {status}")
                elif kind == "limited":
                    r.rate_limited += 1
            except Exception as e:
                r.errors.append(type(e).__name__ + ": " + str(e)[:80])
            r.latencies.append((time.perf_counter() - t0) * 1000)

    t0 = time.perf_counter()
    await asyncio.gather(*(one(i) for i in range(total)))
    r.wall = time.perf_counter() - t0
    if on_result:
        on_result(r)
    print_result(r)
    return r


async def spike(name, request, total) -> Result:
    """尖峰冲击：全部请求同一瞬间发出（无信号量），统计状态码分布。"""
    r = Result(name=name, total=total)
    dist: dict[int, int] = {}

    async def one(i):
        t0 = time.perf_counter()
        try:
            status = await request(i)
            dist[status] = dist.get(status, 0) + 1
            kind = classify(status)
            if kind == "error":
                r.errors.append(f"HTTP {status}")
            elif kind == "limited":
                r.rate_limited += 1
        except Exception as e:
            r.errors.append(type(e).__name__ + ": " + str(e)[:80])
        r.latencies.append((time.perf_counter() - t0) * 1000)

    t0 = time.perf_counter()
    await asyncio.gather(*(one(i) for i in range(total)))
    r.wall = time.perf_counter() - t0
    r.extra["status_dist"] = dist
    print_result(r)
    return r


async def soak(name, request, seconds, qps, mem_container=None, batch=2) -> Result:
    """持续浸泡：以目标 QPS 匀速打流（读写混合由 request 自己决定）。

    request: `async def request(i) -> int`，返回状态码。
    mem_container: 可选 docker 容器名，自动采样内存用于泄漏判断。
    """
    r = Result(name=name)
    interval = 1.0 / qps
    mem_samples = []
    errors_5xx = 0

    async def worker(i):
        nonlocal errors_5xx
        try:
            status = await request(i)
            r.total += 1
            if status >= 500 and status != 503:
                errors_5xx += 1
                r.errors.append(f"HTTP {status}")
        except Exception as e:
            r.total += 1
            r.errors.append(type(e).__name__ + ": " + str(e)[:80])

    start = time.perf_counter()
    next_beat = start
    i = 0
    while time.perf_counter() - start < seconds:
        await asyncio.gather(*(worker(i + k) for k in range(batch)))
        i += batch
        if mem_container and i % 30 == 0:
            m = docker_mem_mb(mem_container)
            if m:
                mem_samples.append(m)
        elapsed = time.perf_counter() - next_beat
        if elapsed < interval * batch:
            await asyncio.sleep(interval * batch - elapsed)
        next_beat += interval * batch

    r.wall = time.perf_counter() - start
    r.extra["errors_5xx"] = errors_5xx
    if len(mem_samples) >= 2:
        growth = round(mem_samples[-1] - mem_samples[0], 1)
        r.extra["mem_first_mb"] = mem_samples[0]
        r.extra["mem_last_mb"] = mem_samples[-1]
        r.extra["mem_growth_mb"] = growth
        r.extra["leak"] = growth >= 100  # 增长超过 100MB 视为疑似泄漏
    print_result(r)
    return r


# ==================== 输出 ====================

def print_result(r: Result) -> None:
    print(f"\n[{r.name}]")
    if r.latencies:
        lat = sorted(r.latencies)
        print(f"  请求={r.total}  耗时={r.wall:.2f}s  QPS={r.qps:.1f}")
        print(f"  P50={statistics.median(lat):.0f}ms  "
              f"P95={r.percentile(0.95):.0f}ms  P99={r.percentile(0.99):.0f}ms  "
              f"max={lat[-1]:.0f}ms")
    if r.extra.get("status_dist"):
        print(f"  状态码分布={r.extra['status_dist']}")
    if "mem_growth_mb" in r.extra:
        print(f"  内存: {r.extra['mem_first_mb']}MB → {r.extra['mem_last_mb']}MB "
              f"(增长 {r.extra['mem_growth_mb']}MB)")
    msg = f"  错误={len(r.errors)}"
    if r.errors:
        msg += f"  示例: {r.errors[0]}"
    if r.rate_limited:
        msg += f"  限流/保护触发={r.rate_limited}（安全特性，不计失败）"
    print(msg)


def report(results: list[Result]) -> bool:
    """打印汇总表，返回总体是否通过（有真实错误即失败；限流不算）。"""
    print("\n========== 压测汇总 ==========")
    all_ok = True
    for r in results:
        ok = r.ok and not r.extra.get("leak")
        all_ok &= ok
        tag = "PASS" if ok else "FAIL"
        extra = ""
        if "mem_growth_mb" in r.extra:
            extra = f" 内存增长={r.extra['mem_growth_mb']}MB"
        print(f"  {tag}  {r.name}: QPS={r.qps:.1f} "
              f"P95={r.percentile(0.95):.0f}ms 错误={len(r.errors)}{extra}")
    print("\n总评:", "全部通过 ✅" if all_ok else "存在问题，需修复 ❌")
    return all_ok
