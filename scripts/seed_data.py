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

RELATED_SCENARIOS = [
    (
        "Monitoring and alerts",
        "This record describes alert ownership and telemetry for {subject}. It helps support identify when the behavior began, but does not prescribe the recovery procedure.",
    ),
    (
        "Staging validation",
        "This record covers a staging checklist for {subject}. The team compared the new configuration with the previous deployment and saved the validation logs before rollout.",
    ),
    (
        "Permissions review",
        "This record tracks which team owns {subject} configuration and who may approve changes. It does not change the product behavior described by the maintained guide.",
    ),
    (
        "Incident timeline",
        "This record is a historical timeline for an incident involving {subject}. It records detection, escalation, and communication steps; the current procedure is maintained separately.",
    ),
    (
        "Release planning",
        "This record describes how {subject} changes were staged for a release. It covers rollout windows, review owners, and rollback coordination rather than product instructions.",
    ),
    (
        "Support handoff",
        "This record helps the next support shift take over a case about {subject}. It lists open questions, the responsible team, and the next customer update.",
    ),
]

CASE_RECORDS = {
    "case-oauth-rotation": {
        "ticket-001": (
            "Case AC-181: Northstar Labs receives 401s after OAuth secret rotation",
            "Northstar Labs rotated its OAuth client secret while long-lived workers were running JavaScript SDK 4.2.0. New requests returned HTTP 401 because workers retained the old secret. Support reproduced the failure and linked the investigation to issue-001.",
            "2026-07-15",
        ),
        "issue-001": (
            "JavaScript SDK 4.2.0 retains old secret after rotation",
            "Engineering confirmed that JavaScript SDK 4.2.0 can retain a cached OAuth client secret after rotation. Restarting affected workers clears the cache. The defect is fixed in SDK 4.2.1.",
            "2026-07-16",
        ),
        "release-001": (
            "Release 4.2.1: OAuth credential cache fix",
            "JavaScript SDK 4.2.1 fixes the credential cache invalidation defect tracked as issue-001 in 4.2.0. After upgrading, restart long-lived workers and verify OAuth requests with the replacement secret. See doc-001 for the maintained rotation procedure.",
            "2026-08-02",
        ),
        "doc-001": (None, None, "2026-08-03"),
        "faq-001": (
            "FAQ: Why can OAuth return 401 after secret rotation?",
            "Long-lived workers on JavaScript SDK 4.2.0 may retain the previous client secret after rotation. SDK 4.2.1 fixes the cache defect. See doc-001 for the maintained rotation procedure.",
            "2026-08-04",
        ),
    },
    "case-webhook-signature": {
        "ticket-005": (
            "Case AC-185: Bluebird Retail webhook signatures fail",
            "Bluebird Retail receives webhook signature mismatch errors. Its receiver parses and reserializes the JSON body before HMAC verification. The payload bytes no longer match the bytes AcmeCloud signed. Support linked issue-005 and asked the customer to verify the raw request body.",
            "2026-06-10",
        ),
        "issue-005": (
            "Webhook HMAC mismatch after JSON reserialization",
            "Engineering reproduced a signature mismatch when a receiver computes HMAC-SHA256 over reserialized JSON rather than the raw request body. This is an integration behavior, not a product defect. See doc-005 for the maintained raw-body verification procedure.",
            "2026-06-11",
        ),
        "doc-005": (None, None, "2026-06-12"),
        "faq-005": (
            "FAQ: Why does webhook signature verification fail?",
            "If a receiver parses and reserializes JSON before HMAC verification, its bytes differ from the signed payload. Verify the raw request body. See doc-005 for the maintained procedure.",
            "2026-06-12",
        ),
    },
    "case-sso-roles": {
        "ticket-004": (
            "Case AC-184: Meridian Health standard users cannot sign in with Okta",
            "Meridian Health reports that administrators can sign in through Okta SSO but standard users cannot. The Okta application is assigned, but the group claim and AcmeCloud default role mapping have not been confirmed. Support linked issue-004 and is waiting for the customer's sanitized claim sample.",
            "2026-05-14",
        ),
        "issue-004": (
            "Okta SSO role mapping investigation for standard users",
            "Engineering identified two possible causes for standard-user sign-in failures: a missing Okta group claim or a missing AcmeCloud default role mapping. See doc-004 for the maintained troubleshooting procedure. The customer's claim sample is needed to distinguish the causes. No product defect has been confirmed.",
            "2026-05-15",
        ),
        "doc-004": (None, None, "2026-05-16"),
        "faq-004": (
            "FAQ: Why can Okta admins sign in while standard users cannot?",
            "Check the Okta application assignment, group claim, and AcmeCloud default role mapping. A sanitized claim sample may be needed to identify the cause. See doc-004 for the maintained troubleshooting procedure.",
            "2026-05-16",
        ),
    },
}

CASE_BY_DOCUMENT = {
    document_id: (case_id, title, content, date)
    for case_id, records in CASE_RECORDS.items()
    for document_id, (title, content, date) in records.items()
}


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
            scenario_index = (number - 1) // len(TOPICS)
            if scenario_index:
                scenario, scenario_text = RELATED_SCENARIOS[
                    (scenario_index - 1) % len(RELATED_SCENARIOS)
                ]
                title = f"{title} — {scenario}"
                body = scenario_text.format(subject=subject.lower())
            else:
                scenario = "core"
                body = guidance
            detail = {
                "documentation": "This is the maintained product procedure. Verify configuration in a staging environment before applying it to production.",
                "github_issue": "Engineering reproduced the reported behavior and linked the mitigation to the maintained documentation.",
                "support_ticket": "A fictional customer reported this symptom. Support confirmed the resolution using the documented steps.",
                "faq": "This short answer summarizes the documented behavior; consult the full product guide for operational details.",
                "release_note": "This release note records a product change and points to the current guide for the supported procedure.",
            }[source]
            date = base + timedelta(days=(number * 3 + topic_index * 7) % 250)
            record = {
                "id": f"{id_prefix}-{suffix}",
                "title": title,
                "content": f"{title}. {body} {detail} Context: {keywords}.",
                "product": product.title(),
                "category": subject
                if scenario == "core"
                else f"{subject} — {scenario}",
                "url": f"https://docs.acmecloud.example/knowledge/{id_prefix}-{suffix}",
                "created_at": date.isoformat(),
                "updated_at": (date + timedelta(days=2)).isoformat(),
                "tags": [product, *keywords.split()[:2]],
                "visibility": "support" if source == "support_ticket" else "public",
                "metadata": {
                    "synthetic": True,
                    "topic_key": product,
                    "scenario": scenario,
                },
            }
            if record["id"] in CASE_BY_DOCUMENT:
                case_id, case_title, case_content, case_date = CASE_BY_DOCUMENT[
                    record["id"]
                ]
                record["case_id"] = case_id
                record["metadata"]["case_id"] = case_id
                if case_title:
                    record["title"] = case_title
                if case_content:
                    record["content"] = case_content
                record["created_at"] = f"{case_date}T09:00:00+00:00"
                record["updated_at"] = f"{case_date}T10:00:00+00:00"
            records.append(record)
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
