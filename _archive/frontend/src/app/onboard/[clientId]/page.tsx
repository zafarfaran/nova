import { notFound } from "next/navigation";
import { getClient } from "~/domains/clients/api/client";
import { listEngagements } from "~/domains/engagements/api/engagement";
import { listRequestSets, listRequestItems } from "~/domains/requests/api/request";
import type { Engagement } from "~/domains/engagements/types";
import type { RequestItem } from "~/domains/requests/types";
import { logger } from "~/lib/utils/logger";

import { OnboardingContent } from "./OnboardingContent";

interface PageProps {
    params: Promise<{
        clientId: string;
    }>;
}

export default async function OnboardingPage({ params }: PageProps) {
    const { clientId } = await params;
    const clientIdNum = parseInt(clientId, 10);

    if (isNaN(clientIdNum) || clientIdNum <= 0) {
        notFound();
    }

    // Fetch client data from backend API
    let client;
    try {
        client = await getClient(clientIdNum);
    } catch (error) {
        logger.error("Failed to fetch client", error, { clientId: clientIdNum });
        notFound();
    }

    // Fetch engagements (VAT periods) for this client
    let latestEngagement: Engagement | null = null;
    try {
        const engagementsResponse = await listEngagements(clientIdNum);
        const engagements = engagementsResponse.items;
        
        if (engagements.length > 0) {
            // Get the most recent engagement by period_end
            latestEngagement = engagements.reduce((latest, current) => {
                const latestDate = new Date(latest.period_end).getTime();
                const currentDate = new Date(current.period_end).getTime();
                return currentDate > latestDate ? current : latest;
            });
        }
    } catch (error) {
        logger.warn("Failed to fetch engagements", { clientId: clientIdNum, error });
        // Continue without engagements - not critical for onboarding
    }

    // Fetch request sets and items for this engagement
    let requestItems: RequestItem[] = [];
    if (latestEngagement?.id) {
        try {
            const requestSetsResponse = await listRequestSets(latestEngagement.id);
            const requestSets = requestSetsResponse.items;
            
            // Fetch request items from all request sets in parallel
            const itemsPromises = requestSets.map(async (requestSet) => {
                try {
                    const itemsResponse = await listRequestItems(requestSet.id);
                    return itemsResponse.items;
                } catch (error) {
                    logger.warn("Failed to fetch request items", {
                        requestSetId: requestSet.id,
                        error,
                    });
                    return [];
                }
            });

            const itemsArrays = await Promise.all(itemsPromises);
            requestItems = itemsArrays.flat();
        } catch (error) {
            logger.warn("Failed to fetch request sets", {
                engagementId: latestEngagement.id,
                error,
            });
            // Continue without request items - user can still see the page
        }
    }

    // Use backend data directly - no transformation
    const clientData = {
        id: client.id,
        name: client.name,
        contact_email: client.contact_email ?? null,
        entity_type: client.entity_type,
        vat_scheme: client.vat_scheme ?? null,
        requestItems,
        latestEngagement,
    };

    return (
        <div className="min-h-screen bg-[#F4F5F7]">
            <OnboardingContent 
                client={clientData} 
                latestEngagement={latestEngagement}
            />
        </div>
    );
}
