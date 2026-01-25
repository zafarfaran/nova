import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { db } from "~/server/db";

const StatusSchema = z.object({
    status: z.enum(["READY", "UNDER_REVIEW", "IN_PROGRESS", "DRAFT", "SUBMITTED", "LOCKED"]),
});

export async function PATCH(
    request: NextRequest,
    { params }: { params: Promise<{ periodId: string }> }
) {
    try {
        const { periodId } = await params;
        const periodIdNum = parseInt(periodId, 10);
        if (isNaN(periodIdNum)) {
            return NextResponse.json(
                { success: false, error: "Invalid tax period ID" },
                { status: 400 }
            );
        }

        const body = StatusSchema.parse(await request.json());

        const period = await db.vATPeriod.findUnique({
            where: { id: periodIdNum },
            include: {
                client: {
                    include: {
                        checklistItems: true,
                        bankConnections: { where: { isActive: true } },
                    },
                },
                evidenceItems: {
                    include: {
                        documents: {
                            include: {
                                validationResults: true,
                            },
                        },
                    },
                },
            },
        });

        if (!period) {
            return NextResponse.json(
                { success: false, error: "Tax period not found" },
                { status: 404 }
            );
        }

        if (body.status === "READY") {
            const requiredItems = period.client.checklistItems.filter((item) => item.required);
            const incompleteRequired = requiredItems.filter(
                (item) =>
                    item.status !== "uploaded" &&
                    item.status !== "confirmed" &&
                    item.status !== "not_applicable"
            );
            if (incompleteRequired.length > 0) {
                return NextResponse.json(
                    {
                        success: false,
                        error: "Not all required items are complete",
                        incompleteItems: incompleteRequired.map((item) => item.title),
                    },
                    { status: 400 }
                );
            }

            const hasFailedDocs = period.evidenceItems.some((item) =>
                item.documents.some((doc) => doc.status === "FAILED")
            );
            if (hasFailedDocs) {
                return NextResponse.json(
                    { success: false, error: "Document failures must be resolved before ready" },
                    { status: 400 }
                );
            }

            const hasUnapprovedIssues = period.evidenceItems.some((item) =>
                item.documents.some((doc) =>
                    doc.validationResults.some(
                        (result) =>
                            (result.status === "FAILED" || result.status === "WARNING") &&
                            result.reviewAction !== "approve"
                    )
                )
            );
            if (hasUnapprovedIssues) {
                return NextResponse.json(
                    { success: false, error: "All validation issues must be approved before ready" },
                    { status: 400 }
                );
            }

            // Bank connection is optional for now
        }

        const updated = await db.vATPeriod.update({
            where: { id: periodIdNum },
            data: { status: body.status },
        });

        return NextResponse.json({
            success: true,
            status: updated.status,
        });
    } catch (error) {
        if (error instanceof z.ZodError) {
            return NextResponse.json(
                { success: false, error: "Invalid payload", details: error.errors },
                { status: 400 }
            );
        }
        console.error("Error updating tax period status:", error);
        return NextResponse.json(
            { success: false, error: "Internal server error" },
            { status: 500 }
        );
    }
}
