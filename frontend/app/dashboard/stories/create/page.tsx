'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import {
  Loader2,
  ArrowLeft,
  Sparkles,
  Users,
  Search,
  History,
  Check,
  ChevronDown,
  ChevronUp,
  X,
  FileText
} from "lucide-react"
import Link from "next/link"
import { toast } from "@/components/ui/use-toast"
import { getApiUrl } from '@/utils/api-utils';
import { useAuth } from '@/contexts/auth-context';

export default function CreateStoryPage() {
  const { getToken } = useAuth();
  const router = useRouter();
  const [characters, setCharacters] = useState<any[]>([]);
  const [isLoadingCharacters, setIsLoadingCharacters] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    participants: [] as string[]
  });
  
  const [userScenes, setUserScenes] = useState<any[]>([]);
  const [isLoadingScenes, setIsLoadingScenes] = useState(false);
  const [selectedSceneId, setSelectedSceneId] = useState<string>('');
  const [sceneLogs, setSceneLogs] = useState<any[]>([]);
  const [selectedLogs, setSelectedLogs] = useState<any[]>([]);
  const [isImporting, setIsImporting] = useState(false);

  useEffect(() => {
    const fetchCharacters = async () => {
      try {
        const token = await getToken();
        const response = await fetch(`${getApiUrl()}/api/characters/mgmt`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
          const data = await response.json();
          setCharacters(data.data || []);
        }
      } catch (err) {
        console.error('Error fetching characters:', err);
      } finally {
        setIsLoadingCharacters(false);
      }
    };
    fetchCharacters();
  }, []);

  const fetchUserScenes = async () => {
    setIsLoadingScenes(true);
    try {
      const token = await getToken();
      const response = await fetch(`${getApiUrl()}/api/scenes?limit=50`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setUserScenes(data.data || []);
      }
    } catch (err) {
      console.error('Error fetching scenes:', err);
    } finally {
      setIsLoadingScenes(false);
    }
  };

  const handleSceneSelect = async (sceneId: string) => {
    setSelectedSceneId(sceneId);
    const scene = userScenes.find(s => s.id === sceneId);
    if (scene && scene.history_log) {
      setSceneLogs(scene.history_log);
    } else {
      setSceneLogs([]);
    }
  };

  const toggleLogSelection = (log: any) => {
    const isSelected = selectedLogs.some(l => l.timestamp === log.timestamp && l.event_description === log.event_description);
    if (isSelected) {
      setSelectedLogs(selectedLogs.filter(l => !(l.timestamp === log.timestamp && l.event_description === log.event_description)));
    } else {
      setSelectedLogs([...selectedLogs, log]);
      
      // Auto-prepopulate participant if character name is present
      if (log.character_name) {
        const char = characters.find(c => c.name === log.character_name);
        if (char && !formData.participants.includes(char.id)) {
          setFormData(prev => ({
            ...prev,
            participants: [...prev.participants, char.id]
          }));
        }
      }
    }
  };

  const moveLog = (index: number, direction: 'up' | 'down') => {
    const newLogs = [...selectedLogs];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    if (targetIndex >= 0 && targetIndex < newLogs.length) {
      [newLogs[index], newLogs[targetIndex]] = [newLogs[targetIndex], newLogs[index]];
      setSelectedLogs(newLogs);
    }
  };

  const removeLog = (index: number) => {
    setSelectedLogs(selectedLogs.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name) {
      toast({ title: "Error", description: "Scene name is required", variant: "destructive" });
      return;
    }

    setIsSubmitting(true);
    try {
      const token = await getToken();
      const response = await fetch(`${getApiUrl()}/api/scenes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: formData.name,
          description: formData.description,
          initial_participants: formData.participants,
          initial_history_log: selectedLogs
        })
      });

      if (response.ok) {
        toast({ title: "Success", description: "Story created successfully" });
        router.push('/dashboard/stories');
      } else {
        const data = await response.json();
        toast({ title: "Error", description: data.message || "Failed to create story", variant: "destructive" });
      }
    } catch (err) {
      console.error('Submit error:', err);
      toast({ title: "Error", description: "An unexpected error occurred", variant: "destructive" });
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleParticipant = (id: string) => {
    setFormData(prev => ({
      ...prev,
      participants: prev.participants.includes(id)
        ? prev.participants.filter(p => p !== id)
        : [...prev.participants, id]
    }));
  };

  return (
    <div className="flex-1 p-4 md:p-8">
      <div className="mx-auto max-w-2xl">
        <Button variant="ghost" asChild className="mb-6">
          <Link href="/dashboard/stories">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Stories
          </Link>
        </Button>

        <Card>
          <CardHeader>
            <CardTitle className="text-2xl flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-primary" />
              Create New Story
            </CardTitle>
            <CardDescription>
              Set the stage for your next roleplay scene.
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="name">Story Name</Label>
                <Input
                  id="name"
                  placeholder="e.g. The Moonlit Encounter"
                  value={formData.name}
                  onChange={e => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Initial Setting / Description</Label>
                <Textarea
                  id="description"
                  placeholder="Describe the start of the scene..."
                  rows={4}
                  value={formData.description}
                  onChange={e => setFormData({ ...formData, description: e.target.value })}
                />
              </div>

              {/* History Log Import Section */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label className="flex items-center gap-2 cursor-pointer" onClick={() => {
                    if (!isImporting && userScenes.length === 0) fetchUserScenes();
                    setIsImporting(!isImporting);
                  }}>
                    <History className="h-4 w-4" />
                    Set Starting Plot Context
                  </Label>
                  <Button 
                    type="button" 
                    variant="ghost" 
                    size="sm"
                    onClick={() => {
                      if (!isImporting && userScenes.length === 0) fetchUserScenes();
                      setIsImporting(!isImporting);
                    }}
                  >
                    {isImporting ? 'Cancel' : 'Import Past Scene History'}
                  </Button>
                </div>

                {isImporting && (
                  <Card className="bg-muted/50 border-dashed">
                    <CardContent className="pt-6 space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="scene-select">1. Select Past Scene</Label>
                        {isLoadingScenes ? (
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <Loader2 className="h-3 w-3 animate-spin" />
                            Loading your scenes...
                          </div>
                        ) : (
                          <select 
                            id="scene-select"
                            className="w-full bg-background border rounded-md p-2 text-sm"
                            value={selectedSceneId}
                            onChange={(e) => handleSceneSelect(e.target.value)}
                          >
                            <option value="">-- Choose a scene --</option>
                            {userScenes.map(scene => (
                              <option key={scene.id} value={scene.id}>{scene.name}</option>
                            ))}
                          </select>
                        )}
                      </div>

                      {selectedSceneId && sceneLogs.length > 0 && (
                        <div className="space-y-3">
                          <Label>2. Pick Narrative Milestones</Label>
                          <div className="max-h-40 overflow-y-auto border rounded-md p-2 space-y-2 bg-background">
                            {sceneLogs.map((log, i) => {
                              const isSelected = selectedLogs.some(l => l.timestamp === log.timestamp && l.event_description === log.event_description);
                              return (
                                <div 
                                  key={i} 
                                  className="flex items-start gap-2 p-2 rounded hover:bg-muted cursor-pointer"
                                  onClick={() => toggleLogSelection(log)}
                                >
                                  <div className={`mt-1 h-4 w-4 rounded border flex items-center justify-center transition-colors ${isSelected ? 'bg-primary border-primary' : 'border-input'}`}>
                                    {isSelected && <Check className="h-3 w-3 text-primary-foreground" />}
                                  </div>
                                  <div className="text-xs leading-tight">
                                    {log.event_description}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {selectedLogs.length > 0 && (
                        <div className="space-y-3">
                          <Label>3. Organize Progression</Label>
                          <div className="space-y-2">
                            {selectedLogs.map((log, i) => (
                              <div key={i} className="flex items-center gap-2 p-2 bg-background border rounded-md group">
                                <div className="flex-1 text-xs">{log.event_description}</div>
                                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                  <Button 
                                    type="button" 
                                    variant="ghost" 
                                    size="icon" 
                                    className="h-6 w-6" 
                                    onClick={(e) => { e.stopPropagation(); moveLog(i, 'up'); }}
                                    disabled={i === 0}
                                  >
                                    <ChevronUp className="h-3 w-3" />
                                  </Button>
                                  <Button 
                                    type="button" 
                                    variant="ghost" 
                                    size="icon" 
                                    className="h-6 w-6" 
                                    onClick={(e) => { e.stopPropagation(); moveLog(i, 'down'); }}
                                    disabled={i === selectedLogs.length - 1}
                                  >
                                    <ChevronDown className="h-3 w-3" />
                                  </Button>
                                  <Button 
                                    type="button" 
                                    variant="ghost" 
                                    size="icon" 
                                    className="h-6 w-6 text-destructive" 
                                    onClick={(e) => { e.stopPropagation(); removeLog(i); }}
                                  >
                                    <X className="h-3 w-3" />
                                  </Button>
                                </div>
                              </div>
                            ))}
                          </div>
                          <p className="text-[10px] text-muted-foreground italic">
                            These events will form the foundation of your new story's timeline.
                          </p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}
              </div>

              <div className="space-y-4">
                <Label className="flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  Initial Participants
                </Label>
                {isLoadingCharacters ? (
                  <div className="flex justify-center py-4">
                    <Loader2 className="h-6 w-6 animate-spin" />
                  </div>
                ) : characters.length === 0 ? (
                  <p className="text-sm text-muted-foreground italic">
                    No characters found. You might want to <Link href="/dashboard/characters/create" className="text-primary hover:underline">create one</Link> first.
                  </p>
                ) : (
                  <div className="grid grid-cols-2 gap-3">
                    {characters.map(char => (
                      <div
                        key={char.id}
                        onClick={() => toggleParticipant(char.id)}
                        className={`
                          cursor-pointer p-3 rounded-lg border flex items-center gap-3 transition-colors
                          ${formData.participants.includes(char.id) 
                            ? 'border-primary bg-primary/5' 
                            : 'border-border hover:bg-muted'}
                        `}
                      >
                        <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center overflow-hidden">
                          {char.avatarUrl ? (
                            <img src={char.avatarUrl} alt={char.name} className="h-full w-full object-cover" />
                          ) : (
                            <Users className="h-4 w-4 text-muted-foreground" />
                          )}
                        </div>
                        <span className="text-sm font-medium">{char.name}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
            <CardFooter>
              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : "Start Story"}
              </Button>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
}
