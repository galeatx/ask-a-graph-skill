import asyncio
import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
import aiohttp
from bls_constants import *

def parse_args() -> dict:
    parser = argparse.ArgumentParser(
        description="Search, filter, and summarize scientific literature."
    )
    parser.add_argument("-i", "--input", type=Path, required=True, help="path to JSON input file")
    raw = parser.parse_args()

    with open(raw.input) as f:
        params = json.load(f)

    for k in REQUIRED_INPUT_KEYS:
        if k not in params:
              raise ValueError(f"ValueError: input JSON must contain '{k}'")

    params.setdefault("filter_query", None)
    params.setdefault("max_n_search", MAX_N_SEARCH)
    params.setdefault("max_n_filter", MAX_N_FILTER)

    params.setdefault("save_articles", False)
    params["out_dir"] = Path(params["base_dir"]) / datetime.now().strftime("%Y%m%d_%H%M%S")
    params["input_path"] = raw.input

    return params


def _api_error(step: str, status: int, detail: str) -> RuntimeError:
    msg = f"[ERROR:{step}] status={status} — {detail}"
    print(msg)
    return RuntimeError(msg)


def _empty_result(query: str = "") -> dict:
    return {
        "query": query,
        "filter_query": "",
        "query_info": None,
        "total_articles": 0,
        "timestamp": datetime.now().isoformat(),
        "articles": [],
        "filtered_articles": [],
        "success": False,
        "filter_cost": 0,
        "summary_cost": 0
    }


def _write_report(res: dict, out_dir: Path, prefix: str = "summary_report") -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{prefix}.md"
    out_path.write_text(res["report"])
    print(f"Report saved to {out_path}")


def _write_articles(res: dict, out_dir: Path, prefix: str = "articles") -> None:
    if not res["articles"]:
        raise ValueError("ValueError: No articles to save — re-run with save_articles = true")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{prefix}.json"
    subset = [{k: a[k] for k in ARTICLE_ATTRIBUTES if k in a} for a in res["articles"]]
    out_path.write_text(json.dumps(subset, indent=2))
    print(f"Articles saved to {out_path}")


async def _search(session, query: str, max_n: int) -> dict:
    async with session.post(
        f"{BASE_URL}/search",
        json={"user_request": query, "max_results": max_n},
        ssl=False
    ) as resp:
        if resp.status != 200:
            raise _api_error("search", resp.status, await resp.text())
        result = await resp.json()
        articles = result.get("articles", [])
    print (f"Found {len(articles)} articles for: {query}")

    fmted_result = _empty_result(query=query)

    if not articles:
        return fmted_result

    for k in result:
        fmted_result[k] = result[k]
    fmted_result["success"] = True

    return fmted_result

async def _filter(
    session,
    glob_result: dict,
    filter_query: str | None,
    max_n: int
) -> dict:

    articles = glob_result['articles']
    search_query = glob_result['query']

    filtering_prompt = FILTER_PROMPT_TEMPLATE.format(
        query=search_query, filter_query=filter_query
    ) if filter_query else None

    filter_payload = {
        "articles": articles,
        "user_query": search_query,
        "model": MODELS['filter'],
        "max_number": max_n,
        "max_classifications": min(len(articles), max(3 * MAX_N_FILTER, 100)),
        "max_concurrency": MAX_CONCURRENCY,
        "filtering_prompt": filtering_prompt
    }

    async with session.post(
        f"{BASE_URL}/filter",
        json=filter_payload,
        ssl=False,
        timeout=aiohttp.ClientTimeout(total=TIMEOUT)
    ) as resp:
        if resp.status != 200:
            raise _api_error("filter", resp.status, await resp.text())
        result = await resp.json()

    filtered_articles = result.get("filtered_articles", [])
    filter_cost = result.get("cost", 0)
    n = len(filtered_articles)
    glob_result["selected_articles"] = n
    glob_result["filter_cost"] = filter_cost

    print(f"Selected {n} articles after filtering (cost: ${filter_cost:.4f})")
    
    if not filtered_articles:
        glob_result["success"] = False
        return
    
    glob_result["filtered_articles"] = filtered_articles
    return
        

async def _summarize(
    session,
    glob_result: dict
):
    summarize_payload = {
        "articles": glob_result["filtered_articles"],
        "model": MODELS['summary']
    }
    async with session.post(
        f"{BASE_URL}/summarize",
        json=summarize_payload,
        ssl=False,
        timeout=aiohttp.ClientTimeout(total=TIMEOUT)
    ) as resp:
        if resp.status != 200:
            raise _api_error("summarize", resp.status, await resp.text())
        result = await resp.json()
    
    summary_cost = result.get("cost", 0)
    print(f"Report generated (cost: ${summary_cost:.4f})")

    glob_result["report"] = result.get("report", "")
    glob_result["summary_cost"] = summary_cost
    return


async def search_literature(args: dict):
    result = None
    proc = ""
    async with aiohttp.ClientSession() as session:
        proc = "search"
        result = await _search(
            session, args["query"], args["max_n_search"]
        )

        if not result["success"]:
            return result, proc

        proc = "filter"
        await _filter(
            session, result, 
            args["filter_query"], args["max_n_filter"]
        )

        if not result["success"]:
            return result, proc

        await _summarize(
            session, result
        )

    return result, None
        

def main():
    args = parse_args()
    args["out_dir"].mkdir(parents=True, exist_ok=True)
    shutil.copy(args["input_path"], args["out_dir"] / "input.json")

    result, proc = asyncio.run(search_literature(args))
    if not result["success"]:
        print(f"\n{'='*50}")
        print(f"Failed literature search - no articles found after the {proc} module")
        print(f"{'='*50}\n")
        return

    print(f"\n{'='*50}")
    print(f"Articles found:    {result['total_articles']}")
    print(f"Articles selected: {result['filtered_articles']}")
    print(f"Filter cost:       ${result['filter_cost']:.4f}")
    print(f"Summary cost:      ${result['summary_cost']:.4f}")
    print(f"Total cost:        ${result['filter_cost'] + result['summary_cost']:.4f}")
    print(f"{'='*50}\n")

    if result["success"]:
        _write_report(result, args["out_dir"])
        if args["save_articles"]:
            _write_articles(result, args["out_dir"])
    return


if __name__ == "__main__":
    main()








