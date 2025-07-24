"use client"

import { useState, useEffect } from "react"
import { useSearchParams } from "next/navigation"
import { useAuth } from "@/contexts/auth-context"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import Link from "next/link"
import { Icons } from "@/components/icons"
import { Crown } from "lucide-react"
import { getApiUrl } from '@/utils/api-utils';

export default function SignupPage() {
  const { signup, isLoading, user } = useAuth()
  const searchParams = useSearchParams()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [displayName, setDisplayName] = useState("")
  const [error, setError] = useState("")
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null)

  useEffect(() => {
    const plan = searchParams.get('plan')
    if (plan) {
      setSelectedPlan(plan)
    }
  }, [searchParams])

  const getPlanDetails = (plan: string) => {
    switch (plan) {
      case 'basic':
        return { name: 'Basic', price: '$9.99/month', features: '200 generations/month, 10 characters' }
      case 'pro':
        return { name: 'Pro', price: '$19.99/month', features: '500 generations/month, unlimited characters' }
      default:
        return null
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    if (!email || !password || !confirmPassword || !displayName) {
      setError("Please fill in all fields")
      return
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match")
      return
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters")
      return
    }

    try {
      await signup(email, password, displayName)
      
      // After successful signup, check if we need to redirect to Stripe
      // The auth context will have the user data available after signup
      if (selectedPlan && selectedPlan !== 'free') {
        // We'll use a small delay to ensure the auth context has updated
        // Then redirect to Stripe checkout
        setTimeout(async () => {
          // Get the current user from auth context or make an API call to get user ID
          await handlePaidPlanRedirect(selectedPlan)
        }, 500)
      }
      // If no plan selected or free plan, normal signup flow continues (redirect to dashboard)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signup failed")
    }
  }

  const handlePaidPlanRedirect = async (plan: string) => {
    try {
      // Get current user info from API since auth context might not be fully updated
      const userResponse = await fetch(`${getApiUrl()}/api/auth/me`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        credentials: 'include'
      })

      if (!userResponse.ok) {
        setError('Failed to get user information for checkout')
        return
      }

      const userData = await userResponse.json()
      if (userData.user && userData.user._id) {
        await redirectToStripeCheckout(userData.user._id, plan)
      } else {
        setError('User information not available for checkout')
      }
    } catch (error) {
      setError('Failed to process paid plan signup')
    }
  }

  const redirectToStripeCheckout = async (userId: string, plan: string) => {
    try {
      const response = await fetch(`${getApiUrl()}/api/purchase/create-checkout-session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          user_id: userId,
          type: 'subscription',
          plan: plan
        })
      })

      const data = await response.json()
      if (data.success && data.checkout_url) {
        // Redirect to Stripe checkout
        window.location.href = data.checkout_url
      } else {
        setError('Failed to create checkout session. Please try again.')
      }
    } catch (error) {
      setError('Failed to redirect to checkout. Please try again.')
    }
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle>Create an Account</CardTitle>
          <CardDescription>
            {selectedPlan ? (
              <>Get started with PoseWeaver and upgrade to {getPlanDetails(selectedPlan)?.name} after signup.</>
            ) : (
              <>Get started with your AI-powered storytelling assistant.</>
            )}
          </CardDescription>
          {selectedPlan && getPlanDetails(selectedPlan) && (
            <div className="mt-4 p-3 bg-primary/10 rounded-lg border border-primary/20">
              <div className="flex items-center justify-center gap-2 mb-2">
                <Crown className="h-4 w-4 text-primary" />
                <Badge variant="secondary" className="bg-primary/20 text-primary">
                  {getPlanDetails(selectedPlan)!.name} Plan Selected
                </Badge>
              </div>
              <div className="text-sm text-muted-foreground">
                <div className="font-medium">{getPlanDetails(selectedPlan)!.price}</div>
                <div>{getPlanDetails(selectedPlan)!.features}</div>
              </div>
            </div>
          )}
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <div className="space-y-2">
              <Label htmlFor="displayName">Display Name</Label>
              <Input
                id="displayName"
                type="text"
                placeholder="Your Name"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm-password">Confirm Password</Label>
              <Input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? "Creating Account..." : selectedPlan ? `Create Account & Choose ${getPlanDetails(selectedPlan)?.name}` : "Create Account"}
            </Button>
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-card px-2 text-muted-foreground">Or continue with</span>
              </div>
            </div>
            <Button variant="outline" className="w-full bg-transparent" type="button" disabled={isLoading}>
              <Icons.google className="mr-2 h-4 w-4" />
              Sign up with Google
            </Button>
          </CardContent>
        </form>
        <CardFooter className="justify-center">
          <p className="text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link href="/login" className="font-semibold text-primary hover:underline">
              Log in
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  )
}
