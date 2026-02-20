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
        <header className="bg-[#FBFCFD] border-b border-[#E4E7EC]">
            <div className="px-6 py-3 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div>
                        <h1 className="text-[15px] font-semibold text-[#172B4D] tracking-tight">
                            {title}
                        </h1>
                        {subtitle && (
                            <p className="text-[12px] text-[#7A869A] mt-0.5">{subtitle}</p>
                        )}
                    </div>
                </div>

                <div className="flex items-center gap-2.5">
                    {/* Search */}
                    <div className="relative">
                        <SearchIcon
                            size="sm"
                            className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9AA4B2]"
                        />
                        <input
                            type="text"
                            placeholder="Search clients..."
                            onChange={(e) => onSearch?.(e.target.value)}
                            className="w-56 pl-9 pr-4 py-1.5 rounded-md border border-[#E4E7EC] bg-[#F7F8FA] text-[12px] text-[#172B4D] placeholder:text-[#9AA4B2] focus:outline-none focus:border-[#B3C7F9] focus:ring-2 focus:ring-[#E6EDFF] transition"
                        />
                    </div>

                    {/* Add New Client Button */}
                    <button
                        onClick={onAddNew}
                        className="flex items-center gap-2 px-3.5 py-1.5 bg-[#0B5FFF] text-white text-[12px] font-medium rounded-md hover:bg-[#0847C1] transition-colors"
                    >
                        <PlusIcon size="sm" />
                        <span>New Client</span>
                    </button>
                </div>
            </div>
        </header>
    );
}
