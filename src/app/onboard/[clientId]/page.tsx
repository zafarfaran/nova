import { notFound } from "next/navigation";
import { db } from "~/server/db";
import { ChecklistUploader } from "./ChecklistUploader";
import { SubmitButton } from "./SubmitButton";
import { BankConnectionButton } from "./BankConnectionButton";

interface PageProps {
    params: Promise<{
        clientId: string;
    }>;
}

export default async function OnboardingPage({ params }: PageProps) {
    const { clientId } = await params;

    // Fetch client setup data with related checklist items (from Prisma)
    const clientSetup = await db.clientSetup.findUnique({
        where: { id: clientId },
        include: {
            ChecklistItem: true,
            AutoChaser: true,
        },
    });

    if (!clientSetup) {
        notFound();
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100">
            <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-12 lg:px-8">
                {/* Header */}
                <div className="mb-8 text-center sm:mb-12">
                    <div className="mb-4 inline-flex items-center justify-center rounded-full bg-blue-100 p-3 ring-4 ring-blue-50">
                        <svg className="h-8 w-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                    </div>
                    <h1 className="text-3xl font-bold text-slate-900 sm:text-4xl lg:text-5xl">
                        VAT Pack Portal
                    </h1>
                    <p className="mt-2 text-lg font-medium text-blue-600 sm:text-xl">
                        {clientSetup.clientName}
                    </p>
                    <p className="mt-1 text-sm text-slate-600">
                        Complete your document checklist below
                    </p>
                </div>

                {/* Client Setup Information */}
                <div className="mb-6 overflow-hidden rounded-2xl bg-white shadow-lg ring-1 ring-slate-200 sm:mb-8">
                    <div className="border-b border-slate-200 bg-gradient-to-r from-slate-50 to-blue-50 px-6 py-4 sm:px-8">
                        <h2 className="flex items-center gap-2 text-xl font-semibold text-slate-900 sm:text-2xl">
                            <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Client Information
                        </h2>
                    </div>

                    <div className="grid gap-4 p-6 sm:grid-cols-2 sm:gap-6 sm:p-8 lg:grid-cols-3">
                        <InfoCard label="Email" value={clientSetup.email} icon="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        <InfoCard label="Entity Type" value={clientSetup.entityType} icon="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                        <InfoCard label="VAT Scheme" value={clientSetup.vatScheme} icon="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />

                        <div className="sm:col-span-2 lg:col-span-3">
                            <InfoCard
                                label="VAT Period"
                                value={clientSetup.vatPeriodLabel}
                                subtitle={`${new Date(clientSetup.vatPeriodStart).toLocaleDateString()} - ${new Date(clientSetup.vatPeriodEnd).toLocaleDateString()}`}
                                icon="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                            />
                        </div>

                        <div className="sm:col-span-2 lg:col-span-3">
                            <div className="grid gap-4 sm:grid-cols-2">
                                <ListCard label="Bank Accounts" items={clientSetup.bankAccounts} icon="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                                <ListCard label="Sales Channels" items={clientSetup.salesChannels} icon="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                            </div>
                        </div>

                        {clientSetup.notes && (
                            <div className="sm:col-span-2 lg:col-span-3">
                                <InfoCard label="Notes" value={clientSetup.notes} icon="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                            </div>
                        )}
                    </div>
                </div>


                {/* Checklist */}
                <div className="mb-6 overflow-hidden rounded-2xl bg-white shadow-lg ring-1 ring-slate-200 sm:mb-8">
                    <div className="border-b border-slate-200 bg-gradient-to-r from-slate-50 to-purple-50 px-6 py-4 sm:px-8">
                        <h2 className="flex items-center gap-2 text-xl font-semibold text-slate-900 sm:text-2xl">
                            <svg className="h-6 w-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Document Checklist
                        </h2>
                    </div>

                    <div className="space-y-4 p-6 sm:p-8">
                        {clientSetup.ChecklistItem.map((item) => (
                            <ChecklistUploader
                                key={item.id}
                                item={item}
                                clientId={clientSetup.id}
                            />
                        ))}
                    </div>
                </div>

                {/* Bank Connection Section */}
                <div className="mb-6 overflow-hidden rounded-2xl bg-white shadow-lg ring-1 ring-slate-200 sm:mb-8">
                    <div className="border-b border-slate-200 bg-gradient-to-r from-slate-50 to-green-50 px-6 py-4 sm:px-8">
                        <h2 className="flex items-center gap-2 text-xl font-semibold text-slate-900 sm:text-2xl">
                            <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                            </svg>
                            Bank Account Connection
                        </h2>
                        <p className="mt-1 text-sm text-slate-600">
                            Securely connect your bank accounts for automatic transaction sync
                        </p>
                    </div>

                    <div className="p-6 sm:p-8">
                        <BankConnectionButton clientId={clientSetup.id} />
                    </div>
                </div>

                {/* Auto Chasers Info */}
                {clientSetup.AutoChaser.length > 0 && (
                    <div className="mb-6 overflow-hidden rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-50 p-6 shadow-md ring-1 ring-blue-200 sm:mb-8 sm:p-8">
                        <div className="flex items-start gap-4">
                            <div className="flex-shrink-0 rounded-full bg-blue-100 p-3">
                                <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                </svg>
                            </div>
                            <div className="flex-1">
                                <h3 className="text-lg font-semibold text-blue-900">
                                    Automatic Reminders
                                </h3>
                                <p className="mt-1 text-sm text-blue-700">
                                    You'll receive automatic email reminders if any required documents are missing:
                                </p>
                                <ul className="mt-3 space-y-2">
                                    {clientSetup.AutoChaser.map((chaser, idx) => (
                                        <li key={idx} className="flex items-center gap-2 text-sm text-blue-700">
                                            <svg className="h-4 w-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                            </svg>
                                            After {chaser.delayDays} days: Reminder email will be sent
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    </div>
                )}

                {/* Submit Button */}
                <SubmitButton clientId={clientSetup.id} checklistItems={clientSetup.ChecklistItem} />
            </div>
        </div>
    );
}

function InfoCard({ label, value, subtitle, icon }: { label: string; value: string; subtitle?: string; icon: string }) {
    return (
        <div className="flex gap-3 rounded-lg bg-slate-50 p-4 ring-1 ring-slate-200">
            <div className="flex-shrink-0">
                <div className="rounded-lg bg-white p-2 shadow-sm">
                    <svg className="h-5 w-5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={icon} />
                    </svg>
                </div>
            </div>
            <div className="min-w-0 flex-1">
                <label className="block text-xs font-medium uppercase tracking-wide text-slate-500">
                    {label}
                </label>
                <p className="mt-1 break-words text-base font-medium text-slate-900">{value}</p>
                {subtitle && <p className="mt-0.5 text-sm text-slate-600">{subtitle}</p>}
            </div>
        </div>
    );
}

function ListCard({ label, items, icon }: { label: string; items: string[]; icon: string }) {
    return (
        <div className="flex gap-3 rounded-lg bg-slate-50 p-4 ring-1 ring-slate-200">
            <div className="flex-shrink-0">
                <div className="rounded-lg bg-white p-2 shadow-sm">
                    <svg className="h-5 w-5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={icon} />
                    </svg>
                </div>
            </div>
            <div className="min-w-0 flex-1">
                <label className="block text-xs font-medium uppercase tracking-wide text-slate-500">
                    {label}
                </label>
                <ul className="mt-2 space-y-1">
                    {items.map((item, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm text-slate-900">
                            <svg className="mt-0.5 h-4 w-4 flex-shrink-0 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            <span className="break-words">{item}</span>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
}
