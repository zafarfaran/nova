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
        <header className="bg-white border-b border-[#DFE1E6]">
            <div className="px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div>
                        <h1 className="text-lg font-semibold text-[#172B4D]">{title}</h1>
                        {subtitle && (
                            <p className="text-[13px] text-[#5E6C84] mt-0.5">{subtitle}</p>
                        )}
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    {/* Search */}
                    <div className="relative">
                        <SearchIcon
                            size="sm"
                            className="absolute left-3 top-1/2 -translate-y-1/2 text-[#97A0AF]"
                        />
                        <input
                            type="text"
                            placeholder="Search clients..."
                            onChange={(e) => onSearch?.(e.target.value)}
                            className="w-56 pl-9 pr-4 py-2 rounded border-2 border-[#DFE1E6] bg-white text-[13px] text-[#172B4D] placeholder:text-[#97A0AF] focus:outline-none focus:border-[#0052CC] transition-colors"
                        />
                    </div>

                    {/* Add New Client Button */}
                    <button
                        onClick={onAddNew}
                        className="flex items-center gap-2 px-4 py-2 bg-[#0052CC] text-white text-[13px] font-medium rounded hover:bg-[#0747A6] transition-colors"
                    >
                        <PlusIcon size="sm" />
                        <span>New Client</span>
                    </button>
                </div>
            </div>
        </header>
    );
}
