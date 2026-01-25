"use client";

import React, { useState } from "react";
import { ChevronDownIcon, ChevronRightIcon, MoreHorizontalIcon } from "./icons/AccountantIcons";
import { ClientFlowIndicator, getClientStage } from "./ClientFlowDiagram";

// Client data type for VAT compliance
export interface ClientRow {
    id: string;
    clientName: string;
    email: string;
    entityType: string;
    vatScheme: string;
    vatPeriodLabel: string;
    vatPeriodId?: number;
    vatPeriodStatus?: string;
    vatPeriodEnd: Date;
    documentsUploaded: number;
    documentsRequired: number;
    hasBankConnection: boolean;
    status: "needs_attention" | "in_progress" | "complete";
    updatedAt: Date;
    // Validation status fields
    hasFailedValidations?: boolean;
    hasPendingReviews?: boolean;
    failedValidationCount?: number;
}

interface ClientTableProps {
    data: ClientRow[];
    onRowClick?: (client: ClientRow) => void;
    selectedId?: string;
    onDeleteClient?: (clientId: string) => void;
}

// Status badge component - Jira lozenge style
function StatusIndicator({ uploaded, required }: { uploaded: number; required: number }) {
    const percentage = required > 0 ? (uploaded / required) * 100 : 0;
    let bgColor = "#FFEBE6";
    let textColor = "#BF2600";
    let label = "Missing";

    if (percentage === 100) {
        bgColor = "#E3FCEF";
        textColor = "#006644";
        label = "Complete";
    } else if (percentage >= 50) {
        bgColor = "#FFFAE6";
        textColor = "#974F0C";
        label = "Partial";
    }

    return (
        <span
            className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-semibold uppercase tracking-wide"
            style={{ backgroundColor: bgColor, color: textColor }}
        >
            <span>{uploaded}/{required}</span>
        </span>
    );
}

// Bank connection indicator
function BankIndicator({ connected }: { connected: boolean }) {
    return (
        <span className={`flex items-center gap-1.5 text-[13px] ${connected ? "text-[#006644]" : "text-[#97A0AF]"}`}>
            <span
                className={`w-2 h-2 rounded-full ${connected ? "bg-[#36B37E]" : "bg-[#DFE1E6]"}`}
            />
            {connected ? "Connected" : "Not linked"}
        </span>
    );
}

// Entity type badge - Color coded by type
function EntityBadge({ type }: { type: string }) {
    const config: Record<string, { label: string; bg: string; color: string }> = {
        sole_trader: { label: "SOLE TRADER", bg: "#E3FCEF", color: "#006644" },
        partnership: { label: "PARTNERSHIP", bg: "#DEEBFF", color: "#0747A6" },
        llc: { label: "LLC", bg: "#EAE6FF", color: "#403294" },
        corporation: { label: "CORPORATION", bg: "#FFEBE6", color: "#BF2600" },
        limited_company: { label: "LTD CO", bg: "#FFFAE6", color: "#974F0C" },
    };

    const { label, bg, color } = config[type] || { label: type.toUpperCase(), bg: "#EBECF0", color: "#42526E" };

    return (
        <span
            className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wide"
            style={{ backgroundColor: bg, color }}
        >
            {label}
        </span>
    );
}

// Stage header component - Jira-like swimlane
function StageHeader({
    title,
    count,
    isExpanded,
    onToggle,
    dotColor,
}: {
    title: string;
    count: number;
    isExpanded: boolean;
    onToggle: () => void;
    dotColor: string;
}) {
    return (
        <button
            onClick={onToggle}
            className="w-full flex items-center gap-3 px-4 py-2.5 bg-[#F4F5F7] hover:bg-[#EBECF0] transition-colors border-b border-[#DFE1E6]"
        >
            <span
                className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: dotColor }}
            />
            <span className="font-semibold text-[13px] text-[#172B4D]">{title}</span>
            <span className="text-[12px] text-[#5E6C84] font-medium">{count}</span>
            <span className="ml-auto text-[#6B778C]">
                {isExpanded ? <ChevronDownIcon size="sm" /> : <ChevronRightIcon size="sm" />}
            </span>
        </button>
    );
}

