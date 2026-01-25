"use client";

import React, { useState, useEffect, useCallback } from "react";

// Types for flagged documents
export type Severity = "high" | "medium" | "low";
export type ReviewAction = "approve" | "reject" | "request_info";

export interface AIReasoning {
    // From AI agents
    anomaly?: {
        field: string;
        issue: string;
        severity: string;
        suggestion: string;
        expected_value?: string;
        actual_value?: string;
    };
    summary?: string;
    confidence_score?: number;
    is_valid?: boolean;
    agent_type?: string;
    document_type?: string;
    // From rule-based validators
    validator?: string;
    check?: string;
    missing_fields?: Array<{ field: string; reason: string }>;
    calculation?: Record<string, unknown>;
    duplicates?: Array<{ id: number; filename: string; supplier?: string }>;
    issues?: string[];
}

// Map agent types AND validator names to friendly names
const validatorLabels: Record<string, { label: string; color: string; icon: string }> = {
    // AI Agents
    InvoiceVerificationAgent: { label: "Invoice AI", color: "#0052CC", icon: "ai" },
    BankStatementVerificationAgent: { label: "Bank Statement AI", color: "#00875A", icon: "ai" },
    ReceiptVerificationAgent: { label: "Receipt AI", color: "#6554C0", icon: "ai" },
    VATCertificateVerificationAgent: { label: "VAT Certificate AI", color: "#FF5630", icon: "ai" },
    ContractVerificationAgent: { label: "Contract AI", color: "#FF991F", icon: "ai" },
    PayrollVerificationAgent: { label: "Payroll AI", color: "#00B8D9", icon: "ai" },
    // Rule-based validators
    InvoiceValidator: { label: "Invoice Check", color: "#0052CC", icon: "rule" },
    BankStatementValidator: { label: "Bank Statement Check", color: "#00875A", icon: "rule" },
    ReceiptValidator: { label: "Receipt Check", color: "#6554C0", icon: "rule" },
    VATCertificateValidator: { label: "VAT Certificate Check", color: "#FF5630", icon: "rule" },
    ContractValidator: { label: "Contract Check", color: "#FF991F", icon: "rule" },
    PayrollValidator: { label: "Payroll Check", color: "#00B8D9", icon: "rule" },
};

// Helper to get validator/agent info from aiReasoning
function getValidatorInfo(aiReasoning?: AIReasoning): { name: string; label: string; color: string; icon: string } | null {
    if (!aiReasoning) return null;

    const validatorName = aiReasoning.agent_type || aiReasoning.validator;
    if (!validatorName) return null;

    const config = validatorLabels[validatorName];
    if (config) {
        return { name: validatorName, ...config };
    }

    // Fallback for unknown validators
    return { name: validatorName, label: validatorName, color: "#5E6C84", icon: "rule" };
}

export interface FlaggedValidationResult {
    id: string;
    ruleType: string;
    status: "failed" | "warning";
    message: string;
    details?: string;
    fieldName?: string;
    expectedValue?: string;
    actualValue?: string;
    severity?: Severity;
    confidence?: number;
    aiReasoning?: AIReasoning;
    reviewedAt?: string;
    reviewedBy?: string;
    reviewAction?: ReviewAction;
}

export interface FlaggedDocument {
    id: string;
    filename: string;
    fileUrl: string | null;
    documentType: string;
    clientId: string;
    clientName: string;
    uploadedAt: string;
    validationResults: FlaggedValidationResult[];
}

export interface FlaggedDocumentsSummary {
    total: number;
    highSeverity: number;
    mediumSeverity: number;
    lowSeverity: number;
    pendingReview: number;
}

// Severity colors (Jira-like)
const severityConfig: Record<Severity, { bg: string; color: string; border: string; label: string }> = {
    high: { bg: "#FFEBE6", color: "#BF2600", border: "#DE350B", label: "HIGH" },
    medium: { bg: "#FFFAE6", color: "#974F0C", border: "#FF991F", label: "MEDIUM" },
    low: { bg: "#FFF9C4", color: "#594300", border: "#FFAB00", label: "LOW" },
};

