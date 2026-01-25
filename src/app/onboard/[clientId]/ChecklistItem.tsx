"use client";

import { useState } from "react";
import { UploadButton } from "~/utils/uploadthing";
import type { ChecklistItem as ChecklistItemType } from "@prisma/client";

interface ChecklistItemProps {
    item: ChecklistItemType;
    clientId: number;
    isExpanded: boolean;
    onToggleExpand: () => void;
    onItemUpdate: (itemId: number, payload: Partial<ChecklistItemType>) => void;
}

// Document type configuration
const DOCUMENT_TYPES = {
    invoice: { label: "Invoice", color: "#0052CC", bgColor: "#DEEBFF" },
    receipt: { label: "Receipt", color: "#006644", bgColor: "#E3FCEF" },
    bank_statement: { label: "Bank Statement", color: "#5243AA", bgColor: "#EAE6FF" },
    payroll: { label: "Payroll", color: "#FF991F", bgColor: "#FFF0B3" },
    contract: { label: "Contract", color: "#172B4D", bgColor: "#DFE1E6" },
    vat_certificate: { label: "Tax Certificate", color: "#DE350B", bgColor: "#FFEBE6" },
    other: { label: "Other", color: "#5E6C84", bgColor: "#F4F5F7" },
} as const;

// Infer document type from item title
function inferDocumentType(title: string): keyof typeof DOCUMENT_TYPES {
    const lowerTitle = title.toLowerCase();
    if (lowerTitle.includes("invoice")) return "invoice";
    if (lowerTitle.includes("receipt")) return "receipt";
    if (lowerTitle.includes("bank") || lowerTitle.includes("statement")) return "bank_statement";
    if (lowerTitle.includes("payroll") || lowerTitle.includes("payslip") || lowerTitle.includes("p60") || lowerTitle.includes("p45")) return "payroll";
    if (lowerTitle.includes("contract") || lowerTitle.includes("agreement")) return "contract";
    if (lowerTitle.includes("vat") && lowerTitle.includes("certificate")) return "vat_certificate";
    return "other";
}

// Sync uploaded document to backend
async function syncDocumentToBackend(
    clientId: number,
    checklistItemId: number,
    file: { url: string; name: string; size: number; type?: string },
    documentType: string
) {
    try {
        const response = await fetch("/api/sync-document", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                clientId,
                checklistItemId,
                filename: file.name,
                fileUrl: file.url,
                fileSize: file.size,
                contentType: file.type || "application/pdf",
                documentType,
            }),
        });

        const result = await response.json();
        if (!result.success) {
            console.warn("Document sync warning:", result.error);
        }
        return result;
    } catch (error) {
        console.error("Document sync error:", error);
        return { success: false, error: String(error) };
    }
}

