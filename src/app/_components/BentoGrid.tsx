"use client";

import Image from "next/image";
import { AnimateOnScroll } from "./AnimateOnScroll";

export function BentoGrid() {
  return (
    <section className="py-20 bg-[#F6F2ED] border-t border-[#E4DDD3]">
      <div className="max-w-[1200px] mx-auto px-6 sm:px-8 lg:px-12">
        {/* Section Header */}
        <div className="text-center mb-20">
          <AnimateOnScroll variant="up">
            <span className="text-[11px] uppercase tracking-[1px] text-[#9ba1a5] font-mono mb-6 block">
              Supercharged Workflow
            </span>
          </AnimateOnScroll>
          <AnimateOnScroll variant="up" delayClass="lp-delay-1">
            <h2 className="text-[44px] leading-[1.1] font-light text-black mb-6 tracking-tight max-w-[800px] mx-auto">
              Do more with way less effort
            </h2>
          </AnimateOnScroll>
          <AnimateOnScroll variant="up" delayClass="lp-delay-2">
            <p className="text-[18px] leading-[1.6] text-[#000000cc] max-w-[700px] mx-auto font-light">
              From chaos to clarity in seconds. Every feature built to make you unstoppable.
            </p>
          </AnimateOnScroll>
        </div>

        {/* Features Grid */}
        <div className="space-y-4">
          {/* AI Document Processing */}
          <AnimateOnScroll variant="left" delayClass="lp-delay-2">
            <div className="border border-[#E4DDD3] rounded-[4px] p-10 bg-[#FFFEFB] hover:border-[#0052CC] transition-colors relative overflow-hidden">
              {/* Decorative Logo */}
              <div className="absolute top-8 right-8 opacity-5">
                <Image
                  src="/logo.svg"
                  alt=""
                  width={120}
                  height={120}
                  className="w-30 h-30"
                />
              </div>

              <div className="max-w-[700px] relative z-10">
                <span className="text-[11px] uppercase tracking-[1px] text-[#9ba1a5] font-mono mb-4 block">
                  Claude AI Brain
                </span>
                <h3 className="text-[26px] leading-[1.2] font-light text-black mb-4">
                  Intelligence that thinks ahead
                </h3>
                <p className="text-[14px] leading-[1.6] text-[#000000cc] mb-8">
                  Upload hundreds of invoices. Claude extracts every detail, validates tax numbers against HMRC, flags anomalies, and auto-categorizes transactions. In seconds, not hours.
                </p>

                <div className="grid grid-cols-3 gap-4 mt-8">
                  <div className="border border-[#E4DDD3] rounded-[4px] p-6 bg-[#F9F6F1]">
                    <div className="text-[26px] font-medium text-black mb-1">10,000+</div>
                    <div className="text-[11px] uppercase tracking-[1px] text-[#9ba1a5] font-mono">Docs/hour</div>
                  </div>
                  <div className="border border-[#E4DDD3] rounded-[4px] p-6 bg-[#F9F6F1]">
                    <div className="text-[26px] font-medium text-[#36B37E] mb-1">99.9%</div>
                    <div className="text-[11px] uppercase tracking-[1px] text-[#9ba1a5] font-mono">Accuracy</div>
                  </div>
                  <div className="border border-[#E4DDD3] rounded-[4px] p-6 bg-[#F9F6F1]">
                    <div className="text-[26px] font-medium text-[#0052CC] mb-1">&lt;1s</div>
                    <div className="text-[11px] uppercase tracking-[1px] text-[#9ba1a5] font-mono">Per invoice</div>
                  </div>
                </div>
              </div>
            </div>
          </AnimateOnScroll>

          {/* Two Column Layout */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Real-time Banking */}
            <AnimateOnScroll variant="left" delayClass="lp-delay-3">
              <div className="border border-[#E4DDD3] rounded-[4px] p-10 bg-[#FFFEFB] hover:border-[#36B37E] transition-colors">
              <span className="text-[11px] uppercase tracking-[1px] text-[#9ba1a5] font-mono mb-4 block">
                Live Banking
              </span>
              <h3 className="text-[26px] leading-[1.2] font-light text-black mb-4">
                Real-time sync
              </h3>
              <p className="text-[14px] leading-[1.6] text-[#000000cc] mb-8">
                Connect any UK bank. Transactions flow in automatically. Reconciliation happens in the background.
              </p>

              <div className="space-y-3">
                {[
                  { name: "Barclays Business", txns: "1,247" },
                  { name: "HSBC Corporate", txns: "892" },
                  { name: "Lloyds Commercial", txns: "634" }
                ].map((bank) => (
                  <div key={bank.name} className="flex items-center justify-between p-4 border border-[#E4DDD3] rounded-[4px] bg-[#F9F6F1]">
                    <div className="text-[13px] font-medium text-black">{bank.name}</div>
                    <div className="text-[11px] text-[#9ba1a5]">{bank.txns} transactions</div>
                  </div>
                ))}
              </div>
              </div>
            </AnimateOnScroll>

            {/* Autopilot Mode */}
            <AnimateOnScroll variant="right" delayClass="lp-delay-3">
              <div className="border border-[#E4DDD3] rounded-[4px] p-10 bg-[#FFFEFB] hover:border-[#FF991F] transition-colors">
              <span className="text-[11px] uppercase tracking-[1px] text-[#9ba1a5] font-mono mb-4 block">
                Zero Touch
              </span>
              <h3 className="text-[26px] leading-[1.2] font-light text-black mb-4">
                Autopilot mode
              </h3>
              <p className="text-[14px] leading-[1.6] text-[#000000cc] mb-8">
                Smart reminders, automated chasers, deadline alerts. Your clients stay on track without you lifting a finger.
              </p>

              <div className="grid grid-cols-2 gap-4">
                <div className="border border-[#E4DDD3] rounded-[4px] p-6 bg-[#F9F6F1] text-center">
                  <div className="text-[26px] font-medium text-black mb-1">0</div>
                  <div className="text-[11px] uppercase tracking-[1px] text-[#9ba1a5] font-mono">Manual work</div>
                </div>
                <div className="border border-[#E4DDD3] rounded-[4px] p-6 bg-[#F9F6F1] text-center">
                  <div className="text-[26px] font-medium text-[#FF991F] mb-1">24/7</div>
                  <div className="text-[11px] uppercase tracking-[1px] text-[#9ba1a5] font-mono">Monitoring</div>
                </div>
              </div>
              </div>
            </AnimateOnScroll>
          </div>

          {/* Command Center */}
          <AnimateOnScroll variant="right" delayClass="lp-delay-4">
            <div className="border border-[#E4DDD3] rounded-[4px] p-10 bg-[#FFFEFB] hover:border-[#0052CC] transition-colors relative overflow-hidden">
            {/* Decorative Logo */}
            <div className="absolute bottom-8 right-8 opacity-5">
              <Image
                src="/logo.svg"
                alt=""
                width={120}
                height={120}
                className="w-30 h-30"
              />
            </div>

            <div className="max-w-[700px] relative z-10">
              <span className="text-[11px] uppercase tracking-[1px] text-[#9ba1a5] font-mono mb-4 block">
                Mission Control
              </span>
              <h3 className="text-[26px] leading-[1.2] font-light text-black mb-4">
                Manage hundreds of clients with ease
              </h3>
              <p className="text-[14px] leading-[1.6] text-[#000000cc] mb-8">
                Bird's-eye view of every client, every deadline, every document. Sort, filter, search. Know exactly who needs attention and why.
              </p>
            </div>

            <div className="grid grid-cols-3 gap-4 mt-8">
              {[
                { value: "248", label: "Active Clients", color: "#0052CC" },
                { value: "12", label: "Need Attention", color: "#FF991F" },
                { value: "236", label: "On Track", color: "#36B37E" }
              ].map((stat, i) => (
                <div key={i} className="border border-[#E4DDD3] rounded-[4px] p-6 bg-[#F9F6F1]">
                  <div className="text-[26px] font-medium mb-1" style={{ color: stat.color }}>{stat.value}</div>
                  <div className="text-[11px] uppercase tracking-[1px] text-[#9ba1a5] font-mono">{stat.label}</div>
                </div>
              ))}
            </div>
            </div>
          </AnimateOnScroll>

          {/* Two Column Layout */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Anomaly Detection */}
            <AnimateOnScroll variant="left" delayClass="lp-delay-5">
              <div className="border border-[#E4DDD3] rounded-[4px] p-10 bg-[#FFFEFB] hover:border-[#DE350B] transition-colors">
              <span className="text-[11px] uppercase tracking-[1px] text-[#9ba1a5] font-mono mb-4 block">
                Smart Insights
              </span>
              <h3 className="text-[26px] leading-[1.2] font-light text-black mb-4">
                Anomaly detection
              </h3>
              <p className="text-[14px] leading-[1.6] text-[#000000cc] mb-8">
                AI spots irregularities before they become problems. Duplicate invoices, suspicious amounts, missing tax numbers.
              </p>

              <div className="space-y-3">
                <div className="border border-[#DE350B] bg-[#FFEBE6] rounded-[4px] p-4">
                  <div className="text-[14px] font-medium text-[#DE350B] mb-1">Potential duplicate</div>
                  <div className="text-[12px] text-[#5E6C84]">Invoice #12345 matches existing entry</div>
                </div>
                <div className="border border-[#FF991F] bg-[#FFFAE6] rounded-[4px] p-4">
                  <div className="text-[14px] font-medium text-[#FF991F] mb-1">Unusual amount</div>
                  <div className="text-[12px] text-[#5E6C84]">£50,000 is 10x the average</div>
                </div>
              </div>
              </div>
            </AnimateOnScroll>

          {/* Tax Returns */}
            <AnimateOnScroll variant="right" delayClass="lp-delay-5">
              <div className="border border-[#E4DDD3] rounded-[4px] p-10 bg-[#FFFEFB] hover:border-[#36B37E] transition-colors">
              <span className="text-[11px] uppercase tracking-[1px] text-[#9ba1a5] font-mono mb-4 block">
                One-Click Magic
              </span>
              <h3 className="text-[26px] leading-[1.2] font-light text-black mb-4">
                Generate tax returns instantly
              </h3>
              <p className="text-[14px] leading-[1.6] text-[#000000cc] mb-8">
                All your data is validated, categorized, and ready. Hit generate. Get HMRC-ready tax returns in seconds.
              </p>

              <div className="border border-[#E4DDD3] rounded-[4px] p-6 bg-[#F9F6F1]">
                <div className="flex items-center justify-between mb-6">
                  <div className="text-[13px] font-medium text-black">Q4 2024 Tax Return</div>
                  <div className="px-3 py-1.5 bg-[#E3FCEF] border border-[#ABF5D1] rounded-[3px] text-[11px] font-semibold text-[#006644] uppercase tracking-wide">
                    Ready
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-[11px] text-[#9ba1a5] mb-1">Tax Due</div>
                    <div className="text-[20px] font-medium text-[#0052CC]">£15,444</div>
                  </div>
                  <div>
                    <div className="text-[11px] text-[#9ba1a5] mb-1">Total Sales</div>
                    <div className="text-[20px] font-medium text-black">£125,450</div>
                  </div>
                </div>
              </div>
              </div>
            </AnimateOnScroll>
          </div>
        </div>
      </div>
    </section>
  );
}
