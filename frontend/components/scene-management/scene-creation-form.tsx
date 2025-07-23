"use client"

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Separator } from '@/components/ui/separator'
import { 
  Plus, 
  X, 
  Users, 
  Settings, 
  FileText, 
  Save, 
  Eye, 
  EyeOff, 
  Tag,
  Loader2,
  AlertCircle 
} from 'lucide-react'
import type { SceneCreationData, SceneFormState, SceneValidationError } from '@/types/scene'

// Validation schema
const sceneCreationSchema = z.object({
  name: z.string()
    .min(1, 'Scene name is required')
    .max(100, 'Scene name must be 100 characters or less'),
  description: z.string()
    .min(10, 'Scene description must be at least 10 characters')
    .max(1000, 'Scene description must be 1000 characters or less'),
  tags: z.array(z.string()).optional(),
  participants: z.array(z.object({
    character_id: z.string(),
    character_name: z.string()
  })).optional(),
  initial_setting: z.string().optional(),
  scene_type: z.enum(['oneshot', 'ongoing', 'campaign']).optional(),
  privacy_level: z.enum(['private', 'shared', 'public']).optional(),
  allow_new_participants: z.boolean().optional()
})

type SceneCreationFormData = z.infer<typeof sceneCreationSchema>

interface SceneCreationFormProps {
  onSubmit: (data: SceneCreationData) => Promise<void>
  onCancel?: () => void
  initialData?: Partial<SceneCreationData>
  isEditing?: boolean
  loading?: boolean
  error?: string
}

interface Character {
  id: string
  name: string
  description?: string
  avatar?: string
}

