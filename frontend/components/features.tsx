import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { BrainCircuit, ScanText, Sparkles, Users } from "lucide-react"

const features = [
  {
    icon: <BrainCircuit className="w-8 h-8 text-primary" />,
    title: "Character-Aware AI",
    description:
      "Upload your character's background and personality. Our AI maintains their unique voice in every enhanced post.",
  },
  {
    icon: <ScanText className="w-8 h-8 text-primary" />,
    title: "Platform Agnostic",
    description:
      "Copy-paste text from Discord, forums, or any roleplay platform. We automatically identify your posts and preserve the scene's context.",
  },
  {
    icon: <Sparkles className="w-8 h-8 text-primary" />,
    title: "Intelligent Enhancement",
    description:
      "Choose from three styles: a quick polish, a balanced enrichment, or a full narrative expansion for any situation.",
  },
  {
    icon: <Users className="w-8 h-8 text-primary" />,
    title: "Scene Context Analysis",
    description:
      "Our AI analyzes the ongoing scene to identify response hooks, emotional tone, and suggest natural character reactions.",
  },
]

export function Features() {
  return (
    <section id="features" className="container py-12 lg:py-24 bg-muted/20 rounded-lg">
      <div className="text-center space-y-4 mb-12">
        <h2 className="text-3xl md:text-4xl font-bold">A Tool for Serious Roleplayers</h2>
        <p className="text-lg text-muted-foreground max-w-3xl mx-auto">
          We built SceneForge to enhance your creativity, not replace it. Here's how we help you tell better stories.
        </p>
      </div>
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
        {features.map((feature, index) => (
          <Card
            key={index}
            className="bg-card/50 border-border/50 hover:border-primary/50 hover:bg-card transition-all"
          >
            <CardHeader>
              <div className="mb-4">{feature.icon}</div>
              <CardTitle>{feature.title}</CardTitle>
              <CardDescription className="pt-2">{feature.description}</CardDescription>
            </CardHeader>
          </Card>
        ))}
      </div>
    </section>
  )
}
