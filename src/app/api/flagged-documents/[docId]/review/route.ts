import { NextRequest, NextResponse } from "next/server";
import { db } from "~/server/db";

type ReviewAction = "approve" | "reject" | "request_info";

interface ReviewRequestBody {
    resultId?: string;
    action: ReviewAction;
    notes?: string;
    applyToAll?: boolean;
}

// POST - Submit a review action for a flagged validation result
export async function POST(
    request: NextRequest,
    { params }: { params: Promise<{ docId: string }> }
) {
    try {
        const { docId: docIdStr } = await params;
        const docId = parseInt(docIdStr);

        if (isNaN(docId)) {
            return NextResponse.json(
                { success: false, error: "Invalid document ID" },
                { status: 400 }
            );
        }

        const body: ReviewRequestBody = await request.json();
        const { resultId, action, notes } = body;

        const validActions: ReviewAction[] = ["approve", "reject", "request_info"];
        if (!validActions.includes(action)) {
            return NextResponse.json(
                { success: false, error: `Invalid action. Must be one of: ${validActions.join(", ")}` },
                { status: 400 }
            );
        }

        const applyToAll = Boolean(body.applyToAll);
        if (!resultId && !applyToAll) {
            return NextResponse.json(
                { success: false, error: "Missing required fields: resultId or applyToAll" },
                { status: 400 }
            );
        }

        let validationResultId: number | undefined;
        if (!applyToAll) {
            validationResultId = parseInt(resultId || "");
        }
        if (!applyToAll && (validationResultId === undefined || isNaN(validationResultId))) {
            return NextResponse.json(
                { success: false, error: "Invalid result ID" },
                { status: 400 }
            );
        }

        // Bulk update for entire document
        if (applyToAll) {
            const document = await db.document.findUnique({
                where: { id: docId },
                include: {
                    validationResults: {
                        where: {
                            OR: [
                                { status: "FAILED" },
                                { status: "WARNING" },
                            ],
                        },
                    },
                    evidenceItem: {
                        include: {
                            vatPeriod: {
                                include: {
                                    client: true,
                                },
                            },
                        },
                    },
                },
            });

            if (!document) {
                return NextResponse.json(
                    { success: false, error: "Document not found" },
                    { status: 404 }
                );
            }

            // TODO: Get actual user from session/auth when available
            const reviewedBy = "Accountant";
            const now = new Date();

            const updateResult = await db.validationResult.updateMany({
                where: {
                    documentId: docId,
                    OR: [
                        { status: "FAILED" },
                        { status: "WARNING" },
                    ],
                },
                data: {
                    reviewedAt: now,
                    reviewedBy,
                    reviewAction: action,
                },
            });

            if (action === "approve") {
                await db.document.update({
                    where: { id: docId },
                    data: { status: "VALIDATED" },
                });
            } else if (action === "reject") {
                await db.document.update({
                    where: { id: docId },
                    data: { status: "FAILED" },
                });

                const vatPeriod = document.evidenceItem?.vatPeriod;
                if (vatPeriod) {
                    await db.auditTrailEntry.create({
                        data: {
                            vatPeriodId: vatPeriod.id,
                            action: "DOCUMENT_REJECTED",
                            description: `Document "${document.filename}" was rejected during review`,
                            performedBy: reviewedBy,
                            performedAt: now,
                            entityType: "Document",
                            entityId: docId,
                        },
                    });
                }
            } else if (action === "request_info") {
                const vatPeriod = document.evidenceItem?.vatPeriod;
                if (vatPeriod) {
                    await db.auditTrailEntry.create({
                        data: {
                            vatPeriodId: vatPeriod.id,
                            action: "INFO_REQUESTED",
                            description: `Additional information requested for document "${document.filename}"`,
                            performedBy: reviewedBy,
                            performedAt: now,
                            entityType: "Document",
                            entityId: docId,
                        },
                    });
                }
            }

            return NextResponse.json({
                success: true,
                message: `Document ${action === "approve" ? "approved" : action === "reject" ? "rejected" : "flagged for info"} successfully`,
                updatedCount: updateResult.count,
            });
        }

        // Verify the validation result exists and belongs to this document
        const validationResult = await db.validationResult.findFirst({
            where: {
                id: validationResultId!,
                documentId: docId,
            },
            include: {
                document: {
                    include: {
                        evidenceItem: {
                            include: {
                                vatPeriod: {
                                    include: {
                                        client: true,
                                    },
                                },
                            },
                        },
                    },
                },
            },
        });

        if (!validationResult) {
            return NextResponse.json(
                { success: false, error: "Validation result not found" },
                { status: 404 }
            );
        }

        // Update the validation result with review information
        // TODO: Get actual user from session/auth when available
        const reviewedBy = "Accountant"; // Placeholder - should come from auth

        const updatedResult = await db.validationResult.update({
            where: { id: validationResultId },
            data: {
                reviewedAt: new Date(),
                reviewedBy,
                reviewAction: action,
            },
        });

        // Handle different actions
        if (action === "approve") {
            // Check if all validation results for this document have been approved
            const remainingIssues = await db.validationResult.count({
                where: {
                    documentId: docId,
                    OR: [
                        { status: "FAILED" },
                        { status: "WARNING" },
                    ],
                    reviewAction: null,
                },
            });

            // If all issues are resolved, update document status to VALIDATED
            if (remainingIssues === 0) {
                await db.document.update({
                    where: { id: docId },
                    data: { status: "VALIDATED" },
                });
            }
        } else if (action === "reject") {
            // Update document status to FAILED
            await db.document.update({
                where: { id: docId },
                data: { status: "FAILED" },
            });

            // Create audit trail entry
            const vatPeriod = validationResult.document.evidenceItem?.vatPeriod;
            if (vatPeriod) {
                await db.auditTrailEntry.create({
                    data: {
                        vatPeriodId: vatPeriod.id,
                        action: "DOCUMENT_REJECTED",
                        description: `Document "${validationResult.document.filename}" was rejected due to validation issue: ${validationResult.message}`,
                        performedBy: reviewedBy,
                        performedAt: new Date(),
                        entityType: "Document",
                        entityId: docId,
                    },
                });
            }
        } else if (action === "request_info") {
            // TODO: Create a chaser request for additional information
            // For now, just log the action

            // Create audit trail entry
            const vatPeriod = validationResult.document.evidenceItem?.vatPeriod;
            if (vatPeriod) {
                await db.auditTrailEntry.create({
                    data: {
                        vatPeriodId: vatPeriod.id,
                        action: "INFO_REQUESTED",
                        description: `Additional information requested for document "${validationResult.document.filename}" regarding: ${validationResult.message}`,
                        performedBy: reviewedBy,
                        performedAt: new Date(),
                        entityType: "Document",
                        entityId: docId,
                    },
                });
            }
        }

        return NextResponse.json({
            success: true,
            message: `Review action "${action}" recorded successfully`,
            result: {
                id: updatedResult.id.toString(),
                reviewedAt: updatedResult.reviewedAt?.toISOString(),
                reviewedBy: updatedResult.reviewedBy,
                reviewAction: updatedResult.reviewAction,
            },
        });
    } catch (error) {
        console.error("Error processing review action:", error);
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

// GET - Get review history for a document
export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ docId: string }> }
) {
    try {
        const { docId: docIdStr } = await params;
        const docId = parseInt(docIdStr);

        if (isNaN(docId)) {
            return NextResponse.json(
                { success: false, error: "Invalid document ID" },
                { status: 400 }
            );
        }

        const document = await db.document.findUnique({
            where: { id: docId },
            include: {
                validationResults: {
                    where: {
                        reviewAction: { not: null },
                    },
                    orderBy: { reviewedAt: "desc" },
                },
            },
        });

        if (!document) {
            return NextResponse.json(
                { success: false, error: "Document not found" },
                { status: 404 }
            );
        }

        const reviewHistory = document.validationResults.map((r) => ({
            id: r.id.toString(),
            ruleType: r.ruleType,
            message: r.message,
            reviewAction: r.reviewAction,
            reviewedAt: r.reviewedAt?.toISOString(),
            reviewedBy: r.reviewedBy,
        }));

        return NextResponse.json({
            success: true,
            documentId: docId.toString(),
            reviewHistory,
        });
    } catch (error) {
        console.error("Error fetching review history:", error);
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
