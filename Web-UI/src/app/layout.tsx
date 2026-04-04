import "./globals.css";

export const metadata = {
  title: "Monitoring UI",
  description: "Web UI for AI camera monitoring",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body className="min-h-screen bg-neutral-50 text-neutral-900">{children}</body>
    </html>
  );
}
