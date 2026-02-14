/**
 * Request API operations
 * Matches backend FastAPI endpoints
 * @see backend/app/api/v1/requests/routes.py
 */

import { apiFetch, ApiError } from "~/lib/api/base";
import type {
    RequestItem,
    RequestItemCreate,
    RequestItemUpdate,
    RequestItemListResponse,
    RequestSet,
    RequestSetCreate,
    RequestSetUpdate,
    RequestSetListResponse,
} from "../types";

export class RequestApiError extends ApiError {
    constructor(message: string, statusCode: number, details?: unknown) {
        super(message, statusCode, details);
        this.name = "RequestApiError";
    }
}

// ============================================================================
// Request Items
// ============================================================================

/**
 * Lists request items for a request set
 * @see backend/app/api/v1/requests/routes.py::list_request_items
 */
export async function listRequestItems(
    requestSetId: number,
    skip: number = 0,
    limit: number = 100
): Promise<RequestItemListResponse> {
    try {
        return await apiFetch<RequestItemListResponse>(
            `/api/v1/requests/items?request_set_id=${requestSetId}&skip=${skip}&limit=${limit}`,
            { method: "GET" }
        );
    } catch (error) {
        if (error instanceof ApiError) {
            throw new RequestApiError(error.message, error.statusCode, error.details);
        }
        throw error;
    }
}

/**
 * Gets a request item by ID
 * @see backend/app/api/v1/requests/routes.py::get_request_item
 */
export async function getRequestItem(requestItemId: number): Promise<RequestItem> {
    try {
        return await apiFetch<RequestItem>(`/api/v1/requests/items/${requestItemId}`, {
            method: "GET",
        });
    } catch (error) {
        if (error instanceof ApiError) {
            throw new RequestApiError(error.message, error.statusCode, error.details);
        }
        throw error;
    }
}

/**
 * Creates a new request item
 * @see backend/app/api/v1/requests/routes.py::create_request_item
 */
export async function createRequestItem(payload: RequestItemCreate): Promise<RequestItem> {
    try {
        return await apiFetch<RequestItem>("/api/v1/requests/items", {
            method: "POST",
            body: JSON.stringify(payload),
        });
    } catch (error) {
        if (error instanceof ApiError) {
            throw new RequestApiError(error.message, error.statusCode, error.details);
        }
        throw error;
    }
}

/**
 * Updates a request item
 * @see backend/app/api/v1/requests/routes.py::update_request_item
 */
export async function updateRequestItem(
    requestItemId: number,
    payload: RequestItemUpdate
): Promise<RequestItem> {
    try {
        return await apiFetch<RequestItem>(`/api/v1/requests/items/${requestItemId}`, {
            method: "PATCH",
            body: JSON.stringify(payload),
        });
    } catch (error) {
        if (error instanceof ApiError) {
            throw new RequestApiError(error.message, error.statusCode, error.details);
        }
        throw error;
    }
}

/**
 * Deletes a request item
 * @see backend/app/api/v1/requests/routes.py::delete_request_item
 */
export async function deleteRequestItem(requestItemId: number): Promise<void> {
    try {
        await apiFetch(`/api/v1/requests/items/${requestItemId}`, {
            method: "DELETE",
        });
    } catch (error) {
        if (error instanceof ApiError) {
            throw new RequestApiError(error.message, error.statusCode, error.details);
        }
        throw error;
    }
}

// ============================================================================
// Request Sets
// ============================================================================

/**
 * Lists request sets for an engagement
 * @see backend/app/api/v1/requests/routes.py::list_request_sets
 */
export async function listRequestSets(
    engagementId: number,
    skip: number = 0,
    limit: number = 100
): Promise<RequestSetListResponse> {
    try {
        return await apiFetch<RequestSetListResponse>(
            `/api/v1/requests/sets?engagement_id=${engagementId}&skip=${skip}&limit=${limit}`,
            { method: "GET" }
        );
    } catch (error) {
        if (error instanceof ApiError) {
            throw new RequestApiError(error.message, error.statusCode, error.details);
        }
        throw error;
    }
}

/**
 * Gets a request set by ID
 * @see backend/app/api/v1/requests/routes.py::get_request_set
 */
export async function getRequestSet(requestSetId: number): Promise<RequestSet> {
    try {
        return await apiFetch<RequestSet>(`/api/v1/requests/sets/${requestSetId}`, {
            method: "GET",
        });
    } catch (error) {
        if (error instanceof ApiError) {
            throw new RequestApiError(error.message, error.statusCode, error.details);
        }
        throw error;
    }
}

/**
 * Creates a new request set
 * @see backend/app/api/v1/requests/routes.py::create_request_set
 */
export async function createRequestSet(payload: RequestSetCreate): Promise<RequestSet> {
    try {
        return await apiFetch<RequestSet>("/api/v1/requests/sets", {
            method: "POST",
            body: JSON.stringify(payload),
        });
    } catch (error) {
        if (error instanceof ApiError) {
            throw new RequestApiError(error.message, error.statusCode, error.details);
        }
        throw error;
    }
}

/**
 * Updates a request set
 * @see backend/app/api/v1/requests/routes.py::update_request_set
 */
export async function updateRequestSet(
    requestSetId: number,
    payload: RequestSetUpdate
): Promise<RequestSet> {
    try {
        return await apiFetch<RequestSet>(`/api/v1/requests/sets/${requestSetId}`, {
            method: "PATCH",
            body: JSON.stringify(payload),
        });
    } catch (error) {
        if (error instanceof ApiError) {
            throw new RequestApiError(error.message, error.statusCode, error.details);
        }
        throw error;
    }
}

/**
 * Deletes a request set
 * @see backend/app/api/v1/requests/routes.py::delete_request_set
 */
export async function deleteRequestSet(requestSetId: number): Promise<void> {
    try {
        await apiFetch(`/api/v1/requests/sets/${requestSetId}`, {
            method: "DELETE",
        });
    } catch (error) {
        if (error instanceof ApiError) {
            throw new RequestApiError(error.message, error.statusCode, error.details);
        }
        throw error;
    }
}
