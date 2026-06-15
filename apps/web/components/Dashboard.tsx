"use client";

import { FormEvent, useEffect, useMemo, useState, useTransition } from "react";
import Link from "next/link";
import { Background, Controls, ReactFlow, type Edge, type Node } from "@xyflow/react";
import {
  Activity,
  AlertTriangle,
  Brain,
  Building2,
  Clock,
  Database,
  GitFork,
  Layers3,
  Lightbulb,
  Network,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Send,
  TrendingUp,
  Users
} from "lucide-react";
import clsx from "clsx";

import { executeCompanyAction, getCompanyHistory, getCompanyReport, getCompanySignals } from "@/lib/api";
import type { CompanyReport, RawCompanySignal, ReportHistoryItem, TimelineEvent, Trend, WorkflowActionResult } from "@/lib/types";

type DashboardProps = {
  initialReport: CompanyReport | null;
  initialTrends: Trend[];
};

const seedCompanies = [
  "openai.com",
  "anthropic.com",
  "perplexity.ai",
  "cursor.com",
  "reddit.com",
  "gemini",
  "opencv",
  "computer vision",
  "microsoft",
  "notion.so",
  "Tesla"
];

export default function Dashboard({ initialReport, initialTrends }: DashboardProps) {
  const [report, setReport] = useState<CompanyReport | null>(initialReport);
  const [query, setQuery] = useState(initialReport?.company.company_name ?? "OpenAI");
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<ReportHistoryItem[]>([]);
  const [signals, setSignals] = useState<RawCompanySignal[]>([]);
  const [isPending, startTransition] = useTransition();

  const graph = useMemo(() => (report ? buildGraph(report) : { nodes: [], edges: [] }), [report]);

  useEffect(() => {
    if (!report) return;
    const company = report.company.domain || report.company.company_name;
    void Promise.all([getCompanyHistory(company), getCompanySignals(company)]).then(([nextHistory, nextSignals]) => {
      setHistory(nextHistory);
      setSignals(nextSignals);
    });
  }, [report]);

  function runSearch(event?: FormEvent<HTMLFormElement>, forceRefresh = false) {
    event?.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) {
      setError("Enter a company name or domain.");
      return;
    }
    setError(null);
    startTransition(async () => {
      const nextReport = await getCompanyReport(trimmed, forceRefresh);
      if (!nextReport) {
        setError("Could not generate a report. Check that the API is running and credentials are configured.");
        return;
      }
      setReport(nextReport);
    });
  }

  return (
    <main className="min-h-screen text-ink">
      <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-5 px-4 py-4 sm:px-6 lg:px-8">
        <header className="grid gap-4 border-b border-line pb-4 lg:grid-cols-[minmax(0,1fr)_520px] lg:items-end">
          <div>
            <div className="flex items-center gap-2 text-sm font-semibold text-teal">
              <Brain size={18} />
              Dynamic company intelligence platform
            </div>
            <h1 className="mt-2 text-3xl font-semibold leading-tight sm:text-4xl">MagneticSphere AI</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-muted sm:text-base">
              Search any company and generate a live report from signals, graph context, AI reasoning, opportunities, risks, and recommendations.
            </p>
            <Link href="/agents" className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-teal">
              <Network size={17} />
              View LangGraph agents
            </Link>
            <Link href="/integrations" className="ml-4 mt-3 inline-flex items-center gap-2 text-sm font-semibold text-teal">
              <Database size={17} />
              Integration health
            </Link>
          </div>

          <form onSubmit={(event) => runSearch(event)} className="flex flex-col gap-2">
            <div className="flex min-h-12 overflow-hidden rounded-lg border border-line bg-white shadow-soft">
              <div className="flex w-11 items-center justify-center text-teal">
                <Search size={19} />
              </div>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className="min-w-0 flex-1 border-0 px-1 text-sm outline-none"
                placeholder="Search Tesla, OpenAI, Microsoft, notion.so"
              />
              <button
                type="submit"
                className="flex min-w-28 items-center justify-center gap-2 bg-teal px-4 text-sm font-semibold text-white"
                disabled={isPending}
              >
                {isPending ? <RefreshCw className="animate-spin" size={17} /> : <Sparkles size={17} />}
                {isPending ? "Running" : "Analyze"}
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {seedCompanies.map((company) => (
                <button
                  key={company}
                  type="button"
                  onClick={() => {
                    setQuery(company);
                    setError(null);
                    startTransition(async () => {
                      const nextReport = await getCompanyReport(company);
                      if (nextReport) setReport(nextReport);
                    });
                  }}
                  className="rounded-full border border-line bg-white px-3 py-1 text-xs font-medium text-muted transition hover:border-teal hover:text-teal"
                >
                  {company}
                </button>
              ))}
            </div>
            {error ? <div className="text-sm font-medium text-coral">{error}</div> : null}
          </form>
        </header>

        {report ? (
          <CompanyReportView
            report={report}
            graph={graph}
            isPending={isPending}
            onRefresh={() => runSearch(undefined, true)}
            trends={initialTrends}
            history={history}
            signals={signals}
          />
        ) : (
          <EmptyState isPending={isPending} />
        )}
      </div>
    </main>
  );
}

