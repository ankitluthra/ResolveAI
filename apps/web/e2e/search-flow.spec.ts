import { expect, test } from "@playwright/test";

const result = {
  id: "doc-001",
  title: "OAuth client secret rotation",
  content_preview:
    "Rotate the replacement secret before revoking the old secret.",
  source_type: "documentation",
  product: "Authentication",
  category: "OAuth client secret rotation",
  url: null,
  score: 2.5,
  tags: ["oauth", "rotation"],
  visibility: "public",
  updated_at: "2026-01-09T00:00:00Z",
};

test("search results rerun when the provider changes", async ({ page }) => {
  const called: string[] = [];
  await page.route("http://localhost:8000/api/search**", async (route) => {
    const url = new URL(route.request().url());
    called.push(url.searchParams.get("provider") || "");
    await route.fulfill({
      json: {
        query: url.searchParams.get("q"),
        provider: url.searchParams.get("provider"),
        latency_ms: 34,
        total_results: 1,
        results: [result],
        timestamp: "2026-09-26T00:00:00Z",
      },
      headers: { "access-control-allow-origin": "*" },
    });
  });
  await page.goto("/");
  await page
    .getByRole("textbox", { name: "Ask a support question" })
    .fill("Why does OAuth fail after rotation?");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(page.getByRole("heading", { name: result.title })).toBeVisible();
  await page.getByRole("button", { name: "Coveo" }).click();
  await expect.poll(() => called.join(",")).toContain("azure,coveo");
  await expect(page).toHaveURL(/provider=coveo/);
});

test("answer citation opens its local source record", async ({ page }) => {
  await page.route("http://localhost:8000/api/search**", (route) =>
    route.fulfill({
      json: {
        query: "OAuth rotation",
        provider: "azure",
        latency_ms: 30,
        total_results: 1,
        results: [result],
        timestamp: "2026-09-26T00:00:00Z",
      },
      headers: { "access-control-allow-origin": "*" },
    }),
  );
  await page.route("http://localhost:8000/api/answer", (route) =>
    route.fulfill({
      json: {
        answer: "Deploy the new secret before revoking the old one [doc-001].",
        provider: "azure",
        search_latency_ms: 30,
        generation_latency_ms: 100,
        sources: [{ id: "doc-001", title: result.title, url: null }],
        insufficient_evidence: false,
      },
      headers: { "access-control-allow-origin": "*" },
    }),
  );
  await page.route("http://localhost:8000/api/documents/doc-001", (route) =>
    route.fulfill({
      json: {
        ...result,
        content:
          "Rotate the replacement secret before revoking the old secret.",
        created_at: "2026-01-01T00:00:00Z",
        metadata: { synthetic: true },
      },
      headers: { "access-control-allow-origin": "*" },
    }),
  );
  await page.goto("/?q=OAuth+rotation");
  await expect(page.getByRole("heading", { name: result.title })).toBeVisible();
  await page.getByRole("button", { name: "Generate answer" }).click();
  await expect(page.getByText(/Deploy the new secret/)).toBeVisible();
  await page.locator(".answer-sources a").click();
  await expect(page).toHaveURL(/\/documents\/doc-001/);
  await expect(
    page.getByText(
      "Rotate the replacement secret before revoking the old secret.",
      { exact: true },
    ),
  ).toBeVisible();
});

test("filters rerun search and show the empty state", async ({ page }) => {
  const requests: string[] = [];
  await page.route("http://localhost:8000/api/search**", async (route) => {
    const url = new URL(route.request().url());
    requests.push(url.searchParams.toString());
    const filtered = url.searchParams.get("source_type") === "faq";
    await route.fulfill({
      json: {
        query: url.searchParams.get("q"),
        provider: "azure",
        latency_ms: 20,
        total_results: filtered ? 0 : 1,
        results: filtered ? [] : [result],
        timestamp: "2026-09-26T00:00:00Z",
      },
      headers: { "access-control-allow-origin": "*" },
    });
  });
  await page.goto("/?q=OAuth+rotation");
  await expect(page.getByRole("heading", { name: result.title })).toBeVisible();
  await page.getByRole("checkbox", { name: "FAQs" }).click();
  await expect(page.getByText("No matching documents")).toBeVisible();
  expect(requests.some((request) => request.includes("source_type=faq"))).toBe(
    true,
  );
});

test("insufficient evidence shows a fallback", async ({ page }) => {
  await page.route("http://localhost:8000/api/search**", (route) =>
    route.fulfill({
      json: {
        query: "OAuth rotation",
        provider: "azure",
        latency_ms: 20,
        total_results: 1,
        results: [result],
        timestamp: "2026-09-26T00:00:00Z",
      },
      headers: { "access-control-allow-origin": "*" },
    }),
  );
  await page.route("http://localhost:8000/api/answer", (route) =>
    route.fulfill({
      json: {
        answer:
          "I couldn't find enough information to provide a reliable answer. Here are the most relevant search results.",
        provider: "azure",
        search_latency_ms: 20,
        generation_latency_ms: 0,
        sources: [],
        insufficient_evidence: true,
      },
      headers: { "access-control-allow-origin": "*" },
    }),
  );
  await page.goto("/?q=OAuth+rotation");
  await page.getByRole("button", { name: "Generate answer" }).click();
  await expect(
    page.getByText(/I couldn't find enough information/),
  ).toBeVisible();
});
