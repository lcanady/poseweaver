import { Header } from "@/components/header"
import { Hero } from "@/components/hero"
import { Features } from "@/components/features"
import { HowItWorks } from "@/components/how-it-works"
import { Pricing } from "@/components/pricing"
import { Faq } from "@/components/faq"
import { Footer } from "@/components/footer"

export default function LandingPage() {
  return (
    <div className="bg-background text-foreground w-full min-h-screen">
      <Header />
      <main className="flex-1">
        <Hero />
        <Features />
        <HowItWorks />
        <Pricing />
        <Faq />
      </main>
      <Footer />
    </div>
  )
}
