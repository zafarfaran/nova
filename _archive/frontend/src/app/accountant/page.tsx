import { auth } from "~/server/auth";
import { AccountantDashboardClient } from "./DashboardClient";
import type { ClientRow } from "./components/ClientTable";
import type { DashboardMetrics } from "./components/QuickMetrics";
import { listClients } from "~/domains/clients/api/client";
import type { ClientResponse } from "~/domains/clients/types";
import { logger } from "~/lib/utils/logger";

// Server component that fetches data from the backend API
export default async function AccountantDashboard() {
    // Get the current user session
    const session = await auth();
    
    // Fetch clients from backend API
    let clientRows: ClientRow[] = [];
    try {
        const data = await listClients(0, 1000);
        
        // Transform backend API data to ClientRow format
        // Note: Backend API currently returns basic client data only
        // VAT periods, documents, and validation data will need separate API calls or enhanced endpoint
        clientRows = data.items.map((client) => {
            return {
                id: client.id.toString(),
                clientName: client.name,
                email: client.contact_email || "",
                entityType: client.entity_type.toLowerCase(),
                vatScheme: client.vat_scheme || "standard",
                vatPeriodLabel: "No period", // TODO: Fetch from separate endpoint
                vatPeriodId: undefined,
                vatPeriodStatus: undefined,
                vatPeriodEnd: new Date(), // Default to current date
                documentsUploaded: 0, // TODO: Fetch from separate endpoint
                documentsRequired: 0, // TODO: Fetch from separate endpoint
                hasBankConnection: false, // TODO: Fetch from separate endpoint
                status: "needs_attention" as const, // Default status
                updatedAt: new Date(client.updated_at),
                hasFailedValidations: false, // TODO: Fetch from separate endpoint
                hasPendingReviews: false, // TODO: Fetch from separate endpoint
                failedValidationCount: 0, // TODO: Fetch from separate endpoint
            };
        });
    } catch (error) {
        logger.error("Failed to fetch clients for dashboard", error);
        // Return empty array on error - client component will handle loading/error states
        clientRows = [];
    }

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

    return (
        <AccountantDashboardClient
            clients={clientRows}
            metrics={metrics}
            user={{
                name: session?.user?.name ?? null,
                email: session?.user?.email ?? null,
                image: session?.user?.image ?? null,
            }}
        />
    );
}
