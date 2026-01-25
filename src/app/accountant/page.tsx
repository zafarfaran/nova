import { db } from "~/server/db";
import { AccountantDashboardClient } from "./DashboardClient";
import type { ClientRow } from "./components/ClientTable";
import type { DashboardMetrics } from "./components/QuickMetrics";

// Server component that fetches data from the clients table
export default async function AccountantDashboard() {
    // Fetch all clients with their VAT periods, bank connections, checklist items, and validation status
    const clients = await db.client.findMany({
        include: {
            vatPeriods: {
                include: {
                    evidenceItems: {
                        include: {
                            documents: {
                                include: {
                                    validationResults: {
                                        where: {
                                            OR: [
                                                { status: "FAILED" },
                                                { status: "WARNING" },
                                            ],
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
                orderBy: { periodEnd: "desc" },
                take: 1, // Get the most recent VAT period
            },
            bankConnections: {
                where: { isActive: true },
            },
            checklistItems: true,
        },
        orderBy: { updatedAt: "desc" },
    });

    // Transform database data to ClientRow format
    const clientRows: ClientRow[] = clients.map((client) => {
        const latestPeriod = client.vatPeriods[0];

        // Calculate document completion from checklist items
        const requiredItems = client.checklistItems.filter((item) => item.required);
        const uploadedItems = requiredItems.filter((item) => item.status === "uploaded");
        let documentsUploaded = uploadedItems.length;
        let documentsRequired = requiredItems.length;

        // If no checklist items, fall back to evidence items from VAT period
        if (documentsRequired === 0 && latestPeriod) {
            for (const item of latestPeriod.evidenceItems) {
                documentsRequired += item.expectedCount;
                documentsUploaded += item.receivedCount;
            }
        }

        // Calculate validation status from documents
        let failedValidationCount = 0;
        let pendingReviewCount = 0;

        if (latestPeriod) {
            for (const evidenceItem of latestPeriod.evidenceItems) {
                for (const doc of evidenceItem.documents) {
                    for (const result of doc.validationResults) {
                        // Count failed/warning validations
                        if (result.status === "FAILED" || result.status === "WARNING") {
                            failedValidationCount++;
                            // Count those pending review (no review action taken yet)
                            if (!result.reviewAction) {
                                pendingReviewCount++;
                            }
                        }
                    }
                }
            }
        }

        const hasFailedValidations = failedValidationCount > 0;
        const hasPendingReviews = pendingReviewCount > 0;

        // Determine status based on document completion
        let status: "needs_attention" | "in_progress" | "complete" = "needs_attention";
        if (documentsRequired > 0) {
            const completionRate = documentsUploaded / documentsRequired;
            if (completionRate >= 1) {
                // If all docs uploaded but has validation issues, mark as needs_attention
                status = hasPendingReviews ? "needs_attention" : "complete";
            } else if (completionRate > 0) {
                status = "in_progress";
            }
        } else if (latestPeriod) {
            status = "in_progress";
        }

        // Generate VAT period label
        const vatPeriodLabel = latestPeriod
            ? `Q${Math.ceil((latestPeriod.periodStart.getMonth() + 1) / 3)} ${latestPeriod.periodStart.getFullYear()}`
            : "No period";

        return {
            id: client.id.toString(),
            clientName: client.name,
            email: client.contactEmail || "",
            entityType: client.entityType.toLowerCase(),
            vatScheme: client.vatScheme || "standard",
            vatPeriodLabel,
            vatPeriodEnd: latestPeriod?.periodEnd || new Date(),
            documentsUploaded,
            documentsRequired,
            hasBankConnection: client.bankConnections.length > 0,
            status,
            updatedAt: client.updatedAt,
            hasFailedValidations,
            hasPendingReviews,
            failedValidationCount,
        };
    });

    // Calculate metrics
    const totalClients = clientRows.length;
    const documentsPending = clientRows.reduce(
        (sum, c) => sum + Math.max(0, c.documentsRequired - c.documentsUploaded),
        0
    );
    const vatReturnsDue = clientRows.filter((c) => {
        const dueDate = new Date(c.vatPeriodEnd);
        const now = new Date();
        const daysUntilDue = Math.ceil((dueDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
        return daysUntilDue <= 30 && daysUntilDue > 0;
    }).length;
    const clientsNeedingAttention = clientRows.filter((c) => c.status === "needs_attention").length;

    // Calculate flagged documents count
    const flaggedDocuments = clientRows.reduce(
        (sum, c) => sum + (c.failedValidationCount || 0),
        0
    );
    const clientsWithFlags = clientRows.filter((c) => c.hasPendingReviews).length;

    const metrics: DashboardMetrics = {
        totalClients,
        documentsPending,
        pendingSubtitle: `From ${clientRows.filter((c) => c.documentsUploaded < c.documentsRequired).length} clients`,
        vatReturnsDue,
        vatSubtitle: "Due within 30 days",
        bankConnections: clientsNeedingAttention,
        bankSubtitle: "Clients need attention",
        flaggedDocuments,
        flaggedSubtitle: clientsWithFlags > 0 ? `From ${clientsWithFlags} clients` : "All clear",
    };

    return <AccountantDashboardClient clients={clientRows} metrics={metrics} />;
}
