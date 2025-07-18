"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/hooks/use-toast"
import { useAuth } from "@/contexts/auth-context"
import { AvatarUpload } from "@/components/avatar-upload"
import { useState, useEffect } from "react"

export default function ProfilePage() {
  const { user, refreshUser } = useAuth()
  const { toast } = useToast()

  // Profile form state
  const [profileForm, setProfileForm] = useState({
    display_name: '',
    email: '',
    bio: '',
    avatar_url: ''
  })
  const [isLoading, setIsLoading] = useState(false)

  // Initialize form with user data
  useEffect(() => {
    if (user) {
      setProfileForm({
        display_name: user.display_name || '',
        email: user.email || '',
        bio: user.bio || '',
        avatar_url: user.avatar_url || ''
      })
    }
  }, [user])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/auth/update-profile`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(profileForm)
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Profile update failed')
      }

      toast({
        title: "Profile Updated",
        description: "Your profile has been updated successfully.",
      })

      // Refresh user data from the server
      await refreshUser()

    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to update profile",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }



  if (!user) {
    return <div>Loading...</div>
  }
  return (
    <div className="flex-1 p-4 md:p-8">
      <div className="mx-auto grid w-full max-w-4xl gap-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Your Profile</h1>
          <p className="text-muted-foreground mt-1">This is how others will see you on the site.</p>
        </div>
        <form onSubmit={handleSubmit}>
          <Card>
            <CardHeader>
              <CardTitle>Public Profile</CardTitle>
              <CardDescription>Customize your personal information.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex flex-col items-center gap-4">
                <Label>Profile Avatar</Label>
                <AvatarUpload
                  initialImage={profileForm.avatar_url || "/placeholder.svg"}
                  name={user.display_name || user.email}
                  onImageUploaded={(imageUrl) => {
                    setProfileForm(prev => ({
                      ...prev,
                      avatar_url: imageUrl
                    }));
                  }}
                  size="lg"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="username">Display Name</Label>
                <Input
                  id="username"
                  value={profileForm.display_name}
                  onChange={(e) => setProfileForm(prev => ({ ...prev, display_name: e.target.value }))}
                  disabled={isLoading}
                />
                <p className="text-sm text-muted-foreground">
                  This is the name that will be displayed on your profile and in emails.
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={profileForm.email}
                  onChange={(e) => setProfileForm(prev => ({ ...prev, email: e.target.value }))}
                  disabled={isLoading}
                />
                <p className="text-sm text-muted-foreground">Your email address is not displayed publicly.</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="bio">Bio</Label>
                <Textarea
                  id="bio"
                  placeholder="Tell us a little bit about yourself"
                  className="min-h-24"
                  value={profileForm.bio}
                  onChange={(e) => setProfileForm(prev => ({ ...prev, bio: e.target.value }))}
                  disabled={isLoading}
                />
              </div>
            </CardContent>
            <CardFooter>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? "Updating..." : "Update Profile"}
              </Button>
            </CardFooter>
          </Card>
        </form>
      </div>
    </div>
  )
}
