import { db } from "~/server/db";
import { AccountantDashboardClient } from "./DashboardClient";
import type { ClientRow } from "./components/ClientTable";
import type { DashboardMetrics } from "./components/QuickMetrics";

// Server component that fetches data
export default async function AccountantDashboard() {
    // Fetch all clients with their checklist items and bank connections
    const clientSetups = await db.clientSetup.findMany({
        include: {
            checklistItems: true,
            bankConnections: {
                where: { isActive: true },
            },
        },
        orderBy: { updatedAt: "desc" },
    });

    // Transform database data to ClientRow format
    const clients: ClientRow[] = clientSetups.map((client) => {
        const documentsRequired = client.checklistItems.filter((item) => item.required).length;
        const documentsUploaded = client.checklistItems.filter(
            (item) => item.required && item.status === "uploaded"
        ).length;
        const hasBankConnection = client.bankConnections.length > 0;

        // Determine status based on document completion
        let status: "needs_attention" | "in_progress" | "complete" = "needs_attention";
        if (documentsRequired > 0) {
            const completionRate = documentsUploaded / documentsRequired;
            if (completionRate === 1) {
                status = "complete";
            } else if (completionRate > 0) {
                status = "in_progress";
            }
        } else {
            status = hasBankConnection ? "complete" : "in_progress";
        }

        return {
            id: client.id,
            clientName: client.clientName,
            email: client.email,
            entityType: client.entityType,
            vatScheme: client.vatScheme,
            vatPeriodLabel: client.vatPeriodLabel,
            vatPeriodEnd: client.vatPeriodEnd,
            documentsUploaded,
            documentsRequired,
            hasBankConnection,
            status,
            updatedAt: client.updatedAt,
        };
    });

    // Calculate metrics
    const totalClients = clients.length;
    const documentsPending = clients.reduce(
        (sum, c) => sum + (c.documentsRequired - c.documentsUploaded),
        0
    );
    const vatReturnsDue = clients.filter((c) => {
        const dueDate = new Date(c.vatPeriodEnd);
        const now = new Date();
        const daysUntilDue = Math.ceil((dueDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
        return daysUntilDue <= 30 && daysUntilDue > 0;
    }).length;
    const bankConnections = clients.filter((c) => c.hasBankConnection).length;

    const metrics: DashboardMetrics = {
        totalClients,
        documentsPending,
        pendingSubtitle: `From ${clients.filter((c) => c.documentsUploaded < c.documentsRequired).length} clients`,
        vatReturnsDue,
        vatSubtitle: "Due within 30 days",
        bankConnections,
        bankSubtitle: `${totalClients - bankConnections} pending`,
    };

    return <AccountantDashboardClient clients={clients} metrics={metrics} />;
}