function CompanyReportView({
  report,
  graph,
  isPending,
  onRefresh,
  trends,
  history,
  signals
}: {
  report: CompanyReport;
  graph: { nodes: Node[]; edges: Edge[] };
  isPending: boolean;
  onRefresh: () => void;
  trends: Trend[];
  history: ReportHistoryItem[];
  signals: RawCompanySignal[];
}) {
  const [actionResult, setActionResult] = useState<WorkflowActionResult | null>(null);
  const [isActionPending, startActionTransition] = useTransition();

  function runAction(action: string) {
    startActionTransition(async () => {
      const result = await executeCompanyAction(report.company.domain, action);
      setActionResult(
        result ?? {
          action,
          status: "failed",
          detail: "The API did not return an action result. Check that the backend is running on NEXT_PUBLIC_API_URL."
        }
      );
    });
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
      <div className="flex min-w-0 flex-col gap-5">
        <section className="grid gap-5 lg:grid-cols-[260px_minmax(0,1fr)]">
          <Panel title="Opportunity Score" icon={<TrendingUp size={18} />}>
            <div className="flex flex-col items-center gap-4">
              <ScoreRing value={report.opportunity_score} label="Signal strength" />
              <div className="grid w-full grid-cols-2 gap-3">
                <Info label="Confidence" value={`${report.confidence}%`} />
                <Info label="Cache" value={report.cached ? "Reused" : "Fresh"} />
                <Info label="Score Delta" value={formatDelta(report.score_delta)} />
                <Info label="New Events" value={`+${report.timeline_delta}`} />
              </div>
              {report.score_alert ? (
                <div className="rounded-lg border border-gold/40 bg-[#fff8e8] p-3 text-sm leading-5 text-ink">
                  {report.score_alert}
                </div>
              ) : null}
              <button
                type="button"
                onClick={onRefresh}
                className="flex min-h-10 w-full items-center justify-center gap-2 rounded-lg border border-line bg-white px-3 text-sm font-semibold transition hover:border-teal hover:text-teal"
                disabled={isPending}
              >
                <RefreshCw size={17} className={isPending ? "animate-spin" : ""} />
                Refresh Report
              </button>
            </div>
          </Panel>

          <Panel title={report.company.company_name} icon={<Building2 size={18} />} action={report.company.domain}>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <Info label="Industry" value={report.company.industry} />
              <Info label="Headquarters" value={report.company.headquarters} />
              <Info label="Employees" value={report.company.employees} />
              <Info label="Generated" value={formatDate(report.generated_at)} />
            </div>
            <p className="mt-4 text-sm leading-6 text-muted">{report.analysis.executive_summary}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {report.company.technologies.map((technology) => (
                <Badge key={technology}>{technology}</Badge>
              ))}
            </div>
          </Panel>
        </section>

        <section className="grid gap-5 lg:grid-cols-2">
          <ListPanel title="SWOT Analysis" icon={<ShieldCheck size={18} />} items={report.analysis.swot_analysis} />
          <ListPanel title="Growth Signals" icon={<Activity size={18} />} items={report.analysis.growth_signals} />
          <ListPanel title="Risks" icon={<AlertTriangle size={18} />} items={report.analysis.risks} />
          <ListPanel title="AI Recommendations" icon={<Lightbulb size={18} />} items={report.analysis.ai_recommendations} />
        </section>

        <section className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
          <Panel title="Knowledge Graph" icon={<Network size={18} />}>
            <div className="h-[420px] overflow-hidden rounded-lg border border-line bg-white">
              <ReactFlow nodes={graph.nodes} edges={graph.edges} fitView nodesDraggable={false} nodesConnectable={false}>
                <Background />
                <Controls />
              </ReactFlow>
            </div>
          </Panel>

          <Panel title="Competitive Landscape" icon={<GitFork size={18} />}>
            <div className="flex flex-col gap-3">
              {report.company.competitors.length ? (
                report.company.competitors.map((competitor) => (
                  <div key={competitor} className="rounded-lg border border-line bg-panel p-3 text-sm font-semibold">
                    {competitor}
                  </div>
                ))
              ) : (
                <p className="text-sm leading-6 text-muted">No competitors were confidently extracted from the current live sources.</p>
              )}
              {report.analysis.competitive_landscape.map((item) => (
                <p key={item} className="text-sm leading-6 text-muted">
                  {item}
                </p>
              ))}
            </div>
          </Panel>
        </section>

        <section className="grid gap-5 lg:grid-cols-2">
          <TimelinePanel events={report.timeline} />
          <Panel title="Opportunities" icon={<Sparkles size={18} />}>
            <div className="flex flex-col gap-3">
              {report.analysis.opportunities.map((item) => (
                <div key={item} className="rounded-lg border border-line bg-panel p-3 text-sm leading-6 text-muted">
                  {item}
                </div>
              ))}
            </div>
          </Panel>
        </section>

        <section className="grid gap-5 lg:grid-cols-2">
          <HistoryPanel history={history} />
          <EvidencePanel signals={signals} />
        </section>
      </div>

      <aside className="flex flex-col gap-5">
        <Panel title="Action Controls" icon={<Send size={18} />}>
          <div className="grid gap-2">
            <ActionButton label="Send Slack Alert" disabled={isActionPending} onClick={() => runAction("slack")} />
            <ActionButton label="Create HubSpot Company" disabled={isActionPending} onClick={() => runAction("hubspot_company")} />
            <ActionButton label="Create Deal" disabled={isActionPending} onClick={() => runAction("hubspot_deal")} />
          </div>
          {actionResult ? (
            <div className="mt-3 rounded-lg border border-line bg-panel p-3 text-sm leading-5 text-muted">
              <span className="font-semibold text-ink">{actionResult.status}</span>: {actionResult.detail}
            </div>
          ) : null}
        </Panel>

        <Panel title="Live Signals" icon={<Clock size={18} />}>
          <SignalCount label="News" value={report.company.recent_news.length} icon={<Activity size={17} />} />
          <SignalCount label="Funding and deals" value={report.company.funding.length} icon={<TrendingUp size={17} />} />
          <SignalCount label="Hiring" value={report.company.hiring_signals.length} icon={<Users size={17} />} />
          <SignalCount label="Graph entities" value={report.graph_nodes.length} icon={<Network size={17} />} />
        </Panel>

        <Panel title="Recent News" icon={<Layers3 size={18} />}>
          <div className="flex flex-col gap-3">
            {report.company.recent_news.slice(0, 6).map((item) => (
              <a
                key={`${item.title}-${item.source}`}
                href={item.source}
                target="_blank"
                rel="noreferrer"
                className="rounded-lg border border-line bg-panel p-3 transition hover:border-teal"
              >
                <div className="text-sm font-semibold leading-5">{item.title}</div>
                <p className="mt-2 text-xs leading-5 text-muted">{item.summary}</p>
                <div className="mt-2 text-xs font-medium text-teal">{formatDate(item.occurred_at)}</div>
              </a>
            ))}
            {!report.company.recent_news.length ? <p className="text-sm leading-6 text-muted">No live news matched this company yet.</p> : null}
          </div>
        </Panel>

        <Panel title="Report Pipeline" icon={<Database size={18} />}>
          <div className="flex flex-col gap-2">
            {(report.agent_steps.length ? report.agent_steps : []).slice(0, 11).map((step, index) => (
              <div key={step.id} className="grid grid-cols-[32px_minmax(0,1fr)] items-start gap-3 rounded-lg border border-line bg-panel p-3">
                <div className="flex size-8 items-center justify-center rounded-full bg-white text-xs font-semibold text-teal">{index + 1}</div>
                <div>
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-sm font-semibold">{step.name}</div>
                    <span className="rounded-full bg-white px-2 py-1 text-xs text-muted">{step.status}</span>
                  </div>
                  <p className="mt-1 text-xs leading-5 text-muted">{step.output_summary || step.purpose}</p>
                </div>
              </div>
            ))}
            {!report.agent_steps.length ? (
              <p className="text-sm leading-6 text-muted">Run a fresh report to capture per-agent LangGraph execution details.</p>
            ) : null}
          </div>
        </Panel>

        <Panel title="Market Trends" icon={<TrendingUp size={18} />}>
          <div className="flex flex-col gap-2">
            {trends.map((trend) => (
              <div key={trend.id} className="flex items-center justify-between rounded-lg border border-line bg-panel p-3 text-sm">
                <span>{trend.label}</span>
                <span className={clsx("font-semibold", trend.change >= 0 ? "text-teal" : "text-coral")}>
                  {trend.change >= 0 ? "+" : ""}
                  {trend.change}
                </span>
              </div>
            ))}
            {!trends.length ? <p className="text-sm leading-6 text-muted">Trend service did not return market trend rows.</p> : null}
          </div>
        </Panel>
      </aside>
    </div>
  );
}

