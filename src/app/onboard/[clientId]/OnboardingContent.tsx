"use client";

import { useMemo, useState } from "react";
import type { ChecklistItem as ChecklistItemType } from "@prisma/client";
import { ChecklistSection } from "./ChecklistSection";
import { SubmitButton } from "./SubmitButton";
import { BankConnectionButton } from "./BankConnectionButton";
import { OnboardingHeader } from "./OnboardingHeader";

interface OnboardingContentProps {
    client: {
        id: number;
        name: string;
        contactEmail?: string | null;
        entityType: string;
        vatScheme?: string | null;
        autoChasers: { delayDays: number }[];
        checklistItems: ChecklistItemType[];
    };
    latestVatPeriod?: { periodStart: Date | string; periodEnd: Date | string } | null;
}

const COMPLETED_STATUSES = new Set(["uploaded", "confirmed", "not_applicable"]);

export function OnboardingContent({ client, latestVatPeriod }: OnboardingContentProps) {
    const [checklistItems, setChecklistItems] = useState<ChecklistItemType[]>(client.checklistItems);

    const completedItems = useMemo(() => {
        return checklistItems.filter((item) => COMPLETED_STATUSES.has(item.status)).length;
    }, [checklistItems]);

    const totalItems = checklistItems.length;
    const progressPercent = totalItems > 0 ? Math.round((completedItems / totalItems) * 100) : 0;

    const uploadItems = useMemo(
        () => checklistItems.filter((item) => item.ctaAction === "request_upload"),
        [checklistItems]
    );
    const confirmItems = useMemo(
        () => checklistItems.filter((item) => item.ctaAction === "ask_confirm"),
        [checklistItems]
    );

    const updateChecklistItem = (itemId: number, payload: Partial<ChecklistItemType>) => {
        setChecklistItems((prev) => prev.map((item) => (item.id === itemId ? { ...item, ...payload } : item)));
    };

    const periodStart = latestVatPeriod ? new Date(latestVatPeriod.periodStart) : null;
    const periodEnd = latestVatPeriod ? new Date(latestVatPeriod.periodEnd) : null;
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
                            <span className="font-medium text-[#172B4D]">{client.contactEmail || "Not provided"}</span>
                        </div>
                        <div className="h-4 w-px bg-[#DFE1E6]" />
                        <div className="flex items-center gap-2">
                            <span className="text-[#5E6C84]">Entity:</span>
                            <span className="font-medium text-[#172B4D]">{client.entityType}</span>
                        </div>
                        <div className="h-4 w-px bg-[#DFE1E6]" />
                        <div className="flex items-center gap-2">
                            <span className="text-[#5E6C84]">Tax Scheme:</span>
                            <span className="font-medium text-[#172B4D]">{client.vatScheme || "Standard"}</span>
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
                {uploadItems.length > 0 && (
                    <ChecklistSection
                        title="Required Documents"
                        subtitle="Upload the following documents for tax compliance"
                        icon="document"
                        items={uploadItems}
                        clientId={client.id}
                        accentColor="#6554C0"
                        onItemUpdate={updateChecklistItem}
                    />
                )}

                {/* Confirmation Section */}
                {confirmItems.length > 0 && (
                    <ChecklistSection
                        title="Confirmations"
                        subtitle="Please confirm the following items"
                        icon="check"
                        items={confirmItems}
                        clientId={client.id}
                        accentColor="#36B37E"
                        onItemUpdate={updateChecklistItem}
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

                {/* Auto Chasers Info */}
                {client.autoChasers.length > 0 && (
                    <div className="mb-6 rounded-lg bg-[#DEEBFF] p-4 ring-1 ring-[#B3D4FF]">
                        <div className="flex items-start gap-3">
                            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-[#0052CC]">
                                <svg className="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                </svg>
                            </div>
                            <div>
                                <h3 className="text-[13px] font-semibold text-[#0747A6]">Automatic Reminders</h3>
                                <p className="mt-1 text-[11px] text-[#0747A6]">
                                    You'll receive email reminders for missing documents:
                                </p>
                                <div className="mt-2 flex flex-wrap gap-2">
                                    {client.autoChasers.map((chaser, idx) => (
                                        <span
                                            key={idx}
                                            className="inline-flex items-center rounded bg-white px-2 py-1 text-[10px] font-medium text-[#0747A6] ring-1 ring-[#B3D4FF]"
                                        >
                                            After {chaser.delayDays} days
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Submit Button */}
                <SubmitButton clientId={client.id} checklistItems={checklistItems} progress={progressPercent} />
            </div>
        </>
    );
}
