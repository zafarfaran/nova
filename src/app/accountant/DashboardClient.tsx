"use client";

import React, { useState, useMemo, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "./components/Sidebar";
import { TopHeader } from "./components/TopHeader";
import { ClientTable } from "./components/ClientTable";
import type { ClientRow } from "./components/ClientTable";
import { DetailPanel } from "./components/DetailPanel";
import { QuickMetrics } from "./components/QuickMetrics";
import type { DashboardMetrics } from "./components/QuickMetrics";
import { FlaggedDocuments } from "./components/FlaggedDocuments";
import { AIChat } from "./AIChat";
import { SparkleIcon, ChevronRightIcon } from "./components/icons/AccountantIcons";
import "./styles/dashboard.css";

interface AccountantDashboardClientProps {
    clients: ClientRow[];
    metrics: DashboardMetrics;
}

export function AccountantDashboardClient({ clients, metrics }: AccountantDashboardClientProps) {
    const router = useRouter();
    const [selectedClient, setSelectedClient] = useState<ClientRow | null>(null);
    const [showDetailPanel, setShowDetailPanel] = useState(false);
    const [showAIChat, setShowAIChat] = useState(false);
    const [activeNav, setActiveNav] = useState("dashboard");
    const [searchQuery, setSearchQuery] = useState("");
    const [deletingClientId, setDeletingClientId] = useState<string | null>(null);

    // Refresh dashboard data from server
    const refreshDashboard = useCallback(() => {
        router.refresh();
    }, [router]);

    // Calculate flagged document count
    const flaggedDocumentsCount = useMemo(() => {
        return clients.reduce((sum, client) => sum + (client.failedValidationCount || 0), 0);
    }, [clients]);

    const readyClientsCount = useMemo(() => {
        return clients.filter((c) => c.vatPeriodStatus === "ready").length;
    }, [clients]);

    // Filter clients based on search
    const filteredClients = useMemo(() => {
        if (!searchQuery.trim()) return clients;
        const query = searchQuery.toLowerCase();
        return clients.filter(
            (client) =>
                client.clientName.toLowerCase().includes(query) ||
                client.email.toLowerCase().includes(query) ||
                client.entityType.toLowerCase().includes(query)
        );
    }, [clients, searchQuery]);

    const filteredReadyClients = useMemo(() => {
        return filteredClients.filter((client) => client.vatPeriodStatus === "ready");
    }, [filteredClients]);

    // Get page title based on active nav
    const getPageTitle = () => {
        switch (activeNav) {
            case "flagged":
                return "Flagged Documents";
            case "ready":
                return "Ready for Submission";
            case "clients":
                return "Client Portfolio";
            case "vat-returns":
                return "Tax Returns";
            default:
                return "Tax Compliance Dashboard";
        }
    };

    const getPageSubtitle = () => {
        switch (activeNav) {
            case "flagged":
                return "Review documents that require verification or follow-up";
            case "ready":
                return "Clients prepared for tax submission";
            case "clients":
                return "Manage client records, status, and engagement";
            case "vat-returns":
                return "Monitor upcoming tax return deadlines";
            default:
                return "Track documentation, status, and tax readiness";
        }
    };

    const handleRowClick = (client: ClientRow) => {
        setSelectedClient(client);
        setShowDetailPanel(true);
    };

    const handleCloseDetail = () => {
        setShowDetailPanel(false);
        setTimeout(() => setSelectedClient(null), 200);
    };

    const handleSendReminder = (clientId: string) => {
        console.log("Send reminder to client:", clientId);
    };

    const handleViewOnboarding = (clientId: string) => {
        window.open(`/onboard/${clientId}`, "_blank");
    };

    const handleAddNewClient = () => {
        console.log("Add new client");
    };

    const handleDeleteClient = async (clientId: string) => {
        const confirmed = window.confirm("Are you sure you want to delete this client?");
        if (!confirmed) return;
        if (deletingClientId) return;

        setDeletingClientId(clientId);
        try {
            const response = await fetch(`/api/clients/${clientId}`, {
                method: "DELETE",
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                alert(error.error || "Failed to delete client. Please try again.");
                return;
            }

            if (selectedClient?.id === clientId) {
                handleCloseDetail();
            }

            router.refresh();
        } catch (error) {
            console.error("Delete client error:", error);
            alert("Failed to delete client. Please try again.");
        } finally {
            setDeletingClientId(null);
        }
    };

    const aiCtaText = useMemo(() => {
        if (selectedClient) {
            return `Ask about ${selectedClient.clientName}`;
        }

        switch (activeNav) {
            case "flagged":
                return "Review flagged documents";
            case "ready":
                return "Who is ready to submit?";
            case "clients":
                return "Find or create a client";
            case "vat-returns":
                return "Tax returns due this month";
            default:
                return "Ask about missing documents or clients";
        }
    }, [activeNav, selectedClient]);

    const ctaMessages = useMemo(() => {
        const baseMessages = [
            "Psssst...",
            "Need a hand?",
            aiCtaText,
            "Check a client's stage",
            "Find missing docs",
            "Create a new client",
            "See who is ready to submit",
        ];
        const seen = new Set<string>();
        return baseMessages.filter((message) => {
            if (!message) return false;
            if (seen.has(message)) return false;
            seen.add(message);
            return true;
        });
    }, [aiCtaText]);

    const [ctaMessageIndex, setCtaMessageIndex] = useState(0);
    const [ctaCharIndex, setCtaCharIndex] = useState(0);
    const [ctaIsDeleting, setCtaIsDeleting] = useState(false);

    useEffect(() => {
        setCtaMessageIndex(0);
        setCtaCharIndex(0);
        setCtaIsDeleting(false);
    }, [ctaMessages]);

    useEffect(() => {
        if (ctaMessages.length === 0) return;
        const currentMessage = ctaMessages[ctaMessageIndex % ctaMessages.length] || "";
        const atFull = ctaCharIndex >= currentMessage.length;
        const atStart = ctaCharIndex <= 0;

        let delay = ctaIsDeleting ? 40 : 70;
        if (atFull && !ctaIsDeleting) delay = 1800;
        if (atStart && ctaIsDeleting) delay = 400;

        const timer = window.setTimeout(() => {
            if (atFull && !ctaIsDeleting) {
                setCtaIsDeleting(true);
                return;
            }

            if (atStart && ctaIsDeleting) {
                setCtaIsDeleting(false);
                setCtaMessageIndex((prev) => (prev + 1) % ctaMessages.length);
                return;
            }

            setCtaCharIndex((prev) => prev + (ctaIsDeleting ? -1 : 1));
        }, delay);

        return () => window.clearTimeout(timer);
    }, [ctaMessages, ctaMessageIndex, ctaCharIndex, ctaIsDeleting]);

    const currentCtaMessage =
        ctaMessages.length > 0
            ? ctaMessages[ctaMessageIndex % ctaMessages.length] || ""
            : aiCtaText;
    const typedCtaText = currentCtaMessage.slice(0, ctaCharIndex);

    return (
        <div className="flex h-screen bg-[#F4F5F7] overflow-hidden">
            {/* Sidebar */}
            <Sidebar
                activeItem={activeNav}
                clientCount={metrics.totalClients}
                vatDueCount={metrics.vatReturnsDue}
                flaggedCount={flaggedDocumentsCount}
                    readyCount={readyClientsCount}
                onNavigate={(itemId) => {
                    setActiveNav(itemId);
                    if (itemId === "ai-assistant") {
                        setShowAIChat(true);
                    }
                }}
            />

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                {/* Top Header */}
                <TopHeader
                    title={getPageTitle()}
                    subtitle={getPageSubtitle()}
                    onSearch={setSearchQuery}
                    onAddNew={handleAddNewClient}
                />

                {/* Scrollable Content Area */}
                <main className="flex-1 overflow-auto p-6 custom-scrollbar">
                    {/* Dashboard View */}
                    {activeNav === "dashboard" && (
                        <>
                            {/* Quick Metrics */}
                            <div className="mb-6">
                                <QuickMetrics
                                    metrics={metrics}
                                    onMetricClick={(metricId) => {
                                        if (metricId === "flagged-documents") {
                                            setActiveNav("flagged");
                                        }
                                    }}
                                />
                            </div>

                            {/* Client Table */}
                            <div className="animate-fade-in-up" style={{ animationDelay: "100ms" }}>
                                <ClientTable
                                    data={filteredClients}
                                    onRowClick={handleRowClick}
                                    selectedId={selectedClient?.id}
                                onDeleteClient={handleDeleteClient}
                                />
                            </div>
                        </>
                    )}

                    {/* Flagged Documents View */}
                    {activeNav === "flagged" && (
                        <div className="animate-fade-in-up">
                            <FlaggedDocuments onRefresh={refreshDashboard} />
                        </div>
                    )}

                    {/* Ready to Submit View */}
                    {activeNav === "ready" && (
                        <div className="animate-fade-in-up">
                            <ClientTable
                                data={filteredReadyClients}
                                onRowClick={handleRowClick}
                                selectedId={selectedClient?.id}
                                onDeleteClient={handleDeleteClient}
                            />
                        </div>
                    )}

                    {/* Clients View */}
                    {activeNav === "clients" && (
                        <div className="animate-fade-in-up">
                            <ClientTable
                                data={filteredClients}
                                onRowClick={handleRowClick}
                                selectedId={selectedClient?.id}
                            onDeleteClient={handleDeleteClient}
                            />
                        </div>
                    )}

                    {/* Tax Returns View - placeholder */}
                    {activeNav === "vat-returns" && (
                        <div className="animate-fade-in-up bg-white border border-[#DFE1E6] rounded p-8 text-center">
                            <p className="text-[#5E6C84]">Tax Returns view coming soon</p>
                        </div>
                    )}
                </main>
            </div>

            {/* Detail Panel - only render when open */}
            {showDetailPanel && (
                <DetailPanel
                    client={selectedClient}
                    isOpen={showDetailPanel}
                    onClose={handleCloseDetail}
                    onSendReminder={handleSendReminder}
                    onViewOnboarding={handleViewOnboarding}
                    onValidationComplete={refreshDashboard}
                />
            )}

            {/* AI Chat Side Panel */}
            {showAIChat && (
                <>
                    {/* Backdrop */}
                    <div
                        className="fixed inset-0 bg-black/20 z-40"
                        onClick={() => setShowAIChat(false)}
                    />

                    {/* Side Panel */}
                    <div className="fixed right-0 top-0 h-full w-[480px] bg-white border-l border-[#DFE1E6] shadow-xl z-50 flex flex-col animate-slide-in-right">
                        {/* Header */}
                        <div className="flex items-center gap-3 px-4 py-3 border-b border-[#DFE1E6] bg-[#FAFBFC]">
                            <button
                                type="button"
                                onClick={() => setShowAIChat(false)}
                                className="w-8 h-8 flex items-center justify-center rounded hover:bg-[#EBECF0] text-[#6B778C] hover:text-[#172B4D] transition-colors cursor-pointer"
                            >
                                <ChevronRightIcon size="md" />
                            </button>
                            <div className="h-8 w-8 rounded-full bg-black flex items-center justify-center">
                                <img src="/logo.svg" alt="Nova" className="h-4 w-4" />
                            </div>
                            <div>
                                <h2 className="text-[14px] font-semibold text-[#172B4D]">AI Assistant</h2>
                                <p className="text-[11px] text-[#5E6C84]">Ask about your clients</p>
                            </div>
                        </div>

                        {/* Chat Content */}
                        <div className="flex-1 overflow-hidden">
                            <AIChat
                                clientId={selectedClient?.id}
                                clientName={selectedClient?.clientName}
                                allClients={clients.map(c => ({ id: c.id, name: c.clientName, email: c.email }))}
                            />
                        </div>
                    </div>
                </>
            )}

            {/* Floating AI Button */}
            {!showAIChat && (
                <div className="fixed bottom-4 right-4 z-40 flex items-center gap-2">
                    <div className="relative flex items-center">
                        <div
                            className="relative z-10 rounded-full bg-white px-3.5 py-2 text-[11px] font-medium text-[#172B4D] shadow-sm border border-[#DFE1E6] whitespace-nowrap transition-opacity duration-500"
                            style={{ opacity: ctaIsDeleting ? 0.5 : 1 }}
                            aria-live="polite"
                        >
                            <span className="transition-opacity duration-500">{typedCtaText}</span>
                        </div>
                        <span className="absolute right-[-6px] top-1/2 h-3.5 w-3.5 -translate-y-1/2 rotate-45 bg-[#DFE1E6] shadow-sm z-0" />
                        <span className="absolute right-[-5px] top-1/2 h-3 w-3 -translate-y-1/2 rotate-45 bg-white z-0" />
                    </div>
                    <button
                        onClick={() => setShowAIChat(true)}
                        className="relative h-11 w-11 rounded-full bg-[#0B4DBA] text-white shadow-sm hover:bg-[#0842A0] hover:shadow-md transition-all duration-150 ease-out flex items-center justify-center focus:outline-none focus-visible:ring-2 focus-visible:ring-[#2684FF]/40"
                        title="Open AI Assistant"
                    >
                        <img src="/logo.svg" alt="Nova" className="h-5 w-5" />
                    </button>
                </div>
            )}
        </div>
    );
}
