import type { Metadata } from "next";
import { Open_Sans } from "next/font/google";
import "./globals.css";
import "./css/greeting.css";
import { ThemeProvider } from "@/components/theme/ThemeProvider";
import { AuthProvider } from "@/contexts/AuthContext";
import { ChatProvider } from "@/contexts/ChatContext";
import { StockDataProvider } from "@/contexts/StockDataContext";
import { PortfolioProvider } from "@/contexts/PortfolioContext";
import { NotificationProvider } from "@/contexts/NotificationContext";
import { LiveDataOverlay } from "@/components/stock/LiveDataOverlay";
import { Toaster } from "@/utils/toast";

const openSans = Open_Sans({
  variable: "--font-open-sans",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "HedgeMind",
  description: "Your intelligent stock market chatbot for hedge funds",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${openSans.variable} antialiased`}
      >
        <AuthProvider>
          <ChatProvider>
            <StockDataProvider>
              <PortfolioProvider>
                <NotificationProvider>
                  <ThemeProvider>
                    {children}
                    <LiveDataOverlay />
                    <Toaster />
                  </ThemeProvider>
                </NotificationProvider>
              </PortfolioProvider>
            </StockDataProvider>
          </ChatProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
