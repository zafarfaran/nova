import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { getClient } from "~/domains/clients/api/client";
import { listEngagements } from "~/domains/engagements/api/engagement";
import { listRequestSets, listRequestItems } from "~/domains/requests/api/request";
import type { Engagement } from "~/domains/engagements/types";
import type { RequestItem } from "~/domains/requests/types";
import { logger } from "~/lib/utils/logger";
import { API_BASE_URL } from "~/lib/api/base";

const SubmitSchema = z.object({
    clientId: z.number(),
});

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const { clientId } = SubmitSchema.parse(body);

        // Get client from backend API
        const client = await getClient(clientId);

        // Fetch engagements (VAT periods) for this client
        let latestEngagement: Engagement | null = null;
        try {
            const engagementsResponse = await listEngagements(clientId);
            const engagements = engagementsResponse.items;
            
            if (engagements.length > 0) {
                latestEngagement = engagements.reduce((latest, current) => {
                    const latestDate = new Date(latest.period_end).getTime();
                    const currentDate = new Date(current.period_end).getTime();
                    return currentDate > latestDate ? current : latest;
                });
            }
        } catch (error) {
            logger.warn("Failed to fetch engagements for submission", { clientId, error });
            // Continue - engagement is optional for submission
        }

        // Fetch request items (checklist items) for this engagement
        let requestItems: RequestItem[] = [];
        if (latestEngagement?.id) {
            try {
                const requestSetsResponse = await listRequestSets(latestEngagement.id);
                const requestSets = requestSetsResponse.items;
                
                // Fetch all request items in parallel
                const itemsPromises = requestSets.map(async (requestSet) => {
                    try {
                        const itemsResponse = await listRequestItems(requestSet.id);
                        return itemsResponse.items;
                    } catch (error) {
                        logger.warn("Failed to fetch request items for submission", {
                            requestSetId: requestSet.id,
                            error,
                        });
                        return [];
                    }
                });

                const itemsArrays = await Promise.all(itemsPromises);
                requestItems = itemsArrays.flat();
            } catch (error) {
                logger.warn("Failed to fetch request sets for submission", {
                    engagementId: latestEngagement.id,
                    error,
                });
                // Continue - request items are optional
            }
        }

        // Check if all required items are complete
        const requiredItems = requestItems.filter((item) => item.is_required);
        const incompleteRequired = requiredItems.filter(
            (item) => 
                item.status !== "partial" && 
                item.status !== "complete" && 
                item.status !== "waived"
        );

        if (incompleteRequired.length > 0) {
            return NextResponse.json(
                {
                    success: false,
                    error: "Not all required items are complete",
                    incompleteItems: incompleteRequired.map((item) => item.description || `Item ${item.id}`),
                },
                { status: 400 }
            );
        }

        // Get completion summary
        const completedItems = requestItems.filter(
            (item) => item.status === "partial" || item.status === "complete"
        );
        const waivedItems = requestItems.filter(
            (item) => item.status === "waived"
        );

        // Notify backend of submission
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/clients/${clientId}/onboarding-complete`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    client_id: clientId,
                    completed_items: completedItems.length,
                    waived_items: waivedItems.length,
                    total_items: requestItems.length,
                    engagement_id: latestEngagement?.id,
                }),
            });

            if (!response.ok) {
                const errorText = await response.text().catch(() => "Unknown error");
                logger.warn("Backend onboarding notification failed", {
                    clientId,
                    status: response.status,
                    error: errorText,
                });
                // Continue anyway - the submission is still valid
            }
        } catch (backendError) {
            logger.error("Backend onboarding notification error", backendError, { clientId });
            // Continue anyway - the submission is still valid
        }

        // Return success
        return NextResponse.json({
            success: true,
            message: "Onboarding submission complete",
            summary: {
                clientName: client.name,
                completedItems: completedItems.length,
                waivedItems: waivedItems.length,
                totalItems: requestItems.length,
            },
        });
    } catch (error) {
        if (error instanceof z.ZodError) {
            return NextResponse.json(
                { success: false, error: "Invalid request", details: error.errors },
                { status: 400 }
            );
        }

        console.error("Submit error:", error);
        return NextResponse.json(
            { success: false, error: error instanceof Error ? error.message : "Unknown error" },
            { status: 500 }
        );
    }
}
