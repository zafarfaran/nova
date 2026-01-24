"use client";

import React, { useState } from "react";
import { ChevronDownIcon, ChevronRightIcon, MoreHorizontalIcon } from "./icons/AccountantIcons";

// Client data type for VAT compliance
export interface ClientRow {
    id: string;
    clientName: string;
    email: string;
    entityType: string;
    vatScheme: string;
    vatPeriodLabel: string;
    vatPeriodEnd: Date;
    documentsUploaded: number;
    documentsRequired: number;
    hasBankConnection: boolean;
    status: "needs_attention" | "in_progress" | "complete";
    updatedAt: Date;
}

interface ClientTableProps {
    data: ClientRow[];
    onRowClick?: (client: ClientRow) => void;
    selectedId?: string;
}

// Status badge component
function StatusIndicator({ uploaded, required }: { uploaded: number; required: number }) {
    const percentage = required > 0 ? (uploaded / required) * 100 : 0;
    let colorClass = "bg-red-100 text-red-700";
    if (percentage === 100) {
        colorClass = "bg-emerald-100 text-emerald-700";
    } else if (percentage >= 50) {
        colorClass = "bg-amber-100 text-amber-700";
    }

    return (
        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${colorClass}`}>
            {uploaded}/{required} docs
        </span>
    );
}

// Bank connection indicator
function BankIndicator({ connected }: { connected: boolean }) {
    return (
        <span className={`flex items-center gap-1.5 text-sm ${connected ? "text-emerald-600" : "text-slate-400"}`}>
            <span className={`w-2 h-2 rounded-full ${connected ? "bg-emerald-500" : "bg-slate-300"}`} />
            {connected ? "Connected" : "Not connected"}
        </span>
    );
}

// Entity type badge
function EntityBadge({ type }: { type: string }) {
    const labels: Record<string, string> = {
        sole_trader: "Sole Trader",
        partnership: "Partnership",
        llc: "LLC",
        corporation: "Corporation",
        limited_company: "Limited Co.",
    };
    return (
        <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-xs font-medium">
            {labels[type] || type}
        </span>
    );
}

// Stage header component
function StageHeader({
    title,
    count,
    isExpanded,
    onToggle,
    color,
}: {
    title: string;
    count: number;
    isExpanded: boolean;
    onToggle: () => void;
    color: string;
}) {
    return (
        <button
            onClick={onToggle}
            className="w-full flex items-center gap-3 px-4 py-3 bg-slate-50 hover:bg-slate-100 transition-colors border-b border-slate-200"
        >
            <span className={`w-3 h-3 rounded-full ${color}`} />
            <span className="font-semibold text-slate-900">{title}</span>
            <span className="text-sm text-slate-500">({count})</span>
            <span className="ml-auto text-slate-400">
                {isExpanded ? <ChevronDownIcon size="sm" /> : <ChevronRightIcon size="sm" />}
            </span>
        </button>
    );
}

export function ClientTable({ data, onRowClick, selectedId }: ClientTableProps) {
    const [expandedStages, setExpandedStages] = useState({
        needs_attention: true,
        in_progress: true,
        complete: true,
    });

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
        { key: "needs_attention" as const, title: "Needs Attention", color: "bg-red-500" },
        { key: "in_progress" as const, title: "In Progress", color: "bg-amber-500" },
        { key: "complete" as const, title: "Complete", color: "bg-emerald-500" },
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
            <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
                <div className="text-slate-400 mb-2">
                    <svg className="w-12 h-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                </div>
                <h3 className="text-lg font-semibold text-slate-700 mb-1">No clients yet</h3>
                <p className="text-sm text-slate-500">Add your first client to get started with VAT compliance tracking.</p>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            {/* Table Header */}
            <div className="grid grid-cols-[1fr_120px_140px_120px_140px_100px_40px] gap-0 bg-slate-50 border-b border-slate-200">
                <div className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Client
                </div>
                <div className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Entity
                </div>
                <div className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    VAT Period
                </div>
                <div className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Documents
                </div>
                <div className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Bank
                </div>
                <div className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Updated
                </div>
                <div className="w-[40px]" />
            </div>

            {/* Grouped Rows */}
            <div className="divide-y divide-slate-100">
                {stages.map(({ key, title, color }) => {
                    const stageData = groupedData[key];
                    if (stageData.length === 0) return null;

                    return (
                        <div key={key}>
                            <StageHeader
                                title={title}
                                count={stageData.length}
                                isExpanded={expandedStages[key]}
                                onToggle={() => toggleStage(key)}
                                color={color}
                            />

                            {expandedStages[key] && (
                                <div className="divide-y divide-slate-50">
                                    {stageData.map((client, index) => (
                                        <div
                                            key={client.id}
                                            onClick={() => onRowClick?.(client)}
                                            className={`
                                                grid grid-cols-[1fr_120px_140px_120px_140px_100px_40px] gap-0
                                                hover:bg-slate-50 cursor-pointer transition-all duration-150
                                                ${selectedId === client.id ? "bg-violet-50 hover:bg-violet-50" : ""}
                                            `}
                                        >
                                            {/* Client Name */}
                                            <div className="px-4 py-3">
                                                <p className="text-sm font-medium text-slate-900 truncate">
                                                    {client.clientName}
                                                </p>
                                                <p className="text-xs text-slate-400 truncate">
                                                    {client.email}
                                                </p>
                                            </div>

                                            {/* Entity Type */}
                                            <div className="px-4 py-3 flex items-center">
                                                <EntityBadge type={client.entityType} />
                                            </div>

                                            {/* VAT Period */}
                                            <div className="px-4 py-3">
                                                <p className="text-sm text-slate-700">{client.vatPeriodLabel}</p>
                                                <p className="text-xs text-slate-400">
                                                    Due: {formatDate(client.vatPeriodEnd)}
                                                </p>
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

                                            {/* Updated */}
                                            <div className="px-4 py-3 flex items-center">
                                                <span className="text-sm text-slate-500">
                                                    {formatDate(client.updatedAt)}
                                                </span>
                                            </div>

                                            {/* More actions */}
                                            <div className="px-2 py-3 flex items-center justify-center">
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                    }}
                                                    className="p-1 rounded hover:bg-slate-200 text-slate-400 hover:text-slate-600 transition-colors"
                                                >
                                                    <MoreHorizontalIcon size="sm" />
                                                </button>
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
