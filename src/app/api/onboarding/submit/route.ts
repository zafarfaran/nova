import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { db } from "~/server/db";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const SubmitSchema = z.object({
    clientId: z.number(),
});

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const { clientId } = SubmitSchema.parse(body);

        // Get the client with all checklist items
        const client = await db.client.findUnique({
            where: { id: clientId },
            include: {
                checklistItems: true,
                vatPeriods: {
                    orderBy: { periodEnd: "desc" },
                    take: 1,
                },
            },
        });

        if (!client) {
            return NextResponse.json(
                { success: false, error: "Client not found" },
                { status: 404 }
            );
        }

        // Check if all required items are complete
        const requiredItems = client.checklistItems.filter((item) => item.required);
        const incompleteRequired = requiredItems.filter(
            (item) => item.status !== "uploaded" && item.status !== "confirmed" && item.status !== "not_applicable"
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

        // Get completion summary
        const completedItems = client.checklistItems.filter(
            (item) => item.status === "uploaded" || item.status === "confirmed"
        );
        const notApplicableItems = client.checklistItems.filter(
            (item) => item.status === "not_applicable"
        );

        // Notify backend of submission
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/clients/${clientId}/onboarding-complete`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    client_id: clientId,
                    completed_items: completedItems.length,
                    not_applicable_items: notApplicableItems.length,
                    total_items: client.checklistItems.length,
                    vat_period_id: client.vatPeriods[0]?.id,
                }),
            });

            if (!response.ok) {
                console.warn("Backend notification failed:", await response.text());
                // Continue anyway - the submission is still valid
            }
        } catch (backendError) {
            console.error("Backend notification error:", backendError);
            // Continue anyway - the submission is still valid
        }

        // Return success
        return NextResponse.json({
            success: true,
            message: "Onboarding submission complete",
            summary: {
                clientName: client.name,
                completedItems: completedItems.length,
                notApplicableItems: notApplicableItems.length,
                totalItems: client.checklistItems.length,
            },
        });
    } catch (error) {
        if (error instanceof z.ZodError) {
            return NextResponse.json(
                { success: false, error: "Invalid request", details: error.errors },
                { status: 400 }
            );
        }

        console.error("Submit error:", error);
        return NextResponse.json(
            { success: false, error: error instanceof Error ? error.message : "Unknown error" },
            { status: 500 }
        );
    }
}
