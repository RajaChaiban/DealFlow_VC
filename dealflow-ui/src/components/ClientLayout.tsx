"use client";

import { usePathname } from "next/navigation";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import Sidebar from "@/components/Sidebar";
import ErrorBoundary from "@/components/ErrorBoundary";

const AUTH_ROUTES = ["/login", "/register"];

function HeaderBar() {
  const { user } = useAuth();
  const displayName = user?.full_name || user?.email || "Guest";
  const displayEmail = user?.email || "";
  const initials = displayName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  return (
    <div className="border-b border-border bg-card">
      <div className="flex h-16 items-center justify-between px-8">
        <div>
          <h2 className="text-sm font-medium text-muted-foreground">
            Private Equity Intelligence
          </h2>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm font-medium text-foreground">
              {displayName}
            </p>
            {displayEmail && (
              <p className="text-xs text-muted-foreground">{displayEmail}</p>
            )}
          </div>
          <div className="h-10 w-10 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-semibold">
            {initials || "?"}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ClientLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const isAuthRoute = AUTH_ROUTES.includes(pathname);

  return (
    <AuthProvider>
      {isAuthRoute ? (
        children
      ) : (
        <div className="flex min-h-screen bg-background">
          <Sidebar />
          <main className="ml-64 flex-1">
            <HeaderBar />
            <div className="p-8">
              <ErrorBoundary>{children}</ErrorBoundary>
            </div>
          </main>
        </div>
      )}
    </AuthProvider>
  );
}
