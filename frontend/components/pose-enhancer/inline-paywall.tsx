"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/use-toast";
import { Crown, Zap, Check, Star, Sparkles } from "lucide-react";
import { getApiUrl } from '@/utils/api-utils';

interface PricingPackage {
  generation_count: number;
  price: number;
  price_per_generation: number;
  savings?: string;
  popular?: boolean;
  best_value?: boolean;
  price_id?: string;
  product_id?: string;
}

interface PricingData {
  extra_generations: {
    packages: PricingPackage[];
  };
  subscriptions: {
    basic: {
      name: string;
      price: number;
      generations_included: number;
      character_limit: number;
      features: string[];
      price_id: string;
      product_id: string;
      popular?: boolean;
    };
    pro: {
      name: string;
      price: number;
      generations_included: number;
      character_limit: number;
      features: string[];
      price_id: string;
      product_id: string;
      popular?: boolean;
    };
  };
  free_tier: {
    generations_included: number;
    character_limit: number;
    features: string[];
  };
}

interface InlinePaywallProps {
  subscriptionStatus: string;
  onPurchaseComplete?: (generationsAdded: number) => void;
  userId?: string;
}

export function InlinePaywall({
  subscriptionStatus,
  onPurchaseComplete,
  userId
}: InlinePaywallProps) {
  const [pricingData, setPricingData] = useState<PricingData | null>(null);
  const [selectedPackage, setSelectedPackage] = useState<PricingPackage | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isPurchasing, setIsPurchasing] = useState(false);
  const { toast } = useToast();

  const isPremium = subscriptionStatus === 'premium';
  const isFree = subscriptionStatus === 'free' || subscriptionStatus === 'expired';

  useEffect(() => {
    fetchPricingData();
  }, []);

  const fetchPricingData = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(
        `${getApiUrl()}/api/purchase/pricing`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch pricing data');
      }

      const data = await response.json();
      if (data.success) {
        setPricingData(data);
        // Auto-select the best value package
        const bestValuePackage = data.extra_generations.packages.find((pkg: PricingPackage) => pkg.best_value);
        const defaultPackage = bestValuePackage || data.extra_generations.packages[1];
        if (defaultPackage) {
          setSelectedPackage(defaultPackage);
        }
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

  const handlePurchase = async () => {
    console.log('handlePurchase called with:', { selectedPackage, userId, userIdType: typeof userId });
    
    if (!selectedPackage || !userId) {
      toast({
        title: "Error",
        description: "Please select a package and ensure you're logged in",
        variant: "destructive"
      });
      return;
    }

    // Validate ObjectId format (24 character hex string)
    const objectIdRegex = /^[0-9a-fA-F]{24}$/;
    if (!objectIdRegex.test(userId)) {
      console.error('Invalid userId format:', userId);
      toast({
        title: "Error",
        description: "Invalid user ID format. Please try logging out and back in.",
        variant: "destructive"
      });
      return;
    }

    setIsPurchasing(true);
    try {
      const response = await fetch(
        `${getApiUrl()}/api/purchase/create-checkout-session`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_id: userId,
            type: 'recharge',
            generation_count: selectedPackage.generation_count,
            success_url: `${window.location.origin}/dashboard/pose-enhancer?success=true`,
            cancel_url: `${window.location.origin}/dashboard/pose-enhancer?canceled=true`,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        console.error('Backend error response:', errorData);
        throw new Error(errorData.error || `HTTP ${response.status}: Failed to create checkout session`);
      }

      const data = await response.json();
      console.log('Checkout session response:', data);
      
      if (data.success && data.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        throw new Error(data.error || 'No checkout URL received');
      }
    } catch (error) {
      console.error('Error creating checkout session:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
    } finally {
      setIsPurchasing(false);
    }
  };

  const handleUpgrade = async (tier: 'basic' | 'pro') => {
    console.log('handleUpgrade called with:', { tier, userId, userIdType: typeof userId });
    
    if (!userId) {
      toast({
        title: "Error",
        description: "Please ensure you're logged in",
        variant: "destructive"
      });
      return;
    }

    // Validate ObjectId format (24 character hex string)
    const objectIdRegex = /^[0-9a-fA-F]{24}$/;
    if (!objectIdRegex.test(userId)) {
      console.error('Invalid userId format:', userId);
      toast({
        title: "Error",
        description: "Invalid user ID format. Please try logging out and back in.",
        variant: "destructive"
      });
      return;
    }

    setIsPurchasing(true);
    try {
      const subscription = pricingData?.subscriptions?.[tier];
      if (!subscription) {
        throw new Error('Subscription data not available');
      }

      const response = await fetch(
        `${getApiUrl()}/api/purchase/create-checkout-session`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_id: userId,
            type: 'subscription',
            plan: tier,
            success_url: `${window.location.origin}/dashboard/pose-enhancer?success=true`,
            cancel_url: `${window.location.origin}/dashboard/pose-enhancer?canceled=true`,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        console.error('Backend error response:', errorData);
        throw new Error(errorData.error || `HTTP ${response.status}: Failed to create checkout session`);
      }

      const data = await response.json();
      console.log('Checkout session response:', data);
      
      if (data.success && data.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        throw new Error(data.error || 'No checkout URL received');
      }
    } catch (error) {
      console.error('Error creating checkout session:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
    } finally {
      setIsPurchasing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-[600px] flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="text-muted-foreground">Loading pricing information...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[600px] space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-6 py-12">
        <div className="flex justify-center">
          <div className="relative">
            <div className="absolute inset-0 bg-primary/20 blur-3xl rounded-full"></div>
            <div className="relative bg-gradient-to-br from-primary/10 to-secondary/10 p-6 rounded-full">
              <Crown className="h-16 w-16 text-primary" />
            </div>
          </div>
        </div>
        
        <div className="space-y-4">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            {isFree ? "Unlock Your Creative Potential" : "Boost Your Generation Limit"}
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            {isFree 
              ? "Upgrade to premium for unlimited pose generations and advanced features"
              : "Purchase additional pose generations to continue creating amazing content"
            }
          </p>
        </div>

        {isFree && (
          <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
            <Sparkles className="h-4 w-4 text-primary" />
            <span>Join thousands of creators already using our premium features</span>
          </div>
        )}
      </div>

      {/* Pricing Section */}
      {isFree && pricingData && (
        <div className="space-y-8">
          <div className="text-center">
            <h2 className="text-2xl font-semibold mb-2">Choose Your Plan</h2>
            <p className="text-muted-foreground">Unlock unlimited creativity with our subscription plans</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            {/* Basic Plan */}
            <Card className="relative border-2 hover:border-primary/50 transition-colors flex flex-col h-full">
              <CardHeader className="text-center pb-4">
                <CardTitle className="text-xl font-semibold">
                  {pricingData.subscriptions.basic.name}
                </CardTitle>
                <div className="space-y-2">
                  <div className="text-3xl font-bold">
                    ${pricingData.subscriptions.basic.price.toFixed(2)}
                    <span className="text-sm font-normal text-muted-foreground">/month</span>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="flex flex-col flex-grow">
                <ul className="space-y-3 flex-grow">
                  {pricingData.subscriptions.basic.features.map((feature, index) => (
                    <li key={index} className="flex items-center gap-3">
                      <Check className="h-5 w-5 text-accent flex-shrink-0" />
                      <span className="text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-6">
                  <Button 
                    onClick={() => handleUpgrade('basic')}
                    variant="outline"
                    size="lg"
                    className="w-full"
                    disabled={isPurchasing}
                  >
                    {isPurchasing ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
                    ) : (
                      <>
                        <Crown className="mr-2 h-4 w-4" />
                        Upgrade to Basic
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Pro Plan */}
            <Card className="relative border-2 border-primary bg-gradient-to-br from-primary/5 to-secondary/5 flex flex-col h-full">
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <Badge className="bg-primary text-primary-foreground px-4 py-1">
                  <Star className="h-3 w-3 mr-1" />
                  Most Popular
                </Badge>
              </div>
              <CardHeader className="text-center pb-4 pt-8">
                <CardTitle className="text-xl font-semibold">
                  {pricingData.subscriptions.pro.name}
                </CardTitle>
                <div className="space-y-2">
                  <div className="text-3xl font-bold">
                    ${pricingData.subscriptions.pro.price.toFixed(2)}
                    <span className="text-sm font-normal text-muted-foreground">/month</span>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="flex flex-col flex-grow">
                <ul className="space-y-3 flex-grow">
                  {pricingData.subscriptions.pro.features.map((feature, index) => (
                    <li key={index} className="flex items-center gap-3">
                      <Check className="h-5 w-5 text-accent flex-shrink-0" />
                      <span className="text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-6">
                  <Button 
                    onClick={() => handleUpgrade('pro')}
                    size="lg"
                    className="w-full bg-primary hover:bg-primary/90"
                    disabled={isPurchasing}
                  >
                    {isPurchasing ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    ) : (
                      <>
                        <Crown className="mr-2 h-4 w-4" />
                        Upgrade to Pro
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Recharge Packs for Premium Users */}
      {isPremium && pricingData && (
        <div className="space-y-8">
          <div className="text-center">
            <h2 className="text-2xl font-semibold mb-2">Recharge Packs</h2>
            <p className="text-muted-foreground">Purchase additional generations for this month</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 max-w-6xl mx-auto">
            {pricingData.extra_generations.packages.map((pkg, index) => (
              <Card 
                key={index}
                className={`cursor-pointer transition-all hover:scale-105 ${
                  selectedPackage?.generation_count === pkg.generation_count
                    ? 'border-primary bg-primary/5'
                    : 'hover:border-primary/50'
                } ${pkg.best_value ? 'border-2 border-accent' : ''}`}
                onClick={() => setSelectedPackage(pkg)}
              >
                {pkg.best_value && (
                  <div className="absolute -top-2 left-1/2 transform -translate-x-1/2">
                    <Badge className="bg-accent text-accent-foreground">
                      <Star className="h-3 w-3 mr-1" />
                      Best Value
                    </Badge>
                  </div>
                )}
                <CardHeader className="text-center pb-2 pt-6">
                  <CardTitle className="text-lg">
                    {pkg.generation_count} Generations
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-center space-y-2">
                  <div className="text-2xl font-bold">
                    ${pkg.price.toFixed(2)}
                  </div>
                  <p className="text-sm text-muted-foreground">
                    ${pkg.price_per_generation.toFixed(2)} per generation
                  </p>
                  {pkg.savings && pkg.savings !== '0%' && (
                    <Badge variant="outline" className="text-accent border-accent">
                      Save {pkg.savings}
                    </Badge>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>

          {selectedPackage && (
            <div className="text-center">
              <Button 
                onClick={handlePurchase}
                size="lg"
                className="bg-primary hover:bg-primary/90 px-8"
                disabled={isPurchasing}
              >
                {isPurchasing ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                ) : (
                  <Zap className="h-4 w-4 mr-2" />
                )}
                Purchase {selectedPackage.generation_count} Generations for ${selectedPackage.price.toFixed(2)}
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Current Plan Info */}
      <div className="bg-card/50 rounded-lg p-6 max-w-2xl mx-auto">
        <h3 className="font-semibold mb-3">Current Plan: Free Tier</h3>
        <ul className="space-y-2 text-sm">
          {pricingData?.free_tier?.features?.map((feature, index) => (
            <li key={index} className="flex items-center gap-2">
              <Check className="h-4 w-4 text-accent" />
              {feature}
            </li>
          )) || (
            <li className="flex items-center gap-2">
              <Check className="h-4 w-4 text-accent" />
              20 pose generations per month
            </li>
          )}
        </ul>
      </div>
    </div>
  );
}
