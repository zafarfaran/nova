import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { db } from "~/server/db";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Valid document types
const DOCUMENT_TYPES = [
    "invoice",
    "receipt",
    "bank_statement",
    "payroll",
    "contract",
    "vat_certificate",
    "credit_note",
    "debit_note",
    "other",
] as const;

// Schema for the sync request
const SyncDocumentSchema = z.object({
    clientId: z.number(),
    checklistItemId: z.number(),
    filename: z.string(),
    fileUrl: z.string().url(),
    fileSize: z.number().optional(),
    contentType: z.string().optional(),
    documentType: z.enum(DOCUMENT_TYPES).optional(),
});

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const validatedData = SyncDocumentSchema.parse(body);

        // Get the client to verify it exists
        const client = await db.client.findUnique({
            where: { id: validatedData.clientId },
            select: {
                id: true,
                name: true,
            },
        });

        if (!client) {
            return NextResponse.json(
                { success: false, error: "Client not found" },
                { status: 404 }
            );
        }

        // Sync to backend
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
                    content_type: validatedData.contentType || "application/pdf",
                    client_id: client.id,
                    checklist_item_id: validatedData.checklistItemId,
                    document_type: validatedData.documentType,
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
