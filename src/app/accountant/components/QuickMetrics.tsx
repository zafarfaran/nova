"use client";

import React from "react";
import {
    ClientsIcon,
    VatIcon,
    ClockIcon,
    ArrowRightIcon,
} from "./icons/AccountantIcons";

interface MetricCardProps {
    title: string;
    value: string | number;
    subtitle?: string;
    icon: React.ReactNode;
    trend?: {
        value: string;
        isPositive: boolean;
    };
    color: "violet" | "blue" | "amber" | "emerald";
    onClick?: () => void;
}

const colorConfig = {
    violet: {
        bg: "bg-violet-50",
        iconBg: "bg-violet-100",
        iconColor: "text-violet-600",
        trendPositive: "text-emerald-600",
        trendNegative: "text-red-500",
    },
    blue: {
        bg: "bg-blue-50",
        iconBg: "bg-blue-100",
        iconColor: "text-blue-600",
        trendPositive: "text-emerald-600",
        trendNegative: "text-red-500",
    },
    amber: {
        bg: "bg-amber-50",
        iconBg: "bg-amber-100",
        iconColor: "text-amber-600",
        trendPositive: "text-emerald-600",
        trendNegative: "text-red-500",
    },
    emerald: {
        bg: "bg-emerald-50",
        iconBg: "bg-emerald-100",
        iconColor: "text-emerald-600",
        trendPositive: "text-emerald-600",
        trendNegative: "text-red-500",
    },
};

function MetricCard({
    title,
    value,
    subtitle,
    icon,
    trend,
    color,
    onClick,
}: MetricCardProps) {
    const config = colorConfig[color];

    return (
        <button
            onClick={onClick}
            className={`
                w-full p-5 rounded-xl border border-slate-200 bg-white
                text-left transition-all duration-200
                hover:shadow-lg hover:-translate-y-1 hover:border-slate-300
                group
            `}
        >
            <div className="flex items-start justify-between mb-3">
                <div className={`p-2.5 rounded-xl ${config.iconBg}`}>
                    <span className={config.iconColor}>{icon}</span>
                </div>
                {trend && (
                    <span
                        className={`text-xs font-semibold ${trend.isPositive ? config.trendPositive : config.trendNegative}`}
                    >
                        {trend.isPositive ? "↑" : "↓"} {trend.value}
                    </span>
                )}
            </div>

            <div className="mb-1">
                <span className="text-3xl font-bold text-slate-900">{value}</span>
            </div>

            <div className="flex items-center justify-between">
                <div>
                    <p className="text-sm font-medium text-slate-600">{title}</p>
                    {subtitle && (
                        <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>
                    )}
                </div>
                <ArrowRightIcon
                    size="sm"
                    className="text-slate-300 group-hover:text-violet-500 group-hover:translate-x-1 transition-all"
                />
            </div>
        </button>
    );
}

// Document icon component
function DocumentIcon({ size }: { size: string }) {
    const sizeClass = size === "lg" ? "w-6 h-6" : size === "md" ? "w-5 h-5" : "w-4 h-4";
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
    const sizeClass = size === "lg" ? "w-6 h-6" : size === "md" ? "w-5 h-5" : "w-4 h-4";
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

export interface DashboardMetrics {
    totalClients: number;
    documentsPending: number;
    pendingSubtitle?: string;
    vatReturnsDue: number;
    vatSubtitle?: string;
    bankConnections: number;
    bankSubtitle?: string;
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
            subtitle: undefined,
            icon: <ClientsIcon size="lg" />,
            color: "violet" as const,
        },
        {
            id: "documents-pending",
            title: "Documents Pending",
            value: metrics.documentsPending,
            subtitle: metrics.pendingSubtitle || "Missing from clients",
            icon: <DocumentIcon size="lg" />,
            color: "amber" as const,
        },
        {
            id: "vat-returns",
            title: "VAT Returns Due",
            value: metrics.vatReturnsDue,
            subtitle: metrics.vatSubtitle || "This period",
            icon: <VatIcon size="lg" />,
            color: "blue" as const,
        },
        {
            id: "bank-connections",
            title: "Bank Connections",
            value: metrics.bankConnections,
            subtitle: metrics.bankSubtitle || "Active connections",
            icon: <BankIcon size="lg" />,
            color: "emerald" as const,
        },
    ];

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {metricCards.map((metric, index) => (
                <div
                    key={metric.id}
                    className="animate-fade-in-up"
                    style={{ animationDelay: `${index * 100}ms` }}
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
