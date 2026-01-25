"use client";

import React, { useState, useEffect, useCallback } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Validation rule types
export type RuleType =
    | "required_fields"
    | "vat_number_format"
    | "date_in_period"
    | "totals_match"
    | "vat_rate_valid"
    | "duplicate_detection"
    | "ai_anomaly"
    | "currency_valid"
    | "supplier_valid"
    | "ACCOUNT_HOLDER_MATCH";

// Validation status
export type ValidationStatus = "passed" | "failed" | "warning" | "skipped" | "pending";

// Document status
export type DocumentStatus = "pending" | "processing" | "extracted" | "validated" | "failed" | "not_provided";

export interface ValidationResult {
    id: string;
    ruleType: RuleType;
    status: ValidationStatus;
    message?: string;
    details?: string;
    fieldName?: string;
    expectedValue?: string;
    actualValue?: string;
}

export interface DocumentVerificationData {
    id: string;
    filename: string;
    documentType: string;
    status: DocumentStatus;
    uploadedAt: Date;
    validationResults: ValidationResult[];
}

export interface VerificationSummary {
    totalDocuments: number;
    validatedDocuments: number;
    failedDocuments: number;
    pendingDocuments: number;
    notProvidedDocuments: number;
    passedValidations: number;
    failedValidations: number;
    warningValidations: number;
}

// Rule labels
const ruleLabels: Record<RuleType, string> = {
    required_fields: "Required Fields",
    vat_number_format: "VAT Number Format",
    date_in_period: "Date in Period",
    totals_match: "Totals Match",
    vat_rate_valid: "VAT Rate Valid",
    duplicate_detection: "Duplicate Check",
    ai_anomaly: "AI Anomaly Check",
    currency_valid: "Currency Valid",
    supplier_valid: "Supplier Valid",
    ACCOUNT_HOLDER_MATCH: "Account Holder Match",
};

// Status colors
const statusConfig: Record<ValidationStatus, { bg: string; color: string; label: string }> = {
    passed: { bg: "#E3FCEF", color: "#006644", label: "PASSED" },
    failed: { bg: "#FFEBE6", color: "#BF2600", label: "FAILED" },
    warning: { bg: "#FFFAE6", color: "#974F0C", label: "WARNING" },
    skipped: { bg: "#F4F5F7", color: "#5E6C84", label: "SKIPPED" },
    pending: { bg: "#DEEBFF", color: "#0747A6", label: "PENDING" },
};

const docStatusConfig: Record<DocumentStatus, { bg: string; color: string; label: string }> = {
    pending: { bg: "#DEEBFF", color: "#0747A6", label: "PENDING" },
    processing: { bg: "#DEEBFF", color: "#0747A6", label: "PROCESSING" },
    extracted: { bg: "#FFFAE6", color: "#974F0C", label: "EXTRACTED" },
    validated: { bg: "#E3FCEF", color: "#006644", label: "VALIDATED" },
    failed: { bg: "#FFEBE6", color: "#BF2600", label: "FAILED" },
    not_provided: { bg: "#F4F5F7", color: "#5E6C84", label: "NOT PROVIDED" },
};

// Status badge
function StatusBadge({ status, type = "validation" }: { status: string; type?: "validation" | "document" }) {
    const config = type === "document"
        ? docStatusConfig[status as DocumentStatus] || statusConfig.pending
        : statusConfig[status as ValidationStatus] || statusConfig.pending;

    return (
        <span
            className="px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wide"
            style={{ backgroundColor: config.bg, color: config.color }}
        >
            {config.label}
        </span>
    );
}

