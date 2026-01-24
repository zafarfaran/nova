import { NextRequest, NextResponse } from "next/server";
import { db } from "~/server/db";

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ clientId: string }> }
) {
    try {
        const { clientId } = await params;
        const clientIdNum = parseInt(clientId, 10);

        if (isNaN(clientIdNum)) {
            return NextResponse.json(
                { error: "Invalid client ID" },
                { status: 400 }
            );
        }

        const bankConnections = await db.bankConnection.findMany({
            where: {
                clientId: clientIdNum,
                isActive: true,
            },
            select: {
                id: true,
                accountName: true,
                accountMask: true,
                accountType: true,
                accountSubtype: true,
                institutionName: true,
                createdAt: true,
            },
            orderBy: {
                createdAt: "desc",
            },
        });

        return NextResponse.json({ accounts: bankConnections });
    } catch (error) {
        console.error("Error fetching bank accounts:", error);
        return NextResponse.json(
            { error: "Failed to fetch bank accounts" },
            { status: 500 }
        );
    }
}

export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ clientId: string }> }
) {
    try {
        const { searchParams } = new URL(request.url);
        const accountId = searchParams.get("accountId");

        if (!accountId) {
            return NextResponse.json(
                { error: "Account ID is required" },
                { status: 400 }
            );
        }

        const accountIdNum = parseInt(accountId, 10);
        if (isNaN(accountIdNum)) {
            return NextResponse.json(
                { error: "Invalid account ID" },
                { status: 400 }
            );
        }

        await db.bankConnection.update({
            where: { id: accountIdNum },
            data: { isActive: false },
        });

        return NextResponse.json({ success: true });
    } catch (error) {
        console.error("Error disconnecting bank account:", error);
        return NextResponse.json(
            { error: "Failed to disconnect bank account" },
            { status: 500 }
        );
    }
}
