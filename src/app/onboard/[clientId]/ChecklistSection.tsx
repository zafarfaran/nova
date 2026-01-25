"use client";

import { useState } from "react";
import type { ChecklistItem as ChecklistItemType } from "@prisma/client";
import { ChecklistItem } from "./ChecklistItem";

interface ChecklistSectionProps {
    title: string;
    subtitle: string;
    icon: "document" | "check";
    items: ChecklistItemType[];
    clientId: number;
    accentColor: string;
    onItemUpdate: (itemId: number, payload: Partial<ChecklistItemType>) => void;
}

export function ChecklistSection({
    title,
    subtitle,
    icon,
    items,
    clientId,
    accentColor,
    onItemUpdate,
}: ChecklistSectionProps) {
    const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set());

    const completedCount = items.filter(
        (item) => item.status === "uploaded" || item.status === "confirmed" || item.status === "not_applicable"
    ).length;

    const toggleExpand = (itemId: number) => {
        setExpandedItems((prev) => {
            const next = new Set(prev);
            if (next.has(itemId)) {
                next.delete(itemId);
            } else {
                next.add(itemId);
            }
            return next;
        });
    };

    return (
        <div className="mb-6 overflow-hidden rounded-lg bg-white shadow-sm ring-1 ring-[#DFE1E6]">
            {/* Section Header */}
            <div
                className="flex items-center justify-between border-b border-[#DFE1E6] px-4 py-3"
                style={{ borderLeftWidth: "3px", borderLeftColor: accentColor }}
            >
                <div className="flex items-center gap-3">
                    <div
                        className="flex h-8 w-8 items-center justify-center rounded"
                        style={{ backgroundColor: `${accentColor}15` }}
                    >
                        {icon === "document" ? (
                            <svg className="h-4 w-4" style={{ color: accentColor }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                        ) : (
                            <svg className="h-4 w-4" style={{ color: accentColor }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        )}
                    </div>
                    <div>
                        <h2 className="text-[13px] font-semibold text-[#172B4D]">{title}</h2>
                        <p className="text-[11px] text-[#5E6C84]">{subtitle}</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-[11px] font-medium text-[#5E6C84]">
                        {completedCount}/{items.length} completed
                    </span>
                    <div className="h-6 w-20 overflow-hidden rounded-full bg-[#DFE1E6]">
                        <div
                            className="h-full rounded-full transition-all duration-300"
                            style={{
                                width: `${items.length > 0 ? (completedCount / items.length) * 100 : 0}%`,
                                backgroundColor: completedCount === items.length ? "#36B37E" : accentColor,
                            }}
                        />
                    </div>
                </div>
            </div>

            {/* Items List */}
            <div className="divide-y divide-[#EBECF0]">
                {items.map((item) => (
                    <ChecklistItem
                        key={item.id}
                        item={item}
                        clientId={clientId}
                        isExpanded={expandedItems.has(item.id)}
                        onToggleExpand={() => toggleExpand(item.id)}
                        onItemUpdate={onItemUpdate}
                    />
                ))}
            </div>
        </div>
    );
}
