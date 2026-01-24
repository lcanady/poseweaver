"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Crown, Zap, AlertTriangle } from "lucide-react";

interface UsageInfo {
  available_generations: number;
  monthly_limit: number;
  current_usage: number;
  extra_generations: number;
  credits: number;
  subscription_status: string;
}

interface UsageDisplayProps {
  usageInfo?: UsageInfo;
  onUpgrade?: () => void;
  onPurchaseExtra?: () => void;
  className?: string;
}

export function UsageDisplay({ 
  usageInfo, 
  onUpgrade, 
  onPurchaseExtra, 
  className = "" 
}: UsageDisplayProps) {
  // Show loading state if no usage info is available yet
  if (!usageInfo) {
    return (
      <Card className={`${className}`}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium">Credits</CardTitle>
            <Badge variant="secondary">
              Loading...
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Loading usage info...</span>
            </div>
            <Progress value={0} className="h-2" />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Please wait</span>
              <span>Free</span>
            </div>
          </div>
          
          <div className="pt-2 border-t">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>Subscription</span>
              <span className="capitalize font-medium">Loading...</span>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const {
    available_generations,
    monthly_limit,
    current_usage,
    extra_generations,
    credits,
    subscription_status
  } = usageInfo;

  const isUnlimited = monthly_limit === -1;
  const isPremium = subscription_status === 'premium';
  const isFree = subscription_status === 'free' || subscription_status === 'expired';
  const isLowOnGenerations = !isUnlimited && available_generations <= 5;
  const isOutOfGenerations = !isUnlimited && available_generations === 0;

  // Calculate usage percentage for progress bar
  const usagePercentage = isUnlimited ? 0 : Math.min((current_usage / monthly_limit) * 100, 100);

  const getStatusColor = () => {
    if (isUnlimited) return "bg-purple-500";
    if (isOutOfGenerations) return "bg-red-500";
    if (isLowOnGenerations) return "bg-amber-500";
    return "bg-green-500";
  };

  const getStatusText = () => {
    if (isUnlimited) return "Unlimited";
    if (isOutOfGenerations) return "Limit Reached";
    if (isLowOnGenerations) return "Running Low";
    return "Available";
  };

  return (
    <Card className={`${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">Credits</CardTitle>
          <Badge 
            variant={isOutOfGenerations ? "destructive" : isLowOnGenerations ? "secondary" : "default"}
            className={`${getStatusColor()} text-white`}
          >
            {getStatusText()}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Usage Stats */}
        <div className="space-y-2">
          {isUnlimited ? (
            <div className="flex items-center gap-2">
              <Crown className="h-4 w-4 text-purple-500" />
              <span className="text-sm font-medium">Unlimited credits</span>
            </div>
          ) : (
            <>
              <div className="flex justify-between text-sm">
                <span>Credit Balance</span>
                <span className="font-bold text-lg text-primary">
                  {credits}
                </span>
              </div>
              <div className="pt-2 text-xs text-muted-foreground flex justify-between">
                <span>This month&apos;s usage: {current_usage}</span>
                <span>Limit: {monthly_limit}</span>
              </div>
              <Progress value={usagePercentage} className="h-2" />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Total available: {available_generations + credits}</span>
                <span>{subscription_status === 'premium' ? 'Premium' : 'Free'}</span>
              </div>
            </>
          )}
        </div>

        {/* Extra Generations Display */}
        {credits > 0 && (
          <div className="flex items-center gap-2 p-2 bg-blue-50 rounded-md">
            <Zap className="h-4 w-4 text-blue-500" />
            <span className="text-sm text-blue-700">
              {credits} credits available
            </span>
          </div>
        )}

        {/* Action Buttons */}
        <div className="space-y-2">
          {isOutOfGenerations && isFree && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 p-2 bg-amber-50 rounded-md">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                <span className="text-sm text-amber-700">
                  Monthly limit reached. Upgrade for more monthly credits.
                </span>
              </div>
              {onUpgrade && (
                <Button 
                  onClick={onUpgrade} 
                  className="w-full bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600"
                  size="sm"
                >
                  <Crown className="h-4 w-4 mr-2" />
                  Upgrade to Premium
                </Button>
              )}
            </div>
          )}

          {isOutOfGenerations && isPremium && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 p-2 bg-blue-50 rounded-md">
                <Zap className="h-4 w-4 text-blue-500" />
                <span className="text-sm text-blue-700">
                  Monthly limit reached. Purchase additional credits.
                </span>
              </div>
              {onPurchaseExtra && (
                <Button 
                  onClick={onPurchaseExtra} 
                  className="w-full"
                  size="sm"
                  variant="outline"
                >
                  <Zap className="h-4 w-4 mr-2" />
                  Buy More Credits
                </Button>
              )}
            </div>
          )}

          {isLowOnGenerations && !isOutOfGenerations && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 p-2 bg-amber-50 rounded-md">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                <span className="text-sm text-amber-700">
                  Running low on credits this month.
                </span>
              </div>
              <div className="flex gap-2">
                {isFree && onUpgrade && (
                  <Button 
                    onClick={onUpgrade} 
                    className="flex-1 bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600"
                    size="sm"
                  >
                    <Crown className="h-4 w-4 mr-1" />
                    Upgrade
                  </Button>
                )}
                {isPremium && onPurchaseExtra && (
                  <Button 
                    onClick={onPurchaseExtra} 
                    className="flex-1"
                    size="sm"
                    variant="outline"
                  >
                    <Zap className="h-4 w-4 mr-1" />
                    Buy More
                  </Button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Subscription Status */}
        <div className="pt-2 border-t">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Subscription</span>
            <span className="capitalize font-medium">
              {subscription_status}
              {isPremium && <Crown className="inline h-3 w-3 ml-1 text-purple-500" />}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
