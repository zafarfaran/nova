import { NextRequest, NextResponse } from "next/server";
import { Configuration, PlaidApi, PlaidEnvironments, Products, CountryCode } from "plaid";

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
        const { clientId } = await request.json();

        if (!clientId) {
            return NextResponse.json(
                { error: "Client ID is required" },
                { status: 400 }
            );
        }

        const response = await plaidClient.linkTokenCreate({
            user: {
                client_user_id: clientId,
            },
            client_name: "VAT Pack Portal",
            products: [Products.Auth, Products.Transactions],
            country_codes: [CountryCode.Gb, CountryCode.Us],
            language: "en",
            webhook: `${process.env.NEXTAUTH_URL}/api/plaid/webhook`,
        });

        return NextResponse.json({ link_token: response.data.link_token });
    } catch (error) {
        console.error("Error creating link token:", error);
        return NextResponse.json(
            { error: "Failed to create link token" },
            { status: 500 }
        );
    }
}
