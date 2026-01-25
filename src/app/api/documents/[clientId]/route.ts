import { NextRequest, NextResponse } from "next/server";
import { db } from "~/server/db";
import crypto from "crypto";

// GET - Fetch documents for a client using Prisma
// Syncs ChecklistItem uploads to Document table, then returns with validation results
export async function GET(
    request: NextRequest,
    { params }: { params: { clientId: string } }
) {
    try {
        const clientId = parseInt(params.clientId);

        if (isNaN(clientId)) {
            return NextResponse.json(
                { success: false, error: "Invalid client ID" },
                { status: 400 }
            );
        }

        // Get the client with their checklist items and VAT period
        const client = await db.client.findUnique({
            where: { id: clientId },
            include: {
                checklistItems: true,
                vatPeriods: {
                    orderBy: { periodEnd: "desc" },
                    take: 1,
                    include: {
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
                },
            },
        });

        if (!client) {
            return NextResponse.json(
                { success: false, error: "Client not found" },
                { status: 404 }
            );
        }

        const currentPeriod = client.vatPeriods[0];

        if (!currentPeriod) {
            return NextResponse.json({
                success: true,
                periodId: null,
                documents: [],
                summary: {
                    totalDocuments: 0,
                    validatedDocuments: 0,
                    failedDocuments: 0,
                    pendingDocuments: 0,
                    passedValidations: 0,
                    failedValidations: 0,
                    warningValidations: 0,
                },
            });
        }

        // Get uploaded checklist items
        const uploadedItems = client.checklistItems.filter(
            (item) => item.status === "uploaded" && item.uploadedFileUrl
        );

        // Sync checklist items to Document table
        for (const item of uploadedItems) {
            await syncChecklistItemToDocument(item, currentPeriod.id);
        }

        // Re-fetch documents after sync
        const updatedPeriod = await db.vATPeriod.findUnique({
            where: { id: currentPeriod.id },
            include: {
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

        // Collect all documents from evidence items
        const allDocuments = updatedPeriod?.evidenceItems.flatMap(
            (item) => item.documents
        ) || [];

        // Transform documents to expected format
        const documents = allDocuments.map((doc) => ({
            id: doc.id.toString(),
            filename: doc.filename,
            documentType: doc.documentType || "OTHER",
            status: (doc.status || "PENDING").toLowerCase(),
            uploadedAt: doc.createdAt,
            validationResults: doc.validationResults.map((r) => ({
                id: r.id.toString(),
                ruleType: r.ruleType,
                status: r.status.toLowerCase(),
                message: r.message,
                details: r.details,
                fieldName: r.fieldName,
                expectedValue: r.expectedValue,
                actualValue: r.actualValue,
            })),
        }));

        // Calculate summary
        const summary = {
            totalDocuments: documents.length,
            validatedDocuments: documents.filter(
                (d) => d.status === "validated"
            ).length,
            failedDocuments: documents.filter(
                (d) => d.status === "failed"
            ).length,
            pendingDocuments: documents.filter(
                (d) => d.status === "pending" || d.status === "processing" || d.status === "extracted"
            ).length,
            passedValidations: documents
                .flatMap((d) => d.validationResults)
                .filter((r) => r.status === "passed").length,
            failedValidations: documents
                .flatMap((d) => d.validationResults)
                .filter((r) => r.status === "failed").length,
            warningValidations: documents
                .flatMap((d) => d.validationResults)
                .filter((r) => r.status === "warning").length,
        };

        return NextResponse.json({
            success: true,
            periodId: currentPeriod.id,
            documents,
            summary,
        });
    } catch (error) {
        console.error("Error fetching documents:", error);
        const errorMessage = error instanceof Error ? error.message : "Unknown error";
        const errorStack = error instanceof Error ? error.stack : "";
        console.error("Stack trace:", errorStack);
        return NextResponse.json(
            {
                success: false,
                error: errorMessage,
                details: errorStack,
            },
            { status: 500 }
        );
    }
}

// Sync a checklist item to the Document table
async function syncChecklistItemToDocument(
    item: {
        id: number;
        itemId: string;
        title: string;
        uploadedFileUrl: string | null;
        updatedAt: Date;
    },
    vatPeriodId: number
) {
    if (!item.uploadedFileUrl) return;

    try {
        // Check if document already exists with this URL
        const existingDoc = await db.document.findFirst({
            where: { s3Key: item.uploadedFileUrl },
        });

        if (existingDoc) {
            return existingDoc; // Already synced
        }

        // Find or create an evidence item for this document type
        const category = mapItemIdToCategory(item.itemId);
        let evidenceItem = await db.evidenceItem.findFirst({
            where: {
                vatPeriodId: vatPeriodId,
                category: category,
            },
        });

        if (!evidenceItem) {
            // Create evidence item
            evidenceItem = await db.evidenceItem.create({
                data: {
                    vatPeriodId: vatPeriodId,
                    category: category,
                    description: `${item.title} documents`,
                    status: "PARTIAL",
                    expectedCount: 1,
                    receivedCount: 1,
                },
            });
        } else {
            // Update received count
            await db.evidenceItem.update({
                where: { id: evidenceItem.id },
                data: { receivedCount: { increment: 1 } },
            });
        }

        // Create document record
        const fileHash = crypto
            .createHash("sha256")
            .update(item.uploadedFileUrl + item.id)
            .digest("hex");

        const document = await db.document.create({
            data: {
                evidenceItemId: evidenceItem.id,
                filename: item.title,
                s3Key: item.uploadedFileUrl,
                fileHash: fileHash,
                contentType: "application/pdf",
                status: "EXTRACTED",
                documentType: mapItemIdToDocType(item.itemId),
            },
        });

        return document;
    } catch (error) {
        console.error(`Error syncing checklist item ${item.id}:`, error);
        // Don't throw - just skip this item
        return null;
    }
}

// Helper to map itemId to evidence category
function mapItemIdToCategory(itemId: string): any {
    const mapping: Record<string, string> = {
        "sales_invoices": "SALES_INVOICES",
        "purchase_invoices": "PURCHASE_INVOICES",
        "bank_statements": "BANK_STATEMENTS",
        "receipts": "RECEIPTS",
        "vat_certificate": "VAT_CERTIFICATES",
        "contracts": "CONTRACTS",
    };
    return mapping[itemId] || "OTHER";
}

// Helper to map itemId to document type
function mapItemIdToDocType(itemId: string): any {
    const mapping: Record<string, string> = {
        "sales_invoices": "INVOICE",
        "purchase_invoices": "INVOICE",
        "bank_statements": "BANK_STATEMENT",
        "receipts": "RECEIPT",
        "vat_certificate": "VAT_CERTIFICATE",
        "contracts": "CONTRACT",
    };
    return mapping[itemId] || "OTHER";
}
