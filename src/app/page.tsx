import { auth } from "~/server/auth";
import { SignInButton } from "./_components/SignInButton";
import { SignOutButton } from "./_components/SignOutButton";
import { HeroSection } from "./_components/HeroSection";
import { BentoGrid } from "./_components/BentoGrid";
import { Testimonials } from "./_components/Testimonials";
import { CTASection } from "./_components/CTASection";
import { DashboardEmbed } from "./_components/DashboardEmbed";
import Image from "next/image";

export default async function HomePage() {
  const session = await auth();

  return (
    <main className="min-h-screen bg-[#F6F2ED]">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 border-b border-[#E4DDD3] bg-[#F6F2ED]/90 backdrop-blur-md">
        <div className="max-w-[1200px] mx-auto px-6 sm:px-8 lg:px-12 h-14 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Image
              src="/logo.svg"
              alt="Nova Logo"
              width={28}
              height={28}
              className="w-7 h-7"
            />
            <span className="text-[14px] font-semibold uppercase tracking-[0.08em] text-black">Nova</span>
          </div>
          {session?.user ? <SignOutButton /> : <SignInButton />}
        </div>
      </nav>

      <HeroSection isLoggedIn={!!session?.user} userName={session?.user?.name} />

      {session?.user && <DashboardEmbed />}

      {!session?.user && (
        <>
          <BentoGrid />
          <Testimonials />
          <CTASection />
        </>
      )}

      {/* Footer */}
      <footer className="border-t border-[#E4DDD3] bg-[#F6F2ED] py-12">
        <div className="max-w-[1200px] mx-auto px-6 sm:px-8 lg:px-12">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-3 mb-4 md:mb-0">
              <Image
                src="/logo.svg"
                alt="Nova Logo"
                width={32}
                height={32}
                className="w-8 h-8"
              />
            <span className="text-[15px] font-medium text-black">Nova</span>
            </div>
            <p className="text-[14px] text-[#9ba1a5]">
              © 2026 Nova. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </main>
  );
}
