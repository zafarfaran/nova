"use client";

import { useState, useRef } from "react";
import type { EntityType, VatScheme, ClientCreatePayload } from "../types";
import type { EngagementType, EngagementStatus } from "../../engagements/types";
import { createClient, ClientApiError } from "../api/client";
import {
    validateClientForm,
    getFirstValidationError,
    type ValidationError,
} from "../utils/validation";
import { mapEntityTypeToClientType } from "../types";

interface CreateClientFormResult {
    success: boolean;
    clientId?: number;
    clientName?: string;
    error?: string;
    errorDetails?: unknown;
}

interface CreateClientFormProps {
    onResult?: (result: CreateClientFormResult) => void | Promise<void>;
    onCancel: () => void;
    isLoading?: boolean;
}

export function CreateClientForm({
    onResult,
    onCancel,
    isLoading = false,
}: CreateClientFormProps) {
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [entityType, setEntityType] = useState<EntityType>("limited_company");
    const [vatScheme, setVatScheme] = useState<VatScheme>("standard");
    const [vatNumber, setVatNumber] = useState("");
    const [notes, setNotes] = useState("");
    
    // Engagement fields
    const [createEngagement, setCreateEngagement] = useState(true);
    const [engagementType, setEngagementType] = useState<EngagementType>("vat_return");
    const [periodStart, setPeriodStart] = useState(() => {
        // Default to current quarter start
        const now = new Date();
        const quarterMonth = Math.floor(now.getMonth() / 3) * 3;
        return new Date(now.getFullYear(), quarterMonth, 1).toISOString().split('T')[0];
    });
    const [periodEnd, setPeriodEnd] = useState(() => {
        // Default to current quarter end
        const now = new Date();
        const quarterMonth = Math.floor(now.getMonth() / 3) * 3;
        const quarterEndMonth = quarterMonth + 2;
        const lastDay = new Date(now.getFullYear(), quarterEndMonth + 1, 0).getDate();
        return new Date(now.getFullYear(), quarterEndMonth, lastDay).toISOString().split('T')[0];
    });
    const [engagementStatus, setEngagementStatus] = useState<EngagementStatus>("draft");
    const [engagementReference, setEngagementReference] = useState("");
    const [engagementNotes, setEngagementNotes] = useState("");
    
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);

    // Generate unique form ID to prevent conflicts - use ref to keep it stable across re-renders
    const formIdRef = useRef<string | null>(null);
    if (!formIdRef.current) {
        formIdRef.current = `create-client-form-${Date.now()}-${Math.random()
            .toString(36)
            .substr(2, 9)}`;
    }
    const formId =
        formIdRef.current ||
        `create-client-form-fallback-${Math.random().toString(36).substr(2, 9)}`;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        // Clear previous errors
        setError(null);
        setValidationErrors([]);

        // Validate form
        const errors = validateClientForm({ name, email, entityType });
        if (errors.length > 0) {
            setValidationErrors(errors);
            setError(getFirstValidationError(errors));
            return;
        }

        setIsSubmitting(true);

        try {
            // Map entity_type to client_type
            const clientType = mapEntityTypeToClientType(entityType);

            // Build payload matching backend schema
            const payload: ClientCreatePayload = {
                name: name.trim(),
                contact_email: email.trim(),
                entity_type: entityType,
                ...(clientType && { client_type: clientType }),
                ...(vatScheme && { vat_scheme: vatScheme }),
                ...(vatNumber.trim() && { vat_number: vatNumber.trim() }),
                ...(notes.trim() && { notes: notes.trim() }),
                ...(createEngagement && {
                    engagement: {
                        engagement_type: engagementType,
                        period_start: periodStart,
                        period_end: periodEnd,
                        status: engagementStatus,
                        ...(engagementReference.trim() && { reference: engagementReference.trim() }),
                        ...(engagementNotes.trim() && { notes: engagementNotes.trim() }),
                    },
                }),
            };

            // Create client via API
            const clientData = await createClient(payload);

            // Reset form
            setName("");
            setEmail("");
            setEntityType("limited_company");
            setVatScheme("standard");
            setVatNumber("");
            setNotes("");
            setCreateEngagement(true);
            setEngagementType("vat_return");
            setEngagementStatus("draft");
            setEngagementReference("");
            setEngagementNotes("");
            setValidationErrors([]);
            setError(null);

            // Notify parent of success
            if (onResult) {
                await onResult({
                    success: true,
                    clientId: clientData.id,
                    clientName: clientData.name,
                });
            }
        } catch (err) {
            let errorMessage = "Failed to create client. Please try again.";
            let errorDetails: unknown = undefined;

            if (err instanceof ClientApiError) {
                errorMessage = err.message;
                errorDetails = err.details;

                // Handle specific error cases
                if (err.statusCode === 400) {
                    // Bad request - likely validation error from backend
                    errorMessage = err.message || "Invalid client data. Please check your input.";
                } else if (err.statusCode === 409) {
                    // Conflict - duplicate VAT number or email
                    errorMessage = err.message || "A client with this information already exists.";
                }
            } else if (err instanceof Error) {
                errorMessage = err.message;
                errorDetails = err;
            }

            setError(errorMessage);
            console.error("Error creating client:", err);

            // Notify parent of failure
            if (onResult) {
                await onResult({
                    success: false,
                    error: errorMessage,
                    errorDetails,
                });
            }
        } finally {
            setIsSubmitting(false);
        }
    };

    const getFieldError = (fieldName: string): string | undefined => {
        return validationErrors.find((e) => e.field === fieldName)?.message;
    };

    return (
        <div className="rounded-lg border border-[#C0B6F2] bg-gradient-to-br from-[#F4F5F7] to-[#EAE6FF] p-4">
            <div className="flex items-center gap-2 mb-3">
                <span className="text-[14px]">✨</span>
                <div>
                    <p className="text-[13px] font-semibold text-[#403294]">New Client Capsule</p>
                    <p className="text-[11px] text-[#5E6C84]">Drop the details and I'll handle the rest.</p>
                </div>
            </div>
            <form id={formId} onSubmit={handleSubmit} className="grid gap-2">
                <div>
                    <input
                        id={`${formId}-name`}
                        name="client_name"
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Client name"
                        autoComplete="organization"
                        className={`w-full rounded border ${
                            getFieldError("name")
                                ? "border-[#DE350B]"
                                : "border-[#DFE1E6]"
                        } bg-white px-3 py-2 text-[12px] text-[#172B4D]`}
                        disabled={isSubmitting || isLoading}
                    />
                    {getFieldError("name") && (
                        <p className="text-[11px] text-[#BF2600] mt-1">{getFieldError("name")}</p>
                    )}
                </div>

                <div>
                    <input
                        id={`${formId}-email`}
                        name="client_email"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="Email"
                        autoComplete="email"
                        className={`w-full rounded border ${
                            getFieldError("email")
                                ? "border-[#DE350B]"
                                : "border-[#DFE1E6]"
                        } bg-white px-3 py-2 text-[12px] text-[#172B4D]`}
                        disabled={isSubmitting || isLoading}
                    />
                    {getFieldError("email") && (
                        <p className="text-[11px] text-[#BF2600] mt-1">{getFieldError("email")}</p>
                    )}
                </div>

                <div className="grid grid-cols-2 gap-2">
                    <select
                        id={`${formId}-entity-type`}
                        name="entity_type"
                        value={entityType}
                        onChange={(e) => setEntityType(e.target.value as EntityType)}
                        className="rounded border border-[#DFE1E6] bg-white px-2 py-2 text-[12px] text-[#172B4D]"
                        disabled={isSubmitting || isLoading}
                    >
                        <option value="sole_trader">Sole Trader</option>
                        <option value="partnership">Partnership</option>
                        <option value="llp">LLP</option>
                        <option value="limited_company">Limited Company</option>
                        <option value="plc">PLC</option>
                        <option value="charity">Charity</option>
                        <option value="other">Other</option>
                    </select>
                    <select
                        id={`${formId}-vat-scheme`}
                        name="vat_scheme"
                        value={vatScheme}
                        onChange={(e) => setVatScheme(e.target.value as VatScheme)}
                        className="rounded border border-[#DFE1E6] bg-white px-2 py-2 text-[12px] text-[#172B4D]"
                        disabled={isSubmitting || isLoading}
                    >
                        <option value="standard">Standard</option>
                        <option value="flat_rate">Flat Rate</option>
                        <option value="cash_accounting">Cash Accounting</option>
                        <option value="annual_accounting">Annual Accounting</option>
                    </select>
                </div>

                <input
                    id={`${formId}-vat-number`}
                    name="vat_number"
                    type="text"
                    value={vatNumber}
                    onChange={(e) => setVatNumber(e.target.value)}
                    placeholder="Tax number (optional)"
                    autoComplete="off"
                    className="w-full rounded border border-[#DFE1E6] bg-white px-3 py-2 text-[12px] text-[#172B4D]"
                    disabled={isSubmitting || isLoading}
                />

                <textarea
                    id={`${formId}-notes`}
                    name="notes"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Notes (optional)"
                    autoComplete="off"
                    className="w-full rounded border border-[#DFE1E6] bg-white px-3 py-2 text-[12px] text-[#172B4D]"
                    rows={2}
                    disabled={isSubmitting || isLoading}
                />

                {/* Engagement Section */}
                <div className="border-t border-[#DFE1E6] pt-2 mt-2">
                    <div className="flex items-center gap-2 mb-2">
                        <input
                            type="checkbox"
                            id={`${formId}-create-engagement`}
                            checked={createEngagement}
                            onChange={(e) => setCreateEngagement(e.target.checked)}
                            disabled={isSubmitting || isLoading}
                            className="rounded"
                        />
                        <label
                            htmlFor={`${formId}-create-engagement`}
                            className="text-[12px] font-semibold text-[#403294] cursor-pointer"
                        >
                            Create Engagement
                        </label>
                    </div>

                    {createEngagement && (
                        <div className="grid gap-2 pl-6 border-l-2 border-[#DFE1E6]">
                            <div className="grid grid-cols-2 gap-2">
                                <select
                                    id={`${formId}-engagement-type`}
                                    name="engagement_type"
                                    value={engagementType}
                                    onChange={(e) => setEngagementType(e.target.value as EngagementType)}
                                    className="rounded border border-[#DFE1E6] bg-white px-2 py-2 text-[12px] text-[#172B4D]"
                                    disabled={isSubmitting || isLoading}
                                >
                                    <option value="vat_return">VAT Return</option>
                                    <option value="annual_accounts">Annual Accounts</option>
                                    <option value="tax_return">Tax Return</option>
                                    <option value="audit">Audit</option>
                                    <option value="bookkeeping">Bookkeeping</option>
                                    <option value="other">Other</option>
                                </select>
                                <select
                                    id={`${formId}-engagement-status`}
                                    name="engagement_status"
                                    value={engagementStatus}
                                    onChange={(e) => setEngagementStatus(e.target.value as EngagementStatus)}
                                    className="rounded border border-[#DFE1E6] bg-white px-2 py-2 text-[12px] text-[#172B4D]"
                                    disabled={isSubmitting || isLoading}
                                >
                                    <option value="draft">Draft</option>
                                    <option value="in_progress">In Progress</option>
                                    <option value="under_review">Under Review</option>
                                    <option value="ready">Ready</option>
                                    <option value="submitted">Submitted</option>
                                    <option value="locked">Locked</option>
                                </select>
                            </div>

                            <div className="grid grid-cols-2 gap-2">
                                <input
                                    type="date"
                                    id={`${formId}-period-start`}
                                    name="period_start"
                                    value={periodStart}
                                    onChange={(e) => setPeriodStart(e.target.value)}
                                    className="rounded border border-[#DFE1E6] bg-white px-3 py-2 text-[12px] text-[#172B4D]"
                                    disabled={isSubmitting || isLoading}
                                />
                                <input
                                    type="date"
                                    id={`${formId}-period-end`}
                                    name="period_end"
                                    value={periodEnd}
                                    onChange={(e) => setPeriodEnd(e.target.value)}
                                    className="rounded border border-[#DFE1E6] bg-white px-3 py-2 text-[12px] text-[#172B4D]"
                                    disabled={isSubmitting || isLoading}
                                />
                            </div>

                            <input
                                type="text"
                                id={`${formId}-engagement-reference`}
                                name="engagement_reference"
                                value={engagementReference}
                                onChange={(e) => setEngagementReference(e.target.value)}
                                placeholder="Reference (optional)"
                                className="rounded border border-[#DFE1E6] bg-white px-3 py-2 text-[12px] text-[#172B4D]"
                                disabled={isSubmitting || isLoading}
                            />

                            <textarea
                                id={`${formId}-engagement-notes`}
                                name="engagement_notes"
                                value={engagementNotes}
                                onChange={(e) => setEngagementNotes(e.target.value)}
                                placeholder="Engagement notes (optional)"
                                className="rounded border border-[#DFE1E6] bg-white px-3 py-2 text-[12px] text-[#172B4D]"
                                rows={2}
                                disabled={isSubmitting || isLoading}
                            />
                        </div>
                    )}
                </div>

                {error && (
                    <div className="rounded border border-[#DE350B] bg-[#FFEBE6] px-3 py-2 text-[11px] text-[#BF2600]">
                        {error}
                    </div>
                )}

                <div className="flex items-center gap-2">
                    <button
                        type="submit"
                        disabled={!name.trim() || !email.trim() || isLoading || isSubmitting}
                        className="rounded bg-[#6554C0] px-3 py-2 text-[12px] font-semibold text-white disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isSubmitting ? "Creating..." : "Create client"}
                    </button>
                    <button
                        type="button"
                        onClick={onCancel}
                        disabled={isSubmitting || isLoading}
                        className="rounded border border-[#DFE1E6] px-3 py-2 text-[12px] text-[#5E6C84] disabled:opacity-50"
                    >
                        Cancel
                    </button>
                </div>
            </form>
        </div>
    );
}