// Icons
function FlagIcon({ className }: { className?: string }) {
    return (
        <svg className={className || "w-4 h-4"} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9" />
        </svg>
    );
}

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

function DocumentIcon() {
    return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
    );
}

function SpinnerIcon() {
    return (
        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
    );
}

function CheckCircleIcon() {
    return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
    );
}

function XCircleIcon() {
    return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
    );
}

function InfoIcon() {
    return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
    );
}

function EyeIcon() {
    return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
        </svg>
    );
}

function ExternalLinkIcon() {
    return (
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
        </svg>
    );
}

// Severity badge component
function SeverityBadge({ severity }: { severity: Severity }) {
    const config = severityConfig[severity];
    return (
        <span
            className="px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wide"
            style={{
                backgroundColor: config.bg,
                color: config.color,
                border: `1px solid ${config.border}`,
            }}
        >
            {config.label}
        </span>
    );
}

// Confidence indicator
function ConfidenceIndicator({ confidence }: { confidence: number }) {
    const percentage = Math.round(confidence * 100);
    const color = percentage >= 80 ? "#36B37E" : percentage >= 60 ? "#FF991F" : "#DE350B";

    return (
        <div className="flex items-center gap-1.5">
            <div className="w-12 h-1.5 bg-[#DFE1E6] rounded-full overflow-hidden">
                <div
                    className="h-full rounded-full transition-all duration-300"
                    style={{ width: `${percentage}%`, backgroundColor: color }}
                />
            </div>
            <span className="text-[10px] font-medium text-[#5E6C84]">{percentage}%</span>
        </div>
    );
}

// Validator badge component - shows which validator/agent flagged the issue
function ValidatorBadge({ aiReasoning, ruleType }: { aiReasoning?: AIReasoning; ruleType?: string }) {
    const validatorInfo = getValidatorInfo(aiReasoning);

    // If no validator info, show rule type
    if (!validatorInfo) {
        if (!ruleType) return null;

        // Map rule types to readable labels
        const ruleTypeLabels: Record<string, string> = {
            REQUIRED_FIELDS: "Required Fields",
            VAT_NUMBER_FORMAT: "VAT Format",
            DATE_IN_PERIOD: "Date Check",
            TOTALS_MATCH: "Calculation",
            VAT_RATE_VALID: "VAT Rate",
            DUPLICATE_DETECTION: "Duplicate",
            CURRENCY_VALID: "Currency",
            AI_ANOMALY: "AI Analysis",
        };

        return (
            <span
                className="px-1.5 py-0.5 rounded text-[9px] font-semibold tracking-wide flex items-center gap-1"
                style={{
                    backgroundColor: "#F4F5F7",
                    color: "#5E6C84",
                    border: "1px solid #DFE1E6",
                }}
            >
                {ruleTypeLabels[ruleType] || ruleType}
            </span>
        );
    }

    const isAI = validatorInfo.icon === "ai";

    return (
        <span
            className="px-1.5 py-0.5 rounded text-[9px] font-semibold tracking-wide flex items-center gap-1"
            style={{
                backgroundColor: `${validatorInfo.color}15`,
                color: validatorInfo.color,
                border: `1px solid ${validatorInfo.color}30`,
            }}
        >
            {isAI ? (
                // AI icon
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
            ) : (
                // Rule check icon
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                </svg>
            )}
            {validatorInfo.label}
        </span>
    );
}

