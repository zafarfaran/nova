"use client";

import { SignInButton } from "./SignInButton";
import Image from "next/image";

export function CTASection() {
  return (
    <section className="py-20 bg-[#fafafa] border-t border-[#e8e8e8]">
      <div className="max-w-[1200px] mx-auto px-6 sm:px-8 lg:px-12">
        <div className="border border-[#e8e8e8] rounded-[4px] p-16 md:p-20 bg-white text-center">
          {/* Logo */}
          <div className="inline-flex items-center justify-center mb-8">
            <Image
              src="/logo.svg"
              alt="Nova"
              width={48}
              height={48}
              className="w-12 h-12"
            />
          </div>

          <span className="text-[12px] uppercase tracking-[1px] text-[#9ba1a5] font-mono mb-8 block">
            Join the revolution
          </span>

          <h2 className="text-[56px] leading-[1.1] font-light text-black mb-8 tracking-tight max-w-[700px] mx-auto">
            Ready to 10x your output?
          </h2>

            {/* Heading */}
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Ready to modernize your tax workflow?
            </h2>

            {/* Description */}
            <p className="text-lg md:text-xl text-slate-300 mb-10 leading-relaxed">
              Join accounting teams streamlining tax compliance with automation.
              Get started in minutes, no credit card required.
            </p>

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
