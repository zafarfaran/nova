import { NextRequest, NextResponse } from "next/server";
import { Configuration, PlaidApi, PlaidEnvironments } from "plaid";
import { db } from "~/server/db";
import { UTApi } from "uploadthing/server";

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
const utapi = new UTApi({ token: process.env.UPLOADTHING_TOKEN });

export async function POST(request: NextRequest) {
    try {
        const { clientId } = await request.json();

        if (!clientId) {
            return NextResponse.json(
                { error: "Client ID is required" },
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

        // Get all active bank connections for this client
        const bankConnections = await db.bankConnection.findMany({
            where: {
                clientId: clientIdNum,
                isActive: true,
            },
        });

        if (bankConnections.length === 0) {
            return NextResponse.json(
                { error: "No active bank connections found" },
                { status: 404 }
            );
        }

        // Fetch transactions for the last 90 days
        const endDate = new Date().toISOString().split("T")[0];
        const startDate = new Date(Date.now() - 90 * 24 * 60 * 60 * 1000)
            .toISOString()
            .split("T")[0];

        const allTransactions: any[] = [];

        // Fetch transactions from all connected accounts
        for (const connection of bankConnections) {
            try {
                const response = await plaidClient.transactionsGet({
                    access_token: connection.plaidAccessToken,
                    start_date: startDate!,
                    end_date: endDate!,
                    options: {
                        count: 500,
                        offset: 0,
                    },
                });

                const transactions = response.data.transactions.map((txn) => ({
                    account_id: txn.account_id,
                    account_name: connection.accountName,
                    institution: connection.institutionName,
                    date: txn.date,
                    name: txn.name,
                    amount: txn.amount,
                    currency: txn.iso_currency_code || "GBP",
                    category: txn.category ? txn.category.join(", ") : "Uncategorized",
                    pending: txn.pending,
                    transaction_id: txn.transaction_id,
                    merchant_name: txn.merchant_name || "",
                }));

                allTransactions.push(...transactions);
            } catch (error) {
                console.error(`Error fetching transactions for account ${connection.accountId}:`, error);
            }
        }

        if (allTransactions.length === 0) {
            return NextResponse.json({
                success: true,
                message: "No transactions found",
                count: 0,
            });
        }

        // Convert transactions to CSV format
        const csvHeader = "Account Name,Institution,Date,Description,Amount,Currency,Category,Status,Transaction ID,Merchant\n";
        const csvRows = allTransactions.map((txn) =>
            [
                txn.account_name,
                txn.institution,
                txn.date,
                `"${txn.name.replace(/"/g, '""')}"`,
                txn.amount,
                txn.currency,
                `"${txn.category.replace(/"/g, '""')}"`,
                txn.pending ? "Pending" : "Posted",
                txn.transaction_id,
                `"${txn.merchant_name.replace(/"/g, '""')}"`,
            ].join(",")
        );
        const csvContent = csvHeader + csvRows.join("\n");

        // Upload to UploadThing
        const fileName = `${clientId}_Banktransaction.csv`;
        const file = new File([csvContent], fileName, { type: "text/csv" });

        const uploadResult = await utapi.uploadFiles(file);

        if (uploadResult.error) {
            throw new Error(`UploadThing error: ${uploadResult.error.message}`);
        }

        // Create or update checklist item for bank statements
        const existingItem = await db.checklistItem.findFirst({
            where: {
                clientId: clientIdNum,
                itemId: "bank_statements",
            },
        });

        if (existingItem) {
            // Update existing item
            await db.checklistItem.update({
                where: { id: existingItem.id },
                data: {
                    status: "uploaded",
                    uploadedFileUrl: uploadResult.data?.url,
                    ctaData: JSON.stringify({
                        transactionCount: allTransactions.length,
                        startDate,
                        endDate,
                        fileName,
                        fetchedAt: new Date().toISOString(),
                    }),
                },
            });
        } else {
            // Create new checklist item
            await db.checklistItem.create({
                data: {
                    clientId: clientIdNum,
                    itemId: "bank_statements",
                    title: "Bank Statements (Auto-fetched from Plaid)",
                    required: true,
                    status: "uploaded",
                    acceptance: "auto",
                    ctaAction: "plaid_sync",
                    ctaData: JSON.stringify({
                        transactionCount: allTransactions.length,
                        startDate,
                        endDate,
                        fileName,
                        fetchedAt: new Date().toISOString(),
                    }),
                    uploadedFileUrl: uploadResult.data?.url,
                },
            });
        }

        return NextResponse.json({
            success: true,
            count: allTransactions.length,
            fileUrl: uploadResult.data?.url,
            fileName: fileName,
            startDate,
            endDate,
        });
    } catch (error) {
        console.error("Error fetching transactions:", error);
        return NextResponse.json(
            { error: "Failed to fetch transactions" },
            { status: 500 }
        );
    }
}
