import { auth } from "~/server/auth";
import { SignInButton } from "./_components/SignInButton";
import { SignOutButton } from "./_components/SignOutButton";
import { HeroSection } from "./_components/HeroSection";
import { BentoGrid } from "./_components/BentoGrid";
import { Testimonials } from "./_components/Testimonials";
import { CTASection } from "./_components/CTASection";
import { DashboardEmbed } from "./_components/DashboardEmbed";

export default async function HomePage() {
  const session = await auth();

  return (
    <main className="min-h-screen bg-[#fafafa]">
      {/* Navigation */}
      <nav className="border-b border-[#e8e8e8] bg-[#fafafa] sticky top-0 z-50">
        <div className="max-w-[1200px] mx-auto px-6 sm:px-8 lg:px-12 py-6 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-black rounded-[4px] flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <span className="text-[20px] font-medium text-black">Nova</span>
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
      <footer className="border-t border-[#e8e8e8] bg-[#fafafa] py-12">
        <div className="max-w-[1200px] mx-auto px-6 sm:px-8 lg:px-12">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-3 mb-4 md:mb-0">
              <div className="w-8 h-8 bg-black rounded-[4px] flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <span className="text-[16px] font-medium text-black">Nova</span>
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
