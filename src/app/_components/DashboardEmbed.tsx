import Link from "next/link";

export function DashboardEmbed() {
  return (
    <section className="py-24 bg-black">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Your Dashboard
          </h2>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto mb-8">
            Manage your tax compliance in one place
          </p>
          <Link
            href="/accountant"
            className="inline-flex items-center gap-2 px-6 py-3 bg-white text-black rounded-lg font-semibold hover:bg-slate-200 transition-colors"
          >
            Open Full Dashboard
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>
        </div>

        {/* Dashboard Window Preview */}
        <div className="relative">
          {/* Glow Effect */}
          <div className="absolute -inset-1 bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-pink-500/20 rounded-2xl blur-xl"></div>

          {/* Dashboard Window */}
          <div className="relative bg-slate-900 rounded-2xl border border-slate-800 shadow-2xl overflow-hidden">
            {/* Browser Chrome */}
            <div className="bg-slate-800 border-b border-slate-700 px-4 py-3 flex items-center gap-2">
              <div className="flex gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
              </div>
              <div className="flex-1 text-center">
                <div className="inline-block bg-slate-700 border border-slate-600 rounded px-4 py-1 text-xs text-slate-300">
                  nova.com/accountant
                </div>
              </div>
            </div>

            {/* Dashboard Content Preview */}
            <div className="aspect-[16/10] bg-slate-900 p-8">
              {/* Quick Metrics */}
              <div className="grid grid-cols-4 gap-4 mb-6">
                {[
                  { label: "Total Clients", value: "142", change: "+12%" },
                  { label: "Pending Docs", value: "23", change: "-8%" },
                  { label: "Returns Due", value: "7", change: "Soon" },
                  { label: "Attention Needed", value: "5", change: "High" },
                ].map((metric, i) => (
                  <div key={i} className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                    <div className="text-xs text-slate-400 mb-1">{metric.label}</div>
                    <div className="flex items-baseline justify-between">
                      <div className="text-2xl font-bold text-white">{metric.value}</div>
                      <div className="text-xs text-green-400">{metric.change}</div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Client Table Preview */}
              <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
                {/* Table Header */}
                <div className="bg-slate-750 border-b border-slate-700 px-4 py-3">
                  <h3 className="text-sm font-semibold text-white">Recent Clients</h3>
                </div>

                {/* Table Rows */}
                <div className="divide-y divide-slate-700">
                  {[
                    { name: "Acme Corp Ltd", vat: "GB123456789", status: "Complete", color: "green" },
                    { name: "Tech Solutions Ltd", vat: "GB987654321", status: "Pending", color: "yellow" },
                    { name: "Global Trading Co", vat: "GB456789123", status: "In Progress", color: "blue" },
                    { name: "Digital Services Ltd", vat: "GB789123456", status: "Action Required", color: "red" },
                  ].map((client, i) => (
                    <div key={i} className="px-4 py-3 flex items-center justify-between hover:bg-slate-750 transition-colors">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-slate-700 rounded flex items-center justify-center">
                          <span className="text-sm font-semibold text-slate-300">
                            {client.name.charAt(0)}
                          </span>
                        </div>
                        <div>
                          <div className="text-sm font-medium text-white">{client.name}</div>
                          <div className="text-xs text-slate-400">{client.vat}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <span
                          className={`px-2 py-1 rounded text-xs font-medium ${
                            client.color === "green"
                              ? "bg-green-500/10 text-green-400 border border-green-500/20"
                              : client.color === "yellow"
                                ? "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20"
                                : client.color === "blue"
                                  ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                                  : "bg-red-500/10 text-red-400 border border-red-500/20"
                          }`}
                        >
                          {client.status}
                        </span>
                        <button className="px-3 py-1 bg-slate-700 hover:bg-slate-600 text-white rounded text-xs font-medium transition-colors">
                          View
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="mt-6 flex gap-3">
                <button className="px-4 py-2 bg-white text-black rounded-lg text-sm font-medium hover:bg-slate-200 transition-colors">
                  Add Client
                </button>
                <button className="px-4 py-2 bg-slate-800 border border-slate-700 text-white rounded-lg text-sm font-medium hover:bg-slate-700 transition-colors">
                  Upload Documents
                </button>
                <button className="px-4 py-2 bg-slate-800 border border-slate-700 text-white rounded-lg text-sm font-medium hover:bg-slate-700 transition-colors">
                  Send Reminder
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* CTA to Full Dashboard */}
        <div className="mt-12 text-center">
          <p className="text-slate-400 mb-4">
            This is a preview. Access the full dashboard for complete features.
          </p>
          <Link
            href="/accountant"
            className="inline-flex items-center gap-2 text-white hover:text-slate-300 transition-colors"
          >
            <span className="font-medium">Explore full dashboard</span>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </Link>
        </div>
      </div>
    </section>
  );
}
