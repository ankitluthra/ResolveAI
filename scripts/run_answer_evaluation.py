"""Run the live supported/unsupported answer set through one provider."""

import argparse
import asyncio

from apps.api.app.core.config import get_settings
from apps.api.app.providers.azure_search import AzureSearchProvider
from apps.api.app.providers.coveo import CoveoSearchProvider
from evals.answer_evaluator import run_answer_evaluation


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True, choices=("azure", "coveo"))
    args = parser.parse_args()
    settings = get_settings()
    if not settings.openai_api_key:
        parser.error("set OPENAI_API_KEY in the ignored root .env")
    provider = (
        AzureSearchProvider(settings)
        if args.provider == "azure"
        else CoveoSearchProvider(settings)
    )
    try:
        result = await run_answer_evaluation(args.provider, provider, settings)
    finally:
        await provider.client.aclose()
    print(f"{args.provider}: {result['query_count']} answer cases")
    print(f"Abstention accuracy: {result['summary']['abstention_accuracy']:.2%}")
    print(f"Expected citation hit: {result['summary']['expected_citation_hit']:.2%}")
    print(f"Saved evals/results/{args.provider}-answers.json; factual review remains pending")


if __name__ == "__main__":
    asyncio.run(main())
