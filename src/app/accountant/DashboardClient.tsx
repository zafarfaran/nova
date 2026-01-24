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
import { SparkleIcon, CloseIcon } from "./components/icons/AccountantIcons";
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
        setTimeout(() => setSelectedClient(null), 300);
    };

    const handleSendReminder = (clientId: string) => {
        console.log("Send reminder to client:", clientId);
        // TODO: Implement reminder functionality
    };

    const handleViewOnboarding = (clientId: string) => {
        // Open onboarding link in new tab
        window.open(`/onboard/${clientId}`, "_blank");
    };

    const handleAddNewClient = () => {
        // TODO: Navigate to new client form or open modal
        console.log("Add new client");
    };

    return (
        <div className="flex h-screen bg-slate-100 overflow-hidden">
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
                    <div className="animate-fade-in-up" style={{ animationDelay: "200ms" }}>
                        <ClientTable
                            data={filteredClients}
                            onRowClick={handleRowClick}
                            selectedId={selectedClient?.id}
                        />
                    </div>
                </main>
            </div>

            {/* Detail Panel */}
            <DetailPanel
                client={selectedClient}
                isOpen={showDetailPanel}
                onClose={handleCloseDetail}
                onSendReminder={handleSendReminder}
                onViewOnboarding={handleViewOnboarding}
            />

            {/* AI Chat Modal */}
            {showAIChat && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                    {/* Backdrop */}
                    <div
                        className="absolute inset-0 bg-black/50 backdrop-blur-sm animate-fade-in"
                        onClick={() => setShowAIChat(false)}
                    />

                    {/* Modal */}
                    <div className="relative w-full max-w-4xl h-[80vh] bg-white rounded-2xl shadow-2xl overflow-hidden animate-scale-in">
                        {/* Header */}
                        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-gradient-to-r from-violet-600 to-purple-600">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-white/20 rounded-lg">
                                    <SparkleIcon size="md" className="text-white" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-bold text-white">AI Assistant</h2>
                                    <p className="text-sm text-violet-200">
                                        Ask me anything about your clients
                                    </p>
                                </div>
                            </div>
                            <button
                                onClick={() => setShowAIChat(false)}
                                className="p-2 rounded-lg hover:bg-white/10 text-white transition-colors"
                            >
                                <CloseIcon size="md" />
                            </button>
                        </div>

                        {/* Chat Content */}
                        <div className="h-[calc(100%-72px)]">
                            <AIChat />
                        </div>
                    </div>
                </div>
            )}

            {/* Floating AI Button (when chat is closed) */}
            {!showAIChat && (
                <button
                    onClick={() => setShowAIChat(true)}
                    className="fixed bottom-6 right-6 p-4 bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-full shadow-lg shadow-violet-500/30 hover:shadow-xl hover:shadow-violet-500/40 hover:scale-105 transition-all duration-200 z-40"
                    title="Open AI Assistant"
                >
                    <SparkleIcon size="lg" />
                </button>
            )}
        </div>
    );
}
