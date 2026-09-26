import { Suspense } from "react";
import SearchWorkspace from "@/components/search-workspace";
export default function Page() {
  return (
    <Suspense
      fallback={<div className="workspace">Loading search workspace…</div>}
    >
      <SearchWorkspace />
    </Suspense>
  );
}
