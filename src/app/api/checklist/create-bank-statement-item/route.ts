import { NextRequest, NextResponse } from "next/server";
import { db } from "~/server/db";

export async function POST(request: NextRequest) {
    try {
        const { clientId } = await request.json();

        if (!clientId) {
            return NextResponse.json(
                { error: "Client ID is required" },
                { status: 400 }
            );
        }

        const clientIdNum = parseInt(clientId, 10);
        if (isNaN(clientIdNum)) {
            return NextResponse.json(
                { error: "Invalid client ID" },
                { status: 400 }
            );
        }

        // Check if bank statement item already exists
        const existingItem = await db.checklistItem.findFirst({
            where: {
                clientId: clientIdNum,
                itemId: "bank_statements_manual",
            },
        });

        if (existingItem) {
            return NextResponse.json({ item: existingItem });
        }

        // Create new checklist item for manual upload
        const item = await db.checklistItem.create({
            data: {
                clientId: clientIdNum,
                itemId: "bank_statements_manual",
                title: "Bank Statements (Manual Upload)",
                required: true,
                status: "pending",
                acceptance: "manual",
                ctaAction: "upload",
                ctaData: JSON.stringify({
                    uploadType: "manual",
                    createdAt: new Date().toISOString(),
                }),
            },
        });

        return NextResponse.json({ item });
    } catch (error) {
        console.error("Error creating checklist item:", error);
        return NextResponse.json(
            { error: "Failed to create checklist item" },
            { status: 500 }
        );
    }
}
