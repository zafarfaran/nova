/**
 * Engagement domain types matching backend Pydantic schemas exactly
 * @see backend/app/models/engagements/engagement.py::EngagementType
 * @see backend/app/models/engagements/engagement.py::EngagementStatus
 */

/**
 * EngagementType enum - matches backend exactly
 * @see backend/app/models/engagements/engagement.py::EngagementType
 */
export type EngagementType = 
    | "vat_return" 
    | "annual_accounts" 
    | "tax_return" 
    | "audit" 
    | "bookkeeping" 
    | "other";

/**
 * EngagementStatus enum - matches backend exactly
 * @see backend/app/models/engagements/engagement.py::EngagementStatus
 */
export type EngagementStatus = 
    | "draft" 
    | "in_progress" 
    | "under_review" 
    | "ready" 
    | "submitted" 
    | "locked";

/**
 * Engagement response matching backend schema exactly
 * @see backend/app/schemas/engagements/engagement.py::EngagementResponse
 */
export interface Engagement {
    id: number;
    client_id: number;
    engagement_type: EngagementType;
    period_start: string; // ISO date string (YYYY-MM-DD)
    period_end: string; // ISO date string (YYYY-MM-DD)
    status: EngagementStatus;
    reference: string | null;
    due_date: string | null; // ISO date string (YYYY-MM-DD) or null
    notes: string | null;
    is_locked: boolean;
    created_at: string; // ISO datetime string
    updated_at: string; // ISO datetime string
}

/**
 * Engagement list response
 */
export interface EngagementListResponse {
    items: Engagement[];
    total: number;
}

/**
 * Engagement create payload matching backend schema exactly
 * @see backend/app/schemas/engagements/engagement.py::EngagementCreate
 */
export interface EngagementCreate {
    client_id: number;
    engagement_type?: EngagementType; // Defaults to "vat_return" if not provided
    period_start: string; // ISO date string (YYYY-MM-DD)
    period_end: string; // ISO date string (YYYY-MM-DD)
    status?: EngagementStatus; // Defaults to "draft" if not provided
    reference?: string | null;
    due_date?: string | null; // ISO date string (YYYY-MM-DD) or null
    notes?: string | null;
}

/**
 * Engagement update payload matching backend schema exactly
 * @see backend/app/schemas/engagements/engagement.py::EngagementUpdate
 */
export interface EngagementUpdate {
    engagement_type?: EngagementType;
    period_start?: string; // ISO date string (YYYY-MM-DD)
    period_end?: string; // ISO date string (YYYY-MM-DD)
    status?: EngagementStatus;
    reference?: string | null;
    due_date?: string | null; // ISO date string (YYYY-MM-DD) or null
    notes?: string | null;
    is_locked?: boolean;
}
