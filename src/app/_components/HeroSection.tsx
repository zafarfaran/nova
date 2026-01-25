"use client";

import { SignInButton } from "./SignInButton";
import Link from "next/link";
import Image from "next/image";

interface HeroSectionProps {
  isLoggedIn?: boolean;
  userName?: string | null;
}

export function HeroSection({ isLoggedIn, userName }: HeroSectionProps) {
  return (
    <section className="relative bg-[#fafafa] pt-32 pb-20 border-b border-[#e8e8e8]">
      <div className="max-w-[1200px] mx-auto px-6 sm:px-8 lg:px-12">
        <div className="text-center max-w-[700px] mx-auto">
          {/* Logo Badge */}
          <div className="inline-flex items-center justify-center mb-8">
            <Image
              src="/logo.svg"
              alt="Nova"
              width={64}
              height={64}
              className="w-16 h-16"
            />
          </div>

          {/* Badge */}
          {/* <div className="inline-flex items-center gap-2 mb-8">
            <span className="text-[12px] uppercase tracking-[1px] text-[#9ba1a5] font-mono">
              Powered by Claude AI
            </span>
          </div> */}

          {/* Main Heading */}
          {isLoggedIn ? (
            <>
              <h1 className="text-[56px] leading-[1.1] font-light text-black mb-6 tracking-tight">
                Welcome back,
                <br />
                <span className="font-normal">{userName?.split(" ")[0] || "there"}</span>
              </h1>
              <p className="text-[24px] leading-[1.5] text-[#000000cc] mb-12 font-light">
                Your command center is ready. Manage hundreds of clients, automate compliance, and reclaim your time.
              </p>
              <div className="flex justify-center">
                <Link
                  href="/accountant"
                  className="inline-flex items-center gap-3 px-8 py-4 bg-black text-white text-[16px] font-medium rounded-[4px] hover:bg-[#0052CC] transition-colors"
                >
                  Open Dashboard
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </Link>
              </div>
            </>
          ) : (
            <>
              <h1 className="text-[56px] sm:text-[64px] lg:text-[72px] leading-[1.1] font-light text-black mb-8 tracking-tight">
                10x Your Accounting Power
              </h1>

              {/* Subheading */}
              <p className="text-[24px] leading-[1.5] text-[#000000cc] mb-16 font-light">
                Stop drowning in spreadsheets. Nova is the AI-powered platform that turns accountants into productivity machines.
              </p>

              {/* Power Stats */}
              <div className="flex flex-wrap justify-center gap-8 mb-16 text-[14px]">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-[#36B37E] rounded-full"></div>
                  <span className="text-black font-medium">95% time saved</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-[#0052CC] rounded-full"></div>
                  <span className="text-black font-medium">99.9% accuracy</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-[#FF991F] rounded-full"></div>
                  <span className="text-black font-medium">500+ firms trust us</span>
                </div>
              </div>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-20">
                <SignInButton variant="hero" />
                <button className="inline-flex items-center gap-2 px-6 py-3 text-black text-[16px] font-medium hover:text-[#0052CC] transition-colors">
                  Watch demo
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </button>
              </div>
            </>
          )}
        </div>

        {/* Dashboard Preview - Only show for non-logged in users */}
        {!isLoggedIn && (
          <div className="mt-20">
            <div className="border border-[#e8e8e8] rounded-[4px] overflow-hidden bg-white shadow-sm">
              <div className="bg-[#F4F5F7] border-b border-[#e8e8e8] px-4 py-3 flex items-center gap-3">
                <div className="flex gap-2">
                  <div className="w-3 h-3 rounded-full bg-[#DE350B]"></div>
                  <div className="w-3 h-3 rounded-full bg-[#FF991F]"></div>
                  <div className="w-3 h-3 rounded-full bg-[#36B37E]"></div>
                </div>
                <Image
                  src="/logo.svg"
                  alt="Nova"
                  width={16}
                  height={16}
                  className="w-4 h-4"
                />
                <div className="flex-1 text-center">
                  <div className="inline-flex items-center gap-2 bg-white border border-[#e8e8e8] rounded-[4px] px-4 py-1.5 text-[12px] text-[#5E6C84]">
                    <svg className="w-3 h-3 text-[#36B37E]" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                    </svg>
                    nova.app/dashboard
                  </div>
                </div>
              </div>
              <div className="aspect-[16/9] bg-[#FAFBFC] p-8">
                <div className="grid grid-cols-4 gap-4 mb-6">
                  {[
                    { label: "CLIENTS", value: "248", color: "#0052CC" },
                    { label: "PENDING", value: "12", color: "#FF991F" },
                    { label: "COMPLETE", value: "236", color: "#36B37E" },
                    { label: "FLAGGED", value: "3", color: "#DE350B" }
                  ].map((stat, i) => (
                    <div key={i} className="bg-white border border-[#e8e8e8] rounded-[4px] p-6">
                      <div className="text-[11px] font-semibold uppercase tracking-[0.04em] mb-3" style={{ color: stat.color }}>{stat.label}</div>
                      <div className="text-[32px] font-semibold" style={{ color: stat.color }}>{stat.value}</div>
                    </div>
                  ))}
                </div>
                <div className="bg-white border border-[#e8e8e8] rounded-[4px] p-6 space-y-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="flex items-center gap-4 p-3 hover:bg-[#F4F5F7] rounded-[4px] transition-colors">
                      <div className="w-10 h-10 bg-[#0052CC] rounded-[4px] flex items-center justify-center text-white font-semibold text-[14px]">
                        {String.fromCharCode(64 + i)}
                      </div>
                      <div className="flex-1">
                        <div className="h-3 bg-[#DFE1E6] rounded w-3/4 mb-2"></div>
                        <div className="h-2 bg-[#EBECF0] rounded w-1/2"></div>
                      </div>
                      <div className="flex gap-2">
                        <div className="px-3 py-1.5 bg-[#E3FCEF] border border-[#ABF5D1] rounded-[3px] text-[11px] font-semibold text-[#006644] uppercase tracking-wide">
                          COMPLETE
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
