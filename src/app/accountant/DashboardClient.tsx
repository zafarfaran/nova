"use client";

import React, { useState, useMemo } from "react";
import { Sidebar } from "./components/Sidebar";
import { TopHeader } from "./components/TopHeader";
import { ClientTable } from "./components/ClientTable";
import type { ClientRow } from "./components/ClientTable";
import { DetailPanel } from "./components/DetailPanel";
import { QuickMetrics } from "./components/QuickMetrics";
import type { DashboardMetrics } from "./components/QuickMetrics";
import { AIChat } from "./AIChat";
import { SparkleIcon, ChevronRightIcon } from "./components/icons/AccountantIcons";
import "./styles/dashboard.css";

interface AccountantDashboardClientProps {
    clients: ClientRow[];
    metrics: DashboardMetrics;
}

export function AccountantDashboardClient({ clients, metrics }: AccountantDashboardClientProps) {
    const [selectedClient, setSelectedClient] = useState<ClientRow | null>(null);
    const [showDetailPanel, setShowDetailPanel] = useState(false);
    const [showAIChat, setShowAIChat] = useState(false);
    const [activeNav, setActiveNav] = useState("dashboard");
    const [searchQuery, setSearchQuery] = useState("");

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
                    title="VAT Compliance Dashboard"
                    subtitle="Track client documents and VAT returns"
                    onSearch={setSearchQuery}
                    onAddNew={handleAddNewClient}
                />

                {/* Scrollable Content Area */}
                <main className="flex-1 overflow-auto p-6 custom-scrollbar">
                    {/* Quick Metrics */}
                    <div className="mb-6">
                        <QuickMetrics
                            metrics={metrics}
                            onMetricClick={(metricId) => console.log("Metric clicked:", metricId)}
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
