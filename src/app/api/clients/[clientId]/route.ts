import { NextRequest, NextResponse } from "next/server";
import { db } from "~/server/db";

export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ clientId: string }> }
) {
    try {
        const { clientId: clientIdParam } = await params;
        const clientId = parseInt(clientIdParam, 10);

        if (isNaN(clientId)) {
            return NextResponse.json(
                { success: false, error: "Invalid client ID" },
                { status: 400 }
            );
        }

        const client = await db.client.findUnique({
            where: { id: clientId },
            select: { id: true },
        });

        if (!client) {
            return NextResponse.json(
                { success: false, error: "Client not found" },
                { status: 404 }
            );
        }

        await db.$transaction(async (tx) => {
            await tx.validationResult.deleteMany({
                where: {
                    document: {
                        evidenceItem: {
                            vatPeriod: { clientId },
                        },
                    },
                },
            });

            await tx.document.deleteMany({
                where: {
                    evidenceItem: {
                        vatPeriod: { clientId },
                    },
                },
            });

            await tx.evidenceItem.deleteMany({
                where: {
                    vatPeriod: { clientId },
                },
            });

            await tx.auditTrailEntry.deleteMany({
                where: {
                    vatPeriod: { clientId },
                },
            });

            await tx.chaserResponse.deleteMany({
                where: {
                    chaserRequest: {
                        vatPeriod: { clientId },
                    },
                },
            });

            await tx.chaserRequest.deleteMany({
                where: {
                    vatPeriod: { clientId },
                },
            });

            await tx.vATPeriod.deleteMany({
                where: { clientId },
            });

            await tx.chatMessage.deleteMany({
                where: {
                    session: { clientId },
                },
            });

            await tx.chatSession.deleteMany({
                where: { clientId },
            });

            await tx.bankConnection.deleteMany({
                where: { clientId },
            });

            await tx.autoChaser.deleteMany({
                where: { clientId },
            });

            await tx.checklistItem.deleteMany({
                where: { clientId },
            });

            await tx.client.delete({
                where: { id: clientId },
            });
        });

        return NextResponse.json({ success: true });
    } catch (error) {
        console.error("Error deleting client:", error);
        return NextResponse.json(
            {
                success: false,
                error: error instanceof Error ? error.message : "Unknown error",
            },
            { status: 500 }
        );
    }
}
