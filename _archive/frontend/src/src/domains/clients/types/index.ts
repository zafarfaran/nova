/**
 * Client domain types matching backend Pydantic schemas
 * @see backend/app/schemas/clients/client.py
 */

export type EntityType =
    | "sole_trader"
    | "partnership"
    | "llp"
    | "limited_company"
    | "plc"
    | "charity"
    | "other";

export type ClientType = "sole_trader" | "limited_company";

export type VatScheme = "standard" | "flat_rate" | "cash_accounting" | "annual_accounting";

/**
 * Engagement data for client creation
 */
import type { EngagementType, EngagementStatus } from "../engagements/types";

export interface EngagementCreateData {
    engagement_type?: EngagementType;
    period_start: string; // ISO date string (YYYY-MM-DD)
    period_end: string; // ISO date string (YYYY-MM-DD)
    status?: EngagementStatus;
    reference?: string | null;
    due_date?: string | null; // ISO date string (YYYY-MM-DD) or null
    notes?: string | null;
}

/**
 * Client creation payload matching ClientCreate schema
 */
export interface ClientCreatePayload {
    name: string;
    contact_email: string;
    entity_type: EntityType;
    client_type?: ClientType;
    vat_number?: string | null;
    vat_scheme?: VatScheme | null;
    contact_name?: string | null;
    address?: string | null;
    notes?: string | null;
    engagement?: EngagementCreateData | null;
}

/**
 * Client response matching ClientResponse schema
 */
export interface ClientResponse {
    id: number;
    name: string;
    vat_number: string | null;
    entity_type: EntityType;
    client_type: string | null;
    contact_email: string | null;
    contact_name: string | null;
    address: string | null;
    notes: string | null;
    vat_scheme: string | null;
    created_at: string; // ISO datetime string
    updated_at: string; // ISO datetime string
}

/**
 * Client list response matching ClientList schema
 */
export interface ClientListResponse {
    items: ClientResponse[];
    total: number;
}

/**
 * Maps entity_type to client_type for document scoping
 */
export function mapEntityTypeToClientType(entityType: EntityType): ClientType | null {
    if (entityType === "sole_trader") {
        return "sole_trader";
    }
    if (
        ["limited_company", "llp", "plc", "partnership", "charity", "other"].includes(
            entityType
        )
    ) {
        return "limited_company";
    }
    return null;
}
