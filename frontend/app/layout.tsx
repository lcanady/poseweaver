import type React from "react"
import type { Metadata } from "next"
import { Inter, Lora, Inconsolata } from "next/font/google"
import { cn } from "@/lib/utils"
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { Toaster } from "@/components/ui/toaster"
import { AuthProvider } from "@/contexts/auth-context"
import { SetupProvider } from "@/components/setup-provider"

const fontSans = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  weight: ["400", "500", "600", "700", "800", "900"],
})

const fontSerif = Lora({
  subsets: ["latin"],
  variable: "--font-serif",
  style: ["normal", "italic"],
  weight: ["400", "700"],
})

const fontMono = Inconsolata({
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ["400", "700"],
})

export const metadata: Metadata = {
  title: "PoseWeaver - AI Co-writer for Roleplayers",
  description: "Your AI co-writer for immersive roleplay. Elevate your storytelling in seconds with AI-powered pose enhancement and character development.",
  generator: 'Next.js',
  metadataBase: new URL('https://poseweaver.com'),
  
  // Open Graph
  openGraph: {
    title: "PoseWeaver - AI Co-writer for Roleplayers",
    description: "Your AI co-writer for immersive roleplay. Elevate your storytelling in seconds with AI-powered pose enhancement and character development.",
    url: 'https://poseweaver.com',
    siteName: 'PoseWeaver',
    images: [
      {
        url: '/social-card.svg',
        width: 1200,
        height: 630,
        alt: 'PoseWeaver - AI Co-writer for Roleplayers',
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  
  // Twitter Card
  twitter: {
    card: 'summary_large_image',
    title: "PoseWeaver - AI Co-writer for Roleplayers",
    description: "Your AI co-writer for immersive roleplay. Elevate your storytelling in seconds with AI-powered pose enhancement and character development.",
    images: ['/social-card.svg'],
    creator: '@poseweaver',
    site: '@poseweaver',
  },
  
  // Additional meta tags
  keywords: ['AI', 'roleplay', 'storytelling', 'writing', 'character development', 'pose enhancement', 'creative writing', 'RPG'],
  authors: [{ name: 'PoseWeaver Team' }],
  category: 'Technology',
  
  // Robots
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        suppressHydrationWarning
        className={cn(
          "min-h-screen bg-background font-sans antialiased",
          fontSans.variable,
          fontSerif.variable,
          fontMono.variable,
        )}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <AuthProvider>
            <SetupProvider>
              {children}
            </SetupProvider>
            <Toaster />
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
