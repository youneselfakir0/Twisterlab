#!/usr/bin/env python3
"""
TwisterLab MCP Load Test Script
Tests all 29 MCP tools with concurrent requests and measures performance.
"""

import asyncio
import aiohttp
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List
from collections import defaultdict
import statistics

MCP_URL = "http://192.168.0.30:30080/mcp"

# All 29 MCP tools with their test arguments
MCP_TOOLS = {
    # Monitoring (7)
    "monitoring_health_check": {},
    "monitoring_get_system_metrics": {},
    "monitoring_list_containers": {},
    "monitoring_get_container_logs": {"container_id": "twisterlab-api"},
    "monitoring_get_cache_stats": {},
    "monitoring_get_llm_status": {},
    "monitoring_list_models": {},
    
    # Maestro (5)
    "maestro_chat": {"message": "Hello, status check"},
    "maestro_generate": {"prompt": "Test generation"},
    "maestro_orchestrate": {"command": "check health"},
    "maestro_list_agents": {},
    "maestro_analyze": {"content": "sample data for analysis"},
    
    # Database (4)
    "database_execute_query": {"sql": "SELECT 1"},
    "database_list_tables": {},
    "database_describe_table": {"table_name": "tickets"},
    "database_db_health": {},
    
    # Cache (5)
    "cache_cache_get": {"key": "test_key"},
    "cache_cache_set": {"key": "load_test", "value": "test_value", "ttl": 60},
    "cache_cache_delete": {"key": "load_test"},
    "cache_cache_keys": {"pattern": "*"},
    "cache_cache_stats": {},
    
    # Agents (5)
    "sentiment-analyzer_analyze_sentiment": {"text": "This service is excellent!"},
    "real-classifier_classify_ticket": {"ticket_text": "Server is down and users cannot login"},
    "real-resolver_resolve_ticket": {"ticket_id": "TEST-001", "resolution_note": "Load test"},
    "real-backup_create_backup": {"service_name": "postgres", "location": "local"},
    "real-desktop-commander_execute_command": {"command": "echo test", "device_id": "local"},
    
    # Code & Browser (3)
    "code-review_analyze_code": {"code": "def hello(): return 'world'", "language": "python"},
    "code-review_security_scan": {"code": "password = 'secret123'"},
    "browser_browse": {"url": "http://example.com"},
}


@dataclass
class ToolResult:
    """Result of a single tool call."""
    tool_name: str
    success: bool
    latency_ms: float
    error: str = ""


@dataclass
class LoadTestResults:
    """Aggregated load test results."""
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    total_time_sec: float = 0
    results_by_tool: Dict[str, List[ToolResult]] = field(default_factory=lambda: defaultdict(list))
    
    def add_result(self, result: ToolResult):
        self.total_requests += 1
        if result.success:
            self.successful += 1
        else:
            self.failed += 1
        self.results_by_tool[result.tool_name].append(result)
    
    def get_stats(self) -> Dict[str, Any]:
        """Calculate statistics for all tools."""
        stats = {
            "summary": {
                "total_requests": self.total_requests,
                "successful": self.successful,
                "failed": self.failed,
                "success_rate": f"{(self.successful / self.total_requests * 100):.1f}%" if self.total_requests > 0 else "0%",
                "total_time_sec": round(self.total_time_sec, 2),
                "requests_per_second": round(self.total_requests / self.total_time_sec, 2) if self.total_time_sec > 0 else 0,
            },
            "by_tool": {}
        }
        
        for tool_name, results in self.results_by_tool.items():
            latencies = [r.latency_ms for r in results if r.success]
            successes = sum(1 for r in results if r.success)
            failures = sum(1 for r in results if not r.success)
            
            tool_stats = {
                "calls": len(results),
                "success": successes,
                "failed": failures,
                "success_rate": f"{(successes / len(results) * 100):.1f}%" if results else "0%",
            }
            
            if latencies:
                tool_stats.update({
                    "avg_ms": round(statistics.mean(latencies), 2),
                    "min_ms": round(min(latencies), 2),
                    "max_ms": round(max(latencies), 2),
                    "p50_ms": round(statistics.median(latencies), 2),
                    "p95_ms": round(sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else latencies[0], 2),
                })
            
            if failures > 0:
                errors = [r.error for r in results if not r.success]
                tool_stats["errors"] = list(set(errors))[:3]  # Unique errors, max 3
            
            stats["by_tool"][tool_name] = tool_stats
        
        return stats


