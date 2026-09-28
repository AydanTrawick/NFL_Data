import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EVERY SNAP — 2025 NFL Season",
  description: "A season told through every event in the 2025 NFL dataset.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
