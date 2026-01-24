import { AIChat } from "./AIChat";

export default function AccountantDashboard() {
    return (
        <div className="flex h-screen flex-col bg-gradient-to-br from-slate-50 to-blue-50">
            {/* Header */}
            <div className="border-b border-slate-200 bg-white shadow-sm">
                <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="rounded-lg bg-blue-100 p-2">
                                <svg className="h-8 w-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                </svg>
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold text-slate-900">Accountant Dashboard</h1>
                                <p className="text-sm text-slate-600">AI-Powered Assistant</p>
                            </div>
                        </div>

                        <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2 rounded-lg bg-green-50 px-3 py-2">
                                <div className="h-2 w-2 rounded-full bg-green-500"></div>
                                <span className="text-sm font-medium text-green-700">AI Active</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex flex-1 overflow-hidden">
                {/* Sidebar */}
                <div className="hidden w-64 border-r border-slate-200 bg-white p-4 lg:block">
                    <div className="space-y-4">
                        <div>
                            <h3 className="mb-2 text-sm font-semibold text-slate-700">Quick Actions</h3>
                            <div className="space-y-2">
                                <button className="flex w-full items-center gap-2 rounded-lg bg-slate-50 px-3 py-2 text-left text-sm text-slate-700 transition-colors hover:bg-slate-100">
                                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                    </svg>
                                    Search Clients
                                </button>
                                <button className="flex w-full items-center gap-2 rounded-lg bg-slate-50 px-3 py-2 text-left text-sm text-slate-700 transition-colors hover:bg-slate-100">
                                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                                    </svg>
                                    Calculate VAT
                                </button>
                                <button className="flex w-full items-center gap-2 rounded-lg bg-slate-50 px-3 py-2 text-left text-sm text-slate-700 transition-colors hover:bg-slate-100">
                                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                    </svg>
                                    Check Deadlines
                                </button>
                            </div>
                        </div>

                        <div>
                            <h3 className="mb-2 text-sm font-semibold text-slate-700">AI Capabilities</h3>
                            <div className="space-y-2 text-xs text-slate-600">
                                <div className="flex items-start gap-2">
                                    <svg className="mt-0.5 h-3 w-3 flex-shrink-0 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                    </svg>
                                    <span>Client database search</span>
                                </div>
                                <div className="flex items-start gap-2">
                                    <svg className="mt-0.5 h-3 w-3 flex-shrink-0 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                    </svg>
                                    <span>VAT calculations</span>
                                </div>
                                <div className="flex items-start gap-2">
                                    <svg className="mt-0.5 h-3 w-3 flex-shrink-0 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                    </svg>
                                    <span>Date & time queries</span>
                                </div>
                                <div className="flex items-start gap-2">
                                    <svg className="mt-0.5 h-3 w-3 flex-shrink-0 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                    </svg>
                                    <span>Mathematical calculations</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Chat Area */}
                <div className="flex-1 overflow-hidden bg-white">
                    <AIChat />
                </div>
            </div>
        </div>
    );
}
