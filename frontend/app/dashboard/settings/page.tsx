"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { useToast } from "@/hooks/use-toast"
import { useAuth } from "@/contexts/auth-context"
import { useTheme } from "next-themes"
import { 
  Settings, 
  Bell, 
  Shield, 
  Palette, 
  Moon, 
  Sun, 
  Monitor,
  Download,
  Trash2,
  AlertTriangle
} from "lucide-react"
import { getApiUrl } from '@/utils/api-utils'

interface UserSettings {
  theme: 'light' | 'dark' | 'system'
  notifications: {
    email_updates: boolean
    pose_generation_alerts: boolean
    subscription_reminders: boolean
    feature_announcements: boolean
  }
  privacy: {
    profile_visibility: 'public' | 'private'
    analytics_tracking: boolean
    data_collection: boolean
  }
  preferences: {
    default_enhancement_style: 'minimal' | 'balanced' | 'elaborate'
    auto_save_poses: boolean
    show_advanced_settings: boolean
    character_limit_warnings: boolean
  }
}

export default function SettingsPage() {
  const { user } = useAuth()
  const { toast } = useToast()
  const { theme, setTheme } = useTheme()
  
  const [settings, setSettings] = useState<UserSettings>({
    theme: 'system',
    notifications: {
      email_updates: true,
      pose_generation_alerts: false,
      subscription_reminders: true,
      feature_announcements: true
    },
    privacy: {
      profile_visibility: 'private',
      analytics_tracking: true,
      data_collection: true
    },
    preferences: {
      default_enhancement_style: 'balanced',
      auto_save_poses: true,
      show_advanced_settings: false,
      character_limit_warnings: true
    }
  })
  
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  // Load user settings on component mount
  useEffect(() => {
    loadSettings()
  }, [user?._id])

  // Sync theme state with next-themes provider
  useEffect(() => {
    if (theme) {
      setSettings(prev => ({
        ...prev,
        theme: theme as 'light' | 'dark' | 'system'
      }))
    }
  }, [theme])

  const loadSettings = async () => {
    if (!user?._id) return
    
    setIsLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${getApiUrl()}/api/user/settings`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.success && data.settings) {
          setSettings(data.settings)
        }
      }
    } catch (error) {
      console.error('Error loading settings:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const saveSettings = async () => {
    if (!user?._id) return
    
    setIsSaving(true)
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${getApiUrl()}/api/user/settings`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
      })
      
      if (response.ok) {
        toast({
          title: "Settings Saved",
          description: "Your preferences have been updated successfully."
        })
      } else {
        throw new Error('Failed to save settings')
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save settings. Please try again.",
        variant: "destructive"
      })
    } finally {
      setIsSaving(false)
    }
  }

  const exportData = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${getApiUrl()}/api/user/export-data`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `poseweaver-data-${new Date().toISOString().split('T')[0]}.json`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        
        toast({
          title: "Data Exported",
          description: "Your data has been downloaded successfully."
        })
      }
    } catch (error) {
      toast({
        title: "Export Failed",
        description: "Failed to export your data. Please try again.",
        variant: "destructive"
      })
    }
  }

  const updateSetting = (path: string, value: any) => {
    setSettings(prev => {
      const keys = path.split('.')
      const newSettings = { ...prev }
      let current: any = newSettings
      
      for (let i = 0; i < keys.length - 1; i++) {
        current[keys[i]] = { ...current[keys[i]] }
        current = current[keys[i]]
      }
      
      current[keys[keys.length - 1]] = value
      return newSettings
    })
  }

  if (!user) {
    return <div>Loading...</div>
  }

  return (
    <div className="flex-1 p-4 md:p-8">
      <div className="mx-auto grid w-full max-w-4xl gap-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground mt-1">
            Customize your PoseWeaver experience and manage your preferences.
          </p>
        </div>

        {/* Appearance Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Palette className="h-5 w-5" />
              Appearance
            </CardTitle>
            <CardDescription>
              Customize how PoseWeaver looks and feels.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="theme">Theme</Label>
              <Select 
                value={settings.theme} 
                onValueChange={(value: 'light' | 'dark' | 'system') => {
                  setTheme(value)
                  updateSetting('theme', value)
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select theme" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="light">
                    <div className="flex items-center gap-2">
                      <Sun className="h-4 w-4" />
                      Light
                    </div>
                  </SelectItem>
                  <SelectItem value="dark">
                    <div className="flex items-center gap-2">
                      <Moon className="h-4 w-4" />
                      Dark
                    </div>
                  </SelectItem>
                  <SelectItem value="system">
                    <div className="flex items-center gap-2">
                      <Monitor className="h-4 w-4" />
                      System
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
              <p className="text-sm text-muted-foreground">
                Choose your preferred color scheme.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Notification Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Notifications
            </CardTitle>
            <CardDescription>
              Control what notifications you receive from PoseWeaver.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Email Updates</Label>
                <p className="text-sm text-muted-foreground">
                  Receive important updates and announcements via email.
                </p>
              </div>
              <Switch
                checked={settings.notifications.email_updates}
                onCheckedChange={(checked) => updateSetting('notifications.email_updates', checked)}
              />
            </div>
            
            <Separator />
            
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Pose Generation Alerts</Label>
                <p className="text-sm text-muted-foreground">
                  Get notified when you're approaching your monthly generation limit.
                </p>
              </div>
              <Switch
                checked={settings.notifications.pose_generation_alerts}
                onCheckedChange={(checked) => updateSetting('notifications.pose_generation_alerts', checked)}
              />
            </div>
            
            <Separator />
            
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Subscription Reminders</Label>
                <p className="text-sm text-muted-foreground">
                  Receive reminders about subscription renewals and billing.
                </p>
              </div>
              <Switch
                checked={settings.notifications.subscription_reminders}
                onCheckedChange={(checked) => updateSetting('notifications.subscription_reminders', checked)}
              />
            </div>
            
            <Separator />
            
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Feature Announcements</Label>
                <p className="text-sm text-muted-foreground">
                  Stay updated on new features and improvements.
                </p>
              </div>
              <Switch
                checked={settings.notifications.feature_announcements}
                onCheckedChange={(checked) => updateSetting('notifications.feature_announcements', checked)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Privacy Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Privacy & Security
            </CardTitle>
            <CardDescription>
              Manage your privacy preferences and data sharing settings.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="profile-visibility">Profile Visibility</Label>
              <Select 
                value={settings.privacy.profile_visibility} 
                onValueChange={(value: 'public' | 'private') => updateSetting('privacy.profile_visibility', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select visibility" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="public">Public</SelectItem>
                  <SelectItem value="private">Private</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-sm text-muted-foreground">
                Control who can see your profile information.
              </p>
            </div>
            
            <Separator />
            
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Analytics Tracking</Label>
                <p className="text-sm text-muted-foreground">
                  Help us improve PoseWeaver by sharing anonymous usage data.
                </p>
              </div>
              <Switch
                checked={settings.privacy.analytics_tracking}
                onCheckedChange={(checked) => updateSetting('privacy.analytics_tracking', checked)}
              />
            </div>
            
            <Separator />
            
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Data Collection</Label>
                <p className="text-sm text-muted-foreground">
                  Allow collection of usage patterns to enhance your experience.
                </p>
              </div>
              <Switch
                checked={settings.privacy.data_collection}
                onCheckedChange={(checked) => updateSetting('privacy.data_collection', checked)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Preferences */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Preferences
            </CardTitle>
            <CardDescription>
              Customize your writing and enhancement preferences.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="default-style">Default Enhancement Style</Label>
              <Select 
                value={settings.preferences.default_enhancement_style} 
                onValueChange={(value: 'minimal' | 'balanced' | 'elaborate') => updateSetting('preferences.default_enhancement_style', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select style" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="minimal">Minimal</SelectItem>
                  <SelectItem value="balanced">Balanced</SelectItem>
                  <SelectItem value="elaborate">Elaborate</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-sm text-muted-foreground">
                Your preferred enhancement style for new poses.
              </p>
            </div>
            
            <Separator />
            
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Auto-save Poses</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically save enhanced poses to your history.
                </p>
              </div>
              <Switch
                checked={settings.preferences.auto_save_poses}
                onCheckedChange={(checked) => updateSetting('preferences.auto_save_poses', checked)}
              />
            </div>
            
            <Separator />
            
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Show Advanced Settings</Label>
                <p className="text-sm text-muted-foreground">
                  Display advanced enhancement options by default.
                </p>
              </div>
              <Switch
                checked={settings.preferences.show_advanced_settings}
                onCheckedChange={(checked) => updateSetting('preferences.show_advanced_settings', checked)}
              />
            </div>
            
            <Separator />
            
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Character Limit Warnings</Label>
                <p className="text-sm text-muted-foreground">
                  Show warnings when approaching character creation limits.
                </p>
              </div>
              <Switch
                checked={settings.preferences.character_limit_warnings}
                onCheckedChange={(checked) => updateSetting('preferences.character_limit_warnings', checked)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Data Management */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Download className="h-5 w-5" />
              Data Management
            </CardTitle>
            <CardDescription>
              Export or manage your PoseWeaver data.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Export Your Data</Label>
                <p className="text-sm text-muted-foreground">
                  Download all your characters, poses, and account data.
                </p>
              </div>
              <Button variant="outline" onClick={exportData}>
                <Download className="h-4 w-4 mr-2" />
                Export Data
              </Button>
            </div>
            
            <Separator />
            
            <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-destructive mt-0.5" />
                <div className="space-y-2 flex-1">
                  <Label className="text-destructive">Danger Zone</Label>
                  <p className="text-sm text-muted-foreground">
                    Permanently delete your account and all associated data. This action cannot be undone.
                  </p>
                  <Button variant="destructive" size="sm" className="mt-2">
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete Account
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Save Button */}
        <div className="flex justify-end">
          <Button onClick={saveSettings} disabled={isSaving || isLoading}>
            {isSaving ? "Saving..." : "Save Settings"}
          </Button>
        </div>
      </div>
    </div>
  )
}
