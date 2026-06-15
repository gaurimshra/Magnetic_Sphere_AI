import Dashboard from "@/components/Dashboard";
import { getCompanyReport, getTrends } from "@/lib/api";

export default async function Home() {
  const [report, trends] = await Promise.all([
    getCompanyReport("openai.com"),
    getTrends()
  ]);
  return <Dashboard initialReport={report} initialTrends={trends} />;
}
