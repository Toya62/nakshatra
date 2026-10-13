import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Nakshatra | Vedic Astrology AI Engine",
  description: "Swiss Ephemeris Birth Charts, Shodashavarga, Gochar Transits, Vimshottari Dashas, and Scripture-Grounded AI Consultations",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
