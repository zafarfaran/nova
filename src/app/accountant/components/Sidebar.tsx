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
        bg-gradient-to-b from-[#1e1b4b] to-[#312e81]
        transition-all duration-300 ease-in-out
        ${isCollapsed ? "w-[72px]" : "w-[280px]"}
      `}
        >
            {/* Header / Logo */}
            <div className="flex items-center gap-3 px-5 py-5 border-b border-white/10">
                <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg">
                    <SparkleIcon size="lg" className="text-white" />
                </div>
                {!isCollapsed && (
                    <div className="animate-fade-in">
                        <h1 className="text-lg font-bold text-white tracking-tight">Nova</h1>
                        <p className="text-xs text-violet-300">Accountant Portal</p>
                    </div>
                )}
            </div>

            {/* Search */}
            {!isCollapsed && (
                <div className="px-4 py-3 animate-fade-in">
                    <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg bg-white/5 hover:bg-white/10 transition-colors text-violet-200 text-sm">
                        <SearchIcon size="sm" />
                        <span>Search...</span>
                        <kbd className="ml-auto text-xs bg-white/10 px-1.5 py-0.5 rounded">⌘K</kbd>
                    </button>
                </div>
            )}

            {/* Main Navigation */}
            <nav className="flex-1 px-3 py-2 overflow-y-auto custom-scrollbar-dark">
                <div className="space-y-1">
                    {mainNavItems.map((item) => {
                        const badge = item.id === "clients" ? clientCount : item.id === "vat-returns" ? vatDueCount : undefined;
                        return (
                            <button
                                key={item.id}
                                onClick={() => handleNavClick(item.id)}
                                className={`
                                    w-full flex items-center gap-3 px-3 py-2.5 rounded-lg
                                    transition-all duration-150 text-left
                                    ${activeItem === item.id
                                        ? "bg-violet-600 text-white shadow-lg shadow-violet-900/50"
                                        : "text-violet-200 hover:bg-white/10 hover:text-white"
                                    }
                                `}
                            >
                                <span className="flex-shrink-0">{item.icon}</span>
                                {!isCollapsed && (
                                    <>
                                        <span className="flex-1 font-medium text-sm">{item.label}</span>
                                        {badge !== undefined && badge > 0 && (
                                            <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-white/20">
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
            <div className="px-3 py-3 border-t border-white/10">
                <div className="space-y-2">
                    <button
                        onClick={() => handleNavClick("ai-assistant")}
                        className={`
                            w-full flex items-center gap-3 px-3 py-2.5 rounded-lg
                            bg-gradient-to-r from-violet-600 to-purple-600
                            text-white font-medium text-sm
                            hover:from-violet-500 hover:to-purple-500
                            transition-all duration-200 shadow-lg shadow-violet-900/50
                            ${isCollapsed ? "justify-center" : ""}
                        `}
                    >
                        <SparkleIcon size="md" />
                        {!isCollapsed && <span>AI Assistant</span>}
                    </button>

                    <button
                        onClick={() => handleNavClick("settings")}
                        className={`
                            w-full flex items-center gap-3 px-3 py-2 rounded-lg
                            text-violet-300 hover:bg-white/10 hover:text-white transition-colors
                            ${isCollapsed ? "justify-center" : ""}
                        `}
                    >
                        <SettingsIcon size="sm" />
                        {!isCollapsed && <span className="text-sm">Settings</span>}
                    </button>
                </div>
            </div>

            {/* Collapse Toggle */}
            <button
                onClick={() => setIsCollapsed(!isCollapsed)}
                className="absolute top-1/2 -right-3 transform -translate-y-1/2 w-6 h-6 rounded-full bg-violet-600 text-white shadow-lg flex items-center justify-center hover:bg-violet-500 transition-colors z-10"
            >
                {isCollapsed ? (
                    <ChevronRightIcon size="sm" />
                ) : (
                    <ChevronLeftIcon size="sm" />
                )}
            </button>

            {/* User Profile */}
            {!isCollapsed && (
                <div className="px-4 py-3 border-t border-white/10">
                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-emerald-400 to-cyan-500 flex items-center justify-center text-white font-semibold text-sm">
                            JD
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-white truncate">John Doe</p>
                            <p className="text-xs text-violet-300 truncate">Senior Accountant</p>
                        </div>
                    </div>
                </div>
            )}
        </aside>
    );
}
