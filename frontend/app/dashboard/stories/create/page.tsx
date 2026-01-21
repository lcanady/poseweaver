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
  Users
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
          initial_participants: formData.participants
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
