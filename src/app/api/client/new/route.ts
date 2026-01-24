import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { db } from "~/server/db";
import { clientsApi } from "~/lib/api/client";
import { EntityType } from "~/lib/api/types";

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

const ClientSetupSchema = z.object({
    email: z.string().email(),
    client_name: z.string(),
    entity_type: z.string(),
    vat_scheme: z.string(),
    vat_period: VatPeriodSchema,
    bank_accounts: z.array(z.string()),
    sales_channels: z.array(z.string()),
    notes: z.string().optional(),
});

const AutoChaserSchema = z.object({
    trigger: z.string(),
    delay_days: z.number(),
    message: z.string(),
});

const WebhookPayloadSchema = z.object({
    client_setup: ClientSetupSchema,
    checklist: z.array(ChecklistItemSchema),
    auto_chasers: z.array(AutoChaserSchema),
});

// Map frontend entity type to backend entity type
function mapEntityType(frontendType: string): EntityType {
    const mapping: Record<string, EntityType> = {
        "sole_trader": EntityType.SOLE_TRADER,
        "partnership": EntityType.PARTNERSHIP,
        "llp": EntityType.LLP,
        "limited_company": EntityType.LIMITED_COMPANY,
        "plc": EntityType.PLC,
        "charity": EntityType.CHARITY,
    };
    return mapping[frontendType.toLowerCase()] || EntityType.OTHER;
}

export async function POST(request: NextRequest) {
    try {
        // Parse and validate the request body
        const body = await request.json();
        const validatedData = WebhookPayloadSchema.parse(body);

        // First, try to create the client in the backend
        let backendClientId: number | null = null;
        try {
            const backendClient = await clientsApi.create({
                name: validatedData.client_setup.client_name,
                contact_email: validatedData.client_setup.email,
                entity_type: mapEntityType(validatedData.client_setup.entity_type),
                notes: validatedData.client_setup.notes,
            });
            backendClientId = backendClient.id;
            console.log(`Created backend client with ID: ${backendClientId}`);
        } catch (backendError) {
            // Log but don't fail - backend might be unavailable
            console.error("Failed to create backend client:", backendError);
        }

        // Create the client setup record
        const clientSetup = await db.clientSetup.create({
            data: {
                email: validatedData.client_setup.email,
                clientName: validatedData.client_setup.client_name,
                entityType: validatedData.client_setup.entity_type,
                vatScheme: validatedData.client_setup.vat_scheme,
                vatPeriodStart: new Date(validatedData.client_setup.vat_period.start),
                vatPeriodEnd: new Date(validatedData.client_setup.vat_period.end),
                vatPeriodLabel: validatedData.client_setup.vat_period.label,
                bankAccounts: validatedData.client_setup.bank_accounts,
                salesChannels: validatedData.client_setup.sales_channels,
                notes: validatedData.client_setup.notes,
                backendClientId: backendClientId,
                checklistItems: {
                    create: validatedData.checklist.map((item) => ({
                        itemId: item.id,
                        title: item.title,
                        required: item.required,
                        status: item.status,
                        acceptance: item.acceptance,
                        ctaAction: item.cta.action,
                        ctaData: JSON.stringify(item.cta),
                    })),
                },
                autoChasers: {
                    create: validatedData.auto_chasers.map((chaser) => ({
                        trigger: chaser.trigger,
                        delayDays: chaser.delay_days,
                        message: chaser.message,
                    })),
                },
            },
        });

        // Generate the onboarding link
        const baseUrl = process.env.NEXTAUTH_URL || "http://localhost:3000";
        const onboardingLink = `${baseUrl}/onboard/${clientSetup.id}`;

        return NextResponse.json(
            {
                success: true,
                message: "Client setup created successfully",
                data: {
                    client_id: clientSetup.id,
                    backend_client_id: backendClientId,
                    onboarding_link: onboardingLink,
                    email: clientSetup.email,
                    client_name: clientSetup.clientName,
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

        console.error("Error creating client setup:", error);
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
