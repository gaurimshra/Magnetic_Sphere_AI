import type { Opportunity, OutreachEmail, Trend } from "./types";

export const demoOpportunities: Opportunity[] = [
  {
    id: "opp-neurotech-ai",
    company: {
      id: "neurotech-ai",
      name: "NeuroTech AI",
      industry: "Healthcare AI",
      region: "United States",
      stage: "Series A",
      description: "Clinical workflow automation startup building AI copilots for radiology teams.",
      website: "https://example.com/neurotech",
      competitors: ["MedAssist Cloud", "ClinicMind"],
      technologies: ["AWS", "Kubernetes", "Python", "React"]
    },
    opportunity_type: "High Intent",
    score: 91,
    confidence: 92,
    probability: 91,
    summary:
      "NeuroTech AI is showing high intent for AI infrastructure. The strongest evidence comes from recent funding, expansion hiring, and market intent.",
    recommended_action: "Send personalized outreach within 48 hours.",
    reasons: [
      { label: "Recent funding", impact: 96, evidence: "New capital creates budget for platform adoption and hiring." },
      { label: "Expansion hiring", impact: 88, evidence: "Open AI and infrastructure roles indicate scaling pressure." },
      { label: "Market intent", impact: 82, evidence: "Leadership posts show active interest in clinical AI deployment." },
      { label: "Tech-stack fit", impact: 78, evidence: "AWS and Kubernetes indicate a strong infrastructure fit." }
    ],
    risks: ["Primary risk is competitor speed; outreach should happen quickly."],
    signals: [
      {
        id: "sig-neuro-tech",
        company_id: "neurotech-ai",
        type: "Tech Stack",
        title: "Kubernetes and AWS stack detected",
        summary: "Cloud-native stack indicates fit for AI infrastructure automation.",
        source: "BuiltWith demo adapter",
        strength: 78,
        occurred_at: "2026-06-05"
      },
      {
        id: "sig-neuro-social",
        company_id: "neurotech-ai",
        type: "Social",
        title: "CEO discusses scaling clinical AI",
        summary: "Leadership posts show urgency around reliable model deployment and governance.",
        source: "LinkedIn",
        strength: 82,
        occurred_at: "2026-06-02"
      },
      {
        id: "sig-neuro-hiring",
        company_id: "neurotech-ai",
        type: "Hiring",
        title: "Hiring ML engineers and DevOps leads",
        summary: "Career page added eight AI infrastructure roles in two weeks.",
        source: "Careers page",
        strength: 89,
        occurred_at: "2026-05-28"
      },
      {
        id: "sig-neuro-funding",
        company_id: "neurotech-ai",
        type: "Funding",
        title: "Raised $20M Series A",
        summary: "New funding round led by healthcare-focused investors to expand AI product development.",
        source: "Funding announcement",
        strength: 96,
        occurred_at: "2026-05-24"
      }
    ],
    workflow_actions: [
      { type: "email", title: "Generate outreach email", payload: "Personalized email for NeuroTech AI.", status: "ready" },
      { type: "slack", title: "Send Slack alert", payload: "High Intent Lead: NeuroTech AI scored 91.", status: "ready" },
      { type: "crm", title: "Update CRM", payload: "Create opportunity record with latest signals and score.", status: "ready" }
    ],
    graph_nodes: [
      { id: "neurotech-ai", label: "NeuroTech AI", type: "company" },
      { id: "neurotech-ai-funding", label: "Series A", type: "funding" },
      { id: "neurotech-ai-hiring", label: "Hiring Signals", type: "hiring" },
      { id: "neurotech-ai-tech", label: "AWS, Kubernetes", type: "technology" },
      { id: "neurotech-ai-medassist-cloud", label: "MedAssist Cloud", type: "competitor" }
    ],
    graph_edges: [
      { id: "e1", source: "neurotech-ai", target: "neurotech-ai-funding", label: "raised" },
      { id: "e2", source: "neurotech-ai", target: "neurotech-ai-hiring", label: "expanding" },
      { id: "e3", source: "neurotech-ai", target: "neurotech-ai-tech", label: "uses" },
      { id: "e4", source: "neurotech-ai", target: "neurotech-ai-medassist-cloud", label: "competes" }
    ]
  },
  {
    id: "opp-vision-labs",
    company: {
      id: "vision-labs",
      name: "Vision Labs",
      industry: "Computer Vision",
      region: "Germany",
      stage: "Seed",
      description: "Manufacturing quality inspection company using multimodal vision models.",
      website: "https://example.com/vision-labs",
      competitors: ["InspectIQ", "FactorySight"],
      technologies: ["Azure", "Docker", "PyTorch", "Next.js"]
    },
    opportunity_type: "Emerging Intent",
    score: 86,
    confidence: 84,
    probability: 85,
    summary: "Vision Labs is expanding production AI deployment work after a manufacturing pilot.",
    recommended_action: "Send personalized outreach within 48 hours.",
    reasons: [
      { label: "Expansion hiring", impact: 88, evidence: "Open roles mention production computer vision and MLOps ownership." },
      { label: "Product launch", impact: 81, evidence: "Public pilot suggests near-term expansion." }
    ],
    risks: ["Tech-stack compatibility is inferred and should be confirmed in discovery."],
    signals: [
      {
        id: "sig-vision-hiring",
        company_id: "vision-labs",
        type: "Hiring",
        title: "Hiring edge AI deployment team",
        summary: "Open roles mention production computer vision and MLOps ownership.",
        source: "Job portals",
        strength: 86,
        occurred_at: "2026-06-01"
      },
      {
        id: "sig-vision-news",
        company_id: "vision-labs",
        type: "News",
        title: "Launched factory defect detection pilot",
        summary: "Public pilot with an automotive supplier suggests near-term expansion.",
        source: "Industry news",
        strength: 81,
        occurred_at: "2026-05-30"
      }
    ],
    workflow_actions: [
      { type: "email", title: "Generate outreach email", payload: "Personalized email for Vision Labs.", status: "ready" },
      { type: "slack", title: "Send Slack alert", payload: "High Intent Lead: Vision Labs scored 86.", status: "ready" },
      { type: "crm", title: "Update CRM", payload: "Create opportunity record with latest signals and score.", status: "ready" }
    ],
    graph_nodes: [
      { id: "vision-labs", label: "Vision Labs", type: "company" },
      { id: "vision-labs-hiring", label: "Hiring Signals", type: "hiring" },
      { id: "vision-labs-news", label: "Factory Pilot", type: "news" },
      { id: "vision-labs-inspectiq", label: "InspectIQ", type: "competitor" }
    ],
    graph_edges: [
      { id: "v1", source: "vision-labs", target: "vision-labs-hiring", label: "expanding" },
      { id: "v2", source: "vision-labs", target: "vision-labs-news", label: "launched" },
      { id: "v3", source: "vision-labs", target: "vision-labs-inspectiq", label: "competes" }
    ]
  },
  {
    id: "opp-finedge",
    company: {
      id: "finedge",
      name: "FinEdge",
      industry: "FinTech",
      region: "Singapore",
      stage: "Growth",
      description: "Risk analytics platform modernizing underwriting for SME lenders.",
      website: "https://example.com/finedge",
      competitors: ["RiskPilot", "LedgerLens"],
      technologies: ["GCP", "Go", "Kafka", "PostgreSQL"]
    },
    opportunity_type: "Emerging Intent",
    score: 82,
    confidence: 80,
    probability: 81,
    summary: "FinEdge has competitor dissatisfaction and product automation signals that suggest a wedge opportunity.",
    recommended_action: "Monitor for another strong buying signal.",
    reasons: [
      { label: "Competitor pain", impact: 82, evidence: "Public threads show dissatisfaction with competing analytics pricing." },
      { label: "Product expansion", impact: 77, evidence: "Product update focuses on faster model-assisted workflows." }
    ],
    risks: ["No recent funding signal found, so budget timing may need validation."],
    signals: [
      {
        id: "sig-finedge-competitor",
        company_id: "finedge",
        type: "Competitor",
        title: "Users complain about RiskPilot pricing",
        summary: "Public forum threads show dissatisfaction with a competing analytics vendor.",
        source: "Reddit demo adapter",
        strength: 74,
        occurred_at: "2026-06-03"
      },
      {
        id: "sig-finedge-news",
        company_id: "finedge",
        type: "News",
        title: "Expanding underwriting automation product",
        summary: "Product update focuses on faster model-assisted lender workflows.",
        source: "Company blog",
        strength: 77,
        occurred_at: "2026-05-26"
      }
    ],
    workflow_actions: [
      { type: "email", title: "Generate outreach email", payload: "Personalized email for FinEdge.", status: "ready" },
      { type: "slack", title: "Send Slack alert", payload: "Monitor Lead: FinEdge scored 82.", status: "ready" },
      { type: "crm", title: "Update CRM", payload: "Create opportunity record with latest signals and score.", status: "ready" }
    ],
    graph_nodes: [
      { id: "finedge", label: "FinEdge", type: "company" },
      { id: "finedge-riskpilot", label: "RiskPilot", type: "competitor" },
      { id: "finedge-product", label: "Underwriting AI", type: "product" }
    ],
    graph_edges: [
      { id: "f1", source: "finedge", target: "finedge-riskpilot", label: "competes" },
      { id: "f2", source: "finedge", target: "finedge-product", label: "expanding" }
    ]
  }
];