function ActionButton({ label, disabled, onClick }: { label: string; disabled: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className="flex min-h-10 items-center justify-center gap-2 rounded-lg border border-line bg-white px-3 text-sm font-semibold transition hover:border-teal hover:text-teal disabled:opacity-60"
    >
      {disabled ? <RefreshCw className="animate-spin" size={16} /> : <Send size={16} />}
      {label}
    </button>
  );
}

function HistoryPanel({ history }: { history: ReportHistoryItem[] }) {
  return (
    <Panel title="Report History" icon={<Clock size={18} />}>
      <div className="flex flex-col gap-3">
        {history.slice(0, 6).map((item) => (
          <div key={item.id} className="grid grid-cols-[96px_minmax(0,1fr)_72px] gap-3 rounded-lg border border-line bg-panel p-3 text-sm">
            <div className="text-xs font-semibold text-teal">{formatDate(item.generated_at)}</div>
            <div>
              <div className="font-semibold">{item.company_name}</div>
              <div className="mt-1 text-xs text-muted">{item.timeline_delta > 0 ? `+${item.timeline_delta} timeline events` : "No new timeline delta"}</div>
            </div>
            <div className={clsx("text-right font-semibold", item.score_delta >= 0 ? "text-teal" : "text-coral")}>
              {item.opportunity_score}
              <div className="text-xs">{formatDelta(item.score_delta)}</div>
            </div>
          </div>
        ))}
        {!history.length ? <p className="text-sm leading-6 text-muted">Generate reports to build score history.</p> : null}
      </div>
    </Panel>
  );
}

