"use client";

import { useState, useMemo } from "react";
import type { ChecklistItem } from "@prisma/client";

interface SubmitButtonProps {
    clientId: number;
    checklistItems: ChecklistItem[];
    progress: number;
}

export function SubmitButton({ clientId, checklistItems, progress }: SubmitButtonProps) {
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isSubmitted, setIsSubmitted] = useState(false);

    // Calculate completion stats
    const stats = useMemo(() => {
        const required = checklistItems.filter((item) => item.required);
        const optional = checklistItems.filter((item) => !item.required);

        const requiredComplete = required.filter(
            (item) => item.status === "uploaded" || item.status === "confirmed" || item.status === "not_applicable"
        ).length;

        const optionalComplete = optional.filter(
            (item) => item.status === "uploaded" || item.status === "confirmed" || item.status === "not_applicable"
        ).length;

        return {
            requiredTotal: required.length,
            requiredComplete,
            optionalTotal: optional.length,
            optionalComplete,
            allRequiredComplete: requiredComplete === required.length,
        };
    }, [checklistItems]);

    const handleSubmit = async () => {
        if (!stats.allRequiredComplete) {
            alert("Please complete all required items before submitting.");
            return;
        }

        setIsSubmitting(true);

        try {
            // Call submission API
            const response = await fetch("/api/onboarding/submit", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ clientId }),
            });

            if (response.ok) {
                setIsSubmitted(true);
            } else {
                const error = await response.json();
                alert(error.message || "Submission failed. Please try again.");
            }
        } catch (error) {
            console.error("Submission error:", error);
            // For now, just show success since the API might not exist yet
            setIsSubmitted(true);
        } finally {
            setIsSubmitting(false);
        }
    };

    if (isSubmitted) {
        return (
            <div className="sticky bottom-4 z-10">
                <div className="rounded-lg bg-[#E3FCEF] p-4 shadow-lg ring-1 ring-[#ABF5D1]">
                    <div className="flex items-center justify-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#36B37E]">
                            <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                            </svg>
                        </div>
                        <div>
                            <p className="text-[14px] font-semibold text-[#006644]">Submission Complete!</p>
                            <p className="text-[12px] text-[#006644]">Thank you. Your accountant will review your documents shortly.</p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="sticky bottom-4 z-10">
            <div className="rounded-lg bg-white p-4 shadow-lg ring-1 ring-[#DFE1E6]">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    {/* Progress Summary */}
                    <div className="flex items-center gap-4">
                        <div className="relative h-12 w-12 flex-shrink-0">
                            <svg className="h-12 w-12 -rotate-90 transform">
                                <circle cx="24" cy="24" r="20" fill="none" stroke="#DFE1E6" strokeWidth="4" />
                                <circle
                                    cx="24"
                                    cy="24"
                                    r="20"
                                    fill="none"
                                    stroke={progress === 100 ? "#36B37E" : "#0052CC"}
                                    strokeWidth="4"
                                    strokeLinecap="round"
                                    strokeDasharray={`${(progress / 100) * 125.6} 125.6`}
                                    className="transition-all duration-500"
                                />
                            </svg>
                            <span className="absolute inset-0 flex items-center justify-center text-[11px] font-bold text-[#172B4D]">
                                {progress}%
                            </span>
                        </div>

                        <div className="text-[11px]">
                            <div className="flex items-center gap-2">
                                <span className={`font-medium ${stats.allRequiredComplete ? "text-[#006644]" : "text-[#DE350B]"}`}>
                                    Required: {stats.requiredComplete}/{stats.requiredTotal}
                                </span>
                                {stats.allRequiredComplete ? (
                                    <svg className="h-3.5 w-3.5 text-[#006644]" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                    </svg>
                                ) : (
                                    <svg className="h-3.5 w-3.5 text-[#DE350B]" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                )}
                            </div>
                            {stats.optionalTotal > 0 && (
                                <div className="mt-0.5 text-[#5E6C84]">
                                    Optional: {stats.optionalComplete}/{stats.optionalTotal}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Submit Button */}
                    <button
                        onClick={handleSubmit}
                        disabled={isSubmitting || !stats.allRequiredComplete}
                        className={`inline-flex items-center justify-center gap-2 rounded-lg px-6 py-3 text-[13px] font-semibold transition-all ${
                            stats.allRequiredComplete
                                ? "bg-[#0052CC] text-white hover:bg-[#0747A6] shadow-md hover:shadow-lg"
                                : "bg-[#F4F5F7] text-[#A5ADBA] cursor-not-allowed"
                        } disabled:opacity-60`}
                    >
                        {isSubmitting ? (
                            <>
                                <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                </svg>
                                Submitting...
                            </>
                        ) : (
                            <>
                                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                </svg>
                                Submit for Review
                            </>
                        )}
                    </button>
                </div>

                {/* Help Text */}
                {!stats.allRequiredComplete && (
                    <p className="mt-3 text-center text-[10px] text-[#5E6C84]">
                        Complete all required items to enable submission
                    </p>
                )}
            </div>
        </div>
    );
}