export function SceneCreationForm({ 
  onSubmit, 
  onCancel, 
  initialData, 
  isEditing = false, 
  loading = false, 
  error 
}: SceneCreationFormProps) {
  const [characters, setCharacters] = useState<Character[]>([])
  const [loadingCharacters, setLoadingCharacters] = useState(false)
  const [currentTag, setCurrentTag] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [characterSearchOpen, setCharacterSearchOpen] = useState(false)

  const form = useForm<SceneCreationFormData>({
    resolver: zodResolver(sceneCreationSchema),
    defaultValues: {
      name: initialData?.name || '',
      description: initialData?.description || '',
      tags: initialData?.tags || [],
      participants: initialData?.participants || [],
      initial_setting: initialData?.initial_setting || '',
      scene_type: initialData?.scene_type || 'ongoing',
      privacy_level: initialData?.privacy_level || 'private',
      allow_new_participants: initialData?.allow_new_participants || false
    }
  })

  // Load user's characters
  useEffect(() => {
    const loadCharacters = async () => {
      setLoadingCharacters(true)
      try {
        // TODO: Replace with actual API call
        const response = await fetch('/api/characters', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        })
        if (response.ok) {
          const data = await response.json()
          setCharacters(data.data || [])
        }
      } catch (error) {
        console.error('Failed to load characters:', error)
      } finally {
        setLoadingCharacters(false)
      }
    }

    loadCharacters()
  }, [])

  const handleSubmit = async (data: SceneCreationFormData) => {
    try {
      await onSubmit(data)
    } catch (error) {
      console.error('Form submission error:', error)
    }
  }

  const addTag = (tag: string) => {
    if (tag && !form.getValues('tags')?.includes(tag)) {
      const currentTags = form.getValues('tags') || []
      form.setValue('tags', [...currentTags, tag])
    }
    setCurrentTag('')
  }

  const removeTag = (tagToRemove: string) => {
    const currentTags = form.getValues('tags') || []
    form.setValue('tags', currentTags.filter(tag => tag !== tagToRemove))
  }

  const addParticipant = (character: Character) => {
    const currentParticipants = form.getValues('participants') || []
    if (!currentParticipants.find(p => p.character_id === character.id)) {
      form.setValue('participants', [
        ...currentParticipants,
        { character_id: character.id, character_name: character.name }
      ])
    }
    setCharacterSearchOpen(false)
  }

  const removeParticipant = (characterId: string) => {
    const currentParticipants = form.getValues('participants') || []
    form.setValue('participants', currentParticipants.filter(p => p.character_id !== characterId))
  }

  const tags = form.watch('tags') || []
  const participants = form.watch('participants') || []

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          {isEditing ? 'Edit Scene' : 'Create New Scene'}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Tabs defaultValue="basic" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="basic">Basic Info</TabsTrigger>
                <TabsTrigger value="participants">Participants</TabsTrigger>
                <TabsTrigger value="settings">Settings</TabsTrigger>
              </TabsList>

              <TabsContent value="basic" className="space-y-4">
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Scene Name</FormLabel>
                      <FormControl>
                        <Input 
                          placeholder="Enter scene name..." 
                          {...field}
                        />
                      </FormControl>
                      <FormDescription>
                        A descriptive name for your scene
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="description"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Description</FormLabel>
                      <FormControl>
                        <Textarea 
                          placeholder="Describe your scene, setting, and premise..."
                          className="min-h-[100px]"
                          {...field}
                        />
                      </FormControl>
                      <FormDescription>
                        Provide context and background for your scene
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="initial_setting"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Initial Setting</FormLabel>
                      <FormControl>
                        <Textarea 
                          placeholder="Describe the initial scene location and atmosphere..."
                          className="min-h-[80px]"
                          {...field}
                        />
                      </FormControl>
                      <FormDescription>
                        Set the scene with location and environmental details
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="space-y-2">
                  <Label>Tags</Label>
                  <div className="flex gap-2">
                    <Input
                      placeholder="Add tags..."
                      value={currentTag}
                      onChange={(e) => setCurrentTag(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault()
                          addTag(currentTag)
                        }
                      }}
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => addTag(currentTag)}
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                  {tags.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {tags.map((tag, index) => (
                        <Badge key={index} variant="secondary" className="flex items-center gap-1">
                          <Tag className="h-3 w-3" />
                          {tag}
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="h-4 w-4 p-0 hover:bg-transparent"
                            onClick={() => removeTag(tag)}
                          >
                            <X className="h-3 w-3" />
                          </Button>
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="participants" className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label>Scene Participants</Label>
                  <Dialog open={characterSearchOpen} onOpenChange={setCharacterSearchOpen}>
                    <DialogTrigger asChild>
                      <Button variant="outline" size="sm">
                        <Users className="h-4 w-4 mr-2" />
                        Add Character
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="sm:max-w-md">
                      <DialogHeader>
                        <DialogTitle>Select Character</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4">
                        {loadingCharacters ? (
                          <div className="flex items-center justify-center py-8">
                            <Loader2 className="h-6 w-6 animate-spin" />
                          </div>
                        ) : characters.length === 0 ? (
                          <p className="text-center text-muted-foreground py-8">
                            No characters found. Create a character first.
                          </p>
                        ) : (
                          <div className="grid gap-2">
                            {characters.map((character) => (
                              <Button
                                key={character.id}
                                variant="outline"
                                className="justify-start"
                                onClick={() => addParticipant(character)}
                                disabled={participants.some(p => p.character_id === character.id)}
                              >
                                <Users className="h-4 w-4 mr-2" />
                                {character.name}
                              </Button>
                            ))}
                          </div>
                        )}
                      </div>
                    </DialogContent>
                  </Dialog>
                </div>

                {participants.length > 0 ? (
                  <div className="grid gap-2">
                    {participants.map((participant) => (
                      <div key={participant.character_id} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center gap-3">
                          <Users className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">{participant.character_name}</span>
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeParticipant(participant.character_id)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-muted-foreground py-8">
                    No participants added yet. Add characters to your scene.
                  </p>
                )}
              </TabsContent>

              <TabsContent value="settings" className="space-y-4">
                <FormField
                  control={form.control}
                  name="scene_type"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Scene Type</FormLabel>
                      <Select onValueChange={field.onChange} defaultValue={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select scene type" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="oneshot">One-shot</SelectItem>
                          <SelectItem value="ongoing">Ongoing</SelectItem>
                          <SelectItem value="campaign">Campaign</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormDescription>
                        Choose how long you expect this scene to run
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="privacy_level"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Privacy Level</FormLabel>
                      <Select onValueChange={field.onChange} defaultValue={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select privacy level" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="private">
                            <div className="flex items-center gap-2">
                              <EyeOff className="h-4 w-4" />
                              Private
                            </div>
                          </SelectItem>
                          <SelectItem value="shared">
                            <div className="flex items-center gap-2">
                              <Users className="h-4 w-4" />
                              Shared
                            </div>
                          </SelectItem>
                          <SelectItem value="public">
                            <div className="flex items-center gap-2">
                              <Eye className="h-4 w-4" />
                              Public
                            </div>
                          </SelectItem>
                        </SelectContent>
                      </Select>
                      <FormDescription>
                        Control who can view and participate in your scene
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="allow_new_participants"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                      <div className="space-y-0.5">
                        <FormLabel className="text-base">
                          Allow New Participants
                        </FormLabel>
                        <FormDescription>
                          Allow other users to join this scene with their characters
                        </FormDescription>
                      </div>
                      <FormControl>
                        <Checkbox
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />
              </TabsContent>
            </Tabs>

            <Separator />

            <div className="flex justify-end gap-2">
              {onCancel && (
                <Button type="button" variant="outline" onClick={onCancel}>
                  Cancel
                </Button>
              )}
              <Button type="submit" disabled={loading}>
                {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                <Save className="h-4 w-4 mr-2" />
                {isEditing ? 'Update Scene' : 'Create Scene'}
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  )
} 