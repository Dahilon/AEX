"use client";

import { TopNav } from "@/components/TopNav";
import { AgentTickerBar } from "@/components/AgentTickerBar";
import { AccountCard } from "@/components/AccountCard";
import { MoversList } from "@/components/MoversList";
import { CandleChart } from "@/components/CandleChart";
import { OrderTicket } from "@/components/OrderTicket";
import { MarketDepthTable } from "@/components/MarketDepthTable";
import { PositionsPanel } from "@/components/PositionsPanel";
import { OrdersPanel } from "@/components/OrdersPanel";
import { BottomDock } from "@/components/BottomDock";
import { AnalysisModal } from "@/components/AnalysisModal";

export default function Dashboard() {
  return (
    <div className="flex flex-col h-screen overflow-hidden select-none">
      {/* ─── Top nav ─── */}
      <TopNav />

      {/* ─── Ticker bar ─── */}
      <AgentTickerBar />

      {/* ─── Main 3-column body ─── */}
      <div className="flex-1 flex min-h-0 overflow-hidden">
        {/* Left sidebar */}
        <aside className="w-[268px] shrink-0 border-r border-border-subtle flex flex-col bg-surface-1/30 hidden lg:flex">
          <AccountCard />
          <div className="border-t border-border-subtle flex-1 flex flex-col min-h-0">
            <MoversList />
          </div>
        </aside>

        {/* Center */}
        <main className="flex-1 flex flex-col min-w-0 min-h-0">
          {/* Chart + order ticket row */}
          <div className="flex-1 flex min-h-0">
            <div className="flex-1 flex flex-col min-w-0">
              <CandleChart />
            </div>
            {/* Inline order ticket (hidden on small screens) */}
            <div className="w-[220px] shrink-0 border-l border-border-subtle p-2 overflow-y-auto hidden xl:block">
              <OrderTicket />
            </div>
          </div>

          {/* Market depth */}
          <div className="shrink-0 p-2 border-t border-border-subtle">
            <MarketDepthTable />
          </div>
        </main>

        {/* Right sidebar */}
        <aside className="w-[280px] shrink-0 border-l border-border-subtle flex flex-col bg-surface-1/30 hidden lg:flex">
          <div className="flex-1 flex flex-col min-h-0 border-b border-border-subtle">
            <PositionsPanel />
          </div>
          <div className="flex-1 flex flex-col min-h-0">
            <OrdersPanel />
          </div>
        </aside>
      </div>

      {/* ─── Bottom dock ─── */}
      <BottomDock />

      {/* ─── Analysis modal ─── */}
      <AnalysisModal />
    </div>
  );
}
