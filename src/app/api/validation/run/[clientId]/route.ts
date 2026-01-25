import { NextRequest, NextResponse } from "next/server";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// POST - Run validation for all documents for a client via Python backend
export async function POST(
    request: NextRequest,
    { params }: { params: { clientId: string } }
) {
    try {
        const clientId = params.clientId;

        if (!clientId) {
            return NextResponse.json(
                { success: false, error: "Invalid client ID" },
                { status: 400 }
            );
        }

        // Call Python backend to run validation for the client
        // Try multiple endpoint patterns that the backend might support
        const endpoints = [
            `${API_BASE_URL}/api/v1/validation/run/client/${clientId}`,
            `${API_BASE_URL}/api/v1/clients/${clientId}/validate`,
            `${API_BASE_URL}/api/v1/validation/run?client_id=${clientId}`,
        ];

        let lastError = null;

        for (const endpoint of endpoints) {
            try {
                const response = await fetch(endpoint, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ client_id: clientId }),
                });

                if (response.ok) {
                    const result = await response.json();
                    return NextResponse.json({
                        success: true,
                        message: result.message || "Validation started",
                        data: result,
                    });
                }

                // If 404, try next endpoint
                if (response.status === 404) {
                    continue;
                }

                // Other error, capture it
                const errorData = await response.json().catch(() => ({}));
                lastError = { status: response.status, data: errorData };
            } catch (error) {
                lastError = error;
                continue;
            }
        }

        // All endpoints failed
        console.error("Backend validation error:", lastError);
        return NextResponse.json(
            {
                success: false,
                error: "Validation endpoint not available",
                details: lastError,
            },
            { status: 502 }
        );
    } catch (error) {
        console.error("Error running validation:", error);
        return NextResponse.json(
            {
                success: false,
                error: error instanceof Error ? error.message : "Unknown error",
            },
            { status: 500 }
        );
    }
}
