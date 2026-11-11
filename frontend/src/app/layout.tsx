import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Vendor Onboarding",
  description: "Automated vendor onboarding verification system",
};

function Sidebar() {
  return (
    <aside className="w-64 border-r bg-card flex flex-col h-full shrink-0">
      <div className="p-6 border-b">
        <h1 className="text-lg font-semibold tracking-tight">VendorVerify</h1>
        <p className="text-xs text-muted-foreground mt-1">Automated Onboarding</p>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        <NavLink href="/" icon="grid">Dashboard</NavLink>
        <NavLink href="/submit" icon="plus">New Submission</NavLink>
        <NavLink href="/history" icon="list">Run History</NavLink>
      </nav>
      <div className="p-4 border-t">
        <p className="text-xs text-muted-foreground">Zamp Case Study &middot; PS-2</p>
      </div>
    </aside>
  );
}

function NavLink({ href, icon, children }: { href: string; icon: string; children: React.ReactNode }) {
  const icons: Record<string, string> = {
    grid: "M3 3h7v7H3V3zm11 0h7v7h-7V3zM3 14h7v7H3v-7zm11 0h7v7h-7v-7z",
    plus: "M12 4v16m-8-8h16",
    list: "M4 6h16M4 12h16M4 18h16",
  };
  return (
    <Link
      href={href}
      className="flex items-center gap-3 px-3 py-2 rounded-md text-sm hover:bg-accent transition-colors"
    >
      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d={icons[icon]} />
      </svg>
      {children}
    </Link>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="h-full flex">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <div className="p-8 max-w-6xl mx-auto">{children}</div>
        </main>
      </body>
    </html>
  );
}
