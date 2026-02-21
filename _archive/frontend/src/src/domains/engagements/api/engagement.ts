/**
 * Engagement API operations
 * Matches backend FastAPI endpoints
 * @see backend/app/api/v1/engagements/routes.py
 */

import { apiFetch, ApiError } from "~/lib/api/base";
import type {
    Engagement,
    EngagementListResponse,
    EngagementCreate,
    EngagementUpdate,
} from "../types";

export class EngagementApiError extends ApiError {
    constructor(message: string, statusCode: number, details?: unknown) {
        super(message, statusCode, details);
        this.name = "EngagementApiError";
    }
}

/**
 * Lists engagements, optionally filtered by client_id
 */
export async function listEngagements(
    clientId?: number,
    skip: number = 0,
    limit: number = 100
): Promise<EngagementListResponse> {
    try {
        const params = new URLSearchParams({
            skip: skip.toString(),
            limit: limit.toString(),
        });
        if (clientId !== undefined) {
            params.append("client_id", clientId.toString());
        }

        return await apiFetch<EngagementListResponse>(`/api/v1/engagements?${params.toString()}`, {
            method: "GET",
        });
    } catch (error) {
        if (error instanceof ApiError) {
            throw new EngagementApiError(error.message, error.statusCode, error.details);
        }
        throw error;
    }
}

/**
 * Gets an engagement by ID
 */
export async function getEngagement(engagementId: number): Promise<Engagement> {
    try {
        return await apiFetch<Engagement>(`/api/v1/engagements/${engagementId}`, {
            method: "GET",
        });
    } catch (error) {
        if (error instanceof ApiError) {
            throw new EngagementApiError(error.message, error.statusCode, error.details);
        }
        throw error;
    }
}

/**
 * Creates a new engagement
 */
export async function createEngagement(payload: EngagementCreate): Promise<Engagement> {
    try {
        return await apiFetch<Engagement>("/api/v1/engagements", {
            method: "POST",
            body: JSON.stringify(payload),
        });
    } catch (error) {
        if (error instanceof ApiError) {
            throw new EngagementApiError(error.message, error.statusCode, error.details);
        }
        throw error;
    }
}

/**
 * Updates an engagement
 */
export async function updateEngagement(
    engagementId: number,
    payload: EngagementUpdate
): Promise<Engagement> {
    try {
        return await apiFetch<Engagement>(`/api/v1/engagements/${engagementId}`, {
            method: "PATCH",
            body: JSON.stringify(payload),
        });
    } catch (error) {
        if (error instanceof ApiError) {
            throw new EngagementApiError(error.message, error.statusCode, error.details);
        }
        throw error;
    }
}

/**
 * Deletes an engagement
 */
export async function deleteEngagement(engagementId: number): Promise<void> {
    try {
        await apiFetch(`/api/v1/engagements/${engagementId}`, {
            method: "DELETE",
        });
    } catch (error) {
        if (error instanceof ApiError) {
            throw new EngagementApiError(error.message, error.statusCode, error.details);
        }
        throw error;
    }
}
