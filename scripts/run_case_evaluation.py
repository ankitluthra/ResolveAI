"""Measure retrieval of the source records and links in curated support cases."""

import argparse
import asyncio

from apps.api.app.core.config import get_settings
from apps.api.app.providers.azure_search import AzureSearchProvider
from apps.api.app.providers.coveo import CoveoSearchProvider
from evals.case_evaluator import run_case_evaluation


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True, choices=("azure", "coveo"))
    args = parser.parse_args()
    settings = get_settings()
    provider = (
        AzureSearchProvider(settings)
        if args.provider == "azure"
        else CoveoSearchProvider(settings)
    )
    try:
        result = await run_case_evaluation(args.provider, provider)
    finally:
        await provider.client.aclose()
    print(f"{args.provider}: {result['query_count']} case questions")
    for name, value in result["summary"].items():
        print(f"{name}: {value}")
    print(f"Saved evals/results/{args.provider}-cases.json")


if __name__ == "__main__":
    asyncio.run(main())
