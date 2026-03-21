"""
RAG Comparator Benchmark Script

Uploads documents and runs queries against both Vector RAG and Graph RAG endpoints,
then compares performance and quality metrics.

Usage:
    python benchmark/run.py
    python benchmark/run.py --base-url http://localhost:8000
    python benchmark/run.py --output ./benchmark/results
"""

import argparse
import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx


async def upload_file(
    client: httpx.AsyncClient, base_url: str, file_path: Path
) -> dict:
    """Upload a single file and measure time."""
    start = time.perf_counter()
    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, "text/plain")}
        response = await client.post(f"{base_url}/api/upload", files=files)
    elapsed_ms = (time.perf_counter() - start) * 1000
    response.raise_for_status()
    result = response.json()
    result["upload_time_ms"] = round(elapsed_ms, 2)
    result["file_path"] = str(file_path)
    return result


async def query_endpoint(
    client: httpx.AsyncClient, base_url: str, endpoint: str, query: str, top_k: int = 3
) -> dict:
    """Query a single RAG endpoint and measure time."""
    start = time.perf_counter()
    response = await client.post(
        f"{base_url}{endpoint}",
        json={"query": query, "top_k": top_k},
    )
    elapsed_ms = (time.perf_counter() - start) * 1000
    response.raise_for_status()
    result = response.json()
    result["response_time_ms"] = round(elapsed_ms, 2)
    return result


async def run_query_pair(
    client: httpx.AsyncClient, base_url: str, query_item: dict, top_k: int = 3
) -> dict:
    """Run both vector and graph queries in parallel for a single query."""
    vector_task = query_endpoint(
        client, base_url, "/api/query/vector", query_item["query"], top_k
    )
    graph_task = query_endpoint(
        client, base_url, "/api/query/graph", query_item["query"], top_k
    )
    vector_result, graph_result = await asyncio.gather(
        vector_task, graph_task, return_exceptions=True
    )

    result = {
        "query": query_item["query"],
        "category": query_item["category"],
        "description": query_item["description"],
    }

    if isinstance(vector_result, Exception):
        print(f"  [ERROR] Vector query failed: {vector_result}")
        result["vector"] = {
            "answer": f"ERROR: {vector_result}",
            "score": 0.0,
            "time_ms": 0.0,
            "sources": [],
        }
    else:
        vr = vector_result.get("results", [{}])[0] if vector_result.get("results") else {}
        result["vector"] = {
            "answer": vr.get("answer", ""),
            "score": vr.get("score", 0.0),
            "time_ms": vector_result.get("response_time_ms", 0.0),
            "sources": vr.get("sources", []),
            "rag_type": vr.get("rag_type", "vector"),
        }

    if isinstance(graph_result, Exception):
        print(f"  [ERROR] Graph query failed: {graph_result}")
        result["graph"] = {
            "answer": f"ERROR: {graph_result}",
            "score": 0.0,
            "time_ms": 0.0,
            "sources": [],
        }
    else:
        gr = graph_result.get("results", [{}])[0] if graph_result.get("results") else {}
        result["graph"] = {
            "answer": gr.get("answer", ""),
            "score": gr.get("score", 0.0),
            "time_ms": gr.get("response_time_ms", 0.0),
            "sources": gr.get("sources", []),
            "rag_type": gr.get("rag_type", "graph"),
        }

    return result


def print_upload_table(upload_results: list[dict]) -> None:
    """Print upload results as a formatted table."""
    print("\n" + "=" * 70)
    print("UPLOAD RESULTS")
    print("=" * 70)
    print(f"{'File':<40} {'Status':<12} {'Time (ms)':<12}")
    print("-" * 70)
    for r in upload_results:
        filename = r.get("filename", Path(r.get("file_path", "")).name)
        status = r.get("status", "unknown")
        time_ms = r.get("upload_time_ms", 0)
        print(f"{filename:<40} {status:<12} {time_ms:<12.2f}")
    print()


