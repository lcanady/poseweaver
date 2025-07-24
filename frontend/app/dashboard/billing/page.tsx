"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useToast } from "@/components/ui/use-toast";
import { Check, Download, Crown, Zap } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"

interface PricingData {
  success: boolean;
  subscriptions: {
    basic: {
      name: string;
      price: number;
      generations_included: number;
      features: string[];
      price_id: string;
      product_id: string;
    };
    pro: {
      name: string;
      price: number;
      generations_included: number;
      features: string[];
      price_id: string;
      product_id: string;
    };
  };
  extra_generations: {
    packages: Array<{
      generation_count: number;
      price: number;
      price_per_generation: number;
      price_id: string;
      product_id: string;
      savings?: string;
    }>;
  };
  free_tier: {
    generations_included: number;
    features: string[];
  };
}

export default function BillingPage() {
  const [pricingData, setPricingData] = useState<PricingData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isPurchasing, setIsPurchasing] = useState(false);
  const [usageInfo, setUsageInfo] = useState<any>(null);
  const { toast } = useToast();
  const { user } = useAuth();

  // Get current subscription status from usage info
  const currentSubscription = usageInfo?.subscription_status || 'free';

  // Fetch pricing data and usage info on component mount
  useEffect(() => {
    fetchPricingData();
    fetchUsageInfo();
  }, [user?._id]);

  const fetchPricingData = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/purchase/pricing`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch pricing data');
      }

      const data = await response.json();
      if (data.success) {
        setPricingData(data);
      }
    } catch (error) {
      console.error('Error fetching pricing:', error);
      toast({
        title: "Error",
        description: "Failed to load pricing information",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const fetchUsageInfo = async () => {
    if (!user?._id) return;
    
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/purchase/usage-status?user_id=${user._id}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          },
          credentials: 'include'
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        console.log('Usage info response:', data); // Debug log
        if (data.success && data.usage_info) {
          setUsageInfo(data.usage_info);
        }
      } else {
        console.error('Failed to fetch usage info:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Error fetching usage info:', error);
    }
  };

  const handleSubscriptionUpgrade = async (tier: 'basic' | 'pro') => {
    setIsPurchasing(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/purchase/create-checkout-session`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            type: 'subscription',
            plan: tier,
            user_id: user?._id || user?.id
          })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to create checkout session');
      }

      const data = await response.json();
      if (data.success && data.checkout_url) {
        window.location.href = data.checkout_url;
      }
    } catch (error) {
      console.error('Upgrade error:', error);
      toast({
        title: "Upgrade Failed",
        description: error instanceof Error ? error.message : "An unexpected error occurred",
        variant: "destructive"
      });
    } finally {
      setIsPurchasing(false);
    }
  };

  const handleRechargePackPurchase = async (generationCount: number) => {
    setIsPurchasing(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/purchase/create-checkout-session`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            type: 'recharge',
            generation_count: generationCount,
            user_id: user?._id || user?.id
          })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to create checkout session');
      }

      const data = await response.json();
      if (data.success && data.checkout_url) {
        window.location.href = data.checkout_url;
      }
    } catch (error) {
      console.error('Purchase error:', error);
      toast({
        title: "Purchase Failed",
        description: error instanceof Error ? error.message : "An unexpected error occurred",
        variant: "destructive"
      });
    } finally {
      setIsPurchasing(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (!user?._id) {
      toast({
        title: "Error",
        description: "Please log in to manage your subscription.",
        variant: "destructive"
      });
      return;
    }

    setIsPurchasing(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/purchase/customer-portal`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_id: user._id,
            return_url: `${window.location.origin}/dashboard/billing`
          })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to create customer portal session');
      }

      const data = await response.json();
      if (data.success && data.portal_url) {
        // Redirect to Stripe customer portal
        window.location.href = data.portal_url;
      } else {
        throw new Error('No portal URL received');
      }
    } catch (error) {
      console.error('Customer portal error:', error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to open subscription management.",
        variant: "destructive"
      });
    } finally {
      setIsPurchasing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 p-4 md:p-8">
        <div className="mx-auto grid w-full max-w-6xl gap-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!pricingData) {
    return (
      <div className="flex-1 p-4 md:p-8">
        <div className="mx-auto grid w-full max-w-6xl gap-8">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-red-600">Error Loading Billing Information</h1>
            <p className="text-muted-foreground mt-2">Please try refreshing the page.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-4 md:p-8">
      <div className="mx-auto grid w-full max-w-6xl gap-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Billing & Subscriptions</h1>
          <p className="text-muted-foreground mt-1">Manage your plan, payment method, and view your history.</p>
        </div>

        <div className="grid gap-8">
          {/* Current Plan Section */}
          <Card>
            <CardHeader>
              <CardTitle>Your Plan</CardTitle>
              <CardDescription>
                You are currently on the <strong>
                  {currentSubscription === 'free' ? 'Free' : 
                   currentSubscription === 'basic' ? 'Basic' : 
                   currentSubscription === 'pro' ? 'Pro' : 
                   currentSubscription === 'premium' ? 'Premium (Legacy)' : 
                   currentSubscription === 'admin' ? 'Admin' : 'Free'}
                </strong> plan.
                {currentSubscription !== 'free' && ' Your plan renews on the 1st of next month.'}
                {usageInfo && (
                  <div className="mt-2 text-sm">
                    <strong>Usage this month:</strong> {usageInfo.current_usage || 0} / {usageInfo.monthly_limit === -1 ? 'Unlimited' : usageInfo.monthly_limit || 0} generations
                    {usageInfo.extra_generations > 0 && (
                      <span className="ml-2 text-green-600">+ {usageInfo.extra_generations} extra</span>
                    )}
                  </div>
                )}
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-6 md:grid-cols-3">
              {/* Free Plan */}
              <div className={`rounded-lg border p-6 flex flex-col min-h-[400px] ${currentSubscription === 'free' ? "border-primary bg-primary/5" : "border-border"}`}>
                <div className="flex flex-col flex-1 justify-between">
                  <div>
                    <h3 className="text-lg font-semibold">Free</h3>
                    <p className="text-muted-foreground text-sm">Perfect for getting started.</p>
                  </div>
                  <div>
                    <span className="text-2xl font-bold">Free</span>
                  </div>
                  <ul className="space-y-2 text-sm flex-1">
                    {pricingData?.free_tier?.features?.map((feature, index) => (
                      <li key={index} className="flex items-center gap-2">
                        <Check className="h-4 w-4 text-green-500" />
                        <span>{feature}</span>
                      </li>
                    )) || []}
                  </ul>
                  <div className="pt-4">
                    {currentSubscription === 'free' ? (
                      <Button variant="outline" className="w-full">Current Plan</Button>
                    ) : currentSubscription === 'admin' ? (
                      <Button variant="outline" className="w-full" disabled>Admin Access</Button>
                    ) : (
                      <Button 
                        variant="outline" 
                        className="w-full text-red-600 border-red-200 hover:bg-red-50" 
                        onClick={handleCancelSubscription}
                      >
                        Cancel Subscription
                      </Button>
                    )}
                  </div>
                </div>
              </div>

              {/* Basic Plan */}
              <div className={`rounded-lg border p-6 flex flex-col min-h-[400px] ${currentSubscription === 'basic' ? "border-primary bg-primary/5" : "border-border"}`}>
                <div className="flex flex-col flex-1 justify-between">
                  <div>
                    <h3 className="text-lg font-semibold">Basic</h3>
                    <p className="text-muted-foreground text-sm">For regular roleplayers.</p>
                  </div>
                  <div>
                    <span className="text-2xl font-bold">${pricingData?.subscriptions?.basic?.price?.toFixed(2) || '0.00'}</span>
                    <span className="text-muted-foreground">/ month</span>
                  </div>
                  <ul className="space-y-2 text-sm flex-1">
                    {pricingData?.subscriptions?.basic?.features?.map((feature: string, index: number) => (
                      <li key={index} className="flex items-center gap-2">
                        <Check className="h-4 w-4 text-green-500" />
                        <span>{feature}</span>
                      </li>
                    )) || []}
                  </ul>
                  <div className="pt-4">
                    {currentSubscription === 'basic' ? (
                      <Button variant="outline" className="w-full">Current Plan</Button>
                    ) : currentSubscription === 'admin' ? (
                      <Button variant="outline" className="w-full" disabled>
                        Admin Access
                      </Button>
                    ) : (
                      <Button 
                        className="w-full" 
                        onClick={() => handleSubscriptionUpgrade('basic')}
                        disabled={isPurchasing}
                      >
                        {isPurchasing ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        ) : (
                          <>Switch to Basic</>
                        )}
                      </Button>
                    )}
                  </div>
                </div>
              </div>

              {/* Pro Plan */}
              <div className={`rounded-lg border p-6 flex flex-col min-h-[400px] ${(currentSubscription === 'pro' || currentSubscription === 'premium') ? "border-primary bg-primary/5" : "border-border"}`}>
                <div className="flex flex-col flex-1 justify-between">
                  <div>
                    <h3 className="text-lg font-semibold">Pro</h3>
                    <p className="text-muted-foreground text-sm">For dedicated storytellers.</p>
                  </div>
                  <div>
                    <span className="text-2xl font-bold">${pricingData?.subscriptions?.pro?.price?.toFixed(2) || '0.00'}</span>
                    <span className="text-muted-foreground">/ month</span>
                  </div>
                  <ul className="space-y-2 text-sm flex-1">
                    {pricingData?.subscriptions?.pro?.features?.map((feature: string, index: number) => (
                      <li key={index} className="flex items-center gap-2">
                        <Check className="h-4 w-4 text-green-500" />
                        <span>{feature}</span>
                      </li>
                    )) || []}
                  </ul>
                  <div className="pt-4">
                    {(currentSubscription === 'pro' || currentSubscription === 'premium') ? (
                      <Button variant="outline" className="w-full">
                        {currentSubscription === 'premium' ? 'Current Plan (Legacy)' : 'Current Plan'}
                      </Button>
                    ) : currentSubscription === 'admin' ? (
                      <Button variant="outline" className="w-full" disabled>
                        Admin Access
                      </Button>
                    ) : (
                      <Button 
                        className="w-full bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600" 
                        onClick={() => handleSubscriptionUpgrade('pro')}
                        disabled={isPurchasing}
                      >
                        {isPurchasing ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        ) : (
                          <>
                            <Crown className="h-4 w-4 mr-2" />
                            Switch to Pro
                          </>
                        )}
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Recharge Packs Section */}
          <Card>
            <CardHeader>
              <CardTitle>Recharge Packs</CardTitle>
              <CardDescription>
                Need more generations? Purchase additional pose generations that don't expire monthly.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {(pricingData?.extra_generations?.packages || []).map((pack, index) => (
                  <div key={index} className="rounded-lg border p-4 flex flex-col min-h-[200px]">
                    <div className="flex flex-col flex-1 text-center justify-between">
                      <div className="space-y-2">
                        <div>
                          <div className="text-2xl font-bold">{pack?.generation_count || 0}</div>
                          <div className="text-sm text-muted-foreground">generations</div>
                        </div>
                        <div className="text-lg font-semibold">${pack?.price?.toFixed(2) || '0.00'}</div>
                        {pack?.savings && pack.savings !== '0%' && (
                          <div className="text-xs text-green-600 font-medium">Save {pack.savings}</div>
                        )}
                      </div>
                      <div className="pt-2">
                        <Button 
                          className="w-full" 
                          size="sm"
                          onClick={() => handleRechargePackPurchase(pack?.generation_count || 0)}
                          disabled={isPurchasing}
                        >
                          {isPurchasing ? (
                            <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                          ) : (
                            <>
                              <Zap className="h-3 w-3 mr-1" />
                              Purchase
                            </>
                          )}
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Billing History */}
          <Card>
            <CardHeader>
              <CardTitle>Billing History</CardTitle>
              <CardDescription>Download your past invoices and view transaction history.</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Invoice</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                      No billing history available yet. Your transaction history will appear here after your first purchase.
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
