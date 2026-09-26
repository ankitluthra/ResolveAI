"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, Search, Workflow, Command } from "lucide-react";
const links = [
  { href: "/", label: "Search", Icon: Search },
  { href: "/evaluation", label: "Evaluation", Icon: Activity },
  { href: "/architecture", label: "Architecture", Icon: Workflow },
];
export function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Command size={19} />
          </div>
          <div>
            <strong>ResolveAI</strong>
            <span>ACMECLOUD / SUPPORT</span>
          </div>
        </div>
        <div className="sidebar-section-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          {links.map(({ href, label, Icon }) => (
            <Link
              key={href}
              href={href}
              className={`nav-link ${path === href ? "active" : ""}`}
            >
              <Icon size={17} />
              {label}
            </Link>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className="status-dot" /> Prototype workspace{" "}
          <small>AcmeCloud · Synthetic data</small>
        </div>
      </aside>
      <div className="main-column">
        <header className="topbar">
          <span>Enterprise Support Intelligence</span>
          <span className="topbar-right">
            <span className="topbar-dot" /> ACMECloud / Engineering preview
          </span>
        </header>
        <main>{children}</main>
      </div>
    </div>
  );
}
