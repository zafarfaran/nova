"use client";

export function BentoGrid() {
  return (
    <section className="py-20 bg-[#fafafa] border-t border-[#e8e8e8]">
      <div className="max-w-[1200px] mx-auto px-6 sm:px-8 lg:px-12">
        {/* Section Header */}
        <div className="text-center mb-20">
          <span className="text-[12px] uppercase tracking-[1px] text-[#9ba1a5] font-mono mb-6 block">
            Supercharged Workflow
          </span>
          <h2 className="text-[56px] leading-[1.1] font-light text-black mb-6 tracking-tight max-w-[800px] mx-auto">
            Do more with way less effort
          </h2>
          <p className="text-[24px] leading-[1.5] text-[#000000cc] max-w-[700px] mx-auto font-light">
            From chaos to clarity in seconds. Every feature built to make you unstoppable.
          </p>
        </div>

        {/* Features Grid */}
        <div className="space-y-4">
          {/* AI Document Processing */}
          <div className="border border-[#e8e8e8] rounded-[4px] p-10 bg-white hover:border-[#0052CC] transition-colors">
            <div className="max-w-[700px]">
              <span className="text-[12px] uppercase tracking-[1px] text-[#9ba1a5] font-mono mb-4 block">
                Claude AI Brain
              </span>
              <h3 className="text-[32px] leading-[1.2] font-light text-black mb-4">
                Intelligence that thinks ahead
              </h3>
              <p className="text-[16px] leading-[1.6] text-[#000000cc] mb-8">
                Upload hundreds of invoices. Claude extracts every detail, validates VAT numbers against HMRC, flags anomalies, and auto-categorizes transactions. In seconds, not hours.
              </p>

              <div className="grid grid-cols-3 gap-4 mt-8">
                <div className="border border-[#e8e8e8] rounded-[4px] p-6 bg-[#fafafa]">
                  <div className="text-[32px] font-medium text-black mb-1">10,000+</div>
                  <div className="text-[12px] uppercase tracking-[1px] text-[#9ba1a5] font-mono">Docs/hour</div>
                </div>
                <div className="border border-[#e8e8e8] rounded-[4px] p-6 bg-[#fafafa]">
                  <div className="text-[32px] font-medium text-[#36B37E] mb-1">99.9%</div>
                  <div className="text-[12px] uppercase tracking-[1px] text-[#9ba1a5] font-mono">Accuracy</div>
                </div>
                <div className="border border-[#e8e8e8] rounded-[4px] p-6 bg-[#fafafa]">
                  <div className="text-[32px] font-medium text-[#0052CC] mb-1">&lt;1s</div>
                  <div className="text-[12px] uppercase tracking-[1px] text-[#9ba1a5] font-mono">Per invoice</div>
                </div>
              </div>
            </div>
          </div>

          {/* Two Column Layout */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Real-time Banking */}
            <div className="border border-[#e8e8e8] rounded-[4px] p-10 bg-white hover:border-[#36B37E] transition-colors">
              <span className="text-[12px] uppercase tracking-[1px] text-[#9ba1a5] font-mono mb-4 block">
                Live Banking
              </span>
              <h3 className="text-[32px] leading-[1.2] font-light text-black mb-4">
                Real-time sync
              </h3>
              <p className="text-[16px] leading-[1.6] text-[#000000cc] mb-8">
                Connect any UK bank. Transactions flow in automatically. Reconciliation happens in the background.
              </p>

              <div className="space-y-3">
                {[
                  { name: "Barclays Business", txns: "1,247" },
                  { name: "HSBC Corporate", txns: "892" },
                  { name: "Lloyds Commercial", txns: "634" }
                ].map((bank) => (
                  <div key={bank.name} className="flex items-center justify-between p-4 border border-[#e8e8e8] rounded-[4px] bg-[#fafafa]">
                    <div className="text-[14px] font-medium text-black">{bank.name}</div>
                    <div className="text-[12px] text-[#9ba1a5]">{bank.txns} transactions</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Autopilot Mode */}
            <div className="border border-[#e8e8e8] rounded-[4px] p-10 bg-white hover:border-[#FF991F] transition-colors">
              <span className="text-[12px] uppercase tracking-[1px] text-[#9ba1a5] font-mono mb-4 block">
                Zero Touch
              </span>
              <h3 className="text-[32px] leading-[1.2] font-light text-black mb-4">
                Autopilot mode
              </h3>
              <p className="text-[16px] leading-[1.6] text-[#000000cc] mb-8">
                Smart reminders, automated chasers, deadline alerts. Your clients stay on track without you lifting a finger.
              </p>

              <div className="grid grid-cols-2 gap-4">
                <div className="border border-[#e8e8e8] rounded-[4px] p-6 bg-[#fafafa] text-center">
                  <div className="text-[32px] font-medium text-black mb-1">0</div>
                  <div className="text-[12px] uppercase tracking-[1px] text-[#9ba1a5] font-mono">Manual work</div>
                </div>
                <div className="border border-[#e8e8e8] rounded-[4px] p-6 bg-[#fafafa] text-center">
                  <div className="text-[32px] font-medium text-[#FF991F] mb-1">24/7</div>
                  <div className="text-[12px] uppercase tracking-[1px] text-[#9ba1a5] font-mono">Monitoring</div>
                </div>
              </div>
            </div>
          </div>

          {/* Command Center */}
          <div className="border border-[#e8e8e8] rounded-[4px] p-10 bg-white hover:border-[#0052CC] transition-colors">
            <div className="max-w-[700px]">
              <span className="text-[12px] uppercase tracking-[1px] text-[#9ba1a5] font-mono mb-4 block">
                Mission Control
              </span>
              <h3 className="text-[32px] leading-[1.2] font-light text-black mb-4">
                Manage hundreds of clients with ease
              </h3>
              <p className="text-[16px] leading-[1.6] text-[#000000cc] mb-8">
                Bird's-eye view of every client, every deadline, every document. Sort, filter, search. Know exactly who needs attention and why.
              </p>
            </div>

            <div className="grid grid-cols-3 gap-4 mt-8">
              {[
                { value: "248", label: "Active Clients", color: "#0052CC" },
                { value: "12", label: "Need Attention", color: "#FF991F" },
                { value: "236", label: "On Track", color: "#36B37E" }
              ].map((stat, i) => (
                <div key={i} className="border border-[#e8e8e8] rounded-[4px] p-6 bg-[#fafafa]">
                  <div className="text-[32px] font-medium mb-1" style={{ color: stat.color }}>{stat.value}</div>
                  <div className="text-[12px] uppercase tracking-[1px] text-[#9ba1a5] font-mono">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Two Column Layout */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Anomaly Detection */}
            <div className="border border-[#e8e8e8] rounded-[4px] p-10 bg-white hover:border-[#DE350B] transition-colors">
              <span className="text-[12px] uppercase tracking-[1px] text-[#9ba1a5] font-mono mb-4 block">
                Smart Insights
              </span>
              <h3 className="text-[32px] leading-[1.2] font-light text-black mb-4">
                Anomaly detection
              </h3>
              <p className="text-[16px] leading-[1.6] text-[#000000cc] mb-8">
                AI spots irregularities before they become problems. Duplicate invoices, suspicious amounts, missing VAT numbers.
              </p>

              <div className="space-y-3">
                <div className="border border-[#DE350B] bg-[#FFEBE6] rounded-[4px] p-4">
                  <div className="text-[14px] font-medium text-[#DE350B] mb-1">Potential duplicate</div>
                  <div className="text-[12px] text-[#5E6C84]">Invoice #12345 matches existing entry</div>
                </div>
                <div className="border border-[#FF991F] bg-[#FFFAE6] rounded-[4px] p-4">
                  <div className="text-[14px] font-medium text-[#FF991F] mb-1">Unusual amount</div>
                  <div className="text-[12px] text-[#5E6C84]">£50,000 is 10x the average</div>
                </div>
              </div>
            </div>

            {/* VAT Returns */}
            <div className="border border-[#e8e8e8] rounded-[4px] p-10 bg-white hover:border-[#36B37E] transition-colors">
              <span className="text-[12px] uppercase tracking-[1px] text-[#9ba1a5] font-mono mb-4 block">
                One-Click Magic
              </span>
              <h3 className="text-[32px] leading-[1.2] font-light text-black mb-4">
                Generate VAT returns instantly
              </h3>
              <p className="text-[16px] leading-[1.6] text-[#000000cc] mb-8">
                All your data is validated, categorized, and ready. Hit generate. Get HMRC-ready VAT returns in seconds.
              </p>

              <div className="border border-[#e8e8e8] rounded-[4px] p-6 bg-[#fafafa]">
                <div className="flex items-center justify-between mb-6">
                  <div className="text-[14px] font-medium text-black">Q4 2024 VAT Return</div>
                  <div className="px-3 py-1.5 bg-[#E3FCEF] border border-[#ABF5D1] rounded-[3px] text-[11px] font-semibold text-[#006644] uppercase tracking-wide">
                    Ready
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-[12px] text-[#9ba1a5] mb-1">VAT Due</div>
                    <div className="text-[24px] font-medium text-[#0052CC]">£15,444</div>
                  </div>
                  <div>
                    <div className="text-[12px] text-[#9ba1a5] mb-1">Total Sales</div>
                    <div className="text-[24px] font-medium text-black">£125,450</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