async def call_mcp_tool(session: aiohttp.ClientSession, tool_name: str, arguments: Dict) -> ToolResult:
    """Call a single MCP tool and measure latency."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    # LLM tools need longer timeout (60s), others use 30s
    timeout_seconds = 60 if tool_name.startswith("maestro_") else 30
    
    start = time.perf_counter()
    try:
        async with session.post(MCP_URL, json=payload, timeout=aiohttp.ClientTimeout(total=timeout_seconds)) as response:
            latency_ms = (time.perf_counter() - start) * 1000
            data = await response.json()
            
            if "error" in data:
                return ToolResult(tool_name, False, latency_ms, str(data["error"]))
            
            result = data.get("result", {})
            if result.get("isError", False):
                content = result.get("content", [{}])
                error_text = content[0].get("text", "Unknown error") if content else "Unknown error"
                return ToolResult(tool_name, False, latency_ms, error_text[:100])
            
            return ToolResult(tool_name, True, latency_ms)
            
    except asyncio.TimeoutError:
        latency_ms = (time.perf_counter() - start) * 1000
        return ToolResult(tool_name, False, latency_ms, "Timeout")
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        return ToolResult(tool_name, False, latency_ms, str(e)[:100])


async def run_load_test(
    concurrent_users: int = 5,
    requests_per_tool: int = 3,
    tools_to_test: List[str] = None
) -> LoadTestResults:
    """Run load test with specified parameters."""
    
    if tools_to_test is None:
        tools_to_test = list(MCP_TOOLS.keys())
    
    results = LoadTestResults()
    
    print(f"\n{'='*60}")
    print(f"🌀 TwisterLab MCP Load Test")
    print(f"{'='*60}")
    print(f"Tools to test: {len(tools_to_test)}")
    print(f"Concurrent users: {concurrent_users}")
    print(f"Requests per tool: {requests_per_tool}")
    print(f"Total requests: {len(tools_to_test) * requests_per_tool}")
    print(f"{'='*60}\n")
    
    start_time = time.perf_counter()
    
    async with aiohttp.ClientSession() as session:
        # Create all tasks
        tasks = []
        for tool_name in tools_to_test:
            arguments = MCP_TOOLS.get(tool_name, {})
            for _ in range(requests_per_tool):
                tasks.append(call_mcp_tool(session, tool_name, arguments))
        
        # Run with concurrency limit
        semaphore = asyncio.Semaphore(concurrent_users)
        
        async def bounded_call(task):
            async with semaphore:
                return await task
        
        print(f"⏳ Running {len(tasks)} requests...")
        
        # Execute all tasks
        completed = await asyncio.gather(*[bounded_call(t) for t in tasks], return_exceptions=True)
        
        for result in completed:
            if isinstance(result, ToolResult):
                results.add_result(result)
            else:
                # Exception case
                results.add_result(ToolResult("unknown", False, 0, str(result)))
    
    results.total_time_sec = time.perf_counter() - start_time
    
    return results


def print_results(results: LoadTestResults):
    """Print formatted results."""
    stats = results.get_stats()
    
    print(f"\n{'='*60}")
    print("📊 LOAD TEST RESULTS")
    print(f"{'='*60}")
    
    summary = stats["summary"]
    print(f"\n📈 Summary:")
    print(f"   Total Requests:      {summary['total_requests']}")
    print(f"   Successful:          {summary['successful']} ✅")
    print(f"   Failed:              {summary['failed']} ❌")
    print(f"   Success Rate:        {summary['success_rate']}")
    print(f"   Total Time:          {summary['total_time_sec']}s")
    print(f"   Requests/Second:     {summary['requests_per_second']}")
    
    print(f"\n{'='*60}")
    print("📋 Results by Tool:")
    print(f"{'='*60}")
    
    # Sort by success rate, then by avg latency
    sorted_tools = sorted(
        stats["by_tool"].items(),
        key=lambda x: (x[1].get("success", 0) / max(x[1].get("calls", 1), 1), -x[1].get("avg_ms", 9999)),
        reverse=True
    )
    
    for tool_name, tool_stats in sorted_tools:
        status = "✅" if tool_stats["failed"] == 0 else "⚠️" if tool_stats["success"] > 0 else "❌"
        
        print(f"\n{status} {tool_name}")
        print(f"   Calls: {tool_stats['calls']} | Success: {tool_stats['success_rate']}")
        
        if "avg_ms" in tool_stats:
            print(f"   Latency: avg={tool_stats['avg_ms']}ms, p50={tool_stats['p50_ms']}ms, p95={tool_stats['p95_ms']}ms")
        
        if "errors" in tool_stats:
            for err in tool_stats["errors"]:
                print(f"   ⚠️ Error: {err[:60]}...")
    
    print(f"\n{'='*60}")
    
    # Performance grade
    success_rate = summary["successful"] / summary["total_requests"] * 100 if summary["total_requests"] > 0 else 0
    rps = summary["requests_per_second"]
    
    if success_rate >= 95 and rps >= 10:
        grade = "A+ 🏆"
    elif success_rate >= 90 and rps >= 5:
        grade = "A 🎯"
    elif success_rate >= 80:
        grade = "B 👍"
    elif success_rate >= 60:
        grade = "C ⚠️"
    else:
        grade = "D ❌"
    
    print(f"\n🏅 Performance Grade: {grade}")
    print(f"{'='*60}\n")
    
    return stats


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="TwisterLab MCP Load Test")
    parser.add_argument("-c", "--concurrent", type=int, default=5, help="Concurrent users (default: 5)")
    parser.add_argument("-n", "--requests", type=int, default=3, help="Requests per tool (default: 3)")
    parser.add_argument("-t", "--tools", nargs="+", help="Specific tools to test (default: all)")
    parser.add_argument("--quick", action="store_true", help="Quick test (1 request per tool)")
    parser.add_argument("--stress", action="store_true", help="Stress test (10 concurrent, 10 requests)")
    
    args = parser.parse_args()
    
    concurrent = args.concurrent
    requests = args.requests
    tools = args.tools
    
    if args.quick:
        concurrent = 3
        requests = 1
    elif args.stress:
        concurrent = 10
        requests = 10
    
    results = await run_load_test(
        concurrent_users=concurrent,
        requests_per_tool=requests,
        tools_to_test=tools
    )
    
    stats = print_results(results)
    
    # Save results to JSON
    output_file = f"load_test_results_{int(time.time())}.json"
    with open(output_file, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"📁 Results saved to: {output_file}")
    
    return stats


if __name__ == "__main__":
    asyncio.run(main())