// Single validation result card
function ValidationResultCard({
    result,
    onAction,
    isProcessing,
}: {
    result: FlaggedValidationResult;
    onAction: (action: ReviewAction) => void;
    isProcessing: boolean;
}) {
    const [showDetails, setShowDetails] = useState(false);
    const severity = (result.severity || "medium") as Severity;
    const config = severityConfig[severity];
    const isAIRule = result.ruleType === "AI_ANOMALY";

    return (
        <div
            className="border rounded overflow-hidden"
            style={{ borderColor: config.border, borderLeftWidth: "3px" }}
        >
            <div className="p-3 bg-white">
                {/* Header */}
                <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2 flex-wrap">
                        <SeverityBadge severity={severity} />
                        <ValidatorBadge aiReasoning={result.aiReasoning} ruleType={result.ruleType} />
                        {result.fieldName && (
                            <span className="text-[10px] text-[#5E6C84] uppercase">
                                {result.fieldName.replace(/_/g, " ")}
                            </span>
                        )}
                    </div>
                    {result.confidence !== undefined && (
                        <div className="flex items-center gap-1 text-[10px] text-[#5E6C84]">
                            <span>Confidence:</span>
                            <ConfidenceIndicator confidence={result.confidence} />
                        </div>
                    )}
                </div>

                {/* Issue message */}
                <p className="text-[12px] text-[#172B4D] font-medium mb-2">{result.message}</p>

                {/* Validation Details section */}
                {(result.aiReasoning || result.details) && (
                    <div className="mb-3">
                        <button
                            onClick={() => setShowDetails(!showDetails)}
                            className="flex items-center gap-1 text-[11px] text-[#0052CC] hover:text-[#0747A6] font-medium"
                        >
                            <ChevronIcon expanded={showDetails} />
                            {isAIRule ? "AI Analysis Details" : "Validation Details"}
                        </button>

                        {showDetails && (
                            <div className="mt-2 p-3 bg-[#F4F5F7] rounded text-[11px] space-y-2">
                                {/* Validator/Agent identification */}
                                {(result.aiReasoning?.agent_type || result.aiReasoning?.validator) && (
                                    <div className="flex items-center gap-2 pb-2 border-b border-[#DFE1E6]">
                                        <span className="text-[#5E6C84]">Checked by:</span>
                                        <span className="font-medium text-[#172B4D]">
                                            {validatorLabels[result.aiReasoning.agent_type || result.aiReasoning.validator || ""]?.label ||
                                             result.aiReasoning.agent_type || result.aiReasoning.validator}
                                        </span>
                                        {result.aiReasoning?.check && (
                                            <span className="text-[#97A0AF]">
                                                ({result.aiReasoning.check.replace(/_/g, " ")})
                                            </span>
                                        )}
                                        {result.aiReasoning?.document_type && (
                                            <span className="text-[#97A0AF]">
                                                - {result.aiReasoning.document_type.replace(/_/g, " ")}
                                            </span>
                                        )}
                                    </div>
                                )}

                                {/* Details/Summary */}
                                {(result.details || result.aiReasoning?.summary) && (
                                    <div>
                                        <span className="text-[#5E6C84] font-medium">Details:</span>
                                        <p className="text-[#172B4D] mt-0.5">
                                            {result.details || result.aiReasoning?.summary}
                                        </p>
                                    </div>
                                )}

                                {/* Missing fields list */}
                                {result.aiReasoning?.missing_fields && result.aiReasoning.missing_fields.length > 0 && (
                                    <div className="pt-2 border-t border-[#DFE1E6]">
                                        <span className="text-[#5E6C84] font-medium">Missing Fields:</span>
                                        <ul className="mt-1 space-y-1">
                                            {result.aiReasoning.missing_fields.map((mf, idx) => (
                                                <li key={idx} className="flex items-start gap-2">
                                                    <span className="text-[#BF2600] font-medium">{mf.field}:</span>
                                                    <span className="text-[#172B4D]">{mf.reason}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {/* Calculation details */}
                                {result.aiReasoning?.calculation && (
                                    <div className="pt-2 border-t border-[#DFE1E6]">
                                        <span className="text-[#5E6C84] font-medium">Calculation:</span>
                                        <div className="mt-1 p-2 bg-white rounded border border-[#DFE1E6] font-mono text-[10px]">
                                            {Object.entries(result.aiReasoning.calculation).map(([key, value]) => (
                                                <div key={key} className="flex justify-between">
                                                    <span className="text-[#5E6C84]">{key.replace(/_/g, " ")}:</span>
                                                    <span className="text-[#172B4D]">
                                                        {typeof value === "number" ? `£${value.toLocaleString()}` : String(value)}
                                                    </span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Duplicate documents */}
                                {result.aiReasoning?.duplicates && result.aiReasoning.duplicates.length > 0 && (
                                    <div className="pt-2 border-t border-[#DFE1E6]">
                                        <span className="text-[#5E6C84] font-medium">Potential Duplicates:</span>
                                        <ul className="mt-1 space-y-1">
                                            {result.aiReasoning.duplicates.map((dup, idx) => (
                                                <li key={idx} className="text-[#172B4D]">
                                                    ID #{dup.id}: {dup.filename} {dup.supplier && `(${dup.supplier})`}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {/* Issues list */}
                                {result.aiReasoning?.issues && result.aiReasoning.issues.length > 0 && (
                                    <div className="pt-2 border-t border-[#DFE1E6]">
                                        <span className="text-[#5E6C84] font-medium">Issues Found:</span>
                                        <ul className="mt-1 space-y-1 list-disc list-inside">
                                            {result.aiReasoning.issues.map((issue, idx) => (
                                                <li key={idx} className="text-[#172B4D]">{issue}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {/* AI Anomaly details */}
                                {result.aiReasoning?.anomaly && (
                                    <div className="pt-2 border-t border-[#DFE1E6]">
                                        <span className="text-[#5E6C84] font-medium">AI Finding:</span>
                                        <p className="text-[#172B4D] mt-0.5">
                                            {result.aiReasoning.anomaly.issue}
                                        </p>

                                        {result.aiReasoning.anomaly.suggestion && (
                                            <div className="mt-2 p-2 bg-[#DEEBFF] rounded">
                                                <span className="text-[#0747A6] font-medium">Recommendation: </span>
                                                <span className="text-[#172B4D]">
                                                    {result.aiReasoning.anomaly.suggestion}
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Expected vs Actual values */}
                                {(result.expectedValue || result.actualValue ||
                                  result.aiReasoning?.anomaly?.expected_value || result.aiReasoning?.anomaly?.actual_value) && (
                                    <div className="pt-2 border-t border-[#DFE1E6] grid grid-cols-2 gap-4">
                                        {(result.expectedValue || result.aiReasoning?.anomaly?.expected_value) && (
                                            <div className="p-2 bg-[#E3FCEF] rounded">
                                                <span className="text-[#006644] font-medium block text-[10px]">Expected:</span>
                                                <span className="text-[#006644]">
                                                    {result.expectedValue || result.aiReasoning?.anomaly?.expected_value}
                                                </span>
                                            </div>
                                        )}
                                        {(result.actualValue || result.aiReasoning?.anomaly?.actual_value) && (
                                            <div className="p-2 bg-[#FFEBE6] rounded">
                                                <span className="text-[#BF2600] font-medium block text-[10px]">Actual:</span>
                                                <span className="text-[#BF2600]">
                                                    {result.actualValue || result.aiReasoning?.anomaly?.actual_value}
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {/* Review status */}
                {result.reviewAction ? (
                    <div className="flex items-center gap-2 text-[11px] text-[#5E6C84]">
                        {result.reviewAction === "approve" && (
                            <span className="flex items-center gap-1 text-[#006644]">
                                <CheckCircleIcon /> Approved
                            </span>
                        )}
                        {result.reviewAction === "reject" && (
                            <span className="flex items-center gap-1 text-[#BF2600]">
                                <XCircleIcon /> Rejected
                            </span>
                        )}
                        {result.reviewAction === "request_info" && (
                            <span className="flex items-center gap-1 text-[#0052CC]">
                                <InfoIcon /> Info Requested
                            </span>
                        )}
                        {result.reviewedBy && (
                            <span className="text-[#97A0AF]">by {result.reviewedBy}</span>
                        )}
                    </div>
                ) : (
                    /* Action buttons */
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => onAction("approve")}
                            disabled={isProcessing}
                            className="flex items-center gap-1 px-2 py-1 text-[11px] font-medium text-[#006644] bg-[#E3FCEF] hover:bg-[#ABF5D1] rounded transition-colors disabled:opacity-50"
                        >
                            {isProcessing ? <SpinnerIcon /> : <CheckCircleIcon />}
                            Approve
                        </button>
                        <button
                            onClick={() => onAction("reject")}
                            disabled={isProcessing}
                            className="flex items-center gap-1 px-2 py-1 text-[11px] font-medium text-[#BF2600] bg-[#FFEBE6] hover:bg-[#FFBDAD] rounded transition-colors disabled:opacity-50"
                        >
                            {isProcessing ? <SpinnerIcon /> : <XCircleIcon />}
                            Reject
                        </button>
                        <button
                            onClick={() => onAction("request_info")}
                            disabled={isProcessing}
                            className="flex items-center gap-1 px-2 py-1 text-[11px] font-medium text-[#0052CC] bg-[#DEEBFF] hover:bg-[#B3D4FF] rounded transition-colors disabled:opacity-50"
                        >
                            {isProcessing ? <SpinnerIcon /> : <InfoIcon />}
                            Request Info
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

// Single document card
function FlaggedDocumentCard({
    document,
    onReviewAction,
    processingResultId,
}: {
    document: FlaggedDocument;
    onReviewAction: (docId: string, resultId: string, action: ReviewAction) => void;
    processingResultId: string | null;
}) {
    const [expanded, setExpanded] = useState(true);

    const highCount = document.validationResults.filter(
        (r) => r.severity === "high" || (!r.severity && r.status === "failed")
    ).length;
    const pendingCount = document.validationResults.filter((r) => !r.reviewAction).length;

    const handleViewDocument = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (document.fileUrl) {
            window.open(document.fileUrl, "_blank", "noopener,noreferrer");
        }
    };

    return (
        <div className="border border-[#DFE1E6] rounded overflow-hidden bg-white">
            {/* Document header */}
            <div className="flex items-center gap-3 px-3 py-2.5 bg-[#FAFBFC]">
                <button
                    onClick={() => setExpanded(!expanded)}
                    className="flex items-center gap-3 flex-1 min-w-0 hover:bg-[#F4F5F7] -m-1 p-1 rounded transition-colors text-left"
                >
                    <ChevronIcon expanded={expanded} />
                    <DocumentIcon />
                    <div className="flex-1 min-w-0">
                        <p className="text-[12px] font-medium text-[#172B4D] truncate">
                            {document.filename}
                        </p>
                        <p className="text-[10px] text-[#5E6C84]">
                            {document.clientName} | {document.documentType.replace(/_/g, " ")}
                        </p>
                    </div>
                </button>

                <div className="flex items-center gap-2 flex-shrink-0">
                    {/* View Document Button */}
                    {document.fileUrl && (
                        <button
                            onClick={handleViewDocument}
                            className="flex items-center gap-1 px-2 py-1 text-[11px] font-medium text-[#0052CC] bg-[#DEEBFF] hover:bg-[#B3D4FF] rounded transition-colors"
                            title="View Document"
                        >
                            <EyeIcon />
                            View
                            <ExternalLinkIcon />
                        </button>
                    )}

                    {highCount > 0 && (
                        <span className="flex items-center gap-1 px-1.5 py-0.5 bg-[#FFEBE6] text-[#BF2600] text-[9px] font-bold rounded">
                            {highCount} HIGH
                        </span>
                    )}
                    {pendingCount > 0 && (
                        <span className="flex items-center gap-1 px-1.5 py-0.5 bg-[#DEEBFF] text-[#0052CC] text-[9px] font-bold rounded">
                            {pendingCount} PENDING
                        </span>
                    )}
                </div>
            </div>

            {/* Validation results */}
            {expanded && (
                <div className="p-3 space-y-2 border-t border-[#DFE1E6]">
                    {document.validationResults.map((result) => (
                        <ValidationResultCard
                            key={result.id}
                            result={result}
                            onAction={(action) =>
                                onReviewAction(document.id, result.id, action)
                            }
                            isProcessing={processingResultId === result.id}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}

// Summary header
function SummaryHeader({ summary }: { summary: FlaggedDocumentsSummary }) {
    return (
        <div className="flex items-center gap-4 mb-4">
            <div className="flex items-center gap-1.5">
                <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: severityConfig.high.border }}
                />
                <span className="text-[11px] text-[#5E6C84]">
                    High: <span className="font-semibold text-[#172B4D]">{summary.highSeverity}</span>
                </span>
            </div>
            <div className="flex items-center gap-1.5">
                <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: severityConfig.medium.border }}
                />
                <span className="text-[11px] text-[#5E6C84]">
                    Medium: <span className="font-semibold text-[#172B4D]">{summary.mediumSeverity}</span>
                </span>
            </div>
            <div className="flex items-center gap-1.5">
                <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: severityConfig.low.border }}
                />
                <span className="text-[11px] text-[#5E6C84]">
                    Low: <span className="font-semibold text-[#172B4D]">{summary.lowSeverity}</span>
                </span>
            </div>
        </div>
    );
}

// Main component
interface FlaggedDocumentsProps {
    initialDocuments?: FlaggedDocument[];
    onRefresh?: () => void;
}

export function FlaggedDocuments({ initialDocuments, onRefresh }: FlaggedDocumentsProps) {
    const [documents, setDocuments] = useState<FlaggedDocument[]>(initialDocuments || []);
    const [summary, setSummary] = useState<FlaggedDocumentsSummary>({
        total: 0,
        highSeverity: 0,
        mediumSeverity: 0,
        lowSeverity: 0,
        pendingReview: 0,
    });
    const [isLoading, setIsLoading] = useState(!initialDocuments);
    const [error, setError] = useState<string | null>(null);
    const [processingResultId, setProcessingResultId] = useState<string | null>(null);
    const [statusMessage, setStatusMessage] = useState<string | null>(null);

    // Fetch flagged documents
    const fetchFlaggedDocuments = useCallback(async () => {
        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch("/api/flagged-documents");
            if (!response.ok) {
                throw new Error("Failed to fetch flagged documents");
            }

            const data = await response.json();
            if (data.success) {
                setDocuments(data.flaggedDocuments || []);
                setSummary(data.summary || {
                    total: 0,
                    highSeverity: 0,
                    mediumSeverity: 0,
                    lowSeverity: 0,
                    pendingReview: 0,
                });
            } else {
                throw new Error(data.error || "Failed to fetch flagged documents");
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "An error occurred");
        } finally {
            setIsLoading(false);
        }
    }, []);

    // Load data on mount
    useEffect(() => {
        if (!initialDocuments) {
            fetchFlaggedDocuments();
        } else {
            // Calculate summary from initial documents
            const allResults = initialDocuments.flatMap((d) => d.validationResults);
            setSummary({
                total: initialDocuments.length,
                highSeverity: allResults.filter((r) => r.severity === "high").length,
                mediumSeverity: allResults.filter((r) => r.severity === "medium").length,
                lowSeverity: allResults.filter((r) => r.severity === "low").length,
                pendingReview: allResults.filter((r) => !r.reviewAction).length,
            });
        }
    }, [initialDocuments, fetchFlaggedDocuments]);

    // Handle review action
    const handleReviewAction = async (
        docId: string,
        resultId: string,
        action: ReviewAction
    ) => {
        setProcessingResultId(resultId);
        setError(null);

        try {
            const response = await fetch(`/api/flagged-documents/${docId}/review`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ resultId, action }),
            });

            if (!response.ok) {
                throw new Error("Failed to submit review action");
            }

            const data = await response.json();
            if (data.success) {
                // Update local state
                setDocuments((prev) =>
                    prev.map((doc) => {
                        if (doc.id === docId) {
                            return {
                                ...doc,
                                validationResults: doc.validationResults.map((r) => {
                                    if (r.id === resultId) {
                                        return {
                                            ...r,
                                            reviewAction: action,
                                            reviewedAt: new Date().toISOString(),
                                            reviewedBy: "Current User", // TODO: Get from auth
                                        };
                                    }
                                    return r;
                                }),
                            };
                        }
                        return doc;
                    })
                );

                const actionLabels: Record<ReviewAction, string> = {
                    approve: "approved",
                    reject: "rejected",
                    request_info: "marked for follow-up",
                };
                setStatusMessage(`Issue ${actionLabels[action]} successfully`);
                setTimeout(() => setStatusMessage(null), 3000);

                // Recalculate summary
                const allResults = documents.flatMap((d) => d.validationResults);
                setSummary((prev) => ({
                    ...prev,
                    pendingReview: Math.max(0, prev.pendingReview - 1),
                }));

                // Notify parent to refresh dashboard data
                onRefresh?.();
            } else {
                throw new Error(data.error || "Failed to submit review action");
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "An error occurred");
        } finally {
            setProcessingResultId(null);
        }
    };

    // Filter documents to only show those with pending reviews
    const documentsWithPending = documents.filter((doc) =>
        doc.validationResults.some((r) => !r.reviewAction)
    );

    // If no flagged documents, show empty state
    if (!isLoading && documents.length === 0) {
        return (
            <div className="bg-white border border-[#DFE1E6] rounded p-4">
                <div className="flex items-center gap-2 mb-3">
                    <FlagIcon className="w-4 h-4 text-[#36B37E]" />
                    <h3 className="text-[12px] font-semibold text-[#172B4D]">
                        Flagged for Review
                    </h3>
                </div>
                <div className="text-center py-6">
                    <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-[#E3FCEF] flex items-center justify-center">
                        <CheckCircleIcon />
                    </div>
                    <p className="text-[12px] text-[#5E6C84]">
                        No documents require review
                    </p>
                    <p className="text-[10px] text-[#97A0AF] mt-1">
                        All AI validations have passed or been reviewed
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white border border-[#DFE1E6] rounded">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-[#DFE1E6]">
                <div className="flex items-center gap-2">
                    <FlagIcon className="w-4 h-4 text-[#DE350B]" />
                    <h3 className="text-[12px] font-semibold text-[#172B4D]">
                        Flagged for Review
                    </h3>
                    {summary.pendingReview > 0 && (
                        <span className="px-1.5 py-0.5 bg-[#FFEBE6] text-[#BF2600] text-[10px] font-bold rounded">
                            {summary.pendingReview}
                        </span>
                    )}
                </div>
                <button
                    onClick={() => {
                        fetchFlaggedDocuments();
                        onRefresh?.();
                    }}
                    disabled={isLoading}
                    className="text-[11px] font-medium text-[#5E6C84] hover:text-[#172B4D] transition-colors disabled:opacity-50"
                >
                    {isLoading ? <SpinnerIcon /> : "Refresh"}
                </button>
            </div>

            <div className="p-4">
                {/* Status message */}
                {statusMessage && (
                    <div className="mb-3 p-2 bg-[#E3FCEF] border border-[#ABF5D1] rounded text-[11px] text-[#006644] flex items-center gap-2">
                        <CheckCircleIcon />
                        {statusMessage}
                    </div>
                )}

                {/* Error message */}
                {error && (
                    <div className="mb-3 p-2 bg-[#FFEBE6] border border-[#FFBDAD] rounded text-[11px] text-[#BF2600]">
                        {error}
                    </div>
                )}

                {/* Loading state */}
                {isLoading && (
                    <div className="flex items-center justify-center py-8">
                        <SpinnerIcon />
                        <span className="ml-2 text-[12px] text-[#5E6C84]">
                            Loading flagged documents...
                        </span>
                    </div>
                )}

                {/* Summary */}
                {!isLoading && summary.total > 0 && <SummaryHeader summary={summary} />}

                {/* Document list */}
                {!isLoading && documentsWithPending.length > 0 && (
                    <div className="space-y-3">
                        {documentsWithPending.map((doc) => (
                            <FlaggedDocumentCard
                                key={doc.id}
                                document={doc}
                                onReviewAction={handleReviewAction}
                                processingResultId={processingResultId}
                            />
                        ))}
                    </div>
                )}

                {/* All reviewed state */}
                {!isLoading && documents.length > 0 && documentsWithPending.length === 0 && (
                    <div className="text-center py-4">
                        <p className="text-[12px] text-[#006644]">
                            All flagged items have been reviewed
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}

// Export a compact badge component for sidebar/nav
export function FlaggedDocumentsBadge({ count }: { count: number }) {
    if (count === 0) return null;

    return (
        <span className="px-1.5 py-0.5 bg-[#DE350B] text-white text-[9px] font-bold rounded-full min-w-[18px] text-center">
            {count > 99 ? "99+" : count}
        </span>
    );
}
