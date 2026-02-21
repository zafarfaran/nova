import { NextRequest, NextResponse } from "next/server";
import { db } from "~/server/db";

// GET - Fetch all documents with failed/warning validation results for human review
export async function GET(request: NextRequest) {
    try {
        // Get all documents with failed or warning validation results
        // that haven't been reviewed yet
        const documents = await db.document.findMany({
            where: {
                OR: [
                    // Documents with failed status
                    { status: "FAILED" },
                    // Documents with failed/warning validation results
                    {
                        validationResults: {
                            some: {
                                OR: [
                                    { status: "FAILED" },
                                    { status: "WARNING" },
                                ],
                            },
                        },
                    },
                ],
            },
            include: {
                validationResults: {
                    where: {
                        OR: [
                            { status: "FAILED" },
                            { status: "WARNING" },
                        ],
                    },
                    orderBy: [
                        // Order by severity (high first)
                        { severity: "asc" },
                        { createdAt: "desc" },
                    ],
                },
                evidenceItem: {
                    include: {
                        vatPeriod: {
                            include: {
                                client: {
                                    select: {
                                        id: true,
                                        name: true,
                                    },
                                },
                            },
                        },
                    },
                },
            },
            orderBy: {
                createdAt: "desc",
            },
        });

        // Transform documents to the expected format
        const flaggedDocuments = documents
            .filter((doc) => doc.validationResults.length > 0)
            .map((doc) => {
                const client = doc.evidenceItem?.vatPeriod?.client;

                return {
                    id: doc.id.toString(),
                    filename: doc.filename,
                    fileUrl: doc.s3Key || null, // URL to view the document
                    documentType: doc.documentType || "OTHER",
                    clientId: client?.id?.toString() || "",
                    clientName: client?.name || "Unknown Client",
                    uploadedAt: doc.createdAt.toISOString(),
                    validationResults: doc.validationResults.map((r) => ({
                        id: r.id.toString(),
                        ruleType: r.ruleType,
                        status: r.status.toLowerCase() as "failed" | "warning",
                        message: r.message || "",
                        details: r.details || undefined,
                        fieldName: r.fieldName || undefined,
                        expectedValue: r.expectedValue || undefined,
                        actualValue: r.actualValue || undefined,
                        severity: (r.severity?.toLowerCase() || determineSeverity(r.status, r.ruleType)) as "high" | "medium" | "low",
                        confidence: r.confidence ? parseFloat(r.confidence.toString()) : undefined,
                        aiReasoning: r.aiReasoning as Record<string, unknown> | undefined,
                        reviewedAt: r.reviewedAt?.toISOString() || undefined,
                        reviewedBy: r.reviewedBy || undefined,
                        reviewAction: r.reviewAction as "approve" | "reject" | "request_info" | undefined,
                    })),
                };
            });

        // Calculate summary statistics
        const allResults = flaggedDocuments.flatMap((d) => d.validationResults);
        const summary = {
            total: flaggedDocuments.length,
            highSeverity: allResults.filter((r) => r.severity === "high").length,
            mediumSeverity: allResults.filter((r) => r.severity === "medium").length,
            lowSeverity: allResults.filter((r) => r.severity === "low").length,
            pendingReview: allResults.filter((r) => !r.reviewAction).length,
        };

        return NextResponse.json({
            success: true,
            flaggedDocuments,
            summary,
        });
    } catch (error) {
        console.error("Error fetching flagged documents:", error);
        const errorMessage = error instanceof Error ? error.message : "Unknown error";
        return NextResponse.json(
            {
                success: false,
                error: errorMessage,
            },
            { status: 500 }
        );
    }
}

// Helper to determine severity from status and rule type
function determineSeverity(status: string, ruleType: string): "high" | "medium" | "low" {
    // High severity for critical validation failures
    if (status === "FAILED") {
        const highSeverityRules = [
            "REQUIRED_FIELDS",
            "TOTALS_MATCH",
            "VAT_NUMBER_FORMAT",
            "AI_ANOMALY", // AI-flagged anomalies with failed status
        ];
        if (highSeverityRules.includes(ruleType)) {
            return "high";
        }
        return "medium";
    }

    // Warnings are generally medium or low
    const mediumSeverityRules = [
        "DUPLICATE_DETECTION",
        "DATE_IN_PERIOD",
        "VAT_RATE_VALID",
    ];
    if (mediumSeverityRules.includes(ruleType)) {
        return "medium";
    }

    return "low";
}
