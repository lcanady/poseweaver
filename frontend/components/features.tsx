import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { BrainCircuit, Users, Sparkles, Eye, Wand2, Crown } from "lucide-react"

const features = [
  {
    icon: <Users className="w-8 h-8 text-primary" />,
    title: "Character Management",
    description:
      "Create and manage multiple characters with detailed profiles. Free (3), Basic (10), or Pro (unlimited) characters.",
  },
  {
    icon: <Wand2 className="w-8 h-8 text-primary" />,
    title: "AI Pose Enhancement",
    description:
      "Transform simple poses into rich, engaging narratives with character-aware AI that understands your character's voice and personality.",
  },
  {
    icon: <Eye className="w-8 h-8 text-primary" />,
    title: "Image Description Writer",
    description:
      "Upload images and generate detailed, vivid descriptions perfect for character profiles, scenes, and roleplay references.",
  },
  {
    icon: <Sparkles className="w-8 h-8 text-primary" />,
    title: "Advanced Customization",
    description:
      "Three enhancement styles, refinement tools, version history, and advanced settings for complete creative control.",
  },
  {
    icon: <BrainCircuit className="w-8 h-8 text-primary" />,
    title: "Smart AI Integration",
    description:
      "Powered by OpenRouter AI's multimodal models with built-in character control validation and MUSH roleplay etiquette.",
  },
  {
    icon: <Crown className="w-8 h-8 text-primary" />,
    title: "Flexible Pricing",
    description:
      "Start free (20/month), upgrade to Basic ($9.99 - 200/month) or Pro ($19.99 - 500/month). Buy recharge packs when needed.",
  },
]

export function Features() {
  return (
    <section id="features" className="container py-12 lg:py-24 bg-muted/20 rounded-lg">
      <div className="text-center space-y-4 mb-12">
        <h2 className="text-3xl md:text-4xl font-bold">Everything You Need for Better Roleplay</h2>
        <p className="text-lg text-muted-foreground max-w-3xl mx-auto">
          From character creation to AI-powered pose enhancement, we provide the tools to elevate your storytelling without replacing your creativity.
        </p>
      </div>
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
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
