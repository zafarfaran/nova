/**
 * Client API operations
 * Matches backend FastAPI endpoints
 * @see backend/app/api/v1/clients/routes.py
 */

import { apiFetch, ApiError } from "~/lib/api/base";
import type {
    ClientCreatePayload,
    ClientResponse,
    ClientListResponse,
} from "../types";

export class ClientApiError extends ApiError {
    constructor(message: string, statusCode: number, details?: unknown) {
        super(message, statusCode, details);
        this.name = "ClientApiError";
    }
}

/**
 * Creates a new client
 * @see backend/app/api/v1/clients/routes.py::create_client
 */
export async function createClient(
    payload: ClientCreatePayload
): Promise<ClientResponse> {
    try {
        return await apiFetch<ClientResponse>("/api/v1/clients", {
            method: "POST",
            body: JSON.stringify(payload),
        });
    } catch (error) {
        if (error instanceof ApiError) {
            throw new ClientApiError(error.message, error.statusCode, error.details);
        }
        throw error;
    }
}

/**
 * Lists clients with pagination
 * @see backend/app/api/v1/clients/routes.py::list_clients
 */
export async function listClients(
    skip: number = 0,
    limit: number = 100
): Promise<ClientListResponse> {
    try {
        return await apiFetch<ClientListResponse>(
            `/api/v1/clients?skip=${skip}&limit=${limit}`,
            {
                method: "GET",
            }
        );
    } catch (error) {
        if (error instanceof ApiError) {
            throw new ClientApiError(error.message, error.statusCode, error.details);
        }
        throw error;
    }
}

/**
 * Gets a client by ID
 * @see backend/app/api/v1/clients/routes.py::get_client
 */
export async function getClient(clientId: number): Promise<ClientResponse> {
    try {
        return await apiFetch<ClientResponse>(`/api/v1/clients/${clientId}`, {
            method: "GET",
        });
    } catch (error) {
        if (error instanceof ApiError) {
            throw new ClientApiError(error.message, error.statusCode, error.details);
        }
        throw error;
    }
}

/**
 * Updates a client
 * @see backend/app/api/v1/clients/routes.py::update_client
 */
export async function updateClient(
    clientId: number,
    payload: Partial<ClientCreatePayload>
): Promise<ClientResponse> {
    try {
        return await apiFetch<ClientResponse>(`/api/v1/clients/${clientId}`, {
            method: "PUT",
            body: JSON.stringify(payload),
        });
    } catch (error) {
        if (error instanceof ApiError) {
            throw new ClientApiError(error.message, error.statusCode, error.details);
        }
        throw error;
    }
}

/**
 * Deletes a client
 * @see backend/app/api/v1/clients/routes.py::delete_client
 */
export async function deleteClient(clientId: number): Promise<void> {
    try {
        await apiFetch(`/api/v1/clients/${clientId}`, {
            method: "DELETE",
        });
    } catch (error) {
        if (error instanceof ApiError) {
            throw new ClientApiError(error.message, error.statusCode, error.details);
        }
        throw error;
    }
}
