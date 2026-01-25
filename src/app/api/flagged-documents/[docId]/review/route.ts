import { NextRequest, NextResponse } from "next/server";
import { db } from "~/server/db";

type ReviewAction = "approve" | "reject" | "request_info";

interface ReviewRequestBody {
    resultId: string;
    action: ReviewAction;
    notes?: string;
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

        if (!resultId || !action) {
            return NextResponse.json(
                { success: false, error: "Missing required fields: resultId and action" },
                { status: 400 }
            );
        }

        const validActions: ReviewAction[] = ["approve", "reject", "request_info"];
        if (!validActions.includes(action)) {
            return NextResponse.json(
                { success: false, error: `Invalid action. Must be one of: ${validActions.join(", ")}` },
                { status: 400 }
            );
        }

        const validationResultId = parseInt(resultId);
        if (isNaN(validationResultId)) {
            return NextResponse.json(
                { success: false, error: "Invalid result ID" },
                { status: 400 }
            );
        }

        // Verify the validation result exists and belongs to this document
        const validationResult = await db.validationResult.findFirst({
            where: {
                id: validationResultId,
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
