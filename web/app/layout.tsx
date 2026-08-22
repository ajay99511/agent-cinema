import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Screenplay Structural Map",
  description: "Ask questions about a screenplay corpus — answered by live ClickHouse queries.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