def print_comparison_table(query_results: list[dict]) -> None:
    """Print query comparison as a formatted table."""
    print("=" * 100)
    print("QUERY COMPARISON: Vector RAG vs Graph RAG")
    print("=" * 100)

    for i, r in enumerate(query_results, 1):
        print(f"\n--- Query {i} [{r['category']}]: {r['query']}")
        print(f"    {r['description']}")
        print(f"    {'Type':<8} {'Score':<10} {'Time (ms)':<12} {'Answer (truncated)'}")
        print(f"    {'-' * 80}")

        v = r["vector"]
        g = r["graph"]
        v_answer = (v["answer"][:60] + "...") if len(v["answer"]) > 60 else v["answer"]
        g_answer = (g["answer"][:60] + "...") if len(g["answer"]) > 60 else g["answer"]
        v_score = v["score"] if v["score"] is not None else 0.0
        g_score = g["score"] if g["score"] is not None else 0.0

        print(f"    {'Vector':<8} {v_score:<10.4f} {v['time_ms']:<12.2f} {v_answer}")
        print(f"    {'Graph':<8} {g_score:<10.4f} {g['time_ms']:<12.2f} {g_answer}")

    print()


def print_aggregate_stats(query_results: list[dict]) -> None:
    """Print aggregate statistics."""
    print("=" * 70)
    print("AGGREGATE STATISTICS")
    print("=" * 70)

    vector_times = [r["vector"]["time_ms"] for r in query_results]
    graph_times = [r["graph"]["time_ms"] for r in query_results]
    vector_scores = [
        r["vector"]["score"] for r in query_results if r["vector"]["score"] is not None
    ]
    graph_scores = [
        r["graph"]["score"] for r in query_results if r["graph"]["score"] is not None
    ]

    print(f"{'Metric':<35} {'Vector RAG':<18} {'Graph RAG':<18}")
    print("-" * 70)
    print(
        f"{'Avg Response Time (ms)':<35} "
        f"{sum(vector_times) / len(vector_times):<18.2f} "
        f"{sum(graph_times) / len(graph_times):<18.2f}"
    )
    if vector_scores:
        print(
            f"{'Avg Score':<35} "
            f"{sum(vector_scores) / len(vector_scores):<18.4f} "
            f"{sum(graph_scores) / len(graph_scores):<18.4f}"
        )
    print()


def generate_observations(query_results: list[dict]) -> list[str]:
    """Auto-generate observations about which RAG type performed better per category."""
    observations = []

    categories: dict[str, list[dict]] = {}
    for r in query_results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r)

    for cat, results in categories.items():
        v_avg_score = sum(
            r["vector"]["score"] for r in results if r["vector"]["score"] is not None
        ) / len(results)
        g_avg_score = sum(
            r["graph"]["score"] for r in results if r["graph"]["score"] is not None
        ) / len(results)
        v_avg_time = sum(r["vector"]["time_ms"] for r in results) / len(results)
        g_avg_time = sum(r["graph"]["time_ms"] for r in results) / len(results)

        if v_avg_score > g_avg_score:
            observations.append(
                f"**{cat}** カテゴリでは Vector RAG のスコアが高い "
                f"(Vector: {v_avg_score:.4f}, Graph: {g_avg_score:.4f})"
            )
        elif g_avg_score > v_avg_score:
            observations.append(
                f"**{cat}** カテゴリでは Graph RAG のスコアが高い "
                f"(Vector: {v_avg_score:.4f}, Graph: {g_avg_score:.4f})"
            )
        else:
            observations.append(
                f"**{cat}** カテゴリではスコアが同等 "
                f"(Vector: {v_avg_score:.4f}, Graph: {g_avg_score:.4f})"
            )

        if v_avg_time < g_avg_time:
            observations.append(
                f"**{cat}** カテゴリでは Vector RAG の応答が速い "
                f"(Vector: {v_avg_time:.0f}ms, Graph: {g_avg_time:.0f}ms)"
            )
        elif g_avg_time < v_avg_time:
            observations.append(
                f"**{cat}** カテゴリでは Graph RAG の応答が速い "
                f"(Vector: {v_avg_time:.0f}ms, Graph: {g_avg_time:.0f}ms)"
            )

    # Overall comparison
    all_v_scores = [
        r["vector"]["score"] for r in query_results if r["vector"]["score"] is not None
    ]
    all_g_scores = [
        r["graph"]["score"] for r in query_results if r["graph"]["score"] is not None
    ]
    if all_v_scores and all_g_scores:
        v_total = sum(all_v_scores) / len(all_v_scores)
        g_total = sum(all_g_scores) / len(all_g_scores)
        if v_total > g_total:
            observations.append(
                f"全体的に Vector RAG のスコアが高い傾向 "
                f"(Vector 平均: {v_total:.4f}, Graph 平均: {g_total:.4f})"
            )
        elif g_total > v_total:
            observations.append(
                f"全体的に Graph RAG のスコアが高い傾向 "
                f"(Vector 平均: {v_total:.4f}, Graph 平均: {g_total:.4f})"
            )
        else:
            observations.append("全体的にスコアは同等")

    return observations


