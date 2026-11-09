"""Create any missing ra_* custom fields in the configured Coveo organization."""

import argparse
import asyncio

import httpx

from apps.api.app.core.config import get_settings
from apps.api.app.providers.coveo_fields import CoveoFieldManager


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true", help="List missing fields without creating them"
    )
    args = parser.parse_args()
    manager = CoveoFieldManager(get_settings())
    try:
        report = await manager.ensure_fields(dry_run=args.dry_run)
    except httpx.HTTPStatusError as exc:
        raise SystemExit(
            f"Coveo Field API returned {exc.response.status_code}. COVEO_API_KEY needs "
            "the Fields privilege (view, create and edit); see https://docs.coveo.com/en/1707."
        ) from exc
    finally:
        await manager.client.aclose()
    print(f"Already present: {', '.join(report.existing) or 'none'}")
    verb = "Would create" if args.dry_run else "Created"
    print(f"{verb}: {', '.join(report.created) or 'none'}")
    for name, differences in report.mismatched.items():
        print(f"Warning: {name} exists with different settings: {'; '.join(differences)}")
    if report.mismatched:
        print("Existing fields were not changed. Edit them in the Coveo console if needed.")


if __name__ == "__main__":
    asyncio.run(main())
