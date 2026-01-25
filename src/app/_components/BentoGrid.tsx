"use client";

export function BentoGrid() {
  return (
    <section className="py-24 bg-black border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold text-white mb-4">
            Built for speed and scale
          </h2>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto">
            Everything you need to manage VAT compliance for hundreds of clients
          </p>
        </div>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Large Feature - AI Document Processing */}
          <div className="md:col-span-2 group relative overflow-hidden rounded-2xl bg-slate-900 border border-slate-800 p-8 hover:border-slate-700 transition-all">
            <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-blue-500/10 to-transparent rounded-full blur-3xl"></div>
            <div className="relative">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs font-medium mb-4">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" />
                </svg>
                AI-Powered
              </div>
              <h3 className="text-2xl font-bold text-white mb-2">
                Smart document extraction
              </h3>
              <p className="text-slate-400 mb-6">
                Claude AI automatically extracts invoice data, validates VAT numbers, and flags anomalies. No manual data entry required.
              </p>
              <div className="bg-slate-800 rounded-lg border border-slate-700 p-4 shadow-sm">
                <div className="flex items-start gap-3 mb-3">
                  <div className="w-10 h-10 bg-slate-700 rounded flex items-center justify-center flex-shrink-0">
                    <svg className="w-5 h-5 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-white">Invoice_Q1_2024.pdf</span>
                      <span className="text-xs text-green-400 font-medium">✓ Validated</span>
                    </div>
                    <div className="text-xs text-slate-400 space-y-1">
                      <div>VAT Number: GB123456789</div>
                      <div>Amount: £1,250.00 (VAT: £250.00)</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Bank Integration */}
          <div className="group relative overflow-hidden rounded-2xl bg-slate-900 border border-slate-800 p-8 hover:border-slate-700 transition-all">
            <div className="absolute bottom-0 left-0 w-48 h-48 bg-gradient-to-tr from-green-500/10 to-transparent rounded-full blur-3xl"></div>
            <div className="relative h-full flex flex-col">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 text-green-400 border border-green-500/20 text-xs font-medium mb-4 w-fit">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z" />
                  <path fillRule="evenodd" d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clipRule="evenodd" />
                </svg>
                Plaid Powered
              </div>
              <h3 className="text-2xl font-bold text-white mb-2">
                Direct bank feeds
              </h3>
              <p className="text-slate-400 flex-1">
                Connect client accounts securely. Real-time transaction data synced automatically.
              </p>
              <div className="mt-6 space-y-2">
                {["Barclays", "HSBC", "Lloyds"].map((bank) => (
                  <div key={bank} className="flex items-center gap-2 text-sm">
                    <div className="w-6 h-6 bg-slate-700 rounded"></div>
                    <span className="text-slate-300">{bank}</span>
                    <span className="ml-auto text-green-400 text-xs font-medium">Connected</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Automated Chasers */}
          <div className="group relative overflow-hidden rounded-2xl bg-slate-900 border border-slate-800 p-8 hover:border-slate-700 transition-all">
            <div className="absolute top-0 right-0 w-48 h-48 bg-gradient-to-bl from-purple-500/10 to-transparent rounded-full blur-3xl"></div>
            <div className="relative h-full flex flex-col">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20 text-xs font-medium mb-4 w-fit">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                  <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
                </svg>
                Automated
              </div>
              <h3 className="text-2xl font-bold text-white mb-2">
                Smart reminders
              </h3>
              <p className="text-slate-400 flex-1">
                Set it and forget it. Clients get personalized reminders with secure upload links.
              </p>
              <div className="mt-6 bg-slate-800 rounded-lg border border-slate-700 p-3 text-xs">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-6 h-6 bg-purple-500/20 rounded-full flex items-center justify-center text-purple-400 font-semibold">!</div>
                  <span className="font-medium text-white">Due tomorrow</span>
                </div>
                <p className="text-slate-400 text-xs">3 clients need to submit Q4 documents</p>
              </div>
            </div>
          </div>

          {/* Real-time Collaboration */}
          <div className="md:col-span-2 group relative overflow-hidden rounded-2xl bg-slate-900 border border-slate-800 p-8 hover:border-slate-700 transition-all">
            <div className="absolute bottom-0 right-0 w-64 h-64 bg-gradient-to-tl from-orange-500/10 to-transparent rounded-full blur-3xl"></div>
            <div className="relative">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-500/10 text-orange-400 border border-orange-500/20 text-xs font-medium mb-4">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                </svg>
                Complete Audit Trail
              </div>
              <h3 className="text-2xl font-bold text-white mb-2">
                Every action tracked
              </h3>
              <p className="text-slate-400 mb-6">
                Full compliance logging. Know who did what, when. Perfect for HMRC audits and internal reviews.
              </p>
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-slate-800 rounded-lg border border-slate-700 p-4 text-center">
                  <div className="text-2xl font-bold text-white mb-1">100%</div>
                  <div className="text-xs text-slate-400">Audit ready</div>
                </div>
                <div className="bg-slate-800 rounded-lg border border-slate-700 p-4 text-center">
                  <div className="text-2xl font-bold text-white mb-1">24/7</div>
                  <div className="text-xs text-slate-400">Activity logs</div>
                </div>
                <div className="bg-slate-800 rounded-lg border border-slate-700 p-4 text-center">
                  <div className="text-2xl font-bold text-white mb-1">Real-time</div>
                  <div className="text-xs text-slate-400">Updates</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
