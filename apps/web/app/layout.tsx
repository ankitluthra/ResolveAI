import type { Metadata } from "next";
import { QueryProvider } from "@/components/query-provider";
import { Shell } from "@/components/shell";
import "./globals.css";
export const metadata: Metadata = {
  title: "ResolveAI · Enterprise Support Intelligence",
  description: "AcmeCloud support search and retrieval evaluation",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>
          <Shell>{children}</Shell>
        </QueryProvider>
      </body>
    </html>
  );
}
