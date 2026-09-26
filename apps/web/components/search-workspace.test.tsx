import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import SearchWorkspace from "./search-workspace";
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));
describe("search workspace", () => {
  it("shows the query input and provider switch", () => {
    render(
      <QueryClientProvider client={new QueryClient()}>
        <SearchWorkspace />
      </QueryClientProvider>,
    );
    expect(
      screen.getByRole("textbox", { name: "Ask a support question" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Coveo" })).toBeInTheDocument();
    expect(
      screen.getByText("Search across the places support actually works."),
    ).toBeInTheDocument();
  });
});
