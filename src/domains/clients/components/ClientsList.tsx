"use client";

import { useEffect } from "react";
import { useClients } from "../hooks/useClients";
import type { ClientResponse } from "../types";

interface ClientsListProps {
    onClientSelect?: (client: ClientResponse) => void;
    selectedClientId?: number;
    skip?: number;
    limit?: number;
}

export function ClientsList({
    onClientSelect,
    selectedClientId,
    skip = 0,
    limit = 100,
}: ClientsListProps) {
    const { clients, total, loading, error, fetchClients } = useClients(skip, limit);

    useEffect(() => {
        fetchClients(skip, limit);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [skip, limit]);

    if (loading && clients.length === 0) {
        return (
            <div className="bg-white rounded border border-[#DFE1E6] p-12 text-center">
                <div className="text-[#97A0AF]">Loading clients...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-white rounded border border-[#DE350B] p-4">
                <div className="text-[#BF2600] text-sm font-semibold">Error loading clients</div>
                <div className="text-[#5E6C84] text-xs mt-1">{error}</div>
            </div>
        );
    }

    if (clients.length === 0) {
        return (
            <div className="bg-white rounded border border-[#DFE1E6] p-12 text-center">
                <div className="text-[#97A0AF] mb-3">
                    <svg className="w-12 h-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                </div>
                <h3 className="text-base font-semibold text-[#172B4D] mb-1">No clients yet</h3>
                <p className="text-[13px] text-[#5E6C84]">Add your first client to get started with tax compliance tracking.</p>
            </div>
        );
    }

    return (
        <div className="bg-white rounded border border-[#DFE1E6] overflow-hidden">
            <div className="px-4 py-3 bg-[#FAFBFC] border-b border-[#DFE1E6]">
                <div className="flex items-center justify-between">
                    <div className="text-sm font-semibold text-[#172B4D]">
                        Clients ({total})
                    </div>
                    {loading && (
                        <div className="text-xs text-[#5E6C84]">Refreshing...</div>
                    )}
                </div>
            </div>
            <div className="divide-y divide-[#EBECF0]">
                {clients.map((client) => (
                    <button
                        key={client.id}
                        onClick={() => onClientSelect?.(client)}
                        className={`w-full px-4 py-3 text-left hover:bg-[#F4F5F7] transition-colors ${
                            selectedClientId === client.id ? "bg-[#DEEBFF]" : ""
                        }`}
                    >
                        <div className="flex items-center justify-between">
                            <div className="flex-1">
                                <div className="text-sm font-medium text-[#172B4D]">
                                    {client.name}
                                </div>
                                {client.contact_email && (
                                    <div className="text-xs text-[#5E6C84] mt-1">
                                        {client.contact_email}
                                    </div>
                                )}
                                <div className="flex items-center gap-2 mt-2">
                                    <span className="text-xs text-[#97A0AF] uppercase">
                                        {client.entity_type}
                                    </span>
                                    {client.vat_number && (
                                        <>
                                            <span className="text-[#DFE1E6]">•</span>
                                            <span className="text-xs text-[#97A0AF]">
                                                {client.vat_number}
                                            </span>
                                        </>
                                    )}
                                </div>
                            </div>
                            <div className="ml-4 text-xs text-[#97A0AF]">
                                ID: {client.id}
                            </div>
                        </div>
                    </button>
                ))}
            </div>
        </div>
    );
}
