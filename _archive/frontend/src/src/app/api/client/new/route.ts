import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { createClient } from "~/domains/clients/api/client";
import type { ClientCreatePayload } from "~/domains/clients/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Zod schemas for validation
const VatPeriodSchema = z.object({
    start: z.string(),
    end: z.string(),
    label: z.string(),
});

const CTASchema = z.object({
    action: z.string(),
    upload_type: z.string().optional(),
    question: z.string().optional(),
});

const ChecklistItemSchema = z.object({
    id: z.string(),
    title: z.string(),
    required: z.boolean(),
    status: z.string(),
    acceptance: z.string(),
    cta: CTASchema,
});

const ClientSchema = z.object({
    email: z.string().email(),
    client_name: z.string(),
    entity_type: z.string(),
    vat_scheme: z.string(),
    vat_period: VatPeriodSchema,
    sales_channels: z.array(z.string()).optional(),
    notes: z.string().optional(),
    vat_number: z.string().optional(),
});

const AutoChaserSchema = z.object({
    trigger: z.string(),
    delay_days: z.number(),
    message: z.string(),
});

const WebhookPayloadSchema = z.object({
    client_setup: ClientSchema,
    checklist: z.array(ChecklistItemSchema),
    auto_chasers: z.array(AutoChaserSchema),
});

// Map entity type string to enum value
function mapEntityType(entityType: string): "SOLE_TRADER" | "PARTNERSHIP" | "LLP" | "LIMITED_COMPANY" | "PLC" | "CHARITY" | "OTHER" {
    const mapping: Record<string, "SOLE_TRADER" | "PARTNERSHIP" | "LLP" | "LIMITED_COMPANY" | "PLC" | "CHARITY" | "OTHER"> = {
        sole_trader: "SOLE_TRADER",
        partnership: "PARTNERSHIP",
        llp: "LLP",
        limited_company: "LIMITED_COMPANY",
        plc: "PLC",
        charity: "CHARITY",
        other: "OTHER",
    };
    return mapping[entityType.toLowerCase()] || "LIMITED_COMPANY";
}

export async function POST(request: NextRequest) {
    try {
        // Parse and validate the request body
        const body = await request.json();
        const validatedData = WebhookPayloadSchema.parse(body);

        // Create client via backend API
        const clientPayload: ClientCreatePayload = {
            name: validatedData.client_setup.client_name,
            contact_email: validatedData.client_setup.email,
            entity_type: validatedData.client_setup.entity_type.toLowerCase() as any,
            vat_scheme: validatedData.client_setup.vat_scheme as any,
            vat_number: validatedData.client_setup.vat_number || null,
            notes: validatedData.client_setup.notes || null,
        };

        const client = await createClient(clientPayload);

        // Create engagement (VAT period) via backend API
        let engagementId: number | null = null;
        try {
            const engagementResponse = await fetch(`${API_BASE_URL}/api/v1/engagements`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    client_id: client.id,
                    engagement_type: "vat_return",
                    period_start: validatedData.client_setup.vat_period.start,
                    period_end: validatedData.client_setup.vat_period.end,
                    status: "draft",
                }),
            });

            if (engagementResponse.ok) {
                const engagement = await engagementResponse.json();
                engagementId = engagement.id;
            }
        } catch (error) {
            console.error("Failed to create engagement:", error);
            // Continue - client is created, engagement can be created later
        }

        // Create request set and items (checklist) via backend API
        if (engagementId && validatedData.checklist.length > 0) {
            try {
                // Create request set
                const requestSetResponse = await fetch(`${API_BASE_URL}/api/v1/requests/sets`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        engagement_id: engagementId,
                        title: "Onboarding Checklist",
                        description: "Initial onboarding checklist",
                    }),
                });

                if (requestSetResponse.ok) {
                    const requestSet = await requestSetResponse.json();
                    
                    // Create request items (checklist items)
                    for (const item of validatedData.checklist) {
                        try {
                            await fetch(`${API_BASE_URL}/api/v1/requests/items`, {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({
                                    request_set_id: requestSet.id,
                                    title: item.title,
                                    description: item.cta.question || item.title,
                                    is_required: item.required,
                                    document_type: item.cta.upload_type || "other",
                                    order_index: validatedData.checklist.indexOf(item),
                                }),
                            });
                        } catch (error) {
                            console.error(`Failed to create request item ${item.id}:`, error);
                        }
                    }
                }
            } catch (error) {
                console.error("Failed to create request set:", error);
                // Continue - client is created, checklist can be created later
            }
        }

        // Note: Auto chasers are not yet supported by backend API
        // TODO: Implement auto chaser endpoints in backend or handle via engagement

        // Generate the onboarding link
        const baseUrl = process.env.NEXTAUTH_URL || "http://localhost:3000";
        const onboardingLink = `${baseUrl}/onboard/${client.id}`;

        return NextResponse.json(
            {
                success: true,
                message: "Client created successfully",
                data: {
                    client_id: client.id,
                    onboarding_link: onboardingLink,
                    email: client.contact_email,
                    client_name: client.name,
                },
            },
            { status: 201 }
        );
    } catch (error) {
        if (error instanceof z.ZodError) {
            return NextResponse.json(
                {
                    success: false,
                    message: "Invalid payload",
                    errors: error.errors,
                },
                { status: 400 }
            );
        }

        console.error("Error creating client:", error);
        return NextResponse.json(
            {
                success: false,
                message: "Internal server error",
                error: error instanceof Error ? error.message : "Unknown error",
            },
            { status: 500 }
        );
    }
}
