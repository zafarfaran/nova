import { NextRequest, NextResponse } from "next/server";
import { Configuration, PlaidApi, PlaidEnvironments } from "plaid";
import { db } from "~/server/db";

const configuration = new Configuration({
    basePath: PlaidEnvironments[process.env.PLAID_ENV as keyof typeof PlaidEnvironments] || PlaidEnvironments.sandbox,
    baseOptions: {
        headers: {
            "PLAID-CLIENT-ID": process.env.PLAID_CLIENT_ID,
            "PLAID-SECRET": process.env.PLAID_SECRET,
        },
    },
});

const plaidClient = new PlaidApi(configuration);

export async function POST(request: NextRequest) {
    try {
        const { publicToken, clientId } = await request.json();

        if (!publicToken || !clientId) {
            return NextResponse.json(
                { error: "Public token and client ID are required" },
                { status: 400 }
            );
        }

        const clientIdNum = parseInt(clientId, 10);
        if (isNaN(clientIdNum)) {
            return NextResponse.json(
                { error: "Invalid client ID" },
                { status: 400 }
            );
        }

        // Exchange public token for access token
        const tokenResponse = await plaidClient.itemPublicTokenExchange({
            public_token: publicToken,
        });

        const accessToken = tokenResponse.data.access_token;
        const itemId = tokenResponse.data.item_id;

        // Get account information
        const accountsResponse = await plaidClient.accountsGet({
            access_token: accessToken,
        });

        const accounts = accountsResponse.data.accounts;
        const institution = accountsResponse.data.item.institution_id;

        // Get institution details
        let institutionName = "Unknown Bank";
        try {
            const institutionResponse = await plaidClient.institutionsGetById({
                institution_id: institution!,
                country_codes: ["GB" as any, "US" as any],
            });
            institutionName = institutionResponse.data.institution.name;
        } catch (error) {
            console.error("Error fetching institution:", error);
        }

        // Store each account in the database
        const bankConnections = await Promise.all(
            accounts.map((account) =>
                db.bankConnection.create({
                    data: {
                        clientId: clientIdNum,
                        plaidAccessToken: accessToken, // In production, encrypt this!
                        plaidItemId: itemId,
                        accountId: account.account_id,
                        accountName: account.name,
                        accountMask: account.mask || null,
                        accountType: account.type,
                        accountSubtype: account.subtype || null,
                        institutionName: institutionName,
                        institutionId: institution || "unknown",
                    },
                })
            )
        );

        // Fetch transactions in the background (don't wait for it)
        fetch(`${process.env.NEXTAUTH_URL}/api/plaid/fetch-transactions`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ clientId: clientIdNum }),
        }).catch((err) => console.error("Error triggering transaction fetch:", err));

        return NextResponse.json({
            success: true,
            accounts: bankConnections.map((conn) => ({
                id: conn.id,
                name: conn.accountName,
                mask: conn.accountMask,
                type: conn.accountType,
                institution: conn.institutionName,
            })),
        });
    } catch (error) {
        console.error("Error exchanging token:", error);
        return NextResponse.json(
            { error: "Failed to connect bank account" },
            { status: 500 }
        );
    }
}
