"use client";

import { useState, useCallback } from "react";
import {
    createClient,
    listClients,
    getClient,
    updateClient,
    deleteClient,
    ClientApiError,
} from "../api/client";
import type {
    ClientCreatePayload,
    ClientResponse,
    ClientListResponse,
} from "../types";

interface UseClientsState {
    clients: ClientResponse[];
    total: number;
    loading: boolean;
    error: string | null;
}

interface UseClientsReturn extends UseClientsState {
    fetchClients: (skip?: number, limit?: number) => Promise<void>;
    createNewClient: (payload: ClientCreatePayload) => Promise<ClientResponse>;
    fetchClient: (clientId: number) => Promise<ClientResponse>;
    updateExistingClient: (
        clientId: number,
        payload: Partial<ClientCreatePayload>
    ) => Promise<ClientResponse>;
    removeClient: (clientId: number) => Promise<void>;
    clearError: () => void;
}

/**
 * Hook for managing client operations
 */
export function useClients(initialSkip = 0, initialLimit = 100): UseClientsReturn {
    const [state, setState] = useState<UseClientsState>({
        clients: [],
        total: 0,
        loading: false,
        error: null,
    });

    const fetchClients = useCallback(
        async (skip = initialSkip, limit = initialLimit) => {
            setState((prev) => ({ ...prev, loading: true, error: null }));
            try {
                const response = await listClients(skip, limit);
                setState({
                    clients: response.items,
                    total: response.total,
                    loading: false,
                    error: null,
                });
            } catch (error) {
                const errorMessage =
                    error instanceof ClientApiError
                        ? error.message
                        : "Failed to fetch clients";
                setState((prev) => ({
                    ...prev,
                    loading: false,
                    error: errorMessage,
                }));
                throw error;
            }
        },
        [] // Empty deps - function is stable
    );

    const createNewClient = useCallback(async (payload: ClientCreatePayload) => {
        setState((prev) => ({ ...prev, loading: true, error: null }));
        try {
            const newClient = await createClient(payload);
            // Refresh the list after creation
            await fetchClients();
            return newClient;
        } catch (error) {
            const errorMessage =
                error instanceof ClientApiError
                    ? error.message
                    : "Failed to create client";
            setState((prev) => ({
                ...prev,
                loading: false,
                error: errorMessage,
            }));
            throw error;
        }
    }, [fetchClients]);

    const fetchClient = useCallback(async (clientId: number) => {
        setState((prev) => ({ ...prev, loading: true, error: null }));
        try {
            const client = await getClient(clientId);
            setState((prev) => ({ ...prev, loading: false }));
            return client;
        } catch (error) {
            const errorMessage =
                error instanceof ClientApiError
                    ? error.message
                    : "Failed to fetch client";
            setState((prev) => ({
                ...prev,
                loading: false,
                error: errorMessage,
            }));
            throw error;
        }
    }, []);

    const updateExistingClient = useCallback(
        async (clientId: number, payload: Partial<ClientCreatePayload>) => {
            setState((prev) => ({ ...prev, loading: true, error: null }));
            try {
                const updatedClient = await updateClient(clientId, payload);
                // Refresh the list after update
                await fetchClients();
                return updatedClient;
            } catch (error) {
                const errorMessage =
                    error instanceof ClientApiError
                        ? error.message
                        : "Failed to update client";
                setState((prev) => ({
                    ...prev,
                    loading: false,
                    error: errorMessage,
                }));
                throw error;
            }
        },
        [fetchClients]
    );

    const removeClient = useCallback(
        async (clientId: number) => {
            setState((prev) => ({ ...prev, loading: true, error: null }));
            try {
                await deleteClient(clientId);
                // Refresh the list after deletion
                await fetchClients();
            } catch (error) {
                const errorMessage =
                    error instanceof ClientApiError
                        ? error.message
                        : "Failed to delete client";
                setState((prev) => ({
                    ...prev,
                    loading: false,
                    error: errorMessage,
                }));
                throw error;
            }
        },
        [fetchClients]
    );

    const clearError = useCallback(() => {
        setState((prev) => ({ ...prev, error: null }));
    }, []);

    return {
        ...state,
        fetchClients,
        createNewClient,
        fetchClient,
        updateExistingClient,
        removeClient,
        clearError,
    };
}
