"use client";

import { useMemo, useState } from "react";
import type { RequestItem } from "~/domains/requests/types";
import { ChecklistSection } from "./ChecklistSection";
import { SubmitButton } from "./SubmitButton";
import { BankConnectionButton } from "./BankConnectionButton";
import { OnboardingHeader } from "./OnboardingHeader";

interface OnboardingContentProps {
    client: {
        id: number;
        name: string;
        contact_email: string | null;
        entity_type: string;
        vat_scheme: string | null;
        requestItems: RequestItem[];
    };
    latestEngagement?: {
        id: number;
        period_start: string;
        period_end: string;
        status: string;
    } | null;
}

const COMPLETED_STATUSES = new Set(["partial", "complete", "waived"]);

export function OnboardingContent({ client, latestEngagement }: OnboardingContentProps) {
    const [requestItems, setRequestItems] = useState<RequestItem[]>(client.requestItems);

    const completedItems = useMemo(() => {
        return requestItems.filter((item) => COMPLETED_STATUSES.has(item.status)).length;
    }, [requestItems]);

    const totalItems = requestItems.length;
    const progressPercent = totalItems > 0 ? Math.round((completedItems / totalItems) * 100) : 0;

    // All request items are for document uploads
    const requiredItems = useMemo(
        () => requestItems.filter((item) => item.is_required),
        [requestItems]
    );

    const updateRequestItem = (itemId: number, payload: Partial<RequestItem>) => {
        setRequestItems((prev) => prev.map((item) => (item.id === itemId ? { ...item, ...payload } : item)));
    };

    const periodStart = latestEngagement ? new Date(latestEngagement.period_start) : null;
    const periodEnd = latestEngagement ? new Date(latestEngagement.period_end) : null;
    const vatPeriodLabel = periodStart
        ? `Q${Math.ceil((periodStart.getMonth() + 1) / 3)} ${periodStart.getFullYear()}`
        : "No period";

    return (
        <>
            <OnboardingHeader
                clientName={client.name}
                vatPeriod={vatPeriodLabel}
                progress={progressPercent}
                completedCount={completedItems}
                totalCount={totalItems}
            />

            <div className="mx-auto max-w-4xl px-4 py-6 sm:px-6 lg:px-8">
                {/* Client Info Summary */}
                <div className="mb-6 rounded-lg bg-white p-4 shadow-sm ring-1 ring-[#DFE1E6]">
                    <div className="flex flex-wrap items-center gap-4 text-[12px]">
                        <div className="flex items-center gap-2">
                            <span className="text-[#5E6C84]">Email:</span>
                            <span className="font-medium text-[#172B4D]">{client.contact_email || "Not provided"}</span>
                        </div>
                        <div className="h-4 w-px bg-[#DFE1E6]" />
                        <div className="flex items-center gap-2">
                            <span className="text-[#5E6C84]">Entity:</span>
                            <span className="font-medium text-[#172B4D]">{client.entity_type}</span>
                        </div>
                        <div className="h-4 w-px bg-[#DFE1E6]" />
                        <div className="flex items-center gap-2">
                            <span className="text-[#5E6C84]">Tax Scheme:</span>
                            <span className="font-medium text-[#172B4D]">{client.vat_scheme || "Standard"}</span>
                        </div>
                        {periodStart && periodEnd && (
                            <>
                                <div className="h-4 w-px bg-[#DFE1E6]" />
                                <div className="flex items-center gap-2">
                                    <span className="text-[#5E6C84]">Period:</span>
                                    <span className="font-medium text-[#172B4D]">
                                        {periodStart.toLocaleDateString("en-GB", {
                                            day: "numeric",
                                            month: "short",
                                        })}{" "}
                                        -{" "}
                                        {periodEnd.toLocaleDateString("en-GB", {
                                            day: "numeric",
                                            month: "short",
                                            year: "numeric",
                                        })}
                                    </span>
                                </div>
                            </>
                        )}
                    </div>
                </div>

                {/* Document Upload Section */}
                {requiredItems.length > 0 && (
                    <ChecklistSection
                        title="Required Documents"
                        subtitle="Upload the following documents for tax compliance"
                        icon="document"
                        items={requiredItems}
                        clientId={client.id}
                        accentColor="#6554C0"
                        onItemUpdate={updateRequestItem}
                    />
                )}

                {/* Optional Documents */}
                {requestItems.filter((item) => !item.is_required).length > 0 && (
                    <ChecklistSection
                        title="Optional Documents"
                        subtitle="Additional documents that may be helpful"
                        icon="document"
                        items={requestItems.filter((item) => !item.is_required)}
                        clientId={client.id}
                        accentColor="#36B37E"
                        onItemUpdate={updateRequestItem}
                    />
                )}

                {/* Bank Connection Section */}
                <div className="mb-6 overflow-hidden rounded-lg bg-white shadow-sm ring-1 ring-[#DFE1E6]">
                    <div className="flex items-center gap-3 border-b border-[#DFE1E6] px-4 py-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded bg-[#E3FCEF]">
                            <svg className="h-4 w-4 text-[#006644]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                            </svg>
                        </div>
                        <div>
                            <h2 className="text-[13px] font-semibold text-[#172B4D]">Bank Account Connection</h2>
                            <p className="text-[11px] text-[#5E6C84]">Securely connect for automatic transaction sync</p>
                        </div>
                    </div>
                    <div className="p-4">
                        <BankConnectionButton clientId={client.id} />
                    </div>
                </div>

                {/* Submit Button */}
                <SubmitButton clientId={client.id} requestItems={requestItems} progress={progressPercent} />
            </div>
        </>
    );
}
