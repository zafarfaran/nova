"use client";

import { signOut } from "next-auth/react";

export function SignOutButton() {
  const handleSignOut = () => {
    void signOut({ callbackUrl: "/" });
  };

  return (
    <button
      onClick={handleSignOut}
      className="px-5 py-2 bg-slate-800 text-white rounded-lg font-medium hover:bg-slate-700 transition-colors text-sm border border-slate-700"
    >
      Sign out
    </button>
  );
}
