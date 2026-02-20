"use client";

import { useState, useEffect } from "react";
import { BankStatementChoice } from "./BankStatementChoice";
import { ChecklistUploader } from "./ChecklistUploader";

interface BankStatementChoiceWrapperProps {
    clientId: number;
}

export function BankStatementChoiceWrapper({ clientId }: BankStatementChoiceWrapperProps) {
    const [showManualUpload, setShowManualUpload] = useState(false);
    const [checklistItem, setChecklistItem] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleManualUpload = async () => {
        setIsLoading(true);

        // Create a checklist item for manual bank statement upload
        try {
            const response = await fetch("/api/checklist/create-bank-statement-item", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ clientId }),
            });

            if (response.ok) {
                const data = await response.json();
                setChecklistItem(data.item);
                setShowManualUpload(true);
            } else {
                alert("Failed to create upload item");
            }
        } catch (error) {
            console.error("Error creating checklist item:", error);
            alert("Failed to create upload item");
        } finally {
            setIsLoading(false);
        }
    };

    if (showManualUpload && checklistItem) {
        return (
            <div className="space-y-4">
                <button
                    onClick={() => {
                        setShowManualUpload(false);
                        setChecklistItem(null);
                    }}
                    className="text-sm text-slate-600 hover:text-slate-900 flex items-center gap-1"
                >
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                    Back to options
                </button>

                <div className="rounded-lg bg-blue-50 border border-blue-200 p-4">
                    <div className="flex items-start gap-3">
                        <svg className="h-5 w-5 text-blue-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div className="flex-1">
                            <h4 className="font-semibold text-blue-900 mb-1">Manual Upload</h4>
                            <p className="text-sm text-blue-700">
                                Please upload your bank statements below. Accepted formats: PDF, CSV, Excel
                            </p>
                        </div>
                    </div>
                </div>

                {/* Use the existing ChecklistUploader component */}
                <ChecklistUploader item={checklistItem} clientId={clientId} />
            </div>
        );
    }

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-8">
                <svg className="h-8 w-8 animate-spin text-blue-600" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
            </div>
        );
    }

    return <BankStatementChoice clientId={clientId} onManualUpload={handleManualUpload} />;
}
