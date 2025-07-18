import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Check, Download } from "lucide-react"

const plans = [
  {
    name: "Hobbyist",
    price: "Free",
    description: "For the casual player.",
    features: ["20 Pose Enhancements / month", "Minimal & Balanced Styles", "1 Character Profile"],
    isCurrent: false,
  },
  {
    name: "Auteur",
    price: "$7",
    priceSuffix: "/ month",
    description: "For the dedicated storyteller.",
    features: ["Unlimited Pose Enhancements", "All Enhancement Styles", "Unlimited Character Profiles"],
    isCurrent: true,
  },
]

const billingHistory = [
  { invoice: "INV-2025-003", date: "July 1, 2025", amount: "$7.00", status: "Paid" },
  { invoice: "INV-2025-002", date: "June 1, 2025", amount: "$7.00", status: "Paid" },
  { invoice: "INV-2025-001", date: "May 1, 2025", amount: "$7.00", status: "Paid" },
]

export default function BillingPage() {
  const currentPlan = plans.find((plan) => plan.isCurrent)

  return (
    <div className="flex-1 p-4 md:p-8">
      <div className="mx-auto grid w-full max-w-6xl gap-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Billing & Subscriptions</h1>
          <p className="text-muted-foreground mt-1">Manage your plan, payment method, and view your history.</p>
        </div>

        <div className="grid gap-8 lg:grid-cols-5">
          <div className="lg:col-span-3">
            <Card>
              <CardHeader>
                <CardTitle>Your Plan</CardTitle>
                {currentPlan && (
                  <CardDescription>
                    You are currently on the <strong>{currentPlan.name}</strong> plan. Your plan renews on August 1,
                    2025.
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent className="grid gap-8">
                {plans.map((plan) => (
                  <div
                    key={plan.name}
                    className={`rounded-lg border p-6 ${plan.isCurrent ? "border-primary" : "border-border"}`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="text-lg font-semibold">{plan.name}</h3>
                        <p className="text-muted-foreground">{plan.description}</p>
                      </div>
                      {plan.isCurrent ? (
                        <Button variant="outline">Manage Subscription</Button>
                      ) : (
                        <Button>Switch to this Plan</Button>
                      )}
                    </div>
                    <div className="my-4">
                      <span className="text-3xl font-bold">{plan.price}</span>
                      {plan.priceSuffix && <span className="text-muted-foreground">{plan.priceSuffix}</span>}
                    </div>
                    <ul className="space-y-2 text-sm">
                      {plan.features.map((feature) => (
                        <li key={feature} className="flex items-center gap-2">
                          <Check className="h-4 w-4 text-green-500" />
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          <div className="lg:col-span-2 space-y-8">
            <Card>
              <CardHeader>
                <CardTitle>Billing History</CardTitle>
                <CardDescription>Download your past invoices from Stripe.</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Invoice</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead className="text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {billingHistory.map((item) => (
                      <TableRow key={item.invoice}>
                        <TableCell className="font-medium">{item.invoice}</TableCell>
                        <TableCell>{item.date}</TableCell>
                        <TableCell className="text-right">
                          <Button variant="ghost" size="icon">
                            <Download className="h-4 w-4" />
                            <span className="sr-only">Download Invoice</span>
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
