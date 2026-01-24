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

export async function POST(request: NextRequest) {
    try {
        // Parse and validate the request body
        const body = await request.json();
        const validatedData = WebhookPayloadSchema.parse(body);

        // Create the client setup record
        const clientSetup = await db.clientSetup.create({
            data: {
                id: crypto.randomUUID(),
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
                updatedAt: new Date(),
                ChecklistItem: {
                    create: validatedData.checklist.map((item) => ({
                        id: crypto.randomUUID(),
                        itemId: item.id,
                        title: item.title,
                        required: item.required,
                        status: item.status,
                        acceptance: item.acceptance,
                        ctaAction: item.cta.action,
                        ctaData: JSON.stringify(item.cta),
                        updatedAt: new Date(),
                    })),
                },
                AutoChaser: {
                    create: validatedData.auto_chasers.map((chaser) => ({
                        id: crypto.randomUUID(),
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
