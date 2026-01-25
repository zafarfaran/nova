"use client";

import React from "react";
import {
    ClientsIcon,
    VatIcon,
} from "./icons/AccountantIcons";

interface MetricCardProps {
    title: string;
    value: string | number;
    subtitle?: string;
    icon: React.ReactNode;
    accentColor: string;
    onClick?: () => void;
}

function MetricCard({
    title,
    value,
    subtitle,
    icon,
    accentColor,
    onClick,
}: MetricCardProps) {
    return (
        <button
            onClick={onClick}
            className="sticky-note w-full text-left group"
            style={{
                '--accent-color': accentColor
            } as React.CSSProperties}
        >
            {/* Top accent bar */}
            <div
                className="absolute top-0 left-0 right-0 h-1 rounded-t"
                style={{ backgroundColor: accentColor }}
            />

            <div className="p-5 pt-6">
                {/* Icon and value row */}
                <div className="flex items-start justify-between mb-3">
                    <div
                        className="p-2 rounded"
                        style={{ backgroundColor: `${accentColor}15` }}
                    >
                        <span style={{ color: accentColor }}>{icon}</span>
                    </div>
                </div>

                {/* Value */}
                <div className="mb-1">
                    <span className="text-[32px] font-semibold text-[#172B4D] leading-none tabular-nums">
                        {value}
                    </span>
                </div>

                {/* Label */}
                <p className="text-[12px] font-medium text-[#5E6C84] uppercase tracking-wide">
                    {title}
                </p>

                {/* Subtitle */}
                {subtitle && (
                    <p className="text-[11px] text-[#97A0AF] mt-1">
                        {subtitle}
                    </p>
                )}
            </div>
        </button>
    );
}

// Document icon component
function DocumentIcon({ size }: { size: string }) {
    const sizeClass = size === "lg" ? "w-5 h-5" : size === "md" ? "w-5 h-5" : "w-4 h-4";
    return (
        <svg className={sizeClass} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10 9 9 9 8 9" />
        </svg>
    );
}

// Bank icon component
function BankIcon({ size }: { size: string }) {
    const sizeClass = size === "lg" ? "w-5 h-5" : size === "md" ? "w-5 h-5" : "w-4 h-4";
    return (
        <svg className={sizeClass} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="10" width="18" height="11" rx="2" />
            <path d="M12 2L2 10h20L12 2z" />
            <path d="M7 21V14" />
            <path d="M12 21V14" />
            <path d="M17 21V14" />
        </svg>
    );
}

// Flag icon component for flagged documents
function FlagIcon({ size }: { size: string }) {
    const sizeClass = size === "lg" ? "w-5 h-5" : size === "md" ? "w-5 h-5" : "w-4 h-4";
    return (
        <svg className={sizeClass} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
            <line x1="4" y1="22" x2="4" y2="15" />
        </svg>
    );
}

export interface DashboardMetrics {
    totalClients: number;
    documentsPending: number;
    pendingSubtitle?: string;
    vatReturnsDue: number;
    vatSubtitle?: string;
    bankConnections: number;
    bankSubtitle?: string;
    flaggedDocuments?: number;
    flaggedSubtitle?: string;
}

interface QuickMetricsProps {
    metrics: DashboardMetrics;
    onMetricClick?: (metricId: string) => void;
}

export function QuickMetrics({ metrics, onMetricClick }: QuickMetricsProps) {
    const metricCards = [
        {
            id: "total-clients",
            title: "Total Clients",
            value: metrics.totalClients,
            subtitle: "Active accounts",
            icon: <ClientsIcon size="md" />,
            accentColor: "#0052CC", // Jira blue
        },
        {
            id: "documents-pending",
            title: "Docs Pending",
            value: metrics.documentsPending,
            subtitle: metrics.pendingSubtitle || "Awaiting upload",
            icon: <DocumentIcon size="md" />,
            accentColor: "#FF991F", // Warning amber
        },
        {
            id: "vat-returns",
            title: "VAT Returns Due",
            value: metrics.vatReturnsDue,
            subtitle: metrics.vatSubtitle || "This period",
            icon: <VatIcon size="md" />,
            accentColor: "#6554C0", // Purple
        },
        {
            id: "flagged-documents",
            title: "Flagged",
            value: metrics.flaggedDocuments ?? 0,
            subtitle: metrics.flaggedSubtitle || "Needs review",
            icon: <FlagIcon size="md" />,
            accentColor: "#DE350B", // Error red
        },
    ];

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {metricCards.map((metric, index) => (
                <div
                    key={metric.id}
                    className="animate-fade-in-up"
                    style={{ animationDelay: `${index * 50}ms` }}
                >
                    <MetricCard
                        {...metric}
                        onClick={() => onMetricClick?.(metric.id)}
                    />
                </div>
            ))}
        </div>
    );
}