def save_json_results(
    output_dir: Path,
    timestamp: str,
    upload_results: list[dict],
    query_results: list[dict],
) -> Path:
    """Save detailed JSON results."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"results_{timestamp}.json"
    data = {
        "timestamp": timestamp,
        "upload_results": upload_results,
        "query_results": query_results,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return output_path


def save_markdown_summary(
    output_dir: Path,
    timestamp: str,
    upload_results: list[dict],
    query_results: list[dict],
) -> Path:
    """Save a markdown summary suitable for blog articles."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"summary_{timestamp}.md"

    lines: list[str] = []
    lines.append("# RAG Comparator Benchmark Results")
    lines.append("")
    lines.append("## Test Overview")
    lines.append("")
    lines.append(f"- **実行日時**: {timestamp}")
    lines.append(f"- **アップロード文書数**: {len(upload_results)}")
    total_files = ", ".join(
        Path(r.get("file_path", "")).name or r.get("filename", "unknown")
        for r in upload_results
    )
    lines.append(f"- **文書**: {total_files}")
    lines.append(f"- **クエリ数**: {len(query_results)}")
    lines.append("")

    # Upload results table
    lines.append("## Upload Results")
    lines.append("")
    lines.append("| File | Status | Time (ms) |")
    lines.append("|------|--------|-----------|")
    for r in upload_results:
        filename = r.get("filename", Path(r.get("file_path", "")).name)
        status = r.get("status", "unknown")
        time_ms = r.get("upload_time_ms", 0)
        lines.append(f"| {filename} | {status} | {time_ms:.2f} |")
    lines.append("")

    # Per-query comparison table
    lines.append("## Per-Query Comparison")
    lines.append("")
    lines.append(
        "| # | Query | Category | Vector Score | Graph Score "
        "| Vector Time (ms) | Graph Time (ms) |"
    )
    lines.append("|---|-------|----------|-------------|------------|"
                 "-----------------|----------------|")
    for i, r in enumerate(query_results, 1):
        v = r["vector"]
        g = r["graph"]
        v_score = v["score"] if v["score"] is not None else 0.0
        g_score = g["score"] if g["score"] is not None else 0.0
        lines.append(
            f"| {i} | {r['query']} | {r['category']} "
            f"| {v_score:.4f} | {g_score:.4f} "
            f"| {v['time_ms']:.2f} | {g['time_ms']:.2f} |"
        )
    lines.append("")

    # Per-query answers
    lines.append("## Detailed Answers")
    lines.append("")
    for i, r in enumerate(query_results, 1):
        v = r["vector"]
        g = r["graph"]
        lines.append(f"### Query {i}: {r['query']}")
        lines.append(f"- **Category**: {r['category']} ({r['description']})")
        lines.append("")
        lines.append("**Vector RAG:**")
        lines.append(f"> {v['answer']}")
        lines.append("")
        lines.append("**Graph RAG:**")
        lines.append(f"> {g['answer']}")
        lines.append("")

    # Aggregate statistics
    lines.append("## Aggregate Statistics")
    lines.append("")

    vector_times = [r["vector"]["time_ms"] for r in query_results]
    graph_times = [r["graph"]["time_ms"] for r in query_results]
    vector_scores = [
        r["vector"]["score"] for r in query_results if r["vector"]["score"] is not None
    ]
    graph_scores = [
        r["graph"]["score"] for r in query_results if r["graph"]["score"] is not None
    ]

    lines.append("| Metric | Vector RAG | Graph RAG |")
    lines.append("|--------|-----------|----------|")
    lines.append(
        f"| Avg Response Time (ms) "
        f"| {sum(vector_times) / len(vector_times):.2f} "
        f"| {sum(graph_times) / len(graph_times):.2f} |"
    )
    if vector_scores and graph_scores:
        lines.append(
            f"| Avg Score "
            f"| {sum(vector_scores) / len(vector_scores):.4f} "
            f"| {sum(graph_scores) / len(graph_scores):.4f} |"
        )
    lines.append("")

    # Observations
    observations = generate_observations(query_results)
    lines.append("## Observations")
    lines.append("")
    for obs in observations:
        lines.append(f"- {obs}")
    lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return output_path


