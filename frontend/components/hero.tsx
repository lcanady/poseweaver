"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { Wand2, Loader2 } from "lucide-react"

const initialPost = `From the shadows of the alley, a figure emerges. It's Jax. He looks at the neon sign flickering above the bar, then at you. "Been a while," he says, his voice low.`

const enhancedPosts = {
  minimal: `Jax steps out of the alley. The neon sign flickers red, then blue, then goes dark. He looks at you with tired eyes. "Been a while," he says, voice rough from too many cigarettes.`,
  balanced: `Jax walks out of the alley and stops under the neon sign. The Rusty Cog, it says in faded letters. His jacket looks too big on him now. When he sees you, something changes in his face. Recognition, maybe regret. "Been a while," he says. The words sound heavy.`,
  elaborate: `Jax steps into the light from the alley. The neon sign above him flickers on and off, casting red and blue shadows across his weathered face. The Rusty Cog, the sign reads, though some letters are burned out. He stops when he sees you. His hands go to his jacket pockets, an old habit. The city noise fills the silence between you, cars and music and voices from the apartments above. He looks older than you remember. More tired. "Been a while," he finally says. The words hang in the air like smoke.`,
}

export function Hero() {
  const [post, setPost] = useState(initialPost)
  const [enhancementStyle, setEnhancementStyle] = useState("balanced")
  const [enhancedPost, setEnhancedPost] = useState(enhancedPosts.balanced)
  const [isLoading, setIsLoading] = useState(false)

  const handleEnhance = () => {
    setIsLoading(true)
    setEnhancedPost("")
    setTimeout(() => {
      setEnhancedPost(enhancedPosts[enhancementStyle as keyof typeof enhancedPosts])
      setIsLoading(false)
    }, 1000)
  }

  const handleStyleChange = (style: string) => {
    setEnhancementStyle(style)
    setEnhancedPost(enhancedPosts[style as keyof typeof enhancedPosts])
  }

  return (
    <section className="container py-12 lg:py-24">
      <div className="grid lg:grid-cols-2 gap-12 items-center">
        <div className="space-y-6">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-tighter">
            <span className="bg-gradient-to-r from-primary to-amber-500 bg-clip-text text-transparent">PoseWeaver</span><br />
            Your AI Co-Writer for Immersive Roleplay
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground">
            Transform simple poses into rich narratives and generate vivid descriptions from images. Character-aware AI that understands your voice, follows MUSH etiquette, and elevates your storytelling without replacing your creativity.
          </p>
          <div className="flex flex-col sm:flex-row gap-4">
            <Button size="lg" className="w-full sm:w-auto" asChild>
              <a href="/signup">
                Start Free - 20 Poses/Month
              </a>
            </Button>
            <Button size="lg" variant="outline" className="w-full sm:w-auto bg-transparent" asChild>
              <a href="#pricing">
                View All Plans
              </a>
            </Button>
          </div>
        </div>
        <Card className="bg-card/50">
          <CardContent className="p-4 md:p-6">
            <Tabs value={enhancementStyle} onValueChange={handleStyleChange}>
              <TabsList className="grid w-full grid-cols-3 mb-4">
                <TabsTrigger value="minimal">Minimal</TabsTrigger>
                <TabsTrigger value="balanced">Balanced</TabsTrigger>
                <TabsTrigger value="elaborate">Elaborate</TabsTrigger>
              </TabsList>
              <div className="space-y-4">
                <div>
                  <label htmlFor="before-post" className="text-sm font-medium text-muted-foreground">
                    Your Post
                  </label>
                  <Textarea
                    id="before-post"
                    value={post}
                    onChange={(e) => setPost(e.target.value)}
                    className="mt-1 h-32 font-mono text-sm"
                    placeholder="Paste your roleplay post here..."
                  />
                </div>
                <div className="flex justify-center">
                  <Button onClick={handleEnhance} disabled={isLoading}>
                    {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Wand2 className="mr-2 h-4 w-4" />}
                    Enhance Post
                  </Button>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">AI-Enhanced Narrative</label>
                  <div className="mt-1 p-3 rounded-md border bg-background min-h-32 font-serif text-base">
                    {isLoading ? (
                      <div className="flex items-center justify-center h-full text-muted-foreground">
                        <Loader2 className="h-6 w-6 animate-spin" />
                      </div>
                    ) : (
                      <p>{enhancedPost}</p>
                    )}
                  </div>
                </div>
              </div>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </section>
  )
}