function EvidencePanel({ signals }: { signals: RawCompanySignal[] }) {
  return (
    <Panel title="Evidence Store" icon={<Database size={18} />}>
      <div className="flex flex-col gap-3">
        {signals.slice(0, 6).map((signal) => (
          <div key={signal.id} className="rounded-lg border border-line bg-panel p-3">
            <div className="flex items-center justify-between gap-3">
              <div className="text-sm font-semibold leading-5">{signal.title}</div>
              <span className="rounded-full bg-white px-2 py-1 text-xs text-muted">{signal.provider}</span>
            </div>
            <p className="mt-2 text-xs leading-5 text-muted">{signal.raw_snippet}</p>
            <div className="mt-2 flex flex-wrap gap-2 text-xs">
              <span className="rounded-full bg-white px-2 py-1">{signal.signal_type}</span>
              <span className="rounded-full bg-white px-2 py-1">{signal.confidence}% confidence</span>
              <span className="rounded-full bg-white px-2 py-1">dedup {signal.dedup_key.slice(0, 7)}</span>
            </div>
          </div>
        ))}
        {!signals.length ? <p className="text-sm leading-6 text-muted">No first-class raw signals have been stored for this company yet.</p> : null}
      </div>
    </Panel>
  );
}

function Panel({ title, icon, action, children }: { title: string; icon: React.ReactNode; action?: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg border border-line bg-white/90 p-4 shadow-soft">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2">
          <span className="text-teal">{icon}</span>
          <h2 className="truncate text-base font-semibold">{title}</h2>
        </div>
        {action ? <span className="shrink-0 rounded-full bg-[#fff4ee] px-3 py-1 text-xs font-semibold text-coral">{action}</span> : null}
      </div>
      {children}
    </section>
  );
}

