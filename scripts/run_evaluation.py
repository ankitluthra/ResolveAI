"""Run the fixed retrieval evaluation against a configured live provider."""

import argparse
import asyncio

from apps.api.app.core.config import get_settings
from apps.api.app.providers.azure_search import AzureSearchProvider
from apps.api.app.providers.coveo import CoveoSearchProvider
from evals.evaluator import run_evaluation


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True, choices=("azure", "coveo"))
    parser.add_argument("--variant", choices=("baseline", "semantic", "pipeline"), default="baseline")
    args = parser.parse_args()
    settings = get_settings()
    if args.variant == "semantic" and args.provider != "azure":
        parser.error("semantic variant requires --provider azure")
    if args.variant == "pipeline" and args.provider != "coveo":
        parser.error("pipeline variant requires --provider coveo")
    if args.variant == "pipeline" and not settings.coveo_experiment_pipeline:
        parser.error("set COVEO_EXPERIMENT_PIPELINE in .env")
    provider = (
        AzureSearchProvider(settings, semantic=args.variant == "semantic")
        if args.provider == "azure"
        else CoveoSearchProvider(
            settings,
            pipeline=settings.coveo_experiment_pipeline if args.variant == "pipeline" else "",
        )
    )
    try:
        result = await run_evaluation(args.provider, provider, args.variant)
    finally:
        await provider.client.aclose()
    print(f"{args.provider}: {result['query_count']} questions")
    for metric, value in result["summary"].items():
        print(f"{metric}: {value}")
    suffix = "" if args.variant == "baseline" else f"-{args.variant}"
    print(f"Saved evals/results/{args.provider}{suffix}.json")


if __name__ == "__main__":
    asyncio.run(main())
