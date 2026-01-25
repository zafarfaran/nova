"use client";

import React, { useEffect, useRef, useState } from "react";

type Variant = "up" | "left" | "right" | "fade";

interface AnimateOnScrollProps {
    children: React.ReactNode;
    className?: string;
    variant?: Variant;
    delayClass?: string;
}

const animationClassMap: Record<Variant, string> = {
    up: "lp-animate",
    left: "lp-animate-left",
    right: "lp-animate-right",
    fade: "lp-animate-fade",
};

const hiddenClassMap: Record<Variant, string> = {
    up: "lp-hidden-up",
    left: "lp-hidden-left",
    right: "lp-hidden-right",
    fade: "lp-hidden",
};

export function AnimateOnScroll({
    children,
    className,
    variant = "up",
    delayClass,
}: AnimateOnScrollProps) {
    const ref = useRef<HTMLDivElement | null>(null);
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        if (!ref.current || typeof window === "undefined") return;

        const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        if (reduceMotion) {
            setIsVisible(true);
            return;
        }

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        setIsVisible(true);
                        observer.unobserve(entry.target);
                    }
                });
            },
            {
                threshold: 0.2,
                rootMargin: "0px 0px -10% 0px",
            }
        );

        observer.observe(ref.current);

        return () => observer.disconnect();
    }, []);

    const animationClass = isVisible
        ? `${animationClassMap[variant]} ${delayClass ?? ""}`.trim()
        : hiddenClassMap[variant];

    return (
        <div ref={ref} className={`${className ?? ""} ${animationClass}`.trim()}>
            {children}
        </div>
    );
}
