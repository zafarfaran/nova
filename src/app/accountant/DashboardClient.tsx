"use client";

import React, { useState, useMemo, useCallback } from "react";
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

    // Refresh dashboard data from server
    const refreshDashboard = useCallback(() => {
        router.refresh();
    }, [router]);

    // Calculate flagged count (clients with pending reviews)
    const flaggedClientsCount = useMemo(() => {
        return clients.filter((c) => c.hasPendingReviews).length;
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

    // Get page title based on active nav
    const getPageTitle = () => {
        switch (activeNav) {
            case "flagged":
                return "Flagged Documents";
            case "clients":
                return "All Clients";
            case "vat-returns":
                return "VAT Returns";
            default:
                return "VAT Compliance Dashboard";
        }
    };

    const getPageSubtitle = () => {
        switch (activeNav) {
            case "flagged":
                return "Review AI-flagged documents requiring attention";
            case "clients":
                return "Manage your client portfolio";
            case "vat-returns":
                return "Track VAT return deadlines";
            default:
                return "Track client documents and VAT returns";
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

    return (
        <div className="flex h-screen bg-[#F4F5F7] overflow-hidden">
            {/* Sidebar */}
            <Sidebar
                activeItem={activeNav}
                clientCount={metrics.totalClients}
                vatDueCount={metrics.vatReturnsDue}
                flaggedCount={flaggedClientsCount}
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

                    {/* Clients View */}
                    {activeNav === "clients" && (
                        <div className="animate-fade-in-up">
                            <ClientTable
                                data={filteredClients}
                                onRowClick={handleRowClick}
                                selectedId={selectedClient?.id}
                            />
                        </div>
                    )}

                    {/* VAT Returns View - placeholder */}
                    {activeNav === "vat-returns" && (
                        <div className="animate-fade-in-up bg-white border border-[#DFE1E6] rounded p-8 text-center">
                            <p className="text-[#5E6C84]">VAT Returns view coming soon</p>
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
                            <div className="p-1.5 bg-[#0052CC] rounded">
                                <SparkleIcon size="sm" className="text-white" />
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
                <button
                    onClick={() => setShowAIChat(true)}
                    className="fixed bottom-4 right-4 p-2.5 bg-[#0052CC] text-white rounded-full shadow-md hover:bg-[#0747A6] hover:shadow-lg transition-all duration-150 z-40"
                    title="Open AI Assistant"
                >
                    <SparkleIcon size="sm" />
                </button>
            )}
        </div>
    );
}
