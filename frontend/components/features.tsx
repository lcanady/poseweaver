import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { BrainCircuit, Users, Sparkles, Crown } from "lucide-react"

const features = [
  {
    icon: <Users className="w-8 h-8 text-primary" />,
    title: "Character Management",
    description:
      "Create and manage multiple characters with detailed profiles. Free (3), Basic (10), or Pro (unlimited) characters.",
  },
  {
    icon: <BrainCircuit className="w-8 h-8 text-primary" />,
    title: "Character-Aware AI",
    description:
      "Our AI understands your character's personality, background, and voice to generate authentic, in-character poses.",
  },
  {
    icon: <Sparkles className="w-8 h-8 text-primary" />,
    title: "Three Enhancement Styles",
    description:
      "Choose minimal polish, balanced enrichment, or elaborate narrative expansion. Perfect for any roleplay situation.",
  },
  {
    icon: <Crown className="w-8 h-8 text-primary" />,
    title: "Tiered Pricing",
    description:
      "Start free (20/month), upgrade to Basic (200/month) or Pro (500/month). Buy recharge packs when you need more.",
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
