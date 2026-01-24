import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { db } from "~/server/db";

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

        // Create the client record
        const client = await db.client.create({
            data: {
                name: validatedData.client_setup.client_name,
                contactEmail: validatedData.client_setup.email,
                entityType: mapEntityType(validatedData.client_setup.entity_type),
                vatScheme: validatedData.client_setup.vat_scheme,
                vatNumber: validatedData.client_setup.vat_number,
                salesChannels: validatedData.client_setup.sales_channels || [],
                notes: validatedData.client_setup.notes,
                vatPeriods: {
                    create: {
                        periodStart: new Date(validatedData.client_setup.vat_period.start),
                        periodEnd: new Date(validatedData.client_setup.vat_period.end),
                        status: "DRAFT",
                        isLocked: false,
                    },
                },
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
        const onboardingLink = `${baseUrl}/onboard/${client.id}`;

        return NextResponse.json(
            {
                success: true,
                message: "Client created successfully",
                data: {
                    client_id: client.id,
                    onboarding_link: onboardingLink,
                    email: client.contactEmail,
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
