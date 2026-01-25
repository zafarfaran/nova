"use client";

import React from "react";
import type { ClientRow } from "./ClientTable";
import {
    CloseIcon,
    CalendarIcon,
    MailIcon,
} from "./icons/AccountantIcons";
import { ClientFlowDiagram, getClientStage } from "./ClientFlowDiagram";
import { DocumentVerification } from "./DocumentVerification";

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
        uploaded: { bg: "#E3FCEF", color: "#006644", label: "Done" },
        missing: { bg: "#FFEBE6", color: "#BF2600", label: "Missing" },
        unknown: { bg: "#F4F5F7", color: "#5E6C84", label: "Pending" },
    }[status] || { bg: "#F4F5F7", color: "#5E6C84", label: status };

    return (
        <span
            className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase"
            style={{ backgroundColor: config.bg, color: config.color }}
        >
            {config.label}
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

    if (!isOpen) return null;

    return (
        <>
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black/20 z-40 animate-fade-in"
                onClick={onClose}
            />

            {/* Panel */}
            <div
                className="fixed right-0 top-0 h-full w-[400px] bg-white border-l border-[#DFE1E6] shadow-xl z-50 animate-slide-in-right"
            >
                {client && (
                    <div className="h-full flex flex-col">
                        {/* Header */}
                        <div className="flex items-center justify-between px-5 py-3 border-b border-[#DFE1E6] bg-[#FAFBFC]">
                            <div className="flex items-center gap-2 text-[13px] text-[#5E6C84]">
                                <span className="text-[#0052CC] font-medium">Clients</span>
                                <ChevronRightIcon size="sm" />
                                <span className="text-[#172B4D] font-semibold truncate max-w-[200px]">
                                    {client.clientName}
                                </span>
                            </div>
                            <button
                                onClick={onClose}
                                className="p-1.5 rounded hover:bg-[#EBECF0] text-[#6B778C] hover:text-[#172B4D] transition-colors"
                            >
                                <CloseIcon size="md" />
                            </button>
                        </div>

                        {/* Content */}
                        <div className="flex-1 overflow-y-auto custom-scrollbar px-5 py-5">
                            {/* Client Name & Email */}
                            <h2 className="text-lg font-semibold text-[#172B4D] mb-1">
                                {client.clientName}
                            </h2>
                            <p className="text-[13px] text-[#5E6C84] mb-4">{client.email}</p>

                            {/* Flow Diagram */}
                            <div className="mb-5 p-4 bg-[#FAFBFC] rounded border border-[#DFE1E6]">
                                <h3 className="text-[11px] font-semibold text-[#5E6C84] uppercase tracking-wider mb-4">
                                    Client Journey
                                </h3>
                                <ClientFlowDiagram
                                    currentStage={getClientStage(client)}
                                    variant="vertical"
                                />
                            </div>

                            {/* Quick Info Grid */}
                            <div className="grid grid-cols-2 gap-3 mb-5">
                                <div className="bg-[#F4F5F7] rounded p-3">
                                    <div className="flex items-center gap-2 text-[#6B778C] mb-1">
                                        <BuildingIcon size="sm" />
                                        <span className="text-[11px] font-medium uppercase tracking-wide">Entity</span>
                                    </div>
                                    <p className="text-[13px] font-medium text-[#172B4D]">
                                        {entityLabels[client.entityType] || client.entityType}
                                    </p>
                                </div>
                                <div className="bg-[#F4F5F7] rounded p-3">
                                    <div className="flex items-center gap-2 text-[#6B778C] mb-1">
                                        <CalendarIcon size="sm" />
                                        <span className="text-[11px] font-medium uppercase tracking-wide">Period</span>
                                    </div>
                                    <p className="text-[13px] font-medium text-[#172B4D]">
                                        {client.vatPeriodLabel}
                                    </p>
                                </div>
                                <div className="bg-[#F4F5F7] rounded p-3">
                                    <div className="flex items-center gap-2 text-[#6B778C] mb-1">
                                        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                                            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                                        </svg>
                                        <span className="text-[11px] font-medium uppercase tracking-wide">Scheme</span>
                                    </div>
                                    <p className="text-[13px] font-medium text-[#172B4D]">
                                        {vatSchemeLabels[client.vatScheme] || client.vatScheme}
                                    </p>
                                </div>
                                <div className="bg-[#F4F5F7] rounded p-3">
                                    <div className="flex items-center gap-2 text-[#6B778C] mb-1">
                                        <CalendarIcon size="sm" />
                                        <span className="text-[11px] font-medium uppercase tracking-wide">Due Date</span>
                                    </div>
                                    <p className="text-[13px] font-medium text-[#172B4D]">
                                        {formatDate(client.vatPeriodEnd)}
                                    </p>
                                </div>
                            </div>

                            {/* Bank Connection Status */}
                            <div className="mb-5">
                                <h3 className="text-[11px] font-semibold text-[#5E6C84] uppercase tracking-wider mb-2">
                                    Bank Connection
                                </h3>
                                <div
                                    className={`flex items-center gap-3 p-3 rounded border ${
                                        client.hasBankConnection
                                            ? "bg-[#E3FCEF] border-[#ABF5D1]"
                                            : "bg-[#FFFAE6] border-[#FFE380]"
                                    }`}
                                >
                                    <BankIcon size="md" />
                                    <div className="flex-1">
                                        <p className={`text-[13px] font-medium ${
                                            client.hasBankConnection ? "text-[#006644]" : "text-[#974F0C]"
                                        }`}>
                                            {client.hasBankConnection ? "Bank account connected" : "No bank account connected"}
                                        </p>
                                        <p className="text-[11px] text-[#5E6C84]">
                                            {client.hasBankConnection
                                                ? "Transactions sync automatically"
                                                : "Client needs to connect their bank"
                                            }
                                        </p>
                                    </div>
                                </div>
                            </div>

                            {/* Document Checklist */}
                            <div className="mb-5">
                                <div className="flex items-center justify-between mb-2">
                                    <h3 className="text-[11px] font-semibold text-[#5E6C84] uppercase tracking-wider">
                                        Documents
                                    </h3>
                                    <span className="text-[11px] text-[#5E6C84] font-medium">
                                        {client.documentsUploaded}/{client.documentsRequired}
                                    </span>
                                </div>

                                {/* Progress bar */}
                                <div className="h-1.5 bg-[#DFE1E6] rounded-full mb-3 overflow-hidden">
                                    <div
                                        className="h-full rounded-full transition-all duration-300"
                                        style={{
                                            width: `${client.documentsRequired > 0 ? (client.documentsUploaded / client.documentsRequired) * 100 : 0}%`,
                                            backgroundColor: client.documentsUploaded === client.documentsRequired ? '#36B37E' : '#0052CC'
                                        }}
                                    />
                                </div>

                                {checklistItems.length > 0 ? (
                                    <div className="space-y-2">
                                        {checklistItems.map((item) => (
                                            <div
                                                key={item.id}
                                                className="flex items-center justify-between p-2.5 bg-[#F4F5F7] rounded"
                                            >
                                                <div className="flex items-center gap-2.5">
                                                    <div
                                                        className={`w-4 h-4 rounded border flex items-center justify-center flex-shrink-0 ${
                                                            item.status === "uploaded"
                                                                ? "bg-[#36B37E] border-[#36B37E]"
                                                                : "border-[#C1C7D0] bg-white"
                                                        }`}
                                                    >
                                                        {item.status === "uploaded" && (
                                                            <svg className="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                                            </svg>
                                                        )}
                                                    </div>
                                                    <span className={`text-[13px] ${item.status === "uploaded" ? "text-[#5E6C84]" : "text-[#172B4D]"}`}>
                                                        {item.title}
                                                    </span>
                                                </div>
                                                <DocStatus status={item.status} />
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="p-4 bg-[#F4F5F7] rounded text-center">
                                        <p className="text-[13px] text-[#5E6C84]">
                                            {client.documentsRequired > 0
                                                ? `${client.documentsUploaded} of ${client.documentsRequired} documents uploaded`
                                                : "No documents required"
                                            }
                                        </p>
                                    </div>
                                )}
                            </div>

                            {/* Document Verification */}
                            <div className="mb-5 p-4 bg-[#FAFBFC] rounded border border-[#DFE1E6]">
                                <DocumentVerification clientId={client.id} />
                            </div>

                            {/* Last Updated */}
                            <div className="text-[11px] text-[#97A0AF]">
                                Last updated: {formatDate(client.updatedAt)}
                            </div>
                        </div>

                        {/* Footer Actions */}
                        <div className="px-5 py-4 border-t border-[#DFE1E6] bg-[#FAFBFC]">
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => onSendReminder?.(client.id)}
                                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-[#0052CC] text-white text-[13px] font-medium rounded hover:bg-[#0747A6] transition-colors"
                                >
                                    <MailIcon size="sm" />
                                    <span>Send Reminder</span>
                                </button>
                                <button
                                    onClick={() => onViewOnboarding?.(client.id)}
                                    className="flex items-center justify-center gap-2 px-4 py-2 bg-[#F4F5F7] text-[#172B4D] text-[13px] font-medium rounded hover:bg-[#EBECF0] transition-colors"
                                >
                                    <LinkIcon size="sm" />
                                    <span>Link</span>
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </>
    );
}
