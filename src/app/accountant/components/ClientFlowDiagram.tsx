"use client";

import React from "react";

export type FlowStage =
    | "onboarding"
    | "documents"
    | "bank_connection"
    | "verification"
    | "review"
    | "ready"
    | "submitted";

interface StageConfig {
    id: FlowStage;
    label: string;
    description: string;
    icon: React.ReactNode;
}

const stages: StageConfig[] = [
    {
        id: "onboarding",
        label: "ONBOARDING",
        description: "Client registered",
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
        ),
    },
    {
        id: "documents",
        label: "DOCUMENTS",
        description: "Collecting files",
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
        ),
    },
    {
        id: "bank_connection",
        label: "BANK",
        description: "Connect account",
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
            </svg>
        ),
    },
    {
        id: "verification",
        label: "VERIFICATION",
        description: "Validating docs",
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
        ),
    },
    {
        id: "review",
        label: "REVIEW",
        description: "Accountant check",
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
        ),
    },
    {
        id: "ready",
        label: "READY",
        description: "Ready to submit",
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
        ),
    },
    {
        id: "submitted",
        label: "SUBMITTED",
        description: "VAT filed",
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
        ),
    },
];

interface ClientFlowDiagramProps {
    currentStage: FlowStage;
    completedStages?: FlowStage[];
    failedStages?: FlowStage[];
    onStageClick?: (stage: FlowStage) => void;
    variant?: "horizontal" | "vertical";
}

