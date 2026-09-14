import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Providers } from "@/lib/providers";
import { Sidebar } from "@/components/organisms/Sidebar";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-sans",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "TAPS - Test Analytics & Predictive System",
    template: "%s | TAPS",
  },
  description: "Production-grade Test Analytics Portal with AI-powered failure analysis, real-time execution tracking, and comprehensive reporting.",
  keywords: ["test analytics", "QA dashboard", "test automation", "failure analysis", "test reporting"],
  authors: [{ name: "TAPS Team" }],
  creator: "TAPS Team",
  metadataBase: new URL(process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000"),
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "./",
    title: "TAPS - Test Analytics & Predictive System",
    description: "Production-grade Test Analytics Portal with AI-powered insights",
    siteName: "TAPS",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full" style={{ background: 'var(--bg-primary)' }}>
        <Providers>
          <Sidebar />
          <main
            className="page-content min-h-screen"
            style={{
              marginLeft: '80px', // Fixed sidebar width - same as before
            }}
          >
            {children}
          </main>
        </Providers>
      </body>
    </html>
  );
}
