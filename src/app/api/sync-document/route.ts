import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { db } from "~/server/db";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Schema for the sync request
const SyncDocumentSchema = z.object({
    clientSetupId: z.string(),
    checklistItemId: z.string(),
    filename: z.string(),
    fileUrl: z.string().url(),
    fileSize: z.number().optional(),
    contentType: z.string().optional(),
});

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const validatedData = SyncDocumentSchema.parse(body);

        // Get the client setup to check for backendClientId
        const clientSetup = await db.clientSetup.findUnique({
            where: { id: validatedData.clientSetupId },
            select: {
                backendClientId: true,
                clientName: true,
            },
        });

        if (!clientSetup) {
            return NextResponse.json(
                { success: false, error: "Client setup not found" },
                { status: 404 }
            );
        }

        // If no backend client is linked, just return success
        // Document is stored in UploadThing and tracked by Prisma
        if (!clientSetup.backendClientId) {
            return NextResponse.json({
                success: true,
                synced: false,
                message: "No backend client linked, document stored locally only",
            });
        }

        // Sync to backend - first we need to find or create an evidence item
        // For now, we'll create a document record in the backend
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/documents/sync`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    filename: validatedData.filename,
                    external_url: validatedData.fileUrl,
                    file_size: validatedData.fileSize,
                    content_type: validatedData.contentType,
                    client_id: clientSetup.backendClientId,
                    // evidence_item_id will be null - backend can link it later
                }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                console.error("Backend sync error:", errorData);

                // Don't fail the whole request - document is still saved in UploadThing
                return NextResponse.json({
                    success: true,
                    synced: false,
                    error: `Backend sync failed: ${response.status}`,
                });
            }

            const backendDoc = await response.json();

            return NextResponse.json({
                success: true,
                synced: true,
                backendDocumentId: backendDoc.document_id,
            });
        } catch (error) {
            console.error("Backend sync error:", error);

            // Don't fail - document is still saved in UploadThing
            return NextResponse.json({
                success: true,
                synced: false,
                error: error instanceof Error ? error.message : "Unknown error",
            });
        }
    } catch (error) {
        if (error instanceof z.ZodError) {
            return NextResponse.json(
                {
                    success: false,
                    error: "Invalid request",
                    details: error.errors,
                },
                { status: 400 }
            );
        }

        console.error("Sync document error:", error);
        return NextResponse.json(
            {
                success: false,
                error: error instanceof Error ? error.message : "Unknown error",
            },
            { status: 500 }
        );
    }
}