export function ClientFlowDiagram({
    currentStage,
    completedStages = [],
    failedStages = [],
    onStageClick,
    variant = "horizontal",
}: ClientFlowDiagramProps) {
    const currentIndex = stages.findIndex((s) => s.id === currentStage);

    const getStageStatus = (stage: StageConfig, index: number) => {
        // Check if this stage has failed validation
        if (failedStages.includes(stage.id)) return "failed";
        if (completedStages.includes(stage.id)) return "completed";
        if (stage.id === currentStage) {
            // If current stage is in failed stages, show as failed
            if (failedStages.includes(stage.id)) return "failed";
            return "current";
        }
        if (index < currentIndex) return "completed";
        return "upcoming";
    };

    const getStageColors = (status: string) => {
        switch (status) {
            case "completed":
                return {
                    bg: "#E3FCEF",
                    border: "#36B37E",
                    text: "#006644",
                    icon: "#36B37E",
                    line: "#36B37E",
                };
            case "current":
                return {
                    bg: "#DEEBFF",
                    border: "#0052CC",
                    text: "#0052CC",
                    icon: "#0052CC",
                    line: "#DFE1E6",
                };
            case "failed":
                return {
                    bg: "#FFEBE6",
                    border: "#DE350B",
                    text: "#BF2600",
                    icon: "#DE350B",
                    line: "#DE350B",
                };
            default:
                return {
                    bg: "#F4F5F7",
                    border: "#DFE1E6",
                    text: "#97A0AF",
                    icon: "#97A0AF",
                    line: "#DFE1E6",
                };
        }
    };

    if (variant === "vertical") {
        return (
            <div className="flex flex-col gap-0">
                {stages.map((stage, index) => {
                    const status = getStageStatus(stage, index);
                    const colors = getStageColors(status);
                    const isLast = index === stages.length - 1;

                    return (
                        <div key={stage.id} className="flex gap-3">
                            {/* Line and Node */}
                            <div className="flex flex-col items-center">
                                <button
                                    onClick={() => onStageClick?.(stage.id)}
                                    className="w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200 flex-shrink-0"
                                    style={{
                                        backgroundColor: colors.bg,
                                        border: `2px solid ${colors.border}`,
                                        color: colors.icon,
                                    }}
                                >
                                    {status === "completed" ? (
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                        </svg>
                                    ) : status === "failed" ? (
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                                        </svg>
                                    ) : (
                                        stage.icon
                                    )}
                                </button>
                                {!isLast && (
                                    <div
                                        className="w-0.5 h-8 transition-colors duration-200"
                                        style={{ backgroundColor: colors.line }}
                                    />
                                )}
                            </div>

                            {/* Content */}
                            <div className="pb-8">
                                <p
                                    className="text-[11px] font-bold tracking-wide"
                                    style={{ color: colors.text }}
                                >
                                    {stage.label}
                                </p>
                                <p className="text-[11px] text-[#5E6C84]">{stage.description}</p>
                            </div>
                        </div>
                    );
                })}
            </div>
        );
    }

    // Horizontal variant
    return (
        <div className="w-full">
            <div className="flex items-start justify-between relative">
                {/* Connecting line */}
                <div className="absolute top-4 left-4 right-4 h-0.5 bg-[#DFE1E6] -z-10" />
                <div
                    className="absolute top-4 left-4 h-0.5 bg-[#36B37E] -z-10 transition-all duration-500"
                    style={{
                        width: `${(currentIndex / (stages.length - 1)) * 100}%`,
                        maxWidth: "calc(100% - 32px)",
                    }}
                />

                {stages.map((stage, index) => {
                    const status = getStageStatus(stage, index);
                    const colors = getStageColors(status);

                    return (
                        <div
                            key={stage.id}
                            className="flex flex-col items-center"
                            style={{ width: `${100 / stages.length}%` }}
                        >
                            <button
                                onClick={() => onStageClick?.(stage.id)}
                                className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200 ${
                                    status === "current" ? "ring-4 ring-[#DEEBFF]" : ""
                                } ${status === "failed" ? "ring-4 ring-[#FFEBE6]" : ""}`}
                                style={{
                                    backgroundColor: colors.bg,
                                    border: `2px solid ${colors.border}`,
                                    color: colors.icon,
                                }}
                                title={`${stage.label}: ${stage.description}`}
                            >
                                {status === "completed" ? (
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                    </svg>
                                ) : status === "failed" ? (
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                ) : (
                                    stage.icon
                                )}
                            </button>
                            <p
                                className="text-[9px] font-bold tracking-wide mt-2 text-center"
                                style={{ color: colors.text }}
                            >
                                {stage.label}
                            </p>
                            <p className="text-[9px] text-[#97A0AF] text-center hidden sm:block">
                                {stage.description}
                            </p>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

// Helper function to determine stage from client data
export function getClientStage(client: {
    documentsUploaded: number;
    documentsRequired: number;
    hasBankConnection: boolean;
    status: string;
    hasFailedValidations?: boolean;
    hasPendingReviews?: boolean;
}): FlowStage {
    const docProgress = client.documentsRequired > 0
        ? client.documentsUploaded / client.documentsRequired
        : 0;

    // Submitted
    if (client.status === "submitted" || client.status === "locked") {
        return "submitted";
    }

    // Ready
    if (client.status === "ready" || (docProgress === 1 && client.hasBankConnection)) {
        // Block progression if there are failed validations or pending reviews
        if (client.hasFailedValidations || client.hasPendingReviews) {
            return "verification";
        }
        return "ready";
    }

    // Review
    if (client.status === "review" || client.status === "under_review") {
        // Block at verification if there are unresolved validation issues
        if (client.hasFailedValidations || client.hasPendingReviews) {
            return "verification";
        }
        return "review";
    }

    // Verification (docs complete, checking)
    // Client stays here until all validations pass or are approved
    if (docProgress === 1) {
        return "verification";
    }

    // Bank connection (some docs uploaded)
    if (docProgress > 0 && !client.hasBankConnection) {
        return "bank_connection";
    }

    // Documents (started uploading)
    if (docProgress > 0 || client.hasBankConnection) {
        return "documents";
    }

    // Onboarding (just started)
    return "onboarding";
}

// Helper to check if client has validation issues blocking flow
export function hasBlockingValidationIssues(client: {
    hasFailedValidations?: boolean;
    hasPendingReviews?: boolean;
}): boolean {
    return Boolean(client.hasFailedValidations || client.hasPendingReviews);
}

// Compact inline version for table rows
export function ClientFlowIndicator({
    currentStage,
    hasFailedValidations = false
}: {
    currentStage: FlowStage;
    hasFailedValidations?: boolean;
}) {
    const currentIndex = stages.findIndex((s) => s.id === currentStage);
    const progress = ((currentIndex + 1) / stages.length) * 100;

    const stageConfig = stages.find(s => s.id === currentStage);

    const getColor = () => {
        // Show red if has failed validations at verification stage
        if (hasFailedValidations && currentStage === "verification") return "#DE350B";
        if (currentStage === "submitted") return "#36B37E";
        if (currentStage === "ready") return "#36B37E";
        if (currentStage === "review" || currentStage === "verification") return "#0052CC";
        return "#FF991F";
    };

    const getLabel = () => {
        if (hasFailedValidations && currentStage === "verification") {
            return "FAILED";
        }
        return stageConfig?.label;
    };

    return (
        <div className="flex items-center gap-2">
            <div className="flex-1 h-1.5 bg-[#EBECF0] rounded-full overflow-hidden min-w-[60px]">
                <div
                    className="h-full rounded-full transition-all duration-300"
                    style={{ width: `${progress}%`, backgroundColor: getColor() }}
                />
            </div>
            <span
                className="text-[10px] font-bold tracking-wide whitespace-nowrap"
                style={{ color: getColor() }}
            >
                {getLabel()}
            </span>
        </div>
    );
}