export function ChecklistItem({ item, clientId, isExpanded, onToggleExpand, onItemUpdate }: ChecklistItemProps) {
    const [isUpdating, setIsUpdating] = useState(false);
    const [isSyncing, setIsSyncing] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);

    const ctaData = JSON.parse(item.ctaData || "{}");
    const documentType = inferDocumentType(item.title);
    const docTypeConfig = DOCUMENT_TYPES[documentType];
    const status = item.status;
    const fileUrl = item.uploadedFileUrl;

    const isCompleted = status === "uploaded" || status === "confirmed" || status === "not_applicable";
    const isUploadType = item.ctaAction === "request_upload";

    const applyChecklistUpdate = async (payload: Partial<ChecklistItemType>) => {
        try {
            const response = await fetch(`/api/checklist/${item.id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                console.error("Checklist update failed:", error);
                return false;
            }

            const result = await response.json();
            if (result?.data) {
                onItemUpdate(item.id, result.data);
            } else {
                onItemUpdate(item.id, payload);
            }
            return true;
        } catch (error) {
            console.error("Error updating checklist item:", error);
            return false;
        }
    };

    const handleConfirmation = async (confirmed: boolean) => {
        setIsUpdating(true);
        const nextStatus = confirmed ? "confirmed" : "not_applicable";
        await applyChecklistUpdate({ status: nextStatus });
        setIsUpdating(false);
    };

    const handleReplaceFile = async () => {
        setIsUpdating(true);
        await applyChecklistUpdate({ status: "missing", uploadedFileUrl: null });
        setIsUpdating(false);
    };

    return (
        <div className="group">
            {/* Main Row - Always Visible */}
            <div
                className={`flex cursor-pointer items-center gap-3 px-4 py-3 transition-colors hover:bg-[#FAFBFC] ${isExpanded ? "bg-[#FAFBFC]" : ""}`}
                onClick={onToggleExpand}
            >
                {/* Status Icon */}
                <div className={`flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full ${isCompleted ? "bg-[#E3FCEF]" : "bg-[#F4F5F7]"}`}>
                    {isCompleted ? (
                        <svg className="h-3.5 w-3.5 text-[#006644]" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                    ) : (
                        <div className="h-2 w-2 rounded-full bg-[#DFE1E6]" />
                    )}
                </div>

                {/* Title and Tags */}
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                        <span className={`text-[12px] font-medium ${isCompleted ? "text-[#5E6C84] line-through" : "text-[#172B4D]"}`}>
                            {item.title}
                        </span>
                        {item.required && (
                            <span className="inline-flex items-center rounded px-1.5 py-0.5 text-[9px] font-bold text-[#DE350B] bg-[#FFEBE6]">
                                REQUIRED
                            </span>
                        )}
                        {isUploadType && (
                            <span
                                className="inline-flex items-center rounded px-1.5 py-0.5 text-[9px] font-medium"
                                style={{ color: docTypeConfig.color, backgroundColor: docTypeConfig.bgColor }}
                            >
                                {docTypeConfig.label}
                            </span>
                        )}
                    </div>
                </div>

                {/* Status Badge */}
                <StatusBadge status={status} />

                {/* Expand Icon */}
                <svg
                    className={`h-4 w-4 text-[#5E6C84] transition-transform ${isExpanded ? "rotate-180" : ""}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
            </div>

            {/* Expanded Content */}
            {isExpanded && (
                <div className="border-t border-[#EBECF0] bg-[#FAFBFC] px-4 py-4">
                    {/* Acceptance Criteria */}
                    <p className="mb-4 text-[11px] text-[#5E6C84]">
                        <span className="font-medium text-[#172B4D]">Acceptance:</span> {item.acceptance}
                    </p>

                    {/* Upload Section */}
                    {isUploadType && (
                        <div>
                            {fileUrl ? (
                                <div className="flex items-center justify-between rounded-lg bg-[#E3FCEF] p-3 ring-1 ring-[#ABF5D1]">
                                    <div className="flex items-center gap-2">
                                        <svg className="h-4 w-4 text-[#006644]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        <a
                                            href={fileUrl}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-[11px] font-medium text-[#006644] hover:underline"
                                            onClick={(e) => e.stopPropagation()}
                                        >
                                            View uploaded document
                                        </a>
                                        {isSyncing && (
                                            <span className="text-[10px] text-[#5E6C84]">(Syncing...)</span>
                                        )}
                                    </div>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleReplaceFile();
                                        }}
                                        className="text-[10px] font-medium text-[#5E6C84] hover:text-[#172B4D]"
                                    >
                                        Replace
                                    </button>
                                </div>
                            ) : (
                                <div>
                                    {uploadProgress > 0 && uploadProgress < 100 && (
                                        <div className="mb-3">
                                            <div className="flex items-center justify-between text-[10px] text-[#5E6C84]">
                                                <span>Uploading...</span>
                                                <span>{uploadProgress}%</span>
                                            </div>
                                            <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-[#DFE1E6]">
                                                <div
                                                    className="h-full rounded-full bg-[#0052CC] transition-all"
                                                    style={{ width: `${uploadProgress}%` }}
                                                />
                                            </div>
                                        </div>
                                    )}
                                    <div className="flex flex-col gap-2">
                                        <UploadButton
                                            endpoint="documentUploader"
                                            input={{
                                                clientId: clientId,
                                                checklistItemId: item.id,
                                            }}
                                            onUploadProgress={(progress) => {
                                                setUploadProgress(progress);
                                            }}
                                            onClientUploadComplete={async (res) => {
                                                setUploadProgress(0);
                                                if (res && res[0]) {
                                                    const uploadedFile = res[0];
                                                    onItemUpdate(item.id, {
                                                        status: "uploaded",
                                                        uploadedFileUrl: uploadedFile.url,
                                                    });

                                                    // Sync to backend with document type
                                                    setIsSyncing(true);
                                                    await syncDocumentToBackend(
                                                        clientId,
                                                        item.id,
                                                        {
                                                            url: uploadedFile.url,
                                                            name: uploadedFile.name,
                                                            size: uploadedFile.size,
                                                            type: uploadedFile.type,
                                                        },
                                                        documentType
                                                    );
                                                    setIsSyncing(false);
                                                }
                                            }}
                                            onUploadError={(error: Error) => {
                                                setUploadProgress(0);
                                                console.error("Upload error:", error);
                                                alert(`Upload failed: ${error.message}`);
                                            }}
                                            appearance={{
                                                button: "bg-[#0052CC] hover:bg-[#0747A6] text-white text-[11px] font-medium px-4 py-2 rounded transition-colors",
                                                allowedContent: "hidden",
                                            }}
                                        />
                                        <p className="text-[10px] text-[#5E6C84]">
                                            Accepted: PDF, Images, Word, Excel (max 8MB)
                                        </p>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Confirmation Section */}
                    {item.ctaAction === "ask_confirm" && ctaData.question && (
                        <div>
                            <p className="mb-3 text-[11px] font-medium text-[#172B4D]">{ctaData.question}</p>
                            <div className="flex gap-2">
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleConfirmation(true);
                                    }}
                                    disabled={isUpdating || status === "confirmed"}
                                    className={`inline-flex items-center gap-1.5 rounded px-3 py-1.5 text-[11px] font-medium transition-colors ${
                                        status === "confirmed"
                                            ? "bg-[#E3FCEF] text-[#006644] ring-1 ring-[#ABF5D1]"
                                            : "bg-[#36B37E] text-white hover:bg-[#2D9B6B]"
                                    } disabled:opacity-50`}
                                >
                                    <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                    </svg>
                                    Yes
                                </button>
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleConfirmation(false);
                                    }}
                                    disabled={isUpdating || status === "not_applicable"}
                                    className={`inline-flex items-center gap-1.5 rounded px-3 py-1.5 text-[11px] font-medium transition-colors ${
                                        status === "not_applicable"
                                            ? "bg-[#F4F5F7] text-[#5E6C84] ring-1 ring-[#DFE1E6]"
                                            : "bg-[#DFE1E6] text-[#172B4D] hover:bg-[#C1C7D0]"
                                    } disabled:opacity-50`}
                                >
                                    <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                    No / N/A
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

function StatusBadge({ status }: { status: string }) {
    const statusConfig: Record<string, { bg: string; text: string; label: string }> = {
        missing: { bg: "bg-[#FFFAE6]", text: "text-[#974F0C]", label: "Pending" },
        uploaded: { bg: "bg-[#E3FCEF]", text: "text-[#006644]", label: "Uploaded" },
        confirmed: { bg: "bg-[#E3FCEF]", text: "text-[#006644]", label: "Confirmed" },
        not_applicable: { bg: "bg-[#F4F5F7]", text: "text-[#5E6C84]", label: "N/A" },
        pending: { bg: "bg-[#DEEBFF]", text: "text-[#0747A6]", label: "Pending" },
        unknown: { bg: "bg-[#F4F5F7]", text: "text-[#5E6C84]", label: "Unknown" },
    };

    const config = statusConfig[status] ?? statusConfig.unknown ?? { bg: "bg-[#F4F5F7]", text: "text-[#5E6C84]", label: "Unknown" };

    return (
        <span className={`inline-flex items-center rounded px-2 py-0.5 text-[10px] font-medium ${config.bg} ${config.text}`}>
            {config.label}
        </span>
    );
}
