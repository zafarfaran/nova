"use client";

import { SignInButton } from "./SignInButton";
import Link from "next/link";

interface HeroSectionProps {
  isLoggedIn?: boolean;
  userName?: string | null;
}

export function HeroSection({ isLoggedIn, userName }: HeroSectionProps) {
  return (
    <section className="relative overflow-hidden bg-black pt-20 pb-32">
      {/* Grid Background */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff08_1px,transparent_1px),linear-gradient(to_bottom,#ffffff08_1px,transparent_1px)] bg-[size:24px_24px]" />

      {/* Gradient Orbs */}
      <div className="absolute top-0 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"></div>
      <div className="absolute bottom-0 left-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl"></div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-4xl mx-auto">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-sm font-medium text-slate-300 mb-8">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </span>
            Backed by AI
          </div>

          {/* Main Heading */}
          {isLoggedIn ? (
            <>
              <h1 className="text-5xl sm:text-6xl md:text-7xl font-bold text-white mb-6 tracking-tight">
                Welcome back,
                <br />
                <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                  {userName?.split(" ")[0] || "there"}
                </span>
              </h1>
              <p className="text-xl md:text-2xl text-slate-400 mb-10 max-w-2xl mx-auto leading-relaxed">
                Your VAT compliance dashboard is ready. Manage clients, track documents, and stay ahead of deadlines.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <Link
                  href="/accountant"
                  className="px-8 py-4 bg-white text-black rounded-lg font-semibold hover:bg-slate-200 transition-all flex items-center gap-3 shadow-lg shadow-white/10"
                >
                  Open Dashboard
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </Link>
              </div>
            </>
          ) : (
            <>
              <h1 className="text-5xl sm:text-6xl md:text-7xl font-bold text-white mb-6 tracking-tight">
                VAT compliance on
                <br />
                <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                  autopilot
                </span>
              </h1>

              {/* Subheading */}
              <p className="text-xl md:text-2xl text-slate-400 mb-10 max-w-2xl mx-auto leading-relaxed">
                The only VAT management platform accountants actually want to use. Automate document collection, validation, and reporting.
              </p>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16">
                <SignInButton variant="hero" />
                <button className="px-6 py-3 text-slate-400 font-medium hover:text-white transition-colors flex items-center gap-2">
                  Watch demo
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </button>
              </div>

              {/* Social Proof */}
              <div className="flex flex-col items-center gap-4">
                <div className="flex -space-x-2">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div
                      key={i}
                      className="w-10 h-10 rounded-full bg-gradient-to-br from-slate-700 to-slate-800 border-2 border-slate-900 flex items-center justify-center text-xs font-semibold text-slate-300"
                    >
                      {String.fromCharCode(64 + i)}
                    </div>
                  ))}
                </div>
                <p className="text-sm text-slate-400">
                  Trusted by <span className="font-semibold text-white">500+</span> accounting firms
                </p>
              </div>
            </>
          )}
        </div>

        {/* Dashboard Preview - Only show for non-logged in users */}
        {!isLoggedIn && (
          <div className="mt-20 relative">
            <div className="absolute -inset-1 bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-pink-500/20 rounded-lg blur-xl"></div>
            <div className="relative bg-slate-900 rounded-lg border border-slate-800 shadow-2xl overflow-hidden">
              <div className="bg-slate-800 border-b border-slate-700 px-4 py-3 flex items-center gap-2">
                <div className="flex gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500"></div>
                  <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                </div>
                <div className="flex-1 text-center">
                  <div className="inline-block bg-slate-700 border border-slate-600 rounded px-3 py-1 text-xs text-slate-300">
                    nova.com/dashboard
                  </div>
                </div>
              </div>
              <div className="aspect-[16/10] bg-gradient-to-br from-slate-900 to-slate-800 p-8">
                <div className="grid grid-cols-4 gap-4 mb-4">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="bg-slate-800 border border-slate-700 rounded-lg p-4 shadow-sm">
                      <div className="h-2 w-16 bg-slate-700 rounded mb-2"></div>
                      <div className="h-6 w-12 bg-white rounded"></div>
                    </div>
                  ))}
                </div>
                <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 shadow-sm space-y-3">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-slate-700 rounded"></div>
                      <div className="flex-1 space-y-2">
                        <div className="h-2 bg-slate-700 rounded w-3/4"></div>
                        <div className="h-2 bg-slate-750 rounded w-1/2"></div>
                      </div>
                      <div className="w-16 h-6 bg-white rounded"></div>
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
