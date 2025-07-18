"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { Wand2, Loader2 } from "lucide-react"

const initialPost = `From the shadows of the alley, a figure emerges. It's Jax. He looks at the neon sign flickering above the bar, then at you. "Been a while," he says, his voice low.`

const enhancedPosts = {
  minimal: `Jax steps out from the alley's deep shadows, his form materializing under the stuttering light of a neon sign. He glances from the sign to you, a flicker of recognition in his eyes. "Been a while," he says, his voice a low rumble that barely cuts through the city's hum.`,
  balanced: `The oppressive darkness of the alleyway relinquishes its hold on a solitary figure. Jax emerges, his silhouette sharpened by the erratic pulse of a cheap neon sign advertising 'The Rusty Cog'. His gaze drifts from its flickering promise of drink to your own face, a long, unreadable moment passing between you. "Been a while," he finally rumbles, the words laced with the grit of the streets and the weight of unspoken history.`,
  elaborate: `As if peeled from the very fabric of the alley's oppressive gloom, a figure solidifies into the tangible form of Jax. He moves with a predator's coiled grace, each step silent on the grimy pavement. Above, a neon sign for 'The Rusty Cog' sputters and dies, casting his hardened features in a fleeting, ghostly light. His eyes, chips of obsidian, leave the sign and lock onto yours, a silent acknowledgment of a shared, dangerous past. The air crackles with unspoken tension before he breaks the silence, his voice a low, gravelly current beneath the city's din. "Been a while."`,
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
            Elevate Your Storytelling in Seconds
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground">
            Transform simple actions into rich, engaging narratives with our character-aware AI. Spend less time
            writing, more time roleplaying.
          </p>
          <div className="flex flex-col sm:flex-row gap-4">
            <Button size="lg" className="w-full sm:w-auto">
              Enhance Your First Post Free
            </Button>
            <Button size="lg" variant="outline" className="w-full sm:w-auto bg-transparent">
              See Examples
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
