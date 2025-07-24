"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import Link from "next/link"
import { useState, useEffect } from "react"

import { useAuth } from "@/contexts/auth-context"
import { formatDistanceToNow } from "date-fns"
import { getApiUrl } from '@/utils/api-utils';
import { 
  Users, 
  Clock, 
  TrendingUp, 
  Zap,
  ArrowUpRight,
  Plus,
  User,
  Eye,
  Sparkles,
  Settings,
  CreditCard,
  Crown,
  Star,
  Wand2,
  Palette,
  BarChart3,
  UserPlus,
  Lock
} from "lucide-react"

interface DashboardStats {
  totalCharacters: number
  recentActivity: string
  subscriptionStatus: string
}

interface AITool {
  title: string
  description: string
  href: string
  icon: React.ReactNode
  status: "available" | "premium" | "coming-soon"
  badge?: string
}

interface ManagementTool {
  title: string
  description: string
  href: string
  icon: React.ReactNode
  count?: number
}

export default function DashboardPage() {
  const { user } = useAuth()
  const [stats, setStats] = useState<DashboardStats>({
    totalCharacters: 0,
    recentActivity: "Never",
    subscriptionStatus: "free"
  })
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const token = localStorage.getItem('access_token')
        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
        }
        
        if (token) {
          headers['Authorization'] = `Bearer ${token}`
        }

        // Note: Scenes functionality has been removed from the product

        // Fetch characters data
        try {
          const controller = new AbortController()
          const timeoutId = setTimeout(() => controller.abort(), 60000)
          
          const charactersResponse = await fetch(`${getApiUrl()}/api/characters/mgmt`, {
            headers,
            signal: controller.signal
          })
          
          clearTimeout(timeoutId)

          if (charactersResponse.ok) {
            const charactersData = await charactersResponse.json()
            if (charactersData.success && charactersData.data) {
              setStats(prev => ({
                ...prev,
                totalCharacters: charactersData.data.length
              }))
            }
          }
        } catch (error) {
          console.error('Failed to fetch characters:', error)
        }

        // Fetch usage/subscription status
        try {
          if (user?._id) {
            const usageResponse = await fetch(
              `${getApiUrl()}/api/purchase/usage-status?user_id=${user._id}`,
              {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include'
              }
            )
            
            if (usageResponse.ok) {
              const usageData = await usageResponse.json()
              if (usageData.success && usageData.usage_info) {
                setStats(prev => ({
                  ...prev,
                  subscriptionStatus: usageData.usage_info.subscription_status || 'free'
                }))
              }
            }
          }
        } catch (error) {
          console.error('Failed to fetch usage status:', error)
        }

      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchDashboardData()
  }, [user])

  const aiTools: AITool[] = [
    {
      title: "Pose Enhancer",
      description: "Transform your roleplay poses with AI-powered enhancement and refinement",
      href: "/dashboard/pose-enhancer",
      icon: <Zap className="h-5 w-5" />,
      status: "available",
      badge: "Popular"
    },
    {
      title: "Description Writer",
      description: "Generate detailed character descriptions from images using advanced AI vision",
      href: "/dashboard/description-writer",
      icon: <Eye className="h-5 w-5" />,
      status: "premium",
      badge: "New"
    },
    {
      title: "Scene Generator",
      description: "Create immersive roleplay scenes and environments with AI assistance",
      href: "#",
      icon: <Sparkles className="h-5 w-5" />,
      status: "coming-soon",
      badge: "Soon"
    },
    {
      title: "Style Mimic",
      description: "AI learns your writing style and applies it to enhanced poses for authentic voice",
      href: "#",
      icon: <Palette className="h-5 w-5" />,
      status: "coming-soon",
      badge: "Pro Only"
    },
    {
      title: "Writing Analytics",
      description: "Track your writing evolution, style metrics, and character usage patterns",
      href: "#",
      icon: <BarChart3 className="h-5 w-5" />,
      status: "coming-soon",
      badge: "Pro Only"
    },
    {
      title: "Scene Collaboration",
      description: "Real-time co-writing tools and shared character libraries for group roleplay",
      href: "#",
      icon: <UserPlus className="h-5 w-5" />,
      status: "coming-soon",
      badge: "Pro Only"
    }
  ]

  const managementTools: ManagementTool[] = [
    {
      title: "Characters",
      description: "Manage your character profiles and backstories",
      href: "/dashboard/characters",
      icon: <Users className="h-5 w-5" />,
      count: stats.totalCharacters
    },
    {
      title: "Profile",
      description: "Update your account settings and preferences",
      href: "/dashboard/profile",
      icon: <User className="h-5 w-5" />
    },
    {
      title: "Billing",
      description: "Manage your subscription and payment methods",
      href: "/dashboard/billing",
      icon: <CreditCard className="h-5 w-5" />
    }
  ]

  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return "Good morning"
    if (hour < 17) return "Good afternoon"
    return "Good evening"
  }

  const getSubscriptionBadge = () => {
    switch (stats.subscriptionStatus) {
      case 'basic':
        return <Badge variant="secondary" className="ml-2">Basic</Badge>
      case 'pro':
        return <Badge variant="default" className="ml-2">Pro</Badge>
      case 'premium':
        return <Badge variant="default" className="ml-2 bg-gradient-to-r from-purple-500 to-pink-500">Premium</Badge>
      case 'admin':
        return <Badge variant="default" className="ml-2 bg-gradient-to-r from-yellow-400 to-orange-500"><Crown className="h-3 w-3 mr-1" />Admin</Badge>
      default:
        return <Badge variant="outline" className="ml-2">Free</Badge>
    }
  }

  return (
    <div className="flex-1 p-4 md:p-8">
      <div className="mx-auto grid w-full max-w-7xl gap-8">
        {/* Welcome Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center">
              {getGreeting()}, {user?.display_name || 'Storyteller'}
              {getSubscriptionBadge()}
            </h1>
            <p className="text-muted-foreground mt-1">
              Ready to craft some amazing stories today?
            </p>
          </div>
          {stats.subscriptionStatus === 'free' && (
            <Button asChild variant="default" className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600">
              <Link href="/dashboard/billing">
                <Crown className="h-4 w-4 mr-2" />
                Upgrade
              </Link>
            </Button>
          )}
        </div>

        {/* Stats Overview */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Characters</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalCharacters}</div>
              <p className="text-xs text-muted-foreground">
                {stats.totalCharacters === 0 ? "Create your first character" : "Ready for adventure"}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">AI Tools</CardTitle>
              <Sparkles className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.subscriptionStatus === 'free' ? '1' : '2'}</div>
              <p className="text-xs text-muted-foreground">
                {stats.subscriptionStatus === 'free' ? 'Available tools' : 'Premium tools unlocked'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Subscription</CardTitle>
              <Crown className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold capitalize">{stats.subscriptionStatus}</div>
              <p className="text-xs text-muted-foreground">
                {stats.subscriptionStatus === 'free' ? 'Upgrade for more features' : 'All features unlocked'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Status</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats.totalCharacters > 0 ? "Active" : "Getting Started"}
              </div>
              <p className="text-xs text-muted-foreground">
                {stats.totalCharacters > 0 ? "All systems ready" : "Set up your first character"}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* AI Tools Showcase */}
        <div>
          <div className="flex items-center gap-2 mb-6">
            <Sparkles className="h-5 w-5 text-primary" />
            <h2 className="text-2xl font-bold">AI-Powered Tools</h2>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-2">
            {aiTools.map((tool, index) => {
              const isDisabled = tool.status === 'coming-soon' || (tool.status === 'premium' && stats.subscriptionStatus === 'free')
              
              return (
                <Card key={index} className={`group transition-all duration-200 ${
                  isDisabled 
                    ? 'opacity-60 cursor-not-allowed' 
                    : 'hover:shadow-lg hover:scale-[1.02] cursor-pointer'
                }`}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${
                          tool.status === 'available' ? 'bg-primary/10 text-primary' :
                          tool.status === 'premium' ? 'bg-purple-500/10 text-purple-500' :
                          'bg-muted text-muted-foreground'
                        }`}>
                          {tool.icon}
                        </div>
                        <div>
                          <CardTitle className="text-lg flex items-center gap-2">
                            {tool.title}
                            {tool.status === 'premium' && <Crown className="h-4 w-4 text-purple-500" />}
                          </CardTitle>
                        </div>
                      </div>
                      {tool.badge && (
                        <Badge variant={tool.status === 'available' ? 'default' : tool.status === 'premium' ? 'secondary' : 'outline'}>
                          {tool.badge}
                        </Badge>
                      )}
                    </div>
                    <CardDescription className="text-sm leading-relaxed">
                      {tool.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {tool.status === 'coming-soon' ? (
                      <Button disabled className="w-full">
                        Coming Soon
                      </Button>
                    ) : tool.status === 'premium' && stats.subscriptionStatus === 'free' ? (
                      <Button asChild variant="outline" className="w-full">
                        <Link href="/dashboard/billing">
                          <Crown className="h-4 w-4 mr-2" />
                          Upgrade to Access
                        </Link>
                      </Button>
                    ) : (
                      <Button asChild className="w-full group-hover:bg-primary/90">
                        <Link href={tool.href}>
                          Launch Tool
                          <ArrowUpRight className="h-4 w-4 ml-2" />
                        </Link>
                      </Button>
                    )}
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>

        {/* Management Tools */}
        <div>
          <div className="flex items-center gap-2 mb-6">
            <Settings className="h-5 w-5 text-primary" />
            <h2 className="text-2xl font-bold">Management</h2>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {managementTools.map((tool, index) => (
              <Card key={index} className="group hover:shadow-md transition-all duration-200 hover:scale-[1.02]">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-muted text-muted-foreground group-hover:bg-primary/10 group-hover:text-primary transition-colors">
                      {tool.icon}
                    </div>
                    <div>
                      <CardTitle className="text-lg flex items-center gap-2">
                        {tool.title}
                        {tool.count !== undefined && (
                          <Badge variant="secondary">{tool.count}</Badge>
                        )}
                      </CardTitle>
                    </div>
                  </div>
                  <CardDescription>{tool.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button asChild variant="outline" className="w-full">
                    <Link href={tool.href}>
                      Open
                      <ArrowUpRight className="h-4 w-4 ml-2" />
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Getting Started Guide - Show for new users */}
        {stats.totalCharacters === 0 && (
          <Card className="border-primary/20 bg-primary/5">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Star className="h-5 w-5 text-primary" />
                <CardTitle>Getting Started</CardTitle>
              </div>
              <CardDescription>
                Follow these steps to begin your storytelling journey
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start gap-3">
                <Badge variant="outline" className="mt-1">1</Badge>
                <div>
                  <p className="font-medium">Create your first character</p>
                  <p className="text-sm text-muted-foreground mb-2">
                    Start by building a character profile to bring your stories to life
                  </p>
                  <Button asChild size="sm" variant="outline">
                    <Link href="/dashboard/characters">
                      <Plus className="h-4 w-4 mr-2" />
                      Create Character
                    </Link>
                  </Button>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Badge variant="outline" className="mt-1">2</Badge>
                <div>
                  <p className="font-medium">Try the Pose Enhancer</p>
                  <p className="text-sm text-muted-foreground mb-2">
                    Let AI help enhance your roleplay poses and bring depth to your storytelling
                  </p>
                  <Button asChild size="sm" variant="outline">
                    <Link href="/dashboard/pose-enhancer">
                      <Zap className="h-4 w-4 mr-2" />
                      Launch Tool
                    </Link>
                  </Button>
                </div>
              </div>

            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
