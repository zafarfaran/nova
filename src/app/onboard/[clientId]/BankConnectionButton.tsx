"use client";

import { useCallback, useEffect, useState } from "react";
import { usePlaidLink } from "react-plaid-link";

interface BankAccount {
    id: string;
    accountName: string;
    accountMask: string | null;
    accountType: string;
    accountSubtype: string | null;
    institutionName: string;
    createdAt: string;
}

interface BankConnectionButtonProps {
    clientId: string;
}

export function BankConnectionButton({ clientId }: BankConnectionButtonProps) {
    const [linkToken, setLinkToken] = useState<string | null>(null);
    const [accounts, setAccounts] = useState<BankAccount[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    // Fetch existing bank accounts
    const fetchAccounts = useCallback(async () => {
        try {
            const response = await fetch(`/api/plaid/accounts/${clientId}`);
            const data = await response.json();
            setAccounts(data.accounts || []);
        } catch (error) {
            console.error("Error fetching accounts:", error);
        }
    }, [clientId]);

    useEffect(() => {
        fetchAccounts();
    }, [fetchAccounts]);

    // Create link token
    const createLinkToken = async () => {
        setIsLoading(true);
        try {
            const response = await fetch("/api/plaid/create-link-token", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ clientId }),
            });
            const data = await response.json();
            setLinkToken(data.link_token);
        } catch (error) {
            console.error("Error creating link token:", error);
            alert("Failed to initialize bank connection");
        } finally {
            setIsLoading(false);
        }
    };

    // Handle successful connection
    const onSuccess = useCallback(
        async (publicToken: string) => {
            setIsLoading(true);
            try {
                const response = await fetch("/api/plaid/exchange-token", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ publicToken, clientId }),
                });

                if (response.ok) {
                    await fetchAccounts();
                    alert("✅ Bank account connected successfully!");
                } else {
                    alert("Failed to connect bank account");
                }
            } catch (error) {
                console.error("Error exchanging token:", error);
                alert("Failed to connect bank account");
            } finally {
                setIsLoading(false);
            }
        },
        [clientId, fetchAccounts]
    );

    const { open, ready } = usePlaidLink({
        token: linkToken,
        onSuccess,
    });

    // Disconnect bank account
    const disconnectAccount = async (accountId: string) => {
        if (!confirm("Are you sure you want to disconnect this bank account?")) {
            return;
        }

        try {
            const response = await fetch(
                `/api/plaid/accounts/${clientId}?accountId=${accountId}`,
                { method: "DELETE" }
            );

            if (response.ok) {
                await fetchAccounts();
                alert("Bank account disconnected");
            }
        } catch (error) {
            console.error("Error disconnecting account:", error);
            alert("Failed to disconnect account");
        }
    };

    return (
        <div className="space-y-4">
            {/* Connected Accounts */}
            {accounts.length > 0 && (
                <div className="space-y-3">
                    <h3 className="text-sm font-medium text-slate-700">
                        Connected Bank Accounts
                    </h3>
                    {accounts.map((account) => (
                        <div
                            key={account.id}
                            className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
                        >
                            <div className="flex items-center gap-3">
                                <div className="flex-shrink-0 rounded-full bg-green-100 p-2">
                                    <svg
                                        className="h-5 w-5 text-green-600"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                    >
                                        <path
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth={2}
                                            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                                        />
                                    </svg>
                                </div>
                                <div>
                                    <p className="font-medium text-slate-900">
                                        {account.institutionName}
                                    </p>
                                    <p className="text-sm text-slate-600">
                                        {account.accountName}
                                        {account.accountMask && ` ••••${account.accountMask}`}
                                    </p>
                                    <p className="text-xs text-slate-500 capitalize">
                                        {account.accountSubtype || account.accountType}
                                    </p>
                                </div>
                            </div>
                            <button
                                onClick={() => disconnectAccount(account.id)}
                                className="rounded-lg bg-red-50 px-3 py-2 text-sm font-medium text-red-700 transition-colors hover:bg-red-100"
                            >
                                Disconnect
                            </button>
                        </div>
                    ))}
                </div>
            )}

            {/* Connect Button */}
            <button
                onClick={() => {
                    if (linkToken && ready) {
                        open();
                    } else {
                        createLinkToken();
                    }
                }}
                disabled={isLoading}
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-3.5 text-base font-semibold text-white shadow-lg transition-all hover:from-blue-700 hover:to-indigo-700 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
            >
                {isLoading ? (
                    <>
                        <svg
                            className="h-5 w-5 animate-spin"
                            fill="none"
                            viewBox="0 0 24 24"
                        >
                            <circle
                                className="opacity-25"
                                cx="12"
                                cy="12"
                                r="10"
                                stroke="currentColor"
                                strokeWidth="4"
                            />
                            <path
                                className="opacity-75"
                                fill="currentColor"
                                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            />
                        </svg>
                        Connecting...
                    </>
                ) : (
                    <>
                        <svg
                            className="h-5 w-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                            />
                        </svg>
                        {linkToken && ready ? "Open Bank Selection" : "Connect Bank Account"}
                    </>
                )}
            </button>

            {/* Info Text */}
            <p className="text-xs text-slate-500">
                🔒 Securely connect your bank account using Plaid. Your credentials are never stored.
            </p>
        </div>
    );
}
