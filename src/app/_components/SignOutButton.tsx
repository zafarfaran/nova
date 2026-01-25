"use client";

import { signOut } from "next-auth/react";

export function SignOutButton() {
  const handleSignOut = () => {
    void signOut({ callbackUrl: "/" });
  };

  return (
    <button
      onClick={handleSignOut}
      className="px-5 py-2 border border-[#e8e8e8] text-black rounded-[4px] font-medium hover:bg-[#f4f5f7] transition-colors text-[14px]"
    >
      Sign out
    </button>
  );
}
