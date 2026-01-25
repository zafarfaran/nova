import { NextRequest, NextResponse } from "next/server";
import { db } from "~/server/db";

// GET - Fetch documents for a client using Prisma
// Syncs ChecklistItem uploads to Document table, then returns with validation results
export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ clientId: string }> }
) {
    try {
        const { clientId: clientIdParam } = await params;
        const clientId = parseInt(clientIdParam);

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

        // Re-fetch documents after sync (documents are created via backend sync)
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
        const uploadedDocuments = allDocuments.map((doc) => {
            // Determine actual status - documents marked as VALIDATED but without
            // validation results should be treated as EXTRACTED (needs validation)
            let actualStatus = (doc.status || "PENDING").toLowerCase();
            if (actualStatus === "validated" && doc.validationResults.length === 0) {
                actualStatus = "extracted"; // Needs validation - no results yet
            }

            return {
                id: doc.id.toString(),
                filename: doc.filename,
                documentType: doc.documentType || "OTHER",
                status: actualStatus,
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
            };
        });

        // Get required document types from checklist items that are NOT uploaded
        const missingItems = client.checklistItems.filter(
            (item) => item.required && item.status !== "uploaded"
        );

        // Create "not provided" entries for missing required documents
        const missingDocuments = missingItems.map((item) => ({
            id: `missing-${item.id}`,
            filename: item.title,
            documentType: mapItemIdToDocType(item.itemId),
            status: "not_provided",
            uploadedAt: null,
            validationResults: [],
            isMissing: true,
        }));

        // Combine uploaded and missing documents
        const documents = [...uploadedDocuments, ...missingDocuments];

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
            notProvidedDocuments: documents.filter(
                (d) => d.status === "not_provided"
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

// Helper to map itemId to document type
function mapItemIdToDocType(itemId: string): any {
    const mapping: Record<string, string> = {
        "sales_invoices": "INVOICE",
        "purchase_invoices": "INVOICE",
        "bank_statements": "BANK_STATEMENT",
        "receipts": "RECEIPT",
        "expense_receipts": "RECEIPT",
        "expense_receipt": "RECEIPT",
        "vat_certificate": "VAT_CERTIFICATE",
        "vat_certificates": "VAT_CERTIFICATE",
        "contracts": "CONTRACT",
        "contract": "CONTRACT",
        "payroll": "PAYROLL",
        "payroll_records": "PAYROLL",
        "payslip": "PAYROLL",
        "payslips": "PAYROLL",
    };
    return mapping[itemId] || "OTHER";
}
