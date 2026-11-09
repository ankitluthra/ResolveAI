"""Create the ra_* custom fields in a Coveo organization through the Field API.

Endpoints and payload follow Coveo's official clients:
- list:   GET  {platform}/rest/organizations/{org}/indexes/page/fields?page=N&perPage=1000
          (what push-api-client.js uses before it creates fields)
- create: POST {platform}/rest/organizations/{org}/indexes/fields/batch/create
          with a JSON list of FieldModel objects (platform-client Field.createFields)
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any

import httpx
from apps.api.app.core.config import Settings
from apps.api.app.providers.coveo import RetryPolicy, Sleep, send_with_retry

# Options every ra_* field needs: "Search operator" (includeInQuery) lets the
# @ra_x=="..." expressions in coveo_context() filter on the field, and
# "Displayable in results" (includeInResults) lets fieldsToInclude return it.
_QUERYABLE = {"includeInQuery": True, "includeInResults": True}

REQUIRED_FIELDS: list[dict[str, Any]] = [
    {"name": "ra_id", "type": "STRING", **_QUERYABLE},
    {"name": "ra_case_id", "type": "STRING", "facet": True, **_QUERYABLE},
    {"name": "ra_source_type", "type": "STRING", "facet": True, **_QUERYABLE},
    {"name": "ra_product", "type": "STRING", "facet": True, **_QUERYABLE},
    {"name": "ra_category", "type": "STRING", "facet": True, **_QUERYABLE},
    {"name": "ra_visibility", "type": "STRING", "facet": True, **_QUERYABLE},
    # Arrays of strings need "Multi-value facet"; it can't be combined with "Facet".
    {"name": "ra_tags", "type": "STRING", "multiValueFacet": True, **_QUERYABLE},
    # Facet is mandatory for non-string fields; sort lets results be ordered by date.
    {"name": "ra_updated_at", "type": "DATE", "facet": True, "sort": True, **_QUERYABLE},
]

PAGE_SIZE = 1000


@dataclass
class FieldSetupReport:
    created: list[str] = field(default_factory=list)
    existing: list[str] = field(default_factory=list)
    # Existing fields whose type or options differ from REQUIRED_FIELDS. Not changed.
    mismatched: dict[str, list[str]] = field(default_factory=dict)


class CoveoFieldManager:
    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
        *,
        retry: RetryPolicy | None = None,
        sleep: Sleep = asyncio.sleep,
    ):
        if not settings.coveo_org_id or not settings.coveo_api_key:
            raise ValueError("COVEO_ORG_ID and COVEO_API_KEY are required to manage fields")
        self.client = client or httpx.AsyncClient(timeout=30)
        self.headers = {"Authorization": f"Bearer {settings.coveo_api_key}"}
        self.retry = retry or RetryPolicy.from_settings(settings)
        self.sleep = sleep
        self.base_url = (
            f"{settings.coveo_platform_base_url.rstrip('/')}/rest/organizations/"
            f"{settings.coveo_org_id}/indexes"
        )

    async def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        response = await send_with_retry(
            self.client,
            method,
            url,
            policy=self.retry,
            sleep=self.sleep,
            headers=self.headers,
            **kwargs,
        )
        response.raise_for_status()
        return response

    async def list_fields(self) -> dict[str, dict[str, Any]]:
        fields: dict[str, dict[str, Any]] = {}
        page = 0
        while True:
            response = await self._request(
                "GET",
                f"{self.base_url}/page/fields",
                params={"page": page, "perPage": PAGE_SIZE},
            )
            payload = response.json()
            for item in payload.get("items", []):
                if item.get("name"):
                    fields[item["name"].lower()] = item
            page += 1
            if page >= payload.get("totalPages", 1):
                return fields

    async def ensure_fields(
        self, required: list[dict[str, Any]] | None = None, *, dry_run: bool = False
    ) -> FieldSetupReport:
        required = required or REQUIRED_FIELDS
        existing = await self.list_fields()
        report = FieldSetupReport()
        missing = []
        for spec in required:
            current = existing.get(spec["name"])
            if current is None:
                missing.append(spec)
                continue
            report.existing.append(spec["name"])
            differences = [
                f"{key}={current.get(key)!r} (want {value!r})"
                for key, value in spec.items()
                if key != "name" and current.get(key) != value
            ]
            if differences:
                report.mismatched[spec["name"]] = differences
        if missing and not dry_run:
            await self._request("POST", f"{self.base_url}/fields/batch/create", json=missing)
        report.created = [spec["name"] for spec in missing]
        return report
