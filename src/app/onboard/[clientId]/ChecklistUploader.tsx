"use client";

import { useState } from "react";
import { UploadButton } from "~/utils/uploadthing";
import type { ChecklistItem } from "@prisma/client";

interface ChecklistUploaderProps {
    item: ChecklistItem;
    clientId: string;
}

// Sync uploaded document to backend
async function syncDocumentToBackend(
    clientSetupId: string,
    checklistItemId: string,
    file: { url: string; name: string; size: number; type?: string }
) {
    try {
        const response = await fetch("/api/sync-document", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                clientSetupId,
                checklistItemId,
                filename: file.name,
                fileUrl: file.url,
                fileSize: file.size,
                contentType: file.type,
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

export function ChecklistUploader({ item, clientId }: ChecklistUploaderProps) {
    const [status, setStatus] = useState(item.status);
    const [fileUrl, setFileUrl] = useState(item.uploadedFileUrl);
    const [isUpdating, setIsUpdating] = useState(false);
    const [isSyncing, setIsSyncing] = useState(false);

    const ctaData = JSON.parse(item.ctaData || "{}");

    const handleConfirmation = async (confirmed: boolean) => {
        setIsUpdating(true);
        try {
            const response = await fetch(`/api/checklist/${item.id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    status: confirmed ? "confirmed" : "not_applicable",
                }),
            });

            if (response.ok) {
                setStatus(confirmed ? "confirmed" : "not_applicable");
            }
        } catch (error) {
            console.error("Error updating status:", error);
        } finally {
            setIsUpdating(false);
        }
    };

    return (
        <div className="group relative overflow-hidden rounded-xl border-2 border-slate-200 bg-white p-6 shadow-sm transition-all hover:border-blue-300 hover:shadow-lg">
            {/* Decorative gradient bar */}
            <div className="absolute left-0 top-0 h-1 w-full bg-gradient-to-r from-blue-500 to-purple-500" />

            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div className="flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-lg font-semibold text-slate-900">
                            {item.title}
                        </h3>
                        {item.required && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-3 py-1 text-xs font-medium text-red-700 ring-1 ring-red-200">
                                <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                </svg>
                                Required
                            </span>
                        )}
                        <StatusBadge status={status} />
                    </div>

                    <p className="mt-2 text-sm leading-relaxed text-slate-600">
                        <span className="font-medium text-slate-700">Acceptance:</span>{" "}
                        {item.acceptance}
                    </p>

                    {fileUrl && (
                        <div className="mt-4 flex items-center gap-2 rounded-lg bg-green-50 p-3 ring-1 ring-green-200">
                            <svg
                                className="h-5 w-5 flex-shrink-0 text-green-600"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                                />
                            </svg>
                            <a
                                href={fileUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm font-medium text-green-700 hover:text-green-800 hover:underline"
                            >
                                View uploaded document
                            </a>
                            {isSyncing && (
                                <span className="ml-2 text-xs text-slate-500">
                                    Syncing...
                                </span>
                            )}
                        </div>
                    )}
                </div>
            </div>

            <div className="mt-4">
                {item.ctaAction === "request_upload" && (
                    <div className="flex flex-col gap-3">
                        {!fileUrl ? (
                            <>
                                <UploadButton
                                    endpoint="documentUploader"
                                    input={{
                                        clientId: clientId,
                                        checklistItemId: item.id,
                                    }}
                                    onClientUploadComplete={async (res) => {
                                        console.log("Files uploaded:", res);
                                        if (res && res[0]) {
                                            const uploadedFile = res[0];
                                            setFileUrl(uploadedFile.url);
                                            setStatus("uploaded");

                                            // Sync to backend
                                            setIsSyncing(true);
                                            await syncDocumentToBackend(
                                                clientId,
                                                item.id,
                                                {
                                                    url: uploadedFile.url,
                                                    name: uploadedFile.name,
                                                    size: uploadedFile.size,
                                                    type: uploadedFile.type,
                                                }
                                            );
                                            setIsSyncing(false);
                                        }
                                    }}
                                    onUploadError={(error: Error) => {
                                        console.error("Upload error:", error);
                                        alert(`Upload failed: ${error.message}`);
                                    }}
                                />
                                <p className="text-xs text-slate-500">
                                    📎 Accepted: PDF, Images, Word, Excel, CSV (max 10MB each)
                                </p>
                            </>
                        ) : (
                            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                                <button
                                    onClick={() => {
                                        setFileUrl(null);
                                        setStatus("missing");
                                    }}
                                    className="inline-flex items-center justify-center gap-2 rounded-lg bg-slate-100 px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-200"
                                >
                                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                    </svg>
                                    Replace file
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {item.ctaAction === "ask_confirm" && ctaData.question && (
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                        <p className="text-sm font-medium text-slate-700">{ctaData.question}</p>
                        <div className="flex gap-2">
                            <button
                                onClick={() => handleConfirmation(true)}
                                disabled={isUpdating}
                                className="inline-flex flex-1 items-center justify-center gap-2 rounded-lg bg-green-600 px-5 py-2.5 text-sm font-medium text-white transition-all hover:bg-green-700 disabled:opacity-50 sm:flex-initial"
                            >
                                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                                Yes
                            </button>
                            <button
                                onClick={() => handleConfirmation(false)}
                                disabled={isUpdating}
                                className="inline-flex flex-1 items-center justify-center gap-2 rounded-lg bg-slate-600 px-5 py-2.5 text-sm font-medium text-white transition-all hover:bg-slate-700 disabled:opacity-50 sm:flex-initial"
                            >
                                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                                No
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

function StatusBadge({ status }: { status: string }) {
    const statusConfig: Record<
        string,
        { bg: string; text: string; label: string; icon: string }
    > = {
        missing: {
            bg: "bg-amber-50 ring-amber-200",
            text: "text-amber-700",
            label: "Pending",
            icon: "M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
        },
        uploaded: {
            bg: "bg-green-50 ring-green-200",
            text: "text-green-700",
            label: "Uploaded",
            icon: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
        },
        unknown: {
            bg: "bg-slate-50 ring-slate-200",
            text: "text-slate-700",
            label: "Unknown",
            icon: "M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
        },
        pending: {
            bg: "bg-blue-50 ring-blue-200",
            text: "text-blue-700",
            label: "Pending",
            icon: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z",
        },
        confirmed: {
            bg: "bg-emerald-50 ring-emerald-200",
            text: "text-emerald-700",
            label: "Confirmed",
            icon: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
        },
        not_applicable: {
            bg: "bg-gray-50 ring-gray-200",
            text: "text-gray-700",
            label: "N/A",
            icon: "M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636",
        },
    };

    const config = statusConfig[status] || statusConfig.unknown;

    return (
        <span
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ring-1 ${config.bg} ${config.text}`}
        >
            <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={config.icon} />
            </svg>
            {config.label}
        </span>
    );
}
