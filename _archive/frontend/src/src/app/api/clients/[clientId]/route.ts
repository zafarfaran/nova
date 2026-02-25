import { NextRequest, NextResponse } from "next/server";
import { deleteClient } from "~/domains/clients/api/client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ clientId: string }> }
) {
    try {
        const { clientId: clientIdParam } = await params;
        const clientId = parseInt(clientIdParam, 10);

        if (isNaN(clientId)) {
            return NextResponse.json(
                { success: false, error: "Invalid client ID" },
                { status: 400 }
            );
        }

        // Delete client via backend API (backend handles cascading deletes)
        try {
            await deleteClient(clientId);
            return NextResponse.json({ success: true });
        } catch (error) {
            // If deleteClient throws, it's already an ApiError with proper status
            if (error instanceof Error) {
                const statusCode = "statusCode" in error ? (error.statusCode as number) : 500;
                return NextResponse.json(
                    {
                        success: false,
                        error: error.message,
                    },
                    { status: statusCode }
                );
            }
            throw error;
        }
    } catch (error) {
        console.error("Error deleting client:", error);
        return NextResponse.json(
            {
                success: false,
                error: error instanceof Error ? error.message : "Unknown error",
            },
            { status: 500 }
        );
    }
}
