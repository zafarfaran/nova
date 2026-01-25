"use client";

import { useState } from "react";
import { BankConnectionButton } from "./BankConnectionButton";

interface BankStatementChoiceProps {
    clientId: number;
    onManualUpload: () => void;
}

export function BankStatementChoice({ clientId, onManualUpload }: BankStatementChoiceProps) {
    const [choice, setChoice] = useState<"none" | "connect" | "manual">("none");

    if (choice === "none") {
        return (
            <div className="space-y-4">
                <div className="text-center mb-6">
                    <h3 className="text-lg font-semibold text-slate-900 mb-2">
                        How would you like to provide bank statements?
                    </h3>
                    <p className="text-sm text-slate-600">
                        Choose your preferred method
                    </p>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                    {/* Connect Bank Account Option */}
                    <button
                        onClick={() => setChoice("connect")}
                        className="group relative overflow-hidden rounded-xl border-2 border-green-200 bg-gradient-to-br from-green-50 to-emerald-50 p-6 text-left transition-all hover:border-green-400 hover:shadow-lg"
                    >
                        <div className="flex flex-col items-center text-center">
                            <div className="mb-4 rounded-full bg-green-100 p-4">
                                <svg
                                    className="h-8 w-8 text-green-600"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M13 10V3L4 14h7v7l9-11h-7z"
                                    />
                                </svg>
                            </div>
                            <h4 className="text-lg font-bold text-slate-900 mb-2">
                                Connect Bank Account
                            </h4>
                            <p className="text-sm text-slate-600 mb-4">
                                Automatically sync transactions securely via Plaid
                            </p>
                            <div className="space-y-2 text-xs text-slate-600">
                                <div className="flex items-center gap-2">
                                    <svg className="h-4 w-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                    </svg>
                                    <span>Fully automated</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <svg className="h-4 w-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                    </svg>
                                    <span>90 days of history</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <svg className="h-4 w-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                    </svg>
                                    <span>Bank-grade security</span>
                                </div>
                            </div>
                            <div className="mt-4 text-xs font-semibold text-green-600 group-hover:text-green-700">
                                Recommended ✨
                            </div>
                        </div>
                    </button>

                    {/* Manual Upload Option */}
                    <button
                        onClick={() => {
                            setChoice("manual");
                            onManualUpload();
                        }}
                        className="group relative overflow-hidden rounded-xl border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50 p-6 text-left transition-all hover:border-blue-400 hover:shadow-lg"
                    >
                        <div className="flex flex-col items-center text-center">
                            <div className="mb-4 rounded-full bg-blue-100 p-4">
                                <svg
                                    className="h-8 w-8 text-blue-600"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                                    />
                                </svg>
                            </div>
                            <h4 className="text-lg font-bold text-slate-900 mb-2">
                                Upload Manually
                            </h4>
                            <p className="text-sm text-slate-600 mb-4">
                                Upload PDF or CSV bank statements yourself
                            </p>
                            <div className="space-y-2 text-xs text-slate-600">
                                <div className="flex items-center gap-2">
                                    <svg className="h-4 w-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                    </svg>
                                    <span>Full control</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <svg className="h-4 w-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                    </svg>
                                    <span>No bank login needed</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <svg className="h-4 w-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                    </svg>
                                    <span>Upload existing files</span>
                                </div>
                            </div>
                        </div>
                    </button>
                </div>

                <div className="text-center text-xs text-slate-500 mt-4">
                    <svg className="h-4 w-4 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                    Your data is encrypted and secure
                </div>
            </div>
        );
    }

    if (choice === "connect") {
        return (
            <div className="space-y-4">
                <button
                    onClick={() => setChoice("none")}
                    className="text-sm text-slate-600 hover:text-slate-900 flex items-center gap-1"
                >
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                    Back to options
                </button>
                <BankConnectionButton clientId={clientId} />
            </div>
        );
    }

    // Manual choice - will be handled by parent component
    return null;
}
