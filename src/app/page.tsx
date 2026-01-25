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
    <main className="min-h-screen bg-black">
      {/* Navigation */}
      <nav className="border-b border-slate-800 bg-black/50 sticky top-0 z-50 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-white rounded-md flex items-center justify-center">
              <svg className="w-5 h-5 text-black" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <span className="text-xl font-semibold text-white">Nova</span>
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
      <footer className="border-t border-slate-800 bg-black py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-2 mb-4 md:mb-0">
              <div className="w-8 h-8 bg-white rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-black" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <span className="text-lg font-semibold text-white">Nova</span>
            </div>
            <p className="text-sm text-slate-400">
              © 2026 Nova. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </main>
  );
}
