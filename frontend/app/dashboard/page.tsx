"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import Link from "next/link"
import { useState, useEffect } from "react"

import { useAuth } from "@/contexts/auth-context"
import { formatDistanceToNow } from "date-fns"
import { 
  Users, 
  Clock, 
  TrendingUp, 
  Zap,
  ArrowUpRight,
  Plus,
  User
} from "lucide-react"

interface DashboardStats {
  totalCharacters: number
  recentActivity: string
}

interface QuickAction {
  title: string
  description: string
  href: string
  icon: React.ReactNode
  variant?: "default" | "outline"
}

export default function DashboardPage() {
  const { user } = useAuth()
  const [stats, setStats] = useState<DashboardStats>({
    totalCharacters: 0,
    recentActivity: "Never"
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

        // Fetch characters data from character management API
        try {
          const controller = new AbortController()
          const timeoutId = setTimeout(() => controller.abort(), 60000) // 60 second timeout
          
          const charactersResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/characters/mgmt`, {
            headers,
            signal: controller.signal
          })
          
          clearTimeout(timeoutId)

          console.log('Characters response status:', charactersResponse.status)
          
          if (charactersResponse.ok) {
            const charactersData = await charactersResponse.json()
            console.log('Characters data:', charactersData)
            if (charactersData.success && charactersData.data) {
              setStats(prev => ({
                ...prev,
                totalCharacters: charactersData.data.length
              }))
            }
          } else {
            const errorText = await charactersResponse.text()
            console.error('Characters API error:', charactersResponse.status, errorText)
          }
        } catch (error) {
          console.error('Failed to fetch characters:', error)
        }

      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchDashboardData()
  }, [])

  const quickActions: QuickAction[] = [
    {
      title: "Manage Characters",
      description: "Create and edit your characters",
      href: "/dashboard/characters",
      icon: <Users className="h-4 w-4" />,
      variant: "default"
    },
    {
      title: "Pose Enhancer",
      description: "Enhance your roleplay poses with AI",
      href: "/dashboard/pose-enhancer",
      icon: <Zap className="h-4 w-4" />,
      variant: "outline"
    }
  ]

  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return "Good morning"
    if (hour < 17) return "Good afternoon"
    return "Good evening"
  }

  return (
    <div className="flex-1 p-4 md:p-8">
      <div className="mx-auto grid w-full max-w-7xl gap-8">
        {/* Welcome Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            {getGreeting()}, {user?.display_name || 'Storyteller'}
          </h1>
          <p className="text-muted-foreground mt-1">
            Ready to craft some amazing stories today?
          </p>
        </div>

        {/* Stats Overview */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Your Characters</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{isLoading ? "..." : stats.totalCharacters}</div>
              <p className="text-xs text-muted-foreground">
                {stats.totalCharacters === 1 ? "Character ready" : "Characters ready"} for roleplay
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pose Enhancer</CardTitle>
              <Zap className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">Ready</div>
              <p className="text-xs text-muted-foreground">
                AI-powered pose enhancement
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Status</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalCharacters > 0 ? "Active" : "Getting Started"}</div>
              <p className="text-xs text-muted-foreground">
                {stats.totalCharacters > 0 ? "Ready for adventures" : "Create your first character"}
              </p>
            </CardContent>
          </Card>
        </div>



        {/* Getting Started / Tips */}
        {stats.totalCharacters === 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Welcome to Your Roleplay Journey</CardTitle>
              <CardDescription>Here are some tips to get you started</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start gap-3">
                <Badge variant="outline" className="mt-1">1</Badge>
                <div>
                  <p className="font-medium">Create your first character</p>
                  <p className="text-sm text-muted-foreground">
                    Start by building a character profile to bring your stories to life
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Badge variant="outline" className="mt-1">2</Badge>
                <div>
                  <p className="font-medium">Use Pose Enhancer</p>
                  <p className="text-sm text-muted-foreground">
                    Let AI help enhance your roleplay poses and bring depth to your storytelling
                  </p>
                </div>
              </div>

            </CardContent>
          </Card>
        )}

        {/* Activity Overview - Only show if user has content */}
        {stats.totalCharacters > 0 && (
          <div className="grid gap-6 md:grid-cols-1">
            {/* Character management section */}

            {stats.totalCharacters > 0 && (
              <Card>
                <CardHeader className="flex flex-row items-center">
                  <div className="grid gap-2">
                    <CardTitle>Your Characters</CardTitle>
                    <CardDescription>
                      {stats.totalCharacters} character{stats.totalCharacters > 1 ? 's' : ''} in your cast
                    </CardDescription>
                  </div>
                  <Button asChild size="sm" className="ml-auto gap-1">
                    <Link href="/dashboard/characters">
                      Manage
                      <ArrowUpRight className="h-4 w-4" />
                    </Link>
                  </Button>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Total Characters</span>
                      <Badge variant="secondary">{stats.totalCharacters}</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Status</span>
                      <Badge variant="default">Ready for Adventure</Badge>
                    </div>
                    <div className="pt-2">
                      <Button asChild variant="outline" size="sm" className="w-full">
                        <Link href="/dashboard/characters">
                          <Plus className="h-4 w-4 mr-2" />
                          Add New Character
                        </Link>
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Suggestion for users with characters to try other features */}
            {stats.totalCharacters > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Enhance Your Roleplay</CardTitle>
                  <CardDescription>Take your character interactions to the next level</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-col items-center justify-center py-6 text-center">
                    <Zap className="h-12 w-12 text-muted-foreground mb-4" />
                    <p className="text-sm text-muted-foreground mb-4">
                      Use the Pose Enhancer to improve your roleplay poses with AI assistance
                    </p>
                    <Button asChild>
                      <Link href="/dashboard/pose-enhancer">
                        <Zap className="h-4 w-4 mr-2" />
                        Try Pose Enhancer
                      </Link>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
