import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Check } from "lucide-react"

const tiers = [
  {
    name: "Hobbyist",
    price: "Free",
    description: "For the casual player looking to dip their toes in.",
    features: ["20 Pose Enhancements / month", "Minimal & Balanced Styles", "1 Character Profile", "Community Support"],
    cta: "Start for Free",
    variant: "outline",
  },
  {
    name: "Auteur",
    price: "$7",
    priceSuffix: "/ month",
    description: "For the dedicated storyteller who demands the best.",
    features: [
      "Unlimited Pose Enhancements",
      "All Enhancement Styles",
      "Unlimited Character Profiles",
      "Scene Context Analysis",
      "Priority Support",
    ],
    cta: "Go Premium",
    variant: "default",
  },
]

export function Pricing() {
  return (
    <section id="pricing" className="container py-12 lg:py-24 bg-muted/20 rounded-lg">
      <div className="text-center space-y-4 mb-12">
        <h2 className="text-3xl md:text-4xl font-bold">Find the Perfect Plan</h2>
        <p className="text-lg text-muted-foreground max-w-xl mx-auto">
          Start for free, and upgrade when you're ready to unlock your full storytelling potential.
        </p>
      </div>
      <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
        {tiers.map((tier) => (
          <Card key={tier.name} className={`flex flex-col ${tier.variant === "default" ? "border-primary" : ""}`}>
            <CardHeader>
              <CardTitle>{tier.name}</CardTitle>
              <CardDescription>{tier.description}</CardDescription>
            </CardHeader>
            <CardContent className="flex-grow">
              <div className="mb-6">
                <span className="text-4xl font-bold">{tier.price}</span>
                {tier.priceSuffix && <span className="text-muted-foreground">{tier.priceSuffix}</span>}
              </div>
              <ul className="space-y-3">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-2">
                    <Check className="w-5 h-5 text-green-500" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
            <CardFooter>
              <Button className="w-full" variant={tier.variant as "default" | "outline"}>
                {tier.cta}
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
    </section>
  )
}
