import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MagneticSphere AI",
  description: "Multi-agent opportunity prediction platform"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

