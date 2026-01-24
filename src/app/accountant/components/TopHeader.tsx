"use client";

import React from "react";
import {
    SearchIcon,
    PlusIcon,
} from "./icons/AccountantIcons";

interface TopHeaderProps {
    title: string;
    subtitle?: string;
    onSearch?: (query: string) => void;
    onAddNew?: () => void;
}

export function TopHeader({
    title,
    subtitle,
    onSearch,
    onAddNew,
}: TopHeaderProps) {
    return (
        <header className="bg-white border-b border-slate-200">
            <div className="px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div>
                        <h1 className="text-xl font-bold text-slate-900">{title}</h1>
                        {subtitle && (
                            <p className="text-sm text-slate-500 mt-0.5">{subtitle}</p>
                        )}
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    {/* Search */}
                    <div className="relative">
                        <SearchIcon
                            size="sm"
                            className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                        />
                        <input
                            type="text"
                            placeholder="Search clients..."
                            onChange={(e) => onSearch?.(e.target.value)}
                            className="w-64 pl-9 pr-4 py-2 rounded-lg border border-slate-200 bg-slate-50 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-all"
                        />
                    </div>

                    {/* Add New Client Button */}
                    <button
                        onClick={onAddNew}
                        className="flex items-center gap-2 px-4 py-2 bg-violet-600 text-white text-sm font-medium rounded-lg hover:bg-violet-700 transition-all duration-150 shadow-sm hover:shadow-md"
                    >
                        <PlusIcon size="sm" />
                        <span>New Client</span>
                    </button>
                </div>
            </div>
        </header>
    );
}
