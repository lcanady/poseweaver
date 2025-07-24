import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Check } from "lucide-react"

const tiers = [
  {
    name: "Free",
    price: "$0",
    priceSuffix: " forever",
    description: "Perfect for trying out the platform.",
    features: [
      "20 pose enhancements/month",
      "Up to 3 character profiles",
      "All enhancement styles",
      "Community support",
      "Buy recharge packs when needed"
    ],
    cta: "Start for Free",
    variant: "outline",
  },
  {
    name: "Basic",
    price: "$9.99",
    priceSuffix: "/month",
    description: "Great for regular roleplayers.",
    features: [
      "200 pose enhancements/month",
      "Up to 10 character profiles",
      "All enhancement styles",
      "Email support",
      "Buy recharge packs when needed"
    ],
    cta: "Choose Basic",
    variant: "outline",
  },
  {
    name: "Pro",
    price: "$19.99",
    priceSuffix: "/month",
    description: "For serious storytellers and power users.",
    features: [
      "500 pose enhancements/month",
      "Unlimited character profiles",
      "All enhancement styles",
      "Priority support",
      "Buy recharge packs when needed"
    ],
    cta: "Go Pro",
    variant: "default",
    popular: true,
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
      <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
        {tiers.map((tier) => (
          <Card key={tier.name} className={`flex flex-col relative ${tier.variant === "default" ? "border-primary" : ""} ${tier.popular ? "scale-105" : ""}`}>
            {tier.popular && (
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-primary text-primary-foreground px-3 py-1 rounded-full text-sm font-medium">
                  Most Popular
                </span>
              </div>
            )}
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
      
      {/* Recharge Packs Section */}
      <div className="mt-16 text-center">
        <h3 className="text-2xl font-bold mb-4">Need More Generations?</h3>
        <p className="text-muted-foreground mb-8 max-w-2xl mx-auto">
          Buy recharge packs to add extra pose generations to any plan. Perfect for busy roleplay sessions or special events.
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
          {[
            { count: 50, price: '$4.99', savings: '' },
            { count: 100, price: '$8.99', savings: '10% savings', popular: true },
            { count: 250, price: '$19.99', savings: '20% savings' },
            { count: 500, price: '$34.99', savings: '30% savings' },
          ].map((pack) => (
            <Card key={pack.count} className={`text-center ${pack.popular ? 'border-primary' : ''}`}>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold text-primary">{pack.count}</div>
                <div className="text-sm text-muted-foreground mb-2">generations</div>
                <div className="text-lg font-semibold">{pack.price}</div>
                {pack.savings && (
                  <div className="text-xs text-green-600 font-medium">{pack.savings}</div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
        <p className="text-sm text-muted-foreground mt-4">
          Recharge packs never expire and work with any subscription tier.
        </p>
      </div>
    </section>
  )
}