// Chevron icon
function ChevronIcon({ expanded }: { expanded: boolean }) {
    return (
        <svg
            className={`w-4 h-4 transition-transform duration-200 ${expanded ? "rotate-90" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            strokeWidth={2}
        >
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
        </svg>
    );
}

// Check icon
function CheckIcon() {
    return (
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
    );
}

// X icon
function XIcon() {
    return (
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
    );
}

// Warning icon
function WarningIcon() {
    return (
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
    );
}

// Spinner icon
function SpinnerIcon() {
    return (
        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
    );
}

// Single document verification item
function DocumentItem({
    doc,
    onReprocess,
    isReprocessing,
}: {
    doc: DocumentVerificationData;
    onReprocess?: (docId: string) => void;
    isReprocessing?: boolean;
}) {
    const [expanded, setExpanded] = useState(false);

    const isNotProvided = doc.status === "not_provided";
    const canReprocess = doc.status === "failed" || doc.status === "processing";
    const passed = doc.validationResults.filter((r) => r.status === "passed").length;
    const failed = doc.validationResults.filter((r) => r.status === "failed").length;
    const warnings = doc.validationResults.filter((r) => r.status === "warning").length;

    // For not_provided documents, show a non-expandable item
    if (isNotProvided) {
        return (
            <div className="border border-[#DFE1E6] rounded overflow-hidden opacity-60">
                <div className="w-full flex items-center gap-3 px-3 py-2 bg-[#F4F5F7]">
                    <div className="w-4 h-4 flex items-center justify-center text-[#5E6C84]">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                        <p className="text-[12px] font-medium text-[#5E6C84] truncate">{doc.filename}</p>
                        <p className="text-[10px] text-[#97A0AF] uppercase">{doc.documentType.replace(/_/g, " ")} - Required</p>
                    </div>
                    <StatusBadge status={doc.status} type="document" />
                </div>
            </div>
        );
    }

    return (
        <div className="border border-[#DFE1E6] rounded overflow-hidden">
            <div
                role="button"
                tabIndex={0}
                onClick={() => setExpanded(!expanded)}
                onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        setExpanded((prev) => !prev);
                    }
                }}
                className="w-full flex items-center gap-3 px-3 py-2 bg-[#FAFBFC] hover:bg-[#F4F5F7] transition-colors text-left cursor-pointer"
            >
                <ChevronIcon expanded={expanded} />
                <div className="flex-1 min-w-0">
                    <p className="text-[12px] font-medium text-[#172B4D] truncate">{doc.filename}</p>
                    <p className="text-[10px] text-[#5E6C84] uppercase">{doc.documentType.replace(/_/g, " ")}</p>
                </div>
                <div className="flex items-center gap-2">
                    {failed > 0 && (
                        <span className="flex items-center gap-1 text-[10px] text-[#BF2600]">
                            <XIcon /> {failed}
                        </span>
                    )}
                    {warnings > 0 && (
                        <span className="flex items-center gap-1 text-[10px] text-[#974F0C]">
                            <WarningIcon /> {warnings}
                        </span>
                    )}
                    {passed > 0 && (
                        <span className="flex items-center gap-1 text-[10px] text-[#006644]">
                            <CheckIcon /> {passed}
                        </span>
                    )}
                    <StatusBadge status={doc.status} type="document" />
                    {canReprocess && onReprocess && (
                        <button
                            type="button"
                            onClick={(event) => {
                                event.stopPropagation();
                                onReprocess(doc.id);
                            }}
                            disabled={isReprocessing}
                            className="ml-1 text-[10px] font-semibold text-[#5243AA] hover:text-[#403294] transition-colors disabled:opacity-50"
                        >
                            {isReprocessing ? "Reprocessing..." : "Reprocess"}
                        </button>
                    )}
                </div>
            </div>

            {expanded && doc.validationResults.length > 0 && (
                <div className="border-t border-[#DFE1E6] bg-white">
                    {doc.validationResults.map((result) => (
                        <div
                            key={result.id}
                            className="flex items-start gap-2 px-3 py-2 border-b border-[#EBECF0] last:border-b-0"
                        >
                            <div
                                className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
                                style={{
                                    backgroundColor: statusConfig[result.status].bg,
                                    color: statusConfig[result.status].color,
                                }}
                            >
                                {result.status === "passed" && <CheckIcon />}
                                {result.status === "failed" && <XIcon />}
                                {result.status === "warning" && <WarningIcon />}
                                {(result.status === "skipped" || result.status === "pending") && (
                                    <span className="text-[10px] font-bold">-</span>
                                )}
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-[11px] font-medium text-[#172B4D]">
                                    {ruleLabels[result.ruleType] || result.ruleType}
                                </p>
                                {result.message && (
                                    <p className="text-[10px] text-[#5E6C84] mt-0.5">{result.message}</p>
                                )}
                                {result.fieldName && result.status === "failed" && (
                                    <div className="mt-1 text-[10px]">
                                        <span className="text-[#5E6C84]">Field: </span>
                                        <span className="text-[#172B4D] font-medium">{result.fieldName}</span>
                                        {result.expectedValue && (
                                            <>
                                                <span className="text-[#5E6C84]"> | Expected: </span>
                                                <span className="text-[#006644]">{result.expectedValue}</span>
                                            </>
                                        )}
                                        {result.actualValue && (
                                            <>
                                                <span className="text-[#5E6C84]"> | Got: </span>
                                                <span className="text-[#BF2600]">{result.actualValue}</span>
                                            </>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {expanded && doc.validationResults.length === 0 && (
                <div className="px-3 py-4 text-center text-[11px] text-[#5E6C84] bg-white border-t border-[#DFE1E6]">
                    No validation results yet
                </div>
            )}
        </div>
    );
}

// Summary stats
function SummaryStats({ summary }: { summary: VerificationSummary }) {
    const stats = [
        { label: "Validated", value: summary.validatedDocuments, color: "#36B37E" },
        { label: "Failed", value: summary.failedDocuments, color: "#DE350B" },
        { label: "Pending", value: summary.pendingDocuments, color: "#0052CC" },
        { label: "Not Provided", value: summary.notProvidedDocuments, color: "#5E6C84" },
    ].filter(stat => stat.value > 0);

    return (
        <div className="flex items-center gap-4 mb-3">
            {stats.map((stat) => (
                <div key={stat.label} className="flex items-center gap-1.5">
                    <span
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: stat.color }}
                    />
                    <span className="text-[11px] text-[#5E6C84]">
                        {stat.label}: <span className="font-semibold text-[#172B4D]">{stat.value}</span>
                    </span>
                </div>
            ))}
        </div>
    );
}

// API functions - fetches from Next.js API (Prisma) for documents, Python backend for validation
async function fetchVerificationData(clientId: string): Promise<{
    documents: DocumentVerificationData[];
    summary: VerificationSummary;
    periodId?: number;
}> {
    const emptyResult = {
        documents: [],
        summary: {
            totalDocuments: 0,
            validatedDocuments: 0,
            failedDocuments: 0,
            pendingDocuments: 0,
            notProvidedDocuments: 0,
            passedValidations: 0,
            failedValidations: 0,
            warningValidations: 0,
        },
    };

    try {
        console.log(`[fetchVerificationData] Fetching documents for client ${clientId}`);

        // Use Next.js API route which queries Prisma directly
        const response = await fetch(`/api/documents/${clientId}`, {
            headers: { "Content-Type": "application/json" },
        });

        console.log(`[fetchVerificationData] Response status: ${response.status}`);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error(`[fetchVerificationData] Error:`, errorData);
            return emptyResult;
        }

        const data = await response.json();
        console.log(`[fetchVerificationData] Received:`, data);

        if (!data.success) {
            console.warn(`[fetchVerificationData] API returned success=false`);
            return emptyResult;
        }

        // Transform documents to our format
        const documents: DocumentVerificationData[] = (data.documents || []).map((doc: any) => ({
            id: doc.id?.toString(),
            filename: doc.filename || "Unknown",
            documentType: doc.documentType || "OTHER",
            status: (doc.status || "pending").toLowerCase() as DocumentStatus,
            uploadedAt: new Date(doc.uploadedAt || Date.now()),
            validationResults: (doc.validationResults || []).map((r: any) => ({
                id: r.id?.toString() || Math.random().toString(),
                ruleType: r.ruleType,
                status: (r.status || "pending").toLowerCase() as ValidationStatus,
                message: r.message,
                details: r.details,
                fieldName: r.fieldName,
                expectedValue: r.expectedValue,
                actualValue: r.actualValue,
            })),
        }));

        return {
            documents,
            summary: data.summary || emptyResult.summary,
            periodId: data.periodId,
        };
    } catch (error) {
        console.error("Error fetching verification data:", error);
        return emptyResult;
    }
}

async function runExtraction(periodId: number): Promise<{ success: boolean; message: string; queuedCount: number }> {
    try {
        // Call Python backend to extract all pending documents
        const response = await fetch(`${API_BASE_URL}/api/v1/documents/process-all/${periodId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            return {
                success: false,
                message: errorData.message || errorData.detail || `Extraction failed (${response.status})`,
                queuedCount: 0,
            };
        }

        const result = await response.json();
        return {
            success: true,
            message: result.message || "Extraction started",
            queuedCount: result.queued_count || 0,
        };
    } catch (error) {
        console.error("Error running extraction:", error);
        return {
            success: false,
            message: error instanceof Error ? error.message : "Failed to connect to extraction service",
            queuedCount: 0,
        };
    }
}

async function reprocessStuckDocuments(olderThanMinutes: number): Promise<{ success: boolean; message: string; requeuedCount: number }> {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/documents/reprocess-stuck`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ older_than_minutes: olderThanMinutes, requeue: true }),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            return {
                success: false,
                message: errorData.message || errorData.detail || `Reprocess failed (${response.status})`,
                requeuedCount: 0,
            };
        }

        const result = await response.json();
        return {
            success: true,
            message: "Reprocess started",
            requeuedCount: result.requeued_count || 0,
        };
    } catch (error) {
        console.error("Error reprocessing stuck documents:", error);
        return {
            success: false,
            message: error instanceof Error ? error.message : "Failed to connect to processing service",
            requeuedCount: 0,
        };
    }
}

async function reprocessDocument(docId: string): Promise<{ success: boolean; message: string }> {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/documents/${docId}/process?force=true`, {
            method: "POST",
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            return {
                success: false,
                message: errorData.message || errorData.detail || `Reprocess failed (${response.status})`,
            };
        }

        return { success: true, message: "Reprocess queued" };
    } catch (error) {
        console.error("Error reprocessing document:", error);
        return {
            success: false,
            message: error instanceof Error ? error.message : "Failed to connect to processing service",
        };
    }
}

