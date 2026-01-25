"use client";

import React, { useState } from "react";
import {
    DashboardIcon,
    ClientsIcon,
    VatIcon,
    SettingsIcon,
    ChevronLeftIcon,
    ChevronRightIcon,
    SparkleIcon,
    SearchIcon,
} from "./icons/AccountantIcons";

interface NavItem {
    id: string;
    label: string;
    icon: React.ReactNode;
    badge?: number;
}

interface SidebarProps {
    onNavigate?: (itemId: string) => void;
    activeItem?: string;
    clientCount?: number;
    vatDueCount?: number;
}

const mainNavItems: NavItem[] = [
    { id: "dashboard", label: "Dashboard", icon: <DashboardIcon size="md" /> },
    { id: "clients", label: "Clients", icon: <ClientsIcon size="md" /> },
    { id: "vat-returns", label: "VAT Returns", icon: <VatIcon size="md" /> },
];

export function Sidebar({ onNavigate, activeItem = "dashboard", clientCount, vatDueCount }: SidebarProps) {
    const [isCollapsed, setIsCollapsed] = useState(false);

    const handleNavClick = (itemId: string) => {
        onNavigate?.(itemId);
    };

    return (
        <aside
            className={`
                relative flex flex-col h-full
                bg-[#0D1117]
                transition-all duration-200 ease-in-out
                ${isCollapsed ? "w-[64px]" : "w-[240px]"}
            `}
        >
            {/* Header / Logo */}
            <div className="flex items-center gap-3 px-4 py-4 border-b border-white/5">
                <div className="flex-shrink-0 w-8 h-8 rounded bg-[#0052CC] flex items-center justify-center">
                    <span className="text-white font-bold text-sm">N</span>
                </div>
                {!isCollapsed && (
                    <div className="animate-fade-in">
                        <h1 className="text-sm font-semibold text-white tracking-tight">Nova</h1>
                        <p className="text-[11px] text-[#8B949E]">Accountant Portal</p>
                    </div>
                )}
            </div>

            {/* Search */}
            {!isCollapsed && (
                <div className="px-3 py-3 animate-fade-in">
                    <button className="w-full flex items-center gap-2 px-3 py-2 rounded bg-[#161B22] hover:bg-[#21262D] transition-colors text-[#8B949E] text-sm border border-[#30363D]">
                        <SearchIcon size="sm" />
                        <span className="text-[13px]">Search</span>
                        <kbd className="ml-auto text-[10px] bg-[#21262D] px-1.5 py-0.5 rounded border border-[#30363D]">/</kbd>
                    </button>
                </div>
            )}

            {/* Main Navigation */}
            <nav className="flex-1 px-3 py-2 overflow-y-auto custom-scrollbar-dark">
                <div className="space-y-0.5">
                    {mainNavItems.map((item) => {
                        const badge = item.id === "clients" ? clientCount : item.id === "vat-returns" ? vatDueCount : undefined;
                        return (
                            <button
                                key={item.id}
                                onClick={() => handleNavClick(item.id)}
                                className={`
                                    w-full flex items-center gap-3 px-3 py-2 rounded
                                    transition-all duration-100 text-left
                                    ${activeItem === item.id
                                        ? "bg-[#21262D] text-white"
                                        : "text-[#8B949E] hover:bg-[#161B22] hover:text-[#C9D1D9]"
                                    }
                                `}
                            >
                                <span className="flex-shrink-0 opacity-80">{item.icon}</span>
                                {!isCollapsed && (
                                    <>
                                        <span className="flex-1 font-medium text-[13px]">{item.label}</span>
                                        {badge !== undefined && badge > 0 && (
                                            <span className="px-1.5 py-0.5 text-[11px] font-medium rounded bg-[#30363D] text-[#8B949E]">
                                                {badge}
                                            </span>
                                        )}
                                    </>
                                )}
                            </button>
                        );
                    })}
                </div>
            </nav>

            {/* Bottom Actions */}
            <div className="px-3 py-3 border-t border-white/5">
                <div className="space-y-1">
                    <button
                        onClick={() => handleNavClick("ai-assistant")}
                        className={`
                            w-full flex items-center gap-3 px-3 py-2 rounded
                            bg-[#0052CC] hover:bg-[#0747A6]
                            text-white font-medium text-[13px]
                            transition-all duration-100
                            ${isCollapsed ? "justify-center" : ""}
                        `}
                    >
                        <SparkleIcon size="sm" />
                        {!isCollapsed && <span>AI Assistant</span>}
                    </button>

                    <button
                        onClick={() => handleNavClick("settings")}
                        className={`
                            w-full flex items-center gap-3 px-3 py-2 rounded
                            text-[#8B949E] hover:bg-[#161B22] hover:text-[#C9D1D9] transition-colors
                            ${isCollapsed ? "justify-center" : ""}
                        `}
                    >
                        <SettingsIcon size="sm" />
                        {!isCollapsed && <span className="text-[13px]">Settings</span>}
                    </button>
                </div>
            </div>

            {/* Collapse Toggle */}
            <button
                onClick={() => setIsCollapsed(!isCollapsed)}
                className="absolute top-1/2 -right-3 transform -translate-y-1/2 w-6 h-6 rounded-full bg-[#30363D] border border-[#484F58] text-[#8B949E] flex items-center justify-center hover:bg-[#484F58] hover:text-white transition-colors z-10"
            >
                {isCollapsed ? (
                    <ChevronRightIcon size="sm" />
                ) : (
                    <ChevronLeftIcon size="sm" />
                )}
            </button>

            {/* User Profile */}
            {!isCollapsed && (
                <div className="px-3 py-3 border-t border-white/5">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-[#238636] flex items-center justify-center text-white font-medium text-xs">
                            JD
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-[13px] font-medium text-[#C9D1D9] truncate">John Doe</p>
                            <p className="text-[11px] text-[#8B949E] truncate">Senior Accountant</p>
                        </div>
                    </div>
                </div>
            )}
        </aside>
    );
}
