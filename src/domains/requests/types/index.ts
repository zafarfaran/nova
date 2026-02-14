/**
 * Request domain types matching backend Pydantic schemas exactly
 * @see backend/app/schemas/requests/request.py
 */

/**
 * RequestItemStatus enum from backend
 * @see backend/app/models/requests/item.py::RequestItemStatus
 * 
 * Status meanings:
 * - pending: No documents uploaded yet
 * - partial: Some documents uploaded, but less than expected_count
 * - complete: All expected documents uploaded (doc_count >= expected_count)
 * - waived: Not applicable for this client
 */
export type RequestItemStatus = "pending" | "partial" | "complete" | "waived";

/**
 * RequestSetStatus enum from backend
 * @see backend/app/models/requests/set.py::RequestSetStatus
 */
export type RequestSetStatus = "draft" | "active" | "complete" | "cancelled";

/**
 * Request Item - matches backend RequestItemResponse schema exactly
 * @see backend/app/schemas/requests/request.py::RequestItemResponse
 */
export interface RequestItem {
    id: number;
    request_set_id: number;
    document_type_id: number | null;
    description: string | null;
    expected_count: number;
    is_required: boolean;
    status: RequestItemStatus;
    due_date: string | null; // ISO date string
    assigned_to_contact_id: number | null;
    created_at: string; // ISO datetime string
    updated_at: string; // ISO datetime string
}

/**
 * Request Set - matches backend RequestSetResponse schema exactly
 * @see backend/app/schemas/requests/request.py::RequestSetResponse
 */
export interface RequestSet {
    id: number;
    engagement_id: number;
    name: string;
    status: RequestSetStatus;
    due_date: string | null; // ISO date string
    created_at: string; // ISO datetime string
    updated_at: string; // ISO datetime string
}

/**
 * Request Item Create payload
 * @see backend/app/schemas/requests/request.py::RequestItemCreate
 */
export interface RequestItemCreate {
    request_set_id: number;
    document_type_id?: number | null;
    description?: string | null;
    expected_count?: number;
    is_required?: boolean;
    status?: RequestItemStatus;
    due_date?: string | null;
    assigned_to_contact_id?: number | null;
}

/**
 * Request Item Update payload
 * @see backend/app/schemas/requests/request.py::RequestItemUpdate
 */
export interface RequestItemUpdate {
    description?: string | null;
    expected_count?: number | null;
    is_required?: boolean | null;
    status?: RequestItemStatus | null;
    due_date?: string | null;
    assigned_to_contact_id?: number | null;
}

/**
 * Request Item List response
 * @see backend/app/schemas/requests/request.py::RequestItemList
 */
export interface RequestItemListResponse {
    items: RequestItem[];
    total: number;
}

/**
 * Request Set Create payload
 * @see backend/app/schemas/requests/request.py::RequestSetCreate
 */
export interface RequestSetCreate {
    engagement_id: number;
    name: string;
    status?: RequestSetStatus;
    due_date?: string | null;
}

/**
 * Request Set Update payload
 * @see backend/app/schemas/requests/request.py::RequestSetUpdate
 */
export interface RequestSetUpdate {
    name?: string | null;
    status?: RequestSetStatus | null;
    due_date?: string | null;
}

/**
 * Request Set List response
 * @see backend/app/schemas/requests/request.py::RequestSetList
 */
export interface RequestSetListResponse {
    items: RequestSet[];
    total: number;
}