export const demoTrends: Trend[] = [
  { id: "healthcare-ai", label: "Healthcare AI", direction: "up", score: 92, change: 14 },
  { id: "computer-vision", label: "Computer Vision", direction: "up", score: 86, change: 9 },
  { id: "fintech-ai", label: "FinTech AI", direction: "flat", score: 74, change: 2 },
  { id: "generic-saas", label: "Generic SaaS", direction: "down", score: 61, change: -7 }
];

export function demoOutreach(opportunity: Opportunity): OutreachEmail {
  return {
    subject: `${opportunity.company.name} and scaling AI workflows`,
    body: `Hi ${opportunity.company.name} team,\n\nCongrats on the momentum around ${opportunity.reasons[0].label.toLowerCase()}. I noticed signals that your team is scaling ${opportunity.company.industry.toLowerCase()} initiatives, including ${opportunity.signals[0].title.toLowerCase()}.\n\nMagneticSphere's Cloud AI Platform helps teams deploy, monitor, and govern AI workflows without slowing product teams down. Based on your stack (${opportunity.company.technologies.slice(0, 3).join(", ")}), there may be a strong fit.\n\nWould it be worth a 15-minute conversation next week to compare notes on your AI infrastructure roadmap?\n\nBest,\nAvery from MagneticSphere`
  };
}

