import { UploadCloud, ClipboardPaste, Wand2 } from "lucide-react"

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
            <UploadCloud className="w-8 h-8" />
          </div>
          <h3 className="text-xl font-semibold">1. Upload Character</h3>
          <p className="text-muted-foreground">
            Give the AI a "brain dump" of your character's personality, history, and voice.
          </p>
        </div>
        <div className="flex flex-col items-center space-y-4 z-10 bg-background p-4">
          <div className="flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 border-2 border-primary text-primary">
            <ClipboardPaste className="w-8 h-8" />
          </div>
          <h3 className="text-xl font-semibold">2. Paste Scene</h3>
          <p className="text-muted-foreground">
            Copy the latest scene text from your roleplay session directly into the editor.
          </p>
        </div>
        <div className="flex flex-col items-center space-y-4 z-10 bg-background p-4">
          <div className="flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 border-2 border-primary text-primary">
            <Wand2 className="w-8 h-8" />
          </div>
          <h3 className="text-xl font-semibold">3. Get Enhanced Posts</h3>
          <p className="text-muted-foreground">Receive beautifully crafted, in-character narratives in seconds.</p>
        </div>
      </div>
    </section>
  )
}
