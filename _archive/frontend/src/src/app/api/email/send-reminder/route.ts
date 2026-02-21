import { NextRequest, NextResponse } from "next/server";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface SendReminderRequest {
    clientId: string;
    clientName: string;
    clientEmail: string;
    contextData?: Record<string, unknown>;
}

// POST - Send reminder email to client
export async function POST(request: NextRequest) {
    try {
        const body = await request.json() as SendReminderRequest;
        const { clientId, clientName, clientEmail, contextData } = body;

        if (!clientId || !clientEmail) {
            return NextResponse.json(
                { success: false, error: "Client ID and email are required" },
                { status: 400 }
            );
        }

        // Prepare email request for backend
        const emailRequest = {
            to_email: clientEmail,
            to_name: clientName || clientEmail,
            purpose: "reminder",
            tone: "friendly",
            client_id: parseInt(clientId, 10),
            context_data: contextData || {
                reminder_type: "document upload reminder",
                call_to_action: "Upload your documents to your Nova dashboard.",
            },
        };

        // Call Python backend to send email
        const endpoint = `${API_BASE_URL}/api/v1/email/send`;
        const response = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(emailRequest),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error("Backend email error:", errorData);
            return NextResponse.json(
                {
                    success: false,
                    error: errorData.detail || "Failed to send email",
                },
                { status: response.status }
            );
        }

        const result = await response.json();
        return NextResponse.json({
            success: true,
            message: result.message || "Reminder sent successfully",
            data: result,
        });
    } catch (error) {
        console.error("Error sending reminder:", error);
        return NextResponse.json(
            {
                success: false,
                error: error instanceof Error ? error.message : "Unknown error",
            },
            { status: 500 }
        );
    }
}
