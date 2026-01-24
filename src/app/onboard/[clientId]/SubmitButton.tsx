"use client";

import { useState } from "react";
import type { ChecklistItem } from "@prisma/client";

interface SubmitButtonProps {
    clientId: string;
    checklistItems: ChecklistItem[];
}

export function SubmitButton({ clientId, checklistItems }: SubmitButtonProps) {
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isSubmitted, setIsSubmitted] = useState(false);

    const requiredItems = checklistItems.filter((item) => item.required);
    const completedRequired = requiredItems.filter(
        (item) => item.status === "uploaded" || item.status === "confirmed"
    );
    const allRequiredComplete = requiredItems.length === completedRequired.length;
    const completionPercentage = requiredItems.length > 0
        ? Math.round((completedRequired.length / requiredItems.length) * 100)
        : 100;

    const handleSubmit = async () => {
        if (!allRequiredComplete) {
            alert("Please complete all required items before submitting.");
            return;
        }

        setIsSubmitting(true);
        try {
            // Simulate submission - you can add actual API call here
            await new Promise((resolve) => setTimeout(resolve, 1500));
            setIsSubmitted(true);

            // Show success message
            setTimeout(() => {
                alert("✅ Your VAT pack has been submitted successfully! We'll be in touch soon.");
            }, 500);
        } catch (error) {
            console.error("Submission error:", error);
            alert("Failed to submit. Please try again.");
        } finally {
            setIsSubmitting(false);
        }
    };

    if (isSubmitted) {
        return (
            <div className="sticky bottom-4 z-10 overflow-hidden rounded-2xl bg-gradient-to-r from-green-500 to-emerald-600 p-6 shadow-2xl ring-1 ring-green-400 sm:bottom-8">
                <div className="flex flex-col items-center gap-4 text-center sm:flex-row sm:text-left">
                    <div className="flex-shrink-0 rounded-full bg-white p-3">
                        <svg className="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <div className="flex-1">
                        <h3 className="text-xl font-bold text-white">Successfully Submitted!</h3>
                        <p className="mt-1 text-sm text-green-50">
                            Your VAT pack has been received. We'll review your documents and be in touch soon.
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="sticky bottom-4 z-10 overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-slate-200 sm:bottom-8">
            {/* Progress Bar */}
            <div className="h-2 w-full bg-slate-100">
                <div
                    className="h-full bg-gradient-to-r from-blue-500 to-purple-600 transition-all duration-500"
                    style={{ width: `${completionPercentage}%` }}
                />
            </div>

            <div className="p-6 sm:p-8">
                <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex-1">
                        <div className="flex items-center gap-3">
                            <div className="flex-shrink-0 rounded-full bg-blue-100 p-2">
                                <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold text-slate-900">
                                    Ready to Submit?
                                </h3>
                                <p className="mt-0.5 text-sm text-slate-600">
                                    {allRequiredComplete ? (
                                        <span className="text-green-600 font-medium">
                                            ✓ All required items completed ({completedRequired.length}/{requiredItems.length})
                                        </span>
                                    ) : (
                                        <span>
                                            {completedRequired.length}/{requiredItems.length} required items completed
                                        </span>
                                    )}
                                </p>
                            </div>
                        </div>

                        {!allRequiredComplete && (
                            <div className="mt-4 rounded-lg bg-amber-50 p-3 ring-1 ring-amber-200">
                                <p className="text-sm text-amber-800">
                                    <span className="font-medium">⚠️ Missing items:</span> Please complete all required documents before submitting.
                                </p>
                            </div>
                        )}
                    </div>

                    <button
                        onClick={handleSubmit}
                        disabled={!allRequiredComplete || isSubmitting}
                        className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 px-8 py-4 text-base font-semibold text-white shadow-lg transition-all hover:from-blue-700 hover:to-purple-700 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:from-blue-600 disabled:hover:to-purple-600 sm:w-auto"
                    >
                        {isSubmitting ? (
                            <>
                                <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                </svg>
                                Submitting...
                            </>
                        ) : (
                            <>
                                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                Submit VAT Pack
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}