async function runValidation(periodId: number): Promise<{ success: boolean; message: string }> {
    try {
        // Call Python backend to run validation for the VAT period
        const response = await fetch(`${API_BASE_URL}/api/v1/validation/run-period/${periodId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            return {
                success: false,
                message: errorData.message || errorData.detail || `Validation failed (${response.status})`,
            };
        }

        const result = await response.json();
        return {
            success: true,
            message: result.message || "Validation started",
        };
    } catch (error) {
        console.error("Error running validation:", error);
        return {
            success: false,
            message: error instanceof Error ? error.message : "Failed to connect to validation service",
        };
    }
}

// Main component props
interface DocumentVerificationProps {
    clientId?: string;
    documents?: DocumentVerificationData[];
    summary?: VerificationSummary;
    onValidationComplete?: () => void;
}

export function DocumentVerification({
    clientId,
    documents: initialDocuments,
    summary: initialSummary,
    onValidationComplete,
}: DocumentVerificationProps) {
    const [documents, setDocuments] = useState<DocumentVerificationData[]>(initialDocuments || []);
    const [summary, setSummary] = useState<VerificationSummary | undefined>(initialSummary);
    const [periodId, setPeriodId] = useState<number | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [isRunning, setIsRunning] = useState(false);
    const [isExtracting, setIsExtracting] = useState(false);
    const [isReprocessing, setIsReprocessing] = useState(false);
    const [reprocessingDocId, setReprocessingDocId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [statusMessage, setStatusMessage] = useState<string | null>(null);

    // Fetch data on mount and when clientId changes
    const fetchData = useCallback(async () => {
        if (!clientId) return;

        setIsLoading(true);
        setError(null);

        try {
            console.log(`[DocumentVerification] Fetching data for client: ${clientId}`);
            const data = await fetchVerificationData(clientId);
            console.log(`[DocumentVerification] Received:`, {
                documents: data.documents.length,
                periodId: data.periodId,
                summary: data.summary
            });
            setDocuments(data.documents);
            setSummary(data.summary);
            if (data.periodId) {
                setPeriodId(data.periodId);
            } else {
                setError("No VAT period found for this client. Create a VAT period first.");
            }
        } catch (err) {
            console.error("Error fetching verification data:", err);
            setError(err instanceof Error ? err.message : "Failed to load data");
        } finally {
            setIsLoading(false);
        }
    }, [clientId]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    // Run extraction handler
    const handleRunExtraction = async () => {
        if (!periodId) {
            setError("No VAT period found for this client");
            return;
        }

        const pendingDocs = documents.filter(d => d.status === "pending");
        if (pendingDocs.length === 0) {
            setError("No pending documents to extract. Documents may already be processed.");
            return;
        }

        setIsExtracting(true);
        setError(null);
        setStatusMessage(`Starting extraction for ${pendingDocs.length} document(s)...`);

        const result = await runExtraction(periodId);

        if (!result.success) {
            setError(result.message);
            setStatusMessage(null);
            setIsExtracting(false);
            return;
        }

        setStatusMessage(`Extracting ${result.queuedCount} document(s)...`);

        // Poll for extraction completion
        let attempts = 0;
        const maxAttempts = 30; // 60 seconds max

        const pollForExtraction = async () => {
            attempts++;

            try {
                const data = await fetchVerificationData(clientId!);
                setDocuments(data.documents);
                setSummary(data.summary);

                const stillPending = data.documents.filter(
                    d => d.status === "pending" || d.status === "processing"
                ).length;

                const extractedCount = data.documents.filter(d => d.status === "extracted").length;

                setStatusMessage(`Extracting... ${extractedCount} extracted, ${stillPending} remaining`);

                if (stillPending === 0 || attempts >= maxAttempts) {
                    setIsExtracting(false);
                    if (stillPending === 0) {
                        setStatusMessage(`Extraction complete! ${extractedCount} document(s) ready for validation.`);
                        setTimeout(() => setStatusMessage(null), 3000);
                    } else {
                        setStatusMessage("Extraction still processing in background. Click refresh to check status.");
                        setTimeout(() => setStatusMessage(null), 5000);
                    }
                    return;
                }

                setTimeout(pollForExtraction, 2000);
            } catch (err) {
                console.error("Error polling extraction status:", err);
                setIsExtracting(false);
                setStatusMessage(null);
                setError("Failed to check extraction status");
            }
        };

        setTimeout(pollForExtraction, 2000);
    };

    // Run validation handler with polling
    const handleRunValidation = async () => {
        if (!periodId) {
            setError("No VAT period found for this client");
            return;
        }

        // Filter out "not_provided" documents - they can't be validated
        const providedDocs = documents.filter(d => d.status !== "not_provided");
        const notProvidedCount = documents.filter(d => d.status === "not_provided").length;

        // Check if there are pending documents that need extraction first
        const pendingDocs = providedDocs.filter(d => d.status === "pending");
        if (pendingDocs.length > 0) {
            // Auto-trigger extraction first
            setStatusMessage(`${pendingDocs.length} document(s) need extraction first. Starting extraction...`);
            await handleRunExtraction();
            // After extraction completes, the user can click Run All again
            return;
        }

        // Check if there are documents ready to validate (status = extracted)
        const extractedDocs = providedDocs.filter(d => d.status === "extracted");
        if (extractedDocs.length === 0) {
            const processingDocs = providedDocs.filter(d => d.status === "processing");
            if (processingDocs.length > 0) {
                setError(`${processingDocs.length} document(s) still being processed by AI. Wait for extraction to complete before validating.`);
            } else if (providedDocs.length === 0) {
                if (notProvidedCount > 0) {
                    setError(`${notProvidedCount} required document(s) not yet uploaded. Upload documents first.`);
                } else {
                    setError("No documents found to validate. Upload documents first.");
                }
            } else {
                setError("All uploaded documents have already been validated.");
            }
            return;
        }

        setIsRunning(true);
        setError(null);
        setStatusMessage(`Starting validation for ${extractedDocs.length} document(s)...`);

        const result = await runValidation(periodId);

        if (!result.success) {
            setError(result.message);
            setStatusMessage(null);
            setIsRunning(false);
            return;
        }

        setStatusMessage(`Validating ${extractedDocs.length} document(s)...`);

        // Poll for completion - check every 2 seconds, max 30 seconds
        let attempts = 0;
        const maxAttempts = 15;

        const pollForCompletion = async () => {
            attempts++;

            try {
                // Fetch fresh data
                const data = await fetchVerificationData(clientId!);
                setDocuments(data.documents);
                setSummary(data.summary);

                // Filter out "not_provided" documents - they can't be validated
                const providedDocs = data.documents.filter(d => d.status !== "not_provided");

                // Check if any provided documents are still pending validation
                const pendingCount = providedDocs.filter(
                    d => d.status === "pending" || d.status === "processing" || d.status === "extracted"
                ).length;

                const validatedCount = providedDocs.filter(d => d.status === "validated").length;
                const failedCount = providedDocs.filter(d => d.status === "failed").length;
                const processedCount = validatedCount + failedCount;

                // Only show progress if there are provided documents
                if (providedDocs.length > 0) {
                    setStatusMessage(`Validating... ${processedCount}/${providedDocs.length} documents processed`);
                }

                // If all provided documents are processed or max attempts reached
                if (pendingCount === 0 || attempts >= maxAttempts) {
                    setIsRunning(false);
                    if (pendingCount === 0 && providedDocs.length > 0) {
                        setStatusMessage(`Validation complete! ${validatedCount} passed, ${failedCount} failed`);
                        // Clear success message after 3 seconds
                        setTimeout(() => setStatusMessage(null), 3000);
                        // Notify parent to refresh dashboard data
                        onValidationComplete?.();
                    } else if (pendingCount > 0) {
                        // Don't show "complete" message - validation is still in progress
                        setStatusMessage("Validation still processing in background. Click refresh to check status.");
                        setTimeout(() => setStatusMessage(null), 5000);
                    } else {
                        // No provided documents to validate
                        setStatusMessage(null);
                    }
                    return;
                }

                // Continue polling
                setTimeout(pollForCompletion, 2000);
            } catch (err) {
                console.error("Error polling validation status:", err);
                setIsRunning(false);
                setStatusMessage(null);
                setError("Failed to check validation status");
            }
        };

        // Start polling after a short delay
        setTimeout(pollForCompletion, 2000);
    };

    // Manual refresh handler
    const handleRefresh = () => {
        setStatusMessage("Refreshing...");
        fetchData().then(() => {
            setStatusMessage(null);
        });
    };

    const handleReprocessStuck = async () => {
        const processingDocs = documents.filter((doc) => doc.status === "processing");
        if (processingDocs.length === 0) {
            setError("No processing documents to reprocess.");
            return;
        }

        setIsReprocessing(true);
        setError(null);
        setStatusMessage(`Reprocessing ${processingDocs.length} document(s) stuck in processing...`);

        const result = await reprocessStuckDocuments(30);
        if (!result.success) {
            setError(result.message);
            setStatusMessage(null);
            setIsReprocessing(false);
            return;
        }

        setStatusMessage(`Reprocess queued for ${result.requeuedCount} document(s).`);
        await fetchData();
        setTimeout(() => setStatusMessage(null), 3000);
        setIsReprocessing(false);
    };

    const handleReprocessDocument = async (docId: string) => {
        setReprocessingDocId(docId);
        setError(null);

        const result = await reprocessDocument(docId);
        if (!result.success) {
            setError(result.message);
            setReprocessingDocId(null);
            return;
        }

        setStatusMessage("Reprocess queued.");
        await fetchData();
        setTimeout(() => setStatusMessage(null), 2000);
        setReprocessingDocId(null);
    };

    // Calculate summary if not provided
    const calculatedSummary: VerificationSummary = summary || {
        totalDocuments: documents.length,
        validatedDocuments: documents.filter((d) => d.status === "validated").length,
        failedDocuments: documents.filter((d) => d.status === "failed").length,
        pendingDocuments: documents.filter((d) => d.status === "pending" || d.status === "processing" || d.status === "extracted").length,
        notProvidedDocuments: documents.filter((d) => d.status === "not_provided").length,
        passedValidations: documents.flatMap((d) => d.validationResults).filter((r) => r.status === "passed").length,
        failedValidations: documents.flatMap((d) => d.validationResults).filter((r) => r.status === "failed").length,
        warningValidations: documents.flatMap((d) => d.validationResults).filter((r) => r.status === "warning").length,
    };

    // Calculate validation rate (excluding not_provided documents from the denominator)
    const providedDocuments = calculatedSummary.totalDocuments - calculatedSummary.notProvidedDocuments;
    const validationRate = providedDocuments > 0
        ? Math.round((calculatedSummary.validatedDocuments / providedDocuments) * 100)
        : 0;

    return (
        <div>
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
                <h3 className="text-[11px] font-semibold text-[#5E6C84] uppercase tracking-wider">
                    Document Verification
                </h3>
                <div className="flex items-center gap-2">
                    {isLoading && <SpinnerIcon />}
                    {clientId && (
                        <>
                            <button
                                onClick={handleRefresh}
                                disabled={isRunning || isLoading || isExtracting || isReprocessing}
                                className="text-[11px] font-medium text-[#5E6C84] hover:text-[#172B4D] transition-colors disabled:opacity-50"
                                title="Refresh"
                            >
                                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                </svg>
                            </button>
                            <button
                                onClick={handleRunExtraction}
                                disabled={isRunning || isLoading || isExtracting || isReprocessing}
                                className="text-[11px] font-medium text-[#6554C0] hover:text-[#5243AA] transition-colors disabled:opacity-50 flex items-center gap-1"
                                title="Extract data from pending documents"
                            >
                                {isExtracting && <SpinnerIcon />}
                                {isExtracting ? "Extracting..." : "Extract"}
                            </button>
                            <button
                                onClick={handleReprocessStuck}
                                disabled={isRunning || isLoading || isExtracting || isReprocessing}
                                className="text-[11px] font-medium text-[#FF991F] hover:text-[#FF8B00] transition-colors disabled:opacity-50 flex items-center gap-1"
                                title="Reprocess documents stuck in processing"
                            >
                                {isReprocessing && <SpinnerIcon />}
                                {isReprocessing ? "Reprocessing..." : "Reprocess stuck"}
                            </button>
                            <button
                                onClick={handleRunValidation}
                                disabled={isRunning || isLoading || isExtracting || isReprocessing}
                                className="text-[11px] font-medium text-[#0052CC] hover:text-[#0747A6] transition-colors disabled:opacity-50 flex items-center gap-1"
                            >
                                {isRunning && <SpinnerIcon />}
                                {isRunning ? "Validating..." : "Validate"}
                            </button>
                        </>
                    )}
                </div>
            </div>

            {/* Status message */}
            {statusMessage && (
                <div className={`mb-3 p-2 rounded text-[11px] flex items-center gap-2 ${
                    statusMessage.includes("complete")
                        ? "bg-[#E3FCEF] border border-[#ABF5D1] text-[#006644]"
                        : statusMessage.includes("Extracting")
                        ? "bg-[#EAE6FF] border border-[#C0B6F2] text-[#5243AA]"
                        : "bg-[#DEEBFF] border border-[#B3D4FF] text-[#0747A6]"
                }`}>
                    {(isRunning || isExtracting) && <SpinnerIcon />}
                    {statusMessage.includes("complete") && (
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                    )}
                    {statusMessage}
                </div>
            )}

            {/* Error message */}
            {error && (
                <div className="mb-3 p-2 bg-[#FFEBE6] border border-[#FFBDAD] rounded text-[11px] text-[#BF2600]">
                    {error}
                </div>
            )}

            {/* Progress bar */}
            <div className="mb-3">
                <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] text-[#5E6C84]">Verification Progress</span>
                    <span className="text-[10px] font-semibold text-[#172B4D]">{validationRate}%</span>
                </div>
                <div className="h-1.5 bg-[#DFE1E6] rounded-full overflow-hidden">
                    <div
                        className="h-full rounded-full transition-all duration-300"
                        style={{
                            width: `${validationRate}%`,
                            backgroundColor: validationRate === 100 ? "#36B37E" : "#0052CC",
                        }}
                    />
                </div>
            </div>

            {/* Summary stats */}
            <SummaryStats summary={calculatedSummary} />

            {/* Loading state */}
            {isLoading && documents.length === 0 && (
                <div className="p-4 bg-[#F4F5F7] rounded text-center flex flex-col items-center">
                    <SpinnerIcon />
                    <p className="text-[12px] text-[#5E6C84] mt-2">Fetching documents from server...</p>
                </div>
            )}

            {/* Document list */}
            {!isLoading && documents.length > 0 && (
                <div className="space-y-2">
                    {documents.map((doc) => (
                        <DocumentItem
                            key={doc.id}
                            doc={doc}
                            onReprocess={handleReprocessDocument}
                            isReprocessing={reprocessingDocId === doc.id}
                        />
                    ))}
                </div>
            )}

            {/* Empty state */}
            {!isLoading && documents.length === 0 && !error && (
                <div className="p-4 bg-[#F4F5F7] rounded text-center">
                    <p className="text-[12px] text-[#5E6C84]">No documents found for this client</p>
                    <p className="text-[10px] text-[#97A0AF] mt-1">
                        {periodId
                            ? "Upload documents to the client's VAT period to begin verification."
                            : "Create a VAT period and upload documents first."
                        }
                    </p>
                </div>
            )}

            {/* Document Status Breakdown */}
            {documents.length > 0 && (
                <div className="mt-3 p-3 bg-[#F4F5F7] rounded">
                    <p className="text-[10px] font-semibold text-[#5E6C84] uppercase mb-2">Document Status</p>
                    <div className="grid grid-cols-6 gap-1 text-center">
                        <div className="p-1.5 bg-white rounded">
                            <p className="text-[14px] font-semibold text-[#5E6C84]">
                                {documents.filter(d => d.status === "not_provided").length}
                            </p>
                            <p className="text-[7px] text-[#5E6C84] uppercase">Not Provided</p>
                        </div>
                        <div className="p-1.5 bg-white rounded">
                            <p className="text-[14px] font-semibold text-[#0747A6]">
                                {documents.filter(d => d.status === "pending").length}
                            </p>
                            <p className="text-[8px] text-[#5E6C84] uppercase">Pending</p>
                        </div>
                        <div className="p-1.5 bg-white rounded">
                            <p className="text-[14px] font-semibold text-[#0747A6]">
                                {documents.filter(d => d.status === "processing").length}
                            </p>
                            <p className="text-[8px] text-[#5E6C84] uppercase">Processing</p>
                        </div>
                        <div className="p-1.5 bg-white rounded">
                            <p className="text-[14px] font-semibold text-[#974F0C]">
                                {documents.filter(d => d.status === "extracted").length}
                            </p>
                            <p className="text-[8px] text-[#5E6C84] uppercase">Extracted</p>
                        </div>
                        <div className="p-1.5 bg-white rounded">
                            <p className="text-[14px] font-semibold text-[#006644]">
                                {documents.filter(d => d.status === "validated").length}
                            </p>
                            <p className="text-[8px] text-[#5E6C84] uppercase">Validated</p>
                        </div>
                        <div className="p-1.5 bg-white rounded">
                            <p className="text-[14px] font-semibold text-[#BF2600]">
                                {documents.filter(d => d.status === "failed").length}
                            </p>
                            <p className="text-[8px] text-[#5E6C84] uppercase">Failed</p>
                        </div>
                    </div>
                    <p className="text-[9px] text-[#5E6C84] mt-2 italic">
                        Click "Extract" to process pending documents with AI, then "Validate" to run compliance checks.
                    </p>
                </div>
            )}

            {/* Validation Results Summary */}
            {documents.length > 0 && (calculatedSummary.passedValidations > 0 || calculatedSummary.failedValidations > 0 || calculatedSummary.warningValidations > 0) && (
                <div className="mt-3 p-3 bg-[#F4F5F7] rounded">
                    <p className="text-[10px] font-semibold text-[#5E6C84] uppercase mb-2">Validation Results</p>
                    <div className="grid grid-cols-3 gap-2 text-center">
                        <div>
                            <p className="text-[16px] font-semibold text-[#006644]">{calculatedSummary.passedValidations}</p>
                            <p className="text-[9px] text-[#5E6C84] uppercase">Passed</p>
                        </div>
                        <div>
                            <p className="text-[16px] font-semibold text-[#BF2600]">{calculatedSummary.failedValidations}</p>
                            <p className="text-[9px] text-[#5E6C84] uppercase">Failed</p>
                        </div>
                        <div>
                            <p className="text-[16px] font-semibold text-[#974F0C]">{calculatedSummary.warningValidations}</p>
                            <p className="text-[9px] text-[#5E6C84] uppercase">Warnings</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// Export mock data function for testing/demo
export function getMockVerificationData(): DocumentVerificationData[] {
    return [
        {
            id: "1",
            filename: "invoice_001.pdf",
            documentType: "INVOICE",
            status: "validated",
            uploadedAt: new Date(),
            validationResults: [
                { id: "1a", ruleType: "required_fields", status: "passed", message: "All required fields present" },
                { id: "1b", ruleType: "vat_number_format", status: "passed", message: "VAT number format valid" },
                { id: "1c", ruleType: "date_in_period", status: "passed", message: "Invoice date within VAT period" },
                { id: "1d", ruleType: "totals_match", status: "passed", message: "Net + VAT = Gross" },
                { id: "1e", ruleType: "vat_rate_valid", status: "passed", message: "Standard rate (20%)" },
            ],
        },
        {
            id: "2",
            filename: "receipt_march_15.pdf",
            documentType: "RECEIPT",
            status: "failed",
            uploadedAt: new Date(),
            validationResults: [
                { id: "2a", ruleType: "required_fields", status: "failed", message: "Missing required fields", fieldName: "vat_amount", expectedValue: "number", actualValue: "null" },
                { id: "2b", ruleType: "vat_number_format", status: "skipped", message: "Skipped due to missing data" },
                { id: "2c", ruleType: "totals_match", status: "warning", message: "Totals mismatch by £0.01", fieldName: "gross_amount", expectedValue: "£120.00", actualValue: "£119.99" },
            ],
        },
        {
            id: "3",
            filename: "bank_statement_q1.pdf",
            documentType: "BANK_STATEMENT",
            status: "extracted",
            uploadedAt: new Date(),
            validationResults: [],
        },
    ];
}