export function ClientTable({ data, onRowClick, selectedId, onDeleteClient }: ClientTableProps) {
    const [expandedStages, setExpandedStages] = useState({
        needs_attention: true,
        in_progress: true,
        complete: true,
    });
    const [menuOpenId, setMenuOpenId] = useState<string | null>(null);

    const toggleStage = (stage: keyof typeof expandedStages) => {
        setExpandedStages((prev) => ({ ...prev, [stage]: !prev[stage] }));
    };

    // Group data by status
    const groupedData = {
        needs_attention: data.filter((c) => c.status === "needs_attention"),
        in_progress: data.filter((c) => c.status === "in_progress"),
        complete: data.filter((c) => c.status === "complete"),
    };

    const stages = [
        { key: "needs_attention" as const, title: "Needs Attention", dotColor: "#DE350B" },
        { key: "in_progress" as const, title: "In Progress", dotColor: "#FF991F" },
        { key: "complete" as const, title: "Complete", dotColor: "#36B37E" },
    ];

    const formatDate = (date: Date) => {
        return new Date(date).toLocaleDateString("en-GB", {
            day: "numeric",
            month: "short",
            year: "numeric",
        });
    };

    if (data.length === 0) {
        return (
            <div className="bg-white rounded border border-[#DFE1E6] p-12 text-center">
                <div className="text-[#97A0AF] mb-3">
                    <svg className="w-12 h-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                </div>
                <h3 className="text-base font-semibold text-[#172B4D] mb-1">No clients yet</h3>
                <p className="text-[13px] text-[#5E6C84]">Add your first client to get started with VAT compliance tracking.</p>
            </div>
        );
    }

    return (
        <div className="bg-white rounded border border-[#DFE1E6] overflow-hidden">
            {/* Table Header */}
            <div className="grid grid-cols-[1fr_90px_110px_140px_90px_80px_36px] gap-0 bg-[#FAFBFC] border-b-2 border-[#DFE1E6]">
                <div className="px-4 py-2.5 text-[11px] font-semibold text-[#5E6C84] uppercase tracking-wider">
                    Client
                </div>
                <div className="px-4 py-2.5 text-[11px] font-semibold text-[#5E6C84] uppercase tracking-wider">
                    Type
                </div>
                <div className="px-4 py-2.5 text-[11px] font-semibold text-[#5E6C84] uppercase tracking-wider">
                    VAT Period
                </div>
                <div className="px-4 py-2.5 text-[11px] font-semibold text-[#5E6C84] uppercase tracking-wider">
                    Stage
                </div>
                <div className="px-4 py-2.5 text-[11px] font-semibold text-[#5E6C84] uppercase tracking-wider">
                    Docs
                </div>
                <div className="px-4 py-2.5 text-[11px] font-semibold text-[#5E6C84] uppercase tracking-wider">
                    Bank
                </div>
                <div className="w-[36px]" />
            </div>

            {/* Grouped Rows */}
            <div>
                {stages.map(({ key, title, dotColor }) => {
                    const stageData = groupedData[key];
                    if (stageData.length === 0) return null;

                    return (
                        <div key={key}>
                            <StageHeader
                                title={title}
                                count={stageData.length}
                                isExpanded={expandedStages[key]}
                                onToggle={() => toggleStage(key)}
                                dotColor={dotColor}
                            />

                            {expandedStages[key] && (
                                <div>
                                    {stageData.map((client) => (
                                        <div
                                            key={client.id}
                                            onClick={() => {
                                                setMenuOpenId(null);
                                                onRowClick?.(client);
                                            }}
                                            className={`
                                                grid grid-cols-[1fr_90px_110px_140px_90px_80px_36px] gap-0
                                                hover:bg-[#F4F5F7] cursor-pointer transition-colors duration-100
                                                border-b border-[#EBECF0]
                                                ${selectedId === client.id ? "bg-[#DEEBFF] hover:bg-[#DEEBFF]" : ""}
                                            `}
                                        >
                                            {/* Client Name */}
                                            <div className="px-4 py-3">
                                                <p className="text-[13px] font-medium text-[#172B4D] truncate">
                                                    {client.clientName}
                                                </p>
                                                <p className="text-[11px] text-[#5E6C84] truncate">
                                                    {client.email}
                                                </p>
                                            </div>

                                            {/* Entity Type */}
                                            <div className="px-4 py-3 flex items-center">
                                                <EntityBadge type={client.entityType} />
                                            </div>

                                            {/* VAT Period */}
                                            <div className="px-4 py-3">
                                                <p className="text-[13px] text-[#172B4D]">{client.vatPeriodLabel}</p>
                                                <p className="text-[11px] text-[#5E6C84]">
                                                    {formatDate(client.vatPeriodEnd)}
                                                </p>
                                            </div>

                                            {/* Stage */}
                                            <div className="px-4 py-3 flex items-center">
                                                <ClientFlowIndicator
                                                    currentStage={getClientStage(client)}
                                                    hasFailedValidations={client.hasFailedValidations}
                                                    hasPendingReviews={client.hasPendingReviews}
                                                />
                                            </div>

                                            {/* Documents */}
                                            <div className="px-4 py-3 flex items-center">
                                                <StatusIndicator
                                                    uploaded={client.documentsUploaded}
                                                    required={client.documentsRequired}
                                                />
                                            </div>

                                            {/* Bank Connection */}
                                            <div className="px-4 py-3 flex items-center">
                                                <BankIndicator connected={client.hasBankConnection} />
                                            </div>

                                            {/* More actions */}
                                            <div className="px-1 py-3 flex items-center justify-center">
                                                <div className="relative">
                                                    <button
                                                        onClick={(event) => {
                                                            event.stopPropagation();
                                                            setMenuOpenId((prev) => (prev === client.id ? null : client.id));
                                                        }}
                                                        aria-haspopup="true"
                                                        aria-expanded={menuOpenId === client.id}
                                                        className="p-1.5 rounded hover:bg-[#EBECF0] text-[#6B778C] hover:text-[#172B4D] transition-colors"
                                                    >
                                                        <MoreHorizontalIcon size="sm" />
                                                    </button>
                                                    {menuOpenId === client.id && (
                                                        <div
                                                            className="absolute right-0 z-30 mt-2 w-36 rounded-md border border-[#DFE1E6] bg-white shadow-lg ring-1 ring-black/5"
                                                            onClick={(e) => e.stopPropagation()}
                                                        >
                                                            <button
                                                                onClick={() => {
                                                                    onDeleteClient?.(client.id);
                                                                    setMenuOpenId(null);
                                                                }}
                                                                className="w-full px-3 py-2 text-left text-sm font-semibold text-red-600 hover:bg-slate-50 transition-colors"
                                                            >
                                                                Delete client
                                                            </button>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
