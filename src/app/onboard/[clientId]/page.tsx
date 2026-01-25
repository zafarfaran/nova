import { notFound } from "next/navigation";
import { db } from "~/server/db";
import { OnboardingContent } from "./OnboardingContent";

interface PageProps {
    params: Promise<{
        clientId: string;
    }>;
}

export default async function OnboardingPage({ params }: PageProps) {
    const { clientId } = await params;
    const clientIdNum = parseInt(clientId, 10);

    if (isNaN(clientIdNum)) {
        notFound();
    }

    // Fetch client data with related items
    const client = await db.client.findUnique({
        where: { id: clientIdNum },
        include: {
            checklistItems: {
                orderBy: { id: "asc" },
            },
            autoChasers: true,
            vatPeriods: {
                orderBy: { periodEnd: "desc" },
                take: 1,
            },
        },
    });

    if (!client) {
        notFound();
    }

    const latestVatPeriod = client.vatPeriods[0];
    return (
        <div className="min-h-screen bg-[#F4F5F7]">
            <OnboardingContent client={client} latestVatPeriod={latestVatPeriod} />
        </div>
    );
}
