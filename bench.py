"""Quick local inference speed test against Ollama.

Usage: python bench.py [model] [num_runs]
"""
import asyncio
import statistics
import sys

from app.ollama_client import OllamaError, generate

PROMPT = "Explain the AWS shared responsibility model in three sentences."


async def main() -> None:
    model = sys.argv[1] if len(sys.argv) > 1 else None
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    speeds: list[float] = []
    for i in range(runs):
        try:
            r = await generate(PROMPT, model=model)
        except OllamaError as exc:
            print(f"FAILED: {exc}")
            return
        tps = r["tokens_per_sec"]
        print(
            f"run {i + 1}: {r['eval_count']} tokens in {r['elapsed_sec']}s "
            f"-> {tps} tok/s"
        )
        if tps:
            speeds.append(tps)

    if speeds:
        print(f"\nmedian: {statistics.median(speeds):.2f} tok/s over {len(speeds)} runs")


if __name__ == "__main__":
    asyncio.run(main())
