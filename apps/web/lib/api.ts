import type {
  AgentStep,
  CompanyReport,
  IntegrationStatus,
  Opportunity,
  OutreachEmail,
  RawCompanySignal,
  ReportHistoryItem,
  Trend,
  WorkflowActionResult
} from "./types";

const apiUrl = process.env.NEXT_PUBLIC_API_URL;

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T | null> {
  if (!apiUrl) {
    return null;
  }

  try {
    const response = await fetch(`${apiUrl}/api${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...init?.headers
      },
      cache: "no-store"
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export async function getOpportunities(): Promise<Opportunity[]> {
  return (await fetchJson<Opportunity[]>("/opportunities")) ?? [];
}

export async function getTrends(): Promise<Trend[]> {
  return (await fetchJson<Trend[]>("/trends")) ?? [];
}

export async function generateOutreach(opportunity: Opportunity): Promise<OutreachEmail> {
  const fromApi = await fetchJson<OutreachEmail>("/outreach", {
    method: "POST",
    body: JSON.stringify({
      opportunity_id: opportunity.id,
      sender_name: "Avery from MagneticSphere",
      product_name: "Cloud AI Platform"
    })
  });
  return fromApi ?? {
    subject: `${opportunity.company.name} intelligence follow-up`,
    body: `Hi ${opportunity.company.name} team,\n\nI noticed recent signals around ${opportunity.company.industry}. It may be worth comparing notes on current priorities and where AI workflows can create leverage.\n\nBest,\nAvery from MagneticSphere`
  };
}

export async function getCompanyReport(query = "openai.com", forceRefresh = false): Promise<CompanyReport | null> {
  return fetchJson<CompanyReport>("/company/report", {
    method: "POST",
    body: JSON.stringify({
      query,
      force_refresh: forceRefresh
    })
  });
}

export async function getAgentArchitecture(): Promise<AgentStep[]> {
  return (await fetchJson<AgentStep[]>("/agents/architecture")) ?? [];
}

export async function getCompanyHistory(company: string): Promise<ReportHistoryItem[]> {
  return (await fetchJson<ReportHistoryItem[]>(`/company/${encodeURIComponent(company)}/history`)) ?? [];
}

export async function getCompanySignals(company: string): Promise<RawCompanySignal[]> {
  return (await fetchJson<RawCompanySignal[]>(`/company/${encodeURIComponent(company)}/signals`)) ?? [];
}

export async function getIntegrationStatus(): Promise<Record<string, IntegrationStatus>> {
  return (await fetchJson<Record<string, IntegrationStatus>>("/integrations/status")) ?? {};
}

export async function executeCompanyAction(company: string, action: string): Promise<WorkflowActionResult | null> {
  return fetchJson<WorkflowActionResult>("/company/action", {
    method: "POST",
    body: JSON.stringify({ company, action })
  });
}
