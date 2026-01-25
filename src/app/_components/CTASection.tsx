"use client";

import { SignInButton } from "./SignInButton";

export function CTASection() {
  return (
    <section className="py-20 bg-[#fafafa] border-t border-[#e8e8e8]">
      <div className="max-w-[1200px] mx-auto px-6 sm:px-8 lg:px-12">
        <div className="border border-[#e8e8e8] rounded-[4px] p-16 md:p-20 bg-white text-center">
          <span className="text-[12px] uppercase tracking-[1px] text-[#9ba1a5] font-mono mb-8 block">
            Join the revolution
          </span>

          <h2 className="text-[56px] leading-[1.1] font-light text-black mb-8 tracking-tight max-w-[700px] mx-auto">
            Ready to 10x your output?
          </h2>

          <p className="text-[24px] leading-[1.5] text-[#000000cc] mb-12 max-w-[600px] mx-auto font-light">
            Stop being buried in paperwork. Start being the accountant everyone wants to work with.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16">
            <SignInButton variant="white" />
            <button className="inline-flex items-center gap-2 px-6 py-3 text-black text-[16px] font-medium hover:text-[#0052CC] transition-colors">
              Schedule a demo
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </button>
          </div>

          {/* Trust Indicators */}
          <div className="flex flex-wrap items-center justify-center gap-8 text-[14px] mb-16">
            {[
              { text: "Free trial", subtext: "No credit card" },
              { text: "5 min setup", subtext: "Start today" },
              { text: "Unlimited scale", subtext: "Grow freely" }
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-2">
                <div className="w-2 h-2 bg-[#0052CC] rounded-full"></div>
                <span className="text-black font-medium">{item.text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Value Props */}
        <div className="mt-8 grid md:grid-cols-3 gap-4">
          {[
            {
              title: "Bank-grade security",
              description: "SOC 2 Type II certified. End-to-end encryption. Your data is locked down."
            },
            {
              title: "Blazing fast",
              description: "Process thousands of documents per hour. What used to take days now takes seconds."
            },
            {
              title: "Expert support",
              description: "Real accountants on standby. Get help from people who understand your workflow."
            }
          ].map((prop, i) => (
            <div key={i} className="border border-[#e8e8e8] rounded-[4px] p-10 bg-white hover:border-[#0052CC] transition-colors">
              <h3 className="text-[20px] font-medium text-black mb-3">{prop.title}</h3>
              <p className="text-[16px] leading-[1.6] text-[#000000cc]">{prop.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
