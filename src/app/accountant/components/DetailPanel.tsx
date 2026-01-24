"use client";

import React from "react";
import type { ClientRow } from "./ClientTable";
import {
    CloseIcon,
    CalendarIcon,
    MailIcon,
} from "./icons/AccountantIcons";

interface ChecklistItemData {
    id: string;
    title: string;
    status: "missing" | "uploaded" | "unknown";
    required: boolean;
}

interface DetailPanelProps {
    client: ClientRow | null;
    isOpen: boolean;
    onClose: () => void;
    checklistItems?: ChecklistItemData[];
    onSendReminder?: (clientId: string) => void;
    onViewOnboarding?: (clientId: string) => void;
}

// Entity type labels
const entityLabels: Record<string, string> = {
    sole_trader: "Sole Trader",
    partnership: "Partnership",
    llc: "LLC",
    corporation: "Corporation",
    limited_company: "Limited Company",
};

// VAT scheme labels
const vatSchemeLabels: Record<string, string> = {
    standard: "Standard VAT",
    flat_rate: "Flat Rate Scheme",
    cash_accounting: "Cash Accounting",
    annual_accounting: "Annual Accounting",
};

// Status indicator for document
function DocStatus({ status }: { status: string }) {
    const config = {
        uploaded: { bg: "bg-emerald-500", label: "Uploaded" },
        missing: { bg: "bg-red-500", label: "Missing" },
        unknown: { bg: "bg-slate-400", label: "Pending" },
    }[status] || { bg: "bg-slate-400", label: status };

    return (
        <span className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${config.bg}`} />
            <span className="text-xs text-slate-500">{config.label}</span>
        </span>
    );
}

// Chevron icon
function ChevronRightIcon({ size }: { size: string }) {
    const sizeClass = size === "sm" ? "w-4 h-4" : "w-5 h-5";
    return (
        <svg
            className={sizeClass}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <polyline points="9 18 15 12 9 6" />
        </svg>
    );
}

// Link icon
function LinkIcon({ size }: { size: string }) {
    const sizeClass = size === "sm" ? "w-4 h-4" : "w-5 h-5";
    return (
        <svg className={sizeClass} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
        </svg>
    );
}

// Building icon
function BuildingIcon({ size }: { size: string }) {
    const sizeClass = size === "sm" ? "w-4 h-4" : "w-5 h-5";
    return (
        <svg className={sizeClass} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
            <rect x="4" y="2" width="16" height="20" rx="2" ry="2" />
            <path d="M9 22v-4h6v4" />
            <path d="M8 6h.01" />
            <path d="M16 6h.01" />
            <path d="M12 6h.01" />
            <path d="M12 10h.01" />
            <path d="M12 14h.01" />
            <path d="M16 10h.01" />
            <path d="M16 14h.01" />
            <path d="M8 10h.01" />
            <path d="M8 14h.01" />
        </svg>
    );
}

// Bank icon
function BankIcon({ size }: { size: string }) {
    const sizeClass = size === "sm" ? "w-4 h-4" : "w-5 h-5";
    return (
        <svg className={sizeClass} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="10" width="18" height="11" rx="2" />
            <path d="M12 2L2 10h20L12 2z" />
        </svg>
    );
}

export function DetailPanel({
    client,
    isOpen,
    onClose,
    checklistItems = [],
    onSendReminder,
    onViewOnboarding,
}: DetailPanelProps) {
    const formatDate = (date: Date) => {
        return new Date(date).toLocaleDateString("en-GB", {
            day: "numeric",
            month: "short",
            year: "numeric",
        });
    };

    return (
        <>
            {/* Backdrop */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/20 z-40 animate-fade-in"
                    onClick={onClose}
                />
            )}

            {/* Panel */}
            <div
                className={`
                    fixed right-0 top-0 h-full w-[420px] bg-white border-l border-slate-200 shadow-2xl z-50
                    transform transition-transform duration-300 ease-out
                    ${isOpen ? "translate-x-0" : "translate-x-full"}
                `}
            >
                {client && (
                    <div className="h-full flex flex-col">
                        {/* Header */}
                        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
                            <div className="flex items-center gap-2 text-sm text-slate-500">
                                <span className="text-violet-600 font-medium">Clients</span>
                                <ChevronRightIcon size="sm" />
                                <span className="text-slate-900 font-semibold truncate max-w-[200px]">
                                    {client.clientName}
                                </span>
                            </div>
                            <button
                                onClick={onClose}
                                className="p-2 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors"
                            >
                                <CloseIcon size="md" />
                            </button>
                        </div>

                        {/* Content */}
                        <div className="flex-1 overflow-y-auto custom-scrollbar px-6 py-5">
                            {/* Client Name & Email */}
                            <h2 className="text-xl font-bold text-slate-900 mb-1">
                                {client.clientName}
                            </h2>
                            <p className="text-sm text-slate-500 mb-6">{client.email}</p>

                            {/* Quick Info Grid */}
                            <div className="grid grid-cols-2 gap-4 mb-6">
                                <div className="bg-slate-50 rounded-lg p-3">
                                    <div className="flex items-center gap-2 text-slate-400 mb-1">
                                        <BuildingIcon size="sm" />
                                        <span className="text-xs font-medium">Entity Type</span>
                                    </div>
                                    <p className="text-sm font-semibold text-slate-900">
                                        {entityLabels[client.entityType] || client.entityType}
                                    </p>
                                </div>
                                <div className="bg-slate-50 rounded-lg p-3">
                                    <div className="flex items-center gap-2 text-slate-400 mb-1">
                                        <CalendarIcon size="sm" />
                                        <span className="text-xs font-medium">VAT Period</span>
                                    </div>
                                    <p className="text-sm font-semibold text-slate-900">
                                        {client.vatPeriodLabel}
                                    </p>
                                </div>
                                <div className="bg-slate-50 rounded-lg p-3">
                                    <div className="flex items-center gap-2 text-slate-400 mb-1">
                                        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                                            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                                        </svg>
                                        <span className="text-xs font-medium">VAT Scheme</span>
                                    </div>
                                    <p className="text-sm font-semibold text-slate-900">
                                        {vatSchemeLabels[client.vatScheme] || client.vatScheme}
                                    </p>
                                </div>
                                <div className="bg-slate-50 rounded-lg p-3">
                                    <div className="flex items-center gap-2 text-slate-400 mb-1">
                                        <CalendarIcon size="sm" />
                                        <span className="text-xs font-medium">Period End</span>
                                    </div>
                                    <p className="text-sm font-semibold text-slate-900">
                                        {formatDate(client.vatPeriodEnd)}
                                    </p>
                                </div>
                            </div>

                            {/* Bank Connection Status */}
                            <div className="mb-6">
                                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                                    Bank Connection
                                </h3>
                                <div className={`flex items-center gap-3 p-3 rounded-lg ${client.hasBankConnection ? "bg-emerald-50" : "bg-amber-50"}`}>
                                    <BankIcon size="md" />
                                    <div className="flex-1">
                                        <p className={`text-sm font-medium ${client.hasBankConnection ? "text-emerald-700" : "text-amber-700"}`}>
                                            {client.hasBankConnection ? "Bank account connected" : "No bank account connected"}
                                        </p>
                                        <p className="text-xs text-slate-500">
                                            {client.hasBankConnection
                                                ? "Transactions can be synced automatically"
                                                : "Client needs to connect their bank"
                                            }
                                        </p>
                                    </div>
                                </div>
                            </div>

                            {/* Document Checklist */}
                            <div className="mb-6">
                                <div className="flex items-center justify-between mb-3">
                                    <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                                        Document Checklist
                                    </h3>
                                    <span className="text-xs text-slate-500">
                                        {client.documentsUploaded}/{client.documentsRequired} complete
                                    </span>
                                </div>

                                {checklistItems.length > 0 ? (
                                    <div className="space-y-2">
                                        {checklistItems.map((item) => (
                                            <div
                                                key={item.id}
                                                className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"
                                            >
                                                <div className="flex items-center gap-3">
                                                    <div
                                                        className={`w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 ${
                                                            item.status === "uploaded"
                                                                ? "bg-emerald-500 border-emerald-500"
                                                                : "border-slate-300"
                                                        }`}
                                                    >
                                                        {item.status === "uploaded" && (
                                                            <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                                            </svg>
                                                        )}
                                                    </div>
                                                    <span className={`text-sm ${item.status === "uploaded" ? "text-slate-500" : "text-slate-700"}`}>
                                                        {item.title}
                                                    </span>
                                                </div>
                                                <DocStatus status={item.status} />
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="p-4 bg-slate-50 rounded-lg text-center">
                                        <p className="text-sm text-slate-500">
                                            {client.documentsRequired > 0
                                                ? `${client.documentsUploaded} of ${client.documentsRequired} documents uploaded`
                                                : "No documents required"
                                            }
                                        </p>
                                    </div>
                                )}
                            </div>

                            {/* Last Updated */}
                            <div className="text-xs text-slate-400">
                                Last updated: {formatDate(client.updatedAt)}
                            </div>
                        </div>

                        {/* Footer Actions */}
                        <div className="px-6 py-4 border-t border-slate-200 bg-slate-50">
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => onSendReminder?.(client.id)}
                                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-violet-600 text-white text-sm font-medium rounded-lg hover:bg-violet-700 transition-all"
                                >
                                    <MailIcon size="sm" />
                                    <span>Send Reminder</span>
                                </button>
                                <button
                                    onClick={() => onViewOnboarding?.(client.id)}
                                    className="flex items-center justify-center gap-2 px-4 py-2.5 border border-slate-200 text-slate-700 text-sm font-medium rounded-lg hover:bg-white transition-all"
                                >
                                    <LinkIcon size="sm" />
                                    <span>Onboarding Link</span>
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </>
    );
}
