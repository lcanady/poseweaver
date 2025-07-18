"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import Link from "next/link"
import { useState, useEffect } from "react"

import { useAuth } from "@/contexts/auth-context"
import { formatDistanceToNow } from "date-fns"
import { 
  BookOpen, 
  Users, 
  Clock, 
  TrendingUp, 
  Zap,
  ArrowUpRight,
  Plus,
  User
} from "lucide-react"

interface DashboardStats {
  totalScenes: number
  totalCharacters: number
  recentActivity: string
  activeScenes: number
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
    totalScenes: 0,
    totalCharacters: 0,
    recentActivity: "Never",
    activeScenes: 0
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

        // Fetch scenes data
        const scenesResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/scenes`, {
          headers
        })

        if (scenesResponse.ok) {
          const scenesData = await scenesResponse.json()
          if (scenesData.success && scenesData.data) {
            const scenes = scenesData.data
            const activeScenes = scenes.filter((scene: any) => scene.status === "Ongoing" || !scene.status).length
            const mostRecentUpdate = scenes.length > 0 
              ? Math.max(...scenes.map((scene: any) => new Date(scene.updated_at || scene.created_at).getTime()))
              : null

            setStats(prev => ({
              ...prev,
              totalScenes: scenes.length,
              activeScenes,
              recentActivity: mostRecentUpdate 
                ? formatDistanceToNow(new Date(mostRecentUpdate), { addSuffix: true })
                : "Never"
            }))
          }
        }

        // Fetch characters data from character management API
        try {
          const charactersResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/characters/mgmt`, {
            headers
          })

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
      title: "New Scene",
      description: "Start a fresh storytelling session",
      href: "/dashboard/scenes",
      icon: <Plus className="h-4 w-4" />,
      variant: "default"
    },
    {
      title: "Scene Weaver",
      description: "Continue an existing scene",
      href: "/dashboard/scene-weaver",
      icon: <Zap className="h-4 w-4" />
    },
    {
      title: "Characters",
      description: "Manage your character profiles",
      href: "/dashboard/characters",
      icon: <Users className="h-4 w-4" />
    },
    {
      title: "Browse Scenes",
      description: "View all your scenes",
      href: "/dashboard/scenes",
      icon: <BookOpen className="h-4 w-4" />
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
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Scenes</CardTitle>
              <BookOpen className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{isLoading ? "..." : stats.totalScenes}</div>
              <p className="text-xs text-muted-foreground">
                {stats.activeScenes} active
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Characters</CardTitle>
              <User className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{isLoading ? "..." : stats.totalCharacters}</div>
              <p className="text-xs text-muted-foreground">
                Ready for action
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Last Activity</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{isLoading ? "..." : stats.recentActivity}</div>
              <p className="text-xs text-muted-foreground">
                Keep the momentum going
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Scenes</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{isLoading ? "..." : stats.activeScenes}</div>
              <p className="text-xs text-muted-foreground">
                Stories in progress
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Jump into your most common tasks</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {quickActions.map((action, index) => (
                <Button
                  key={index}
                  asChild
                  variant={action.variant || "outline"}
                  className="h-auto p-4 flex flex-col items-start gap-2"
                >
                  <Link href={action.href}>
                    <div className="flex items-center gap-2 w-full">
                      {action.icon}
                      <span className="font-medium">{action.title}</span>
                    </div>
                    <span className="text-xs text-muted-foreground text-left">
                      {action.description}
                    </span>
                  </Link>
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Getting Started / Tips */}
        {stats.totalScenes === 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Welcome to Your Storytelling Journey</CardTitle>
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
                  <p className="font-medium">Start a new scene</p>
                  <p className="text-sm text-muted-foreground">
                    Create your first scene and begin crafting your narrative
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Badge variant="outline" className="mt-1">3</Badge>
                <div>
                  <p className="font-medium">Use Scene Weaver</p>
                  <p className="text-sm text-muted-foreground">
                    Let AI help enhance your poses and bring depth to your storytelling
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Activity Overview - Only show if user has content */}
        {(stats.totalScenes > 0 || stats.totalCharacters > 0) && (
          <div className="grid gap-6 md:grid-cols-2">
            {/* Show scenes section only if user has scenes */}
            {stats.totalScenes > 0 && (
              <Card>
                <CardHeader className="flex flex-row items-center">
                  <div className="grid gap-2">
                    <CardTitle>Your Scenes</CardTitle>
                    <CardDescription>
                      {stats.activeScenes > 0 
                        ? `${stats.activeScenes} active scene${stats.activeScenes > 1 ? 's' : ''} ready to continue`
                        : "All scenes completed"
                      }
                    </CardDescription>
                  </div>
                  <Button asChild size="sm" className="ml-auto gap-1">
                    <Link href="/dashboard/scenes">
                      View All
                      <ArrowUpRight className="h-4 w-4" />
                    </Link>
                  </Button>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Total Scenes</span>
                      <Badge variant="secondary">{stats.totalScenes}</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Active</span>
                      <Badge variant={stats.activeScenes > 0 ? "default" : "outline"}>
                        {stats.activeScenes}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Last Updated</span>
                      <span className="text-sm text-muted-foreground">{stats.recentActivity}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Show characters section only if user has characters */}
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

            {/* If user only has one type of content, show a suggestion for the other */}
            {stats.totalScenes > 0 && stats.totalCharacters === 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Create Your First Character</CardTitle>
                  <CardDescription>Bring your stories to life with detailed characters</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-col items-center justify-center py-6 text-center">
                    <Users className="h-12 w-12 text-muted-foreground mb-4" />
                    <p className="text-sm text-muted-foreground mb-4">
                      Characters help you craft more engaging and consistent stories
                    </p>
                    <Button asChild>
                      <Link href="/dashboard/characters">
                        <Plus className="h-4 w-4 mr-2" />
                        Create Character
                      </Link>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {stats.totalCharacters > 0 && stats.totalScenes === 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Start Your First Scene</CardTitle>
                  <CardDescription>Put your characters into action</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-col items-center justify-center py-6 text-center">
                    <BookOpen className="h-12 w-12 text-muted-foreground mb-4" />
                    <p className="text-sm text-muted-foreground mb-4">
                      Now that you have characters, create scenes to tell their stories
                    </p>
                    <Button asChild>
                      <Link href="/dashboard/scenes">
                        <Plus className="h-4 w-4 mr-2" />
                        Create Scene
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
