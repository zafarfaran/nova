"use client";

import Image from "next/image";
import { AnimateOnScroll } from "./AnimateOnScroll";

export function Testimonials() {
  const testimonials = [
    {
      quote: "Nova cut our tax prep time by 75%. We can now serve 3x more clients with the same team.",
      author: "Sarah Mitchell",
      role: "Partner",
      company: "Mitchell & Associates",
    },
    {
      quote: "The AI document extraction is scary good. It catches errors we would have missed manually.",
      author: "James Chen",
      role: "Senior Accountant",
      company: "Chen Tax Services",
    },
    {
      quote: "Finally, a tool that clients actually use. The automated chasers have been a game-changer.",
      author: "Emma Thompson",
      role: "Managing Director",
      company: "Thompson Financial",
    },
  ];

  return (
    <section className="py-20 bg-[#F6F2ED] border-t border-[#E4DDD3]">
      <div className="max-w-[1200px] mx-auto px-6 sm:px-8 lg:px-12">
        {/* Section Header */}
        <div className="text-center mb-20">
          <AnimateOnScroll variant="up">
            <span className="text-[11px] uppercase tracking-[1px] text-[#9ba1a5] font-mono mb-6 block">
              Testimonials
            </span>
          </AnimateOnScroll>
          <AnimateOnScroll variant="up" delayClass="lp-delay-1">
            <h2 className="text-[44px] leading-[1.1] font-light text-black mb-6 tracking-tight max-w-[800px] mx-auto">
              Loved by accountants
            </h2>
          </AnimateOnScroll>
          <AnimateOnScroll variant="up" delayClass="lp-delay-2">
            <p className="text-[18px] leading-[1.6] text-[#000000cc] max-w-[700px] mx-auto font-light">
              Join hundreds of practices saving time and reducing errors
            </p>
          </AnimateOnScroll>
        </div>

        {/* Testimonials Grid */}
        <div className="grid md:grid-cols-3 gap-4 mb-16">
          {testimonials.map((testimonial, index) => (
            <AnimateOnScroll
              key={index}
              variant={index % 2 === 0 ? "left" : "right"}
              delayClass="lp-delay-2"
            >
              <div className="border border-[#E4DDD3] rounded-[4px] p-10 bg-[#FFFEFB] hover:border-[#0052CC] transition-colors relative overflow-hidden">
              {/* Decorative Logo */}
              <div className="absolute top-6 right-6 opacity-5">
                <Image
                  src="/logo.svg"
                  alt=""
                  width={48}
                  height={48}
                  className="w-12 h-12"
                />
              </div>

              {/* Quote */}
              <blockquote className="text-[14px] leading-[1.6] text-[#000000cc] mb-8 relative z-10">
                "{testimonial.quote}"
              </blockquote>

              {/* Author */}
              <div className="border-t border-[#E4DDD3] pt-6 relative z-10">
              <div className="font-medium text-black text-[13px]">{testimonial.author}</div>
              <div className="text-[11px] text-[#9ba1a5] mt-1">
                  {testimonial.role}, {testimonial.company}
                </div>
              </div>
              </div>
            </AnimateOnScroll>
          ))}
        </div>

        {/* Stats */}
        <AnimateOnScroll variant="up" delayClass="lp-delay-3">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { value: "500+", label: "Accounting firms" },
            { value: "50K+", label: "Clients managed" },
            { value: "2M+", label: "Documents processed" },
            { value: "99.9%", label: "Uptime" }
          ].map((stat, i) => (
            <div key={i} className="border border-[#E4DDD3] rounded-[4px] p-8 bg-[#FFFEFB] text-center">
              <div className="text-[26px] font-medium text-black mb-2">{stat.value}</div>
              <div className="text-[11px] uppercase tracking-[1px] text-[#9ba1a5] font-mono">{stat.label}</div>
            </div>
          ))}
          </div>
        </AnimateOnScroll>
      </div>
    </section>
  );
}
