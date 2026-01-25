"use client";

interface OnboardingHeaderProps {
    clientName: string;
    vatPeriod: string;
    progress: number;
    completedCount: number;
    totalCount: number;
}

export function OnboardingHeader({
    clientName,
    vatPeriod,
    progress,
    completedCount,
    totalCount,
}: OnboardingHeaderProps) {
    return (
        <header className="sticky top-0 z-10 border-b border-[#DFE1E6] bg-white shadow-sm">
            <div className="mx-auto max-w-4xl px-4 py-4 sm:px-6 lg:px-8">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    {/* Left: Logo and Title */}
                    <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-[#0052CC] to-[#6554C0]">
                            <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                        </div>
                        <div>
                            <h1 className="text-[15px] font-bold text-[#172B4D]">{clientName}</h1>
                            <p className="text-[11px] text-[#5E6C84]">VAT Pack Portal - {vatPeriod}</p>
                        </div>
                    </div>

                    {/* Right: Progress */}
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <div className="text-right">
                                <p className="text-[11px] font-medium text-[#5E6C84]">Progress</p>
                                <p className="text-[13px] font-bold text-[#172B4D]">
                                    {completedCount} of {totalCount}
                                </p>
                            </div>
                            <div className="relative h-10 w-10">
                                <svg className="h-10 w-10 -rotate-90 transform">
                                    <circle
                                        cx="20"
                                        cy="20"
                                        r="16"
                                        fill="none"
                                        stroke="#DFE1E6"
                                        strokeWidth="4"
                                    />
                                    <circle
                                        cx="20"
                                        cy="20"
                                        r="16"
                                        fill="none"
                                        stroke={progress === 100 ? "#36B37E" : "#0052CC"}
                                        strokeWidth="4"
                                        strokeLinecap="round"
                                        strokeDasharray={`${progress} 100`}
                                        className="transition-all duration-500"
                                    />
                                </svg>
                                <span className="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-[#172B4D]">
                                    {progress}%
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Progress Bar */}
                <div className="mt-4">
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-[#DFE1E6]">
                        <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{
                                width: `${progress}%`,
                                backgroundColor: progress === 100 ? "#36B37E" : "#0052CC",
                            }}
                        />
                    </div>
                    <div className="mt-2 flex justify-between text-[10px] text-[#5E6C84]">
                        <span>Getting Started</span>
                        <span>Complete</span>
                    </div>
                </div>
            </div>
        </header>
    );
}
