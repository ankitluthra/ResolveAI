"""Reproducible, clearly synthetic AcmeCloud corpus. No external content is copied."""

import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ingestion.connectors.local import fetch_local

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "synthetic"
OUT = ROOT / "data" / "normalized" / "documents.json"

TOPICS = [
    (
        "authentication",
        "OAuth client secret rotation",
        "Rotate the replacement secret in the AcmeCloud console, deploy it to every worker, then revoke the old secret. A worker using a cached old secret receives HTTP 401 until its credential cache is refreshed. The JavaScript SDK 4.2.1 fixes a cache invalidation defect present in 4.2.0.",
        "oauth rotation 401 secret credential cache",
    ),
    (
        "authentication",
        "API access token lifetime",
        "API access tokens expire after 60 minutes. Refresh tokens can obtain a new access token without asking the user to sign in again. Check the token expiry claim and clock skew before retrying a 401 response.",
        "token expiry refresh 401",
    ),
    (
        "sso",
        "Okta SSO configuration",
        "Create a SAML application in Okta, copy the entity ID and ACS URL from AcmeCloud, then upload the Okta signing certificate. Assign the Okta group to the application and map email to NameID.",
        "okta saml sso configuration",
    ),
    (
        "sso",
        "SSO role mapping",
        "Standard users need both an Okta application assignment and an AcmeCloud role mapping. If admins can sign in but standard users cannot, inspect the group claim and default role policy.",
        "sso standard users role mapping",
    ),
    (
        "webhooks",
        "Webhook signature verification",
        "Compute HMAC-SHA256 over the raw request body using the endpoint signing secret. Compare the result with the X-Acme-Signature header using a constant-time comparison. Do not parse and reserialize JSON before verification.",
        "webhook signature hmac raw body",
    ),
    (
        "webhooks",
        "Multiple webhook endpoints",
        "An organization can register up to ten webhook endpoints. Each endpoint has its own signing secret, event subscriptions, and retry policy.",
        "multiple webhook endpoints",
    ),
    (
        "api",
        "API rate limits",
        "The standard API limit is 600 requests per minute per organization. HTTP 429 responses include Retry-After; use exponential backoff with jitter and avoid immediate retries.",
        "rate limit 429 retry after",
    ),
    (
        "api",
        "API v2 to v3 migration",
        "API v3 uses cursor pagination, renames the accounts endpoint to organizations, and requires the 2026-04 API version header. Migrate in a staging environment before changing production traffic.",
        "api v2 v3 migration version",
    ),
    (
        "sdk",
        "JavaScript SDK token refresh",
        "The JavaScript SDK refreshes access tokens automatically when a refresh token is configured. Version 4.2.0 may retain an old client secret after rotation; upgrade to 4.2.1 and restart long-lived workers.",
        "javascript sdk refresh token 4.2",
    ),
    (
        "billing",
        "Invoice reconciliation",
        "Invoices are generated on the first day of the month. Export the usage report and match organization ID and billing period against invoice line items.",
        "billing invoice usage",
    ),
    (
        "integrations",
        "Connector synchronization",
        "The AcmeCloud connector synchronizes changed records every 15 minutes. A failed sync can be retried from the integration status page after correcting credentials.",
        "integration connector sync",
    ),
    (
        "authentication",
        "Authentication flow version",
        "The new OAuth authentication flow was introduced in API version 2026-04. Clients on earlier versions continue to use the legacy token endpoint until migrated.",
        "authentication flow api version",
    ),
]

SOURCE_SPECS = [
    ("documentation", "documentation.json", 80),
    ("github_issue", "github_issues.json", 55),
    ("support_ticket", "support_tickets.json", 65),
    ("faq", "faq.json", 30),
    ("release_note", "release_notes.json", 20),
]


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    base = datetime(2026, 1, 5, tzinfo=timezone.utc)
    for source, filename, count in SOURCE_SPECS:
        records = []
        for number in range(1, count + 1):
            topic_index = (number - 1) % len(TOPICS)
            product, subject, guidance, keywords = TOPICS[topic_index]
            suffix = f"{number:03d}"
            id_prefix = {
                "documentation": "doc",
                "github_issue": "issue",
                "support_ticket": "ticket",
                "faq": "faq",
                "release_note": "release",
            }[source]
            title = {
                "documentation": subject,
                "github_issue": f"{subject}: reported behavior #{number + 200}",
                "support_ticket": f"Case AC-{number + 180}: {subject}",
                "faq": f"How does {subject.lower()} work?",
                "release_note": f"Release 4.{number // 10}.{number % 10}: {subject}",
            }[source]
            detail = {
                "documentation": "This is the maintained product procedure. Verify configuration in a staging environment before applying it to production.",
                "github_issue": "Engineering reproduced the reported behavior and linked the mitigation to the maintained documentation.",
                "support_ticket": "A fictional customer reported this symptom. Support confirmed the resolution using the documented steps.",
                "faq": "This short answer summarizes the documented behavior; consult the full product guide for operational details.",
                "release_note": "This release note records a product change and points to the current guide for the supported procedure.",
            }[source]
            date = base + timedelta(days=(number * 3 + topic_index * 7) % 250)
            records.append(
                {
                    "id": f"{id_prefix}-{suffix}",
                    "title": title,
                    "content": f"{title}. {guidance} {detail} Context: {keywords}.",
                    "product": product.title(),
                    "category": subject,
                    "url": f"https://docs.acmecloud.example/knowledge/{id_prefix}-{suffix}",
                    "created_at": date.isoformat(),
                    "updated_at": (date + timedelta(days=2)).isoformat(),
                    "tags": [product, *keywords.split()[:2]],
                    "visibility": "support" if source == "support_ticket" else "public",
                    "metadata": {"synthetic": True, "topic_key": product},
                }
            )
        (RAW / filename).write_text(json.dumps(records, indent=2) + "\n")
    docs = fetch_local(RAW)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps([doc.model_dump(mode="json") for doc in docs], indent=2) + "\n"
    )
    print(
        f"Normalized {len(docs)} synthetic documents: {dict(Counter(d.source_type for d in docs))}"
    )
    print(f"Output: {OUT}")


if __name__ == "__main__":
    main()
