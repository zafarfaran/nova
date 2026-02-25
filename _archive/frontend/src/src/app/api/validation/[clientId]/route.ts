import { NextRequest, NextResponse } from "next/server";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// GET - Fetch documents and their validation results for a client from Python backend
export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ clientId: string }> }
) {
    try {
        const { clientId } = await params;

        if (!clientId) {
            return NextResponse.json(
                { success: false, error: "Invalid client ID" },
                { status: 400 }
            );
        }

        // Fetch documents from Python backend
        const documentsResponse = await fetch(
            `${API_BASE_URL}/api/v1/clients/${clientId}/documents`,
            {
                method: "GET",
                headers: { "Content-Type": "application/json" },
            }
        );

        if (!documentsResponse.ok) {
            // If endpoint doesn't exist, try alternative endpoint
            const altResponse = await fetch(
                `${API_BASE_URL}/api/v1/documents?client_id=${clientId}`,
                {
                    method: "GET",
                    headers: { "Content-Type": "application/json" },
                }
            );

            if (!altResponse.ok) {
                console.error("Backend document fetch failed:", altResponse.status);
                return NextResponse.json({
                    success: true,
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

            const altData = await altResponse.json();
            const documents = altData.documents || altData.data || altData || [];
            return formatDocumentsResponse(documents);
        }

        const data = await documentsResponse.json();
        const documents = data.documents || data.data || data || [];

        return formatDocumentsResponse(documents);
    } catch (error) {
        console.error("Error fetching validation data:", error);
        return NextResponse.json(
            {
                success: false,
                error: error instanceof Error ? error.message : "Unknown error",
            },
            { status: 500 }
        );
    }
}

// Helper function to format the response
async function formatDocumentsResponse(documents: any[]) {
    // Fetch validation results for each document from Python backend
    const documentsWithValidation = await Promise.all(
        documents.map(async (doc: any) => {
            try {
                const response = await fetch(
                    `${API_BASE_URL}/api/v1/validation/results/${doc.id}`,
                    {
                        method: "GET",
                        headers: { "Content-Type": "application/json" },
                    }
                );

                let validationResults: any[] = [];
                if (response.ok) {
                    const data = await response.json();
                    validationResults = data.results || data.validation_results || data || [];
                }

                // Determine actual status - documents marked as VALIDATED but without
                // validation results should be treated as EXTRACTED (needs validation)
                let actualStatus = (doc.status || "pending").toLowerCase();
                const hasValidationResults = Array.isArray(validationResults) && validationResults.length > 0;
                if (actualStatus === "validated" && !hasValidationResults) {
                    actualStatus = "extracted"; // Needs validation - no results yet
                }

                return {
                    id: doc.id?.toString() || doc._id?.toString(),
                    filename: doc.filename || doc.file_name || doc.name || "Unknown",
                    documentType: doc.document_type || doc.documentType || doc.type || "OTHER",
                    status: actualStatus,
                    uploadedAt: doc.created_at || doc.createdAt || doc.uploaded_at || new Date(),
                    validationResults: hasValidationResults ? validationResults.map((r: any) => ({
                        id: r.id?.toString() || Math.random().toString(),
                        ruleType: r.rule_type || r.ruleType,
                        status: (r.status || "pending").toLowerCase(),
                        message: r.message,
                        details: r.details,
                        fieldName: r.field_name || r.fieldName,
                        expectedValue: r.expected_value || r.expectedValue,
                        actualValue: r.actual_value || r.actualValue,
                    })) : [],
                };
            } catch (error) {
                console.error(`Error fetching validation for doc ${doc.id}:`, error);
                return {
                    id: doc.id?.toString() || doc._id?.toString(),
                    filename: doc.filename || doc.file_name || doc.name || "Unknown",
                    documentType: doc.document_type || doc.documentType || doc.type || "OTHER",
                    status: (doc.status || "pending").toLowerCase(),
                    uploadedAt: doc.created_at || doc.createdAt || doc.uploaded_at || new Date(),
                    validationResults: [],
                };
            }
        })
    );

    // Calculate summary
    const summary = {
        totalDocuments: documentsWithValidation.length,
        validatedDocuments: documentsWithValidation.filter(
            (d) => d.status === "validated"
        ).length,
        failedDocuments: documentsWithValidation.filter(
            (d) => d.status === "failed"
        ).length,
        pendingDocuments: documentsWithValidation.filter(
            (d) => d.status === "pending" || d.status === "processing" || d.status === "extracted"
        ).length,
        passedValidations: documentsWithValidation
            .flatMap((d) => d.validationResults)
            .filter((r) => r.status === "passed").length,
        failedValidations: documentsWithValidation
            .flatMap((d) => d.validationResults)
            .filter((r) => r.status === "failed").length,
        warningValidations: documentsWithValidation
            .flatMap((d) => d.validationResults)
            .filter((r) => r.status === "warning").length,
    };

    return NextResponse.json({
        success: true,
        documents: documentsWithValidation,
        summary,
    });
}
