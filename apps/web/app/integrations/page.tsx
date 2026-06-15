import Link from "next/link";
import { ArrowLeft, CheckCircle2, Database, PlugZap, XCircle } from "lucide-react";

import { getIntegrationStatus } from "@/lib/api";

export default async function IntegrationsPage() {
  const statuses = await getIntegrationStatus();
  const entries = Object.entries(statuses);

  return (
    <main className="min-h-screen text-ink">
      <div className="mx-auto flex w-full max-w-[1180px] flex-col gap-5 px-4 py-4 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-4 border-b border-line pb-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <Link href="/" className="inline-flex items-center gap-2 text-sm font-semibold text-teal">
              <ArrowLeft size={17} />
              Company dashboard
            </Link>
            <h1 className="mt-3 text-3xl font-semibold leading-tight">Integration Health</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
              Production readiness across live APIs, databases, vector memory, graph storage, and workflow systems.
            </p>
          </div>
          <div className="rounded-lg border border-line bg-white/90 p-4 shadow-soft">
            <div className="flex items-center gap-2 text-sm font-semibold text-teal">
              <Database size={18} />
              Provider checks
            </div>
            <div className="mt-2 text-2xl font-semibold">{entries.length}</div>
          </div>
        </header>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {entries.map(([name, status]) => (
            <article key={name} className="rounded-lg border border-line bg-white/90 p-4 shadow-soft">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold uppercase tracking-normal text-muted">{name.replaceAll("_", " ")}</div>
                  <div className="mt-2 flex items-center gap-2 text-lg font-semibold">
                    {status.reachable || (!status.checked && status.configured) ? (
                      <CheckCircle2 className="text-teal" size={20} />
                    ) : (
                      <XCircle className="text-coral" size={20} />
                    )}
                    {status.reachable ? "Reachable" : status.configured ? "Configured" : "Not configured"}
                  </div>
                </div>
                <PlugZap className={status.enabled ? "text-teal" : "text-muted"} size={22} />
              </div>
              <p className="mt-3 min-h-12 text-sm leading-6 text-muted">{status.detail}</p>
              <div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs">
                <Badge label="Enabled" value={status.enabled} />
                <Badge label="Configured" value={status.configured} />
                <Badge label="Checked" value={status.checked} />
              </div>
              <div className="mt-3 text-xs text-muted">{status.checked_at ? `Checked ${new Date(status.checked_at).toLocaleString()}` : "Not checked"}</div>
            </article>
          ))}
        </section>
      </div>
    </main>
  );
}

function Badge({ label, value }: { label: string; value: boolean }) {
  return (
    <div className="rounded-lg border border-line bg-panel p-2">
      <div className={value ? "font-semibold text-teal" : "font-semibold text-muted"}>{value ? "Yes" : "No"}</div>
      <div className="mt-1 text-muted">{label}</div>
    </div>
  );
}
