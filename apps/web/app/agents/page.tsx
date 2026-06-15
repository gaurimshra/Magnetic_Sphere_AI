import Link from "next/link";
import type { ReactNode } from "react";
import {
  Activity,
  ArrowLeft,
  Brain,
  BriefcaseBusiness,
  Database,
  GitBranch,
  Globe2,
  Layers3,
  Lightbulb,
  Network,
  Newspaper,
  Share2,
  Workflow
} from "lucide-react";

import { getAgentArchitecture } from "@/lib/api";

const iconById: Record<string, ReactNode> = {
  signal_agent: <Activity size={18} />,
  news_agent: <Newspaper size={18} />,
  hiring_agent: <BriefcaseBusiness size={18} />,
  social_agent: <Share2 size={18} />,
  tech_stack_agent: <Layers3 size={18} />,
  retrieval_agent: <Database size={18} />,
  graph_agent: <Network size={18} />,
  reasoning_agent: <Brain size={18} />,
  scoring_agent: <Lightbulb size={18} />,
  action_agent: <Workflow size={18} />,
  monitoring_agent: <Globe2 size={18} />
};

export default async function AgentsPage() {
  const agents = await getAgentArchitecture();

  return (
    <main className="min-h-screen text-ink">
      <div className="mx-auto flex w-full max-w-[1180px] flex-col gap-5 px-4 py-4 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-4 border-b border-line pb-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <Link href="/" className="inline-flex items-center gap-2 text-sm font-semibold text-teal">
              <ArrowLeft size={17} />
              Company dashboard
            </Link>
            <h1 className="mt-3 text-3xl font-semibold leading-tight">Sequential Agent Architecture</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
              MagneticSphere now runs company reports through a LangGraph workflow. Each node receives shared state,
              enriches it, and passes it to the next agent.
            </p>
          </div>
          <div className="rounded-lg border border-line bg-white/90 p-4 shadow-soft">
            <div className="flex items-center gap-2 text-sm font-semibold text-teal">
              <GitBranch size={18} />
              LangGraph StateGraph
            </div>
            <div className="mt-2 text-2xl font-semibold">{agents.length || 11} agents</div>
          </div>
        </header>

        <section className="rounded-lg border border-line bg-white/90 p-4 shadow-soft">
          <div className="flex flex-col gap-3">
            {(agents.length ? agents : fallbackAgents).map((agent, index) => (
              <div key={agent.id} className="grid gap-3 rounded-lg border border-line bg-panel p-4 md:grid-cols-[48px_230px_minmax(0,1fr)_130px] md:items-center">
                <div className="flex size-10 items-center justify-center rounded-full bg-white font-semibold text-teal">
                  {index + 1}
                </div>
                <div>
                  <div className="flex items-center gap-2 font-semibold">
                    <span className="text-teal">{iconById[agent.id] ?? <Activity size={18} />}</span>
                    {agent.name}
                  </div>
                  <div className="mt-1 text-xs text-muted">{agent.id}</div>
                </div>
                <p className="text-sm leading-6 text-muted">{agent.purpose}</p>
                <div className="rounded-full bg-white px-3 py-1 text-center text-xs font-semibold text-muted">
                  {agent.status}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="grid gap-5 lg:grid-cols-3">
          <InfoPanel title="Data Collection" items={["News APIs", "RSS feeds", "Reddit/social text", "Job and hiring signals", "Tech-stack mentions"]} />
          <InfoPanel title="Memory And Graph" items={["PostgreSQL reports", "Qdrant company memory", "Neo4j entity graph", "Timeline history", "Cached refreshes"]} />
          <InfoPanel title="AI Reasoning" items={["Gemini analysis", "SWOT", "Growth signals", "Risks", "Opportunities", "Recommendations"]} />
        </section>
      </div>
    </main>
  );
}

function InfoPanel({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="rounded-lg border border-line bg-white/90 p-4 shadow-soft">
      <h2 className="text-base font-semibold">{title}</h2>
      <div className="mt-4 flex flex-col gap-2">
        {items.map((item) => (
          <div key={item} className="rounded-lg border border-line bg-panel p-3 text-sm text-muted">
            {item}
          </div>
        ))}
      </div>
    </section>
  );
}

const fallbackAgents = [
  { id: "signal_agent", name: "Signal Agent", purpose: "Resolve company and prepare signal collection.", status: "configured" },
  { id: "news_agent", name: "News Agent", purpose: "Collect and summarize news, blogs, press releases, and funding signals.", status: "configured" },
  { id: "hiring_agent", name: "Hiring Agent", purpose: "Detect hiring and expansion signals.", status: "configured" },
  { id: "social_agent", name: "Social Sentiment Agent", purpose: "Analyze public conversations and competitor-pain signals.", status: "configured" },
  { id: "tech_stack_agent", name: "Tech Stack Agent", purpose: "Detect AWS, React, Kubernetes, Docker, Python, and related technology usage.", status: "configured" },
  { id: "retrieval_agent", name: "Retrieval Agent", purpose: "Retrieve similar companies and past opportunities from Qdrant.", status: "configured" },
  { id: "graph_agent", name: "Knowledge Graph Agent", purpose: "Build company relationships in graph form.", status: "configured" },
  { id: "reasoning_agent", name: "Reasoning Agent", purpose: "Use Gemini to combine evidence and produce analysis.", status: "configured" },
  { id: "scoring_agent", name: "Opportunity Scoring Agent", purpose: "Generate explainable scores and confidence.", status: "configured" },
  { id: "action_agent", name: "Workflow Agent", purpose: "Persist reports and prepare Slack/CRM/outreach actions.", status: "configured" },
  { id: "monitoring_agent", name: "Monitoring Agent", purpose: "Track cache freshness, timeline, and ongoing changes.", status: "configured" }
];
