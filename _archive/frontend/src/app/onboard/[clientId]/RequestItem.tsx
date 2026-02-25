"use client";

import { useState } from "react";
import { UploadButton } from "~/utils/uploadthing";
import type { RequestItem } from "~/domains/requests/types";
import { updateRequestItem } from "~/domains/requests/api/request";

interface RequestItemProps {
    item: RequestItem;
    clientId: number;
    isExpanded: boolean;
    onToggleExpand: () => void;
    onItemUpdate: (itemId: number, payload: Partial<RequestItem>) => void;
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

import { logger } from "~/lib/utils/logger";

// Sync uploaded document to backend
async function syncDocumentToBackend(
    clientId: number,
    requestItemId: number,
    file: { url: string; name: string; size: number; type?: string },
    documentType: string
): Promise<{ success: boolean; error?: string }> {
    try {
        const response = await fetch("/api/sync-document", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                clientId,
                checklistItemId: requestItemId, // API still uses checklistItemId
                filename: file.name,
                fileUrl: file.url,
                fileSize: file.size,
                contentType: file.type || "application/pdf",
                documentType,
            }),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            logger.warn("Document sync failed", {
                clientId,
                requestItemId,
                status: response.status,
                error: errorData,
            });
            return { success: false, error: errorData.error || "Sync failed" };
        }

        const result = await response.json();
        if (!result.success) {
            logger.warn("Document sync warning", {
                clientId,
                requestItemId,
                error: result.error,
            });
        }
        return { success: true };
    } catch (error) {
        logger.error("Document sync error", error, {
            clientId,
            requestItemId,
        });
        return { 
            success: false, 
            error: error instanceof Error ? error.message : "Unknown error" 
        };
    }
}

export function RequestItem({ item, clientId, isExpanded, onToggleExpand, onItemUpdate }: RequestItemProps) {
    const [isUpdating, setIsUpdating] = useState(false);
    const [isSyncing, setIsSyncing] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);

    // Use description as title (backend RequestItem uses description field)
    const title = item.description || "Document Request";
    const documentType = inferDocumentType(title);
    const docTypeConfig = DOCUMENT_TYPES[documentType];
    const status = item.status;

    const isCompleted = status === "partial" || status === "complete" || status === "waived";

    const applyRequestItemUpdate = async (payload: Partial<RequestItem>) => {
        try {
            setIsUpdating(true);
            // Update via backend API
            const updated = await updateRequestItem(item.id, {
                status: payload.status || undefined,
            });
            onItemUpdate(item.id, updated);
            return true;
        } catch (error) {
            logger.error("Failed to update request item", error, {
                requestItemId: item.id,
                payload,
            });
            return false;
        } finally {
            setIsUpdating(false);
        }
    };

    const handleMarkComplete = async () => {
        await applyRequestItemUpdate({ status: "complete" });
    };

    const handleMarkWaived = async () => {
        await applyRequestItemUpdate({ status: "waived" });
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
                            {title}
                        </span>
                        {item.is_required && (
                            <span className="inline-flex items-center rounded px-1.5 py-0.5 text-[9px] font-bold text-[#DE350B] bg-[#FFEBE6]">
                                REQUIRED
                            </span>
                        )}
                        <span
                            className="inline-flex items-center rounded px-1.5 py-0.5 text-[9px] font-medium"
                            style={{ color: docTypeConfig.color, backgroundColor: docTypeConfig.bgColor }}
                        >
                            {docTypeConfig.label}
                        </span>
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
                    {/* Description */}
                    {item.description && (
                        <p className="mb-4 text-[11px] text-[#5E6C84]">
                            <span className="font-medium text-[#172B4D]">Description:</span> {item.description}
                        </p>
                    )}

                    {/* Upload Section */}
                    {status !== "complete" && status !== "waived" && (
                        <div>
                            {status === "partial" ? (
                                <div className="flex items-center justify-between rounded-lg bg-[#E3FCEF] p-3 ring-1 ring-[#ABF5D1]">
                                    <div className="flex items-center gap-2">
                                        <svg className="h-4 w-4 text-[#006644]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        <span className="text-[11px] font-medium text-[#006644]">
                                            Document uploaded
                                        </span>
                                        {isSyncing && (
                                            <span className="text-[10px] text-[#5E6C84]">(Syncing...)</span>
                                        )}
                                    </div>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleMarkComplete();
                                        }}
                                        disabled={isUpdating}
                                        className="text-[10px] font-medium text-[#006644] hover:text-[#0052CC] disabled:opacity-50"
                                    >
                                        Mark Complete
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
                                                    // Backend will auto-update status to "partial" or "complete"
                                                    // based on document count, so we don't need to manually update

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
                                                logger.error("File upload failed", error, {
                                                    clientId,
                                                    requestItemId: item.id,
                                                });
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

                    {/* Actions */}
                    {status === "pending" && (
                        <div className="mt-4 flex gap-2">
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handleMarkWaived();
                                }}
                                disabled={isUpdating}
                                className="inline-flex items-center gap-1.5 rounded px-3 py-1.5 text-[11px] font-medium transition-colors bg-[#DFE1E6] text-[#172B4D] hover:bg-[#C1C7D0] disabled:opacity-50"
                            >
                                <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                                </svg>
                                Mark as Not Applicable
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

function StatusBadge({ status }: { status: string }) {
    const statusConfig: Record<string, { bg: string; text: string; label: string }> = {
        pending: { bg: "bg-[#DEEBFF]", text: "text-[#0747A6]", label: "Pending" },
        partial: { bg: "bg-[#E3FCEF]", text: "text-[#006644]", label: "Partial" },
        complete: { bg: "bg-[#E3FCEF]", text: "text-[#006644]", label: "Complete" },
        waived: { bg: "bg-[#F4F5F7]", text: "text-[#5E6C84]", label: "Waived" },
    };

    const config = statusConfig[status] ?? { bg: "bg-[#F4F5F7]", text: "text-[#5E6C84]", label: status };

    return (
        <span className={`inline-flex items-center rounded px-2 py-0.5 text-[10px] font-medium ${config.bg} ${config.text}`}>
            {config.label}
        </span>
    );
}