async def main() -> None:
    parser = argparse.ArgumentParser(description="RAG Comparator Benchmark")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the backend API (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--data-dir",
        default="./benchmark/data",
        help="Directory containing test documents (default: ./benchmark/data)",
    )
    parser.add_argument(
        "--output",
        default="./benchmark/results",
        help="Output directory for results (default: ./benchmark/results)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of results to retrieve per query (default: 3)",
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        return

    # Collect files to upload
    files = sorted(data_dir.glob("*"))
    files = [f for f in files if f.is_file()]
    if not files:
        print(f"Error: No files found in {data_dir}")
        return

    # Load queries
    queries_path = Path(args.data_dir).parent / "queries.json"
    if not queries_path.exists():
        # Try relative to benchmark dir
        queries_path = data_dir.parent / "queries.json"
    if not queries_path.exists():
        print(f"Error: queries.json not found at {queries_path}")
        return

    with open(queries_path, encoding="utf-8") as f:
        queries = json.load(f)

    print(f"RAG Comparator Benchmark")
    print(f"========================")
    print(f"Base URL:   {base_url}")
    print(f"Data dir:   {data_dir}")
    print(f"Output dir: {output_dir}")
    print(f"Files:      {len(files)}")
    print(f"Queries:    {len(queries)}")
    print()

    timeout = httpx.Timeout(120.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        # === Upload Phase ===
        print("Phase 1: Uploading documents...")
        upload_results = []
        for file_path in files:
            print(f"  Uploading: {file_path.name}...", end=" ", flush=True)
            try:
                result = await upload_file(client, base_url, file_path)
                print(f"OK ({result['upload_time_ms']:.0f}ms)")
                upload_results.append(result)
            except httpx.HTTPStatusError as e:
                print(f"FAILED ({e.response.status_code})")
                upload_results.append(
                    {
                        "file_path": str(file_path),
                        "filename": file_path.name,
                        "status": f"error_{e.response.status_code}",
                        "upload_time_ms": 0,
                    }
                )
            except httpx.ConnectError:
                print("FAILED (connection refused - is the server running?)")
                upload_results.append(
                    {
                        "file_path": str(file_path),
                        "filename": file_path.name,
                        "status": "connection_error",
                        "upload_time_ms": 0,
                    }
                )
                print("\nError: Cannot connect to server. Aborting.")
                return

        print_upload_table(upload_results)

        # === Query Phase ===
        print("Phase 2: Running queries (Vector vs Graph)...")
        query_results = []
        for i, query_item in enumerate(queries, 1):
            print(
                f"  [{i}/{len(queries)}] {query_item['query'][:50]}...",
                flush=True,
            )
            try:
                result = await run_query_pair(client, base_url, query_item, args.top_k)
                query_results.append(result)
                v_time = result["vector"]["time_ms"]
                g_time = result["graph"]["time_ms"]
                print(f"           Vector: {v_time:.0f}ms, Graph: {g_time:.0f}ms")
            except Exception as e:
                print(f"           ERROR: {e}")
                query_results.append(
                    {
                        "query": query_item["query"],
                        "category": query_item["category"],
                        "description": query_item["description"],
                        "vector": {
                            "answer": f"ERROR: {e}",
                            "score": 0.0,
                            "time_ms": 0.0,
                            "sources": [],
                        },
                        "graph": {
                            "answer": f"ERROR: {e}",
                            "score": 0.0,
                            "time_ms": 0.0,
                            "sources": [],
                        },
                    }
                )

    # === Results Phase ===
    print_comparison_table(query_results)
    print_aggregate_stats(query_results)

    # Save outputs
    json_path = save_json_results(output_dir, timestamp, upload_results, query_results)
    md_path = save_markdown_summary(
        output_dir, timestamp, upload_results, query_results
    )

    print(f"Results saved:")
    print(f"  JSON:     {json_path}")
    print(f"  Markdown: {md_path}")


if __name__ == "__main__":
    asyncio.run(main())