function ListPanel({ title, icon, items }: { title: string; icon: React.ReactNode; items: string[] }) {
  return (
    <Panel title={title} icon={icon}>
      <div className="flex flex-col gap-3">
        {items.map((item) => (
          <div key={item} className="rounded-lg border border-line bg-panel p-3 text-sm leading-6 text-muted">
            {item}
          </div>
        ))}
      </div>
    </Panel>
  );
}

function TimelinePanel({ events }: { events: TimelineEvent[] }) {
  return (
    <Panel title="Timeline" icon={<Clock size={18} />}>
      <div className="flex flex-col gap-3">
        {events.map((event) => (
          <div key={`${event.id}-${event.title}`} className="grid grid-cols-[88px_minmax(0,1fr)] gap-3 rounded-lg border border-line bg-panel p-3">
            <div>
              <div className="text-xs font-semibold text-teal">{formatDate(event.occurred_at)}</div>
              <div className="mt-2 rounded-full bg-white px-2 py-1 text-center text-xs text-muted">{event.category}</div>
            </div>
            <div>
              <div className="text-sm font-semibold leading-5">{event.title}</div>
              <p className="mt-1 text-sm leading-5 text-muted">{event.summary}</p>
            </div>
          </div>
        ))}
        {!events.length ? <p className="text-sm leading-6 text-muted">No timeline events are available yet.</p> : null}
      </div>
    </Panel>
  );
}

function SignalCount({ label, value, icon }: { label: string; value: number; icon: React.ReactNode }) {
  return (
    <div className="mb-3 flex items-center justify-between rounded-lg border border-line bg-panel p-3">
      <div className="flex items-center gap-2 text-sm font-semibold">
        <span className="text-teal">{icon}</span>
        {label}
      </div>
      <div className="text-lg font-semibold">{value}</div>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-line bg-panel p-3">
      <div className="text-xs text-muted">{label}</div>
      <div className="mt-1 break-words text-sm font-semibold">{value}</div>
    </div>
  );
}

function Badge({ children }: { children: React.ReactNode }) {
  return <span className="rounded-full border border-line bg-panel px-3 py-1 text-xs font-medium">{children}</span>;
}

function ScoreRing({ value, label }: { value: number; label: string }) {
  const size = 158;
  const radius = 64;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-label={`${value}% ${label}`}>
        <circle cx={size / 2} cy={size / 2} r={radius} stroke="#d9e2ec" strokeWidth={10} fill="none" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#0f766e"
          strokeWidth={10}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
        <text x="50%" y="50%" dominantBaseline="middle" textAnchor="middle" className="fill-ink text-3xl font-semibold">
          {value}
        </text>
      </svg>
      <div className="text-center text-xs font-semibold text-muted">{label}</div>
    </div>
  );
}

function buildGraph(report: CompanyReport): { nodes: Node[]; edges: Edge[] } {
  const center = { x: 20, y: 180 };
  const columns = [
    { x: 300, y: 20 },
    { x: 300, y: 120 },
    { x: 300, y: 220 },
    { x: 300, y: 320 },
    { x: 580, y: 70 },
    { x: 580, y: 190 },
    { x: 580, y: 310 }
  ];

  return {
    nodes: report.graph_nodes.map((node, index) => ({
      id: node.id,
      position: index === 0 ? center : columns[(index - 1) % columns.length],
      data: { label: `${node.label} (${node.type})` },
      type: "default"
    })),
    edges: report.graph_edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.label,
      animated: true
    }))
  };
}

function EmptyState({ isPending }: { isPending: boolean }) {
  return (
    <section className="rounded-lg border border-line bg-white/90 p-8 text-center shadow-soft">
      <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-panel text-teal">
        {isPending ? <RefreshCw className="animate-spin" size={22} /> : <Search size={22} />}
      </div>
      <h2 className="mt-4 text-xl font-semibold">Search a company to generate intelligence</h2>
      <p className="mt-2 text-sm text-muted">The report will combine live signals, graph context, AI reasoning, opportunities, and risks.</p>
    </section>
  );
}

function formatDate(date: string) {
  const parsed = new Date(date);
  if (Number.isNaN(parsed.getTime())) return date;
  return new Intl.DateTimeFormat("en", { month: "short", day: "numeric" }).format(parsed);
}

function formatDelta(value: number) {
  if (value > 0) return `+${value}`;
  return String(value);
}
