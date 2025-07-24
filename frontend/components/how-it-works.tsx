import { Users, Wand2, Sparkles } from "lucide-react"

export function HowItWorks() {
  return (
    <section id="how-it-works" className="container py-12 lg:py-24">
      <div className="text-center space-y-4 mb-12">
        <h2 className="text-3xl md:text-4xl font-bold">Get Started in Three Simple Steps</h2>
        <p className="text-lg text-muted-foreground">From a simple post to a brilliant narrative in under a minute.</p>
      </div>
      <div className="grid md:grid-cols-3 gap-8 text-center relative">
        <div className="absolute top-1/2 left-0 w-full h-px bg-border -translate-y-1/2 hidden md:block"></div>
        <div className="absolute top-8 left-1/2 w-px h-full bg-border -translate-x-1/2 md:hidden"></div>

        <div className="flex flex-col items-center space-y-4 z-10 bg-background p-4">
          <div className="flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 border-2 border-primary text-primary">
            <Users className="w-8 h-8" />
          </div>
          <h3 className="text-xl font-semibold">1. Create Characters</h3>
          <p className="text-muted-foreground">
            Build detailed character profiles with personality, background, and voice notes in your dashboard.
          </p>
        </div>
        <div className="flex flex-col items-center space-y-4 z-10 bg-background p-4">
          <div className="flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 border-2 border-primary text-primary">
            <Wand2 className="w-8 h-8" />
          </div>
          <h3 className="text-xl font-semibold">2. Enhance Poses</h3>
          <p className="text-muted-foreground">
            Select your character and paste your simple pose. Choose your enhancement style and let AI work its magic.
          </p>
        </div>
        <div className="flex flex-col items-center space-y-4 z-10 bg-background p-4">
          <div className="flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 border-2 border-primary text-primary">
            <Sparkles className="w-8 h-8" />
          </div>
          <h3 className="text-xl font-semibold">3. Copy & Roleplay</h3>
          <p className="text-muted-foreground">Get rich, in-character narratives ready to paste into any roleplay platform.</p>
        </div>
      </div>
    </section>
  )
}
