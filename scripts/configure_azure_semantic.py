"""Add the optional semantic configuration to an existing Azure search index."""

import asyncio

from apps.api.app.core.config import get_settings
from apps.api.app.providers.azure_search import AzureSearchProvider


async def main() -> None:
    provider = AzureSearchProvider(get_settings())
    try:
        await provider.enable_semantic_config()
    finally:
        await provider.client.aclose()
    print(f"Configured Azure semantic ranking: {provider.settings.azure_semantic_config}")


if __name__ == "__main__":
    asyncio.run(main())
