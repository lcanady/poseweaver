'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import Link from "next/link";
import { Loader2, ArrowLeft } from "lucide-react";
import { toast } from "@/components/ui/use-toast";
import { AvatarUpload } from "@/components/avatar-upload";
import { getApiUrl } from '@/utils/api-utils';

interface CharacterFormData {
  name: string;
  description: string;
  profileImage?: string;
  background?: string;
  personality?: string[];
  skills?: string[];
  goals?: string[];
  voiceNotes?: string;
  brainDump?: string;
}

import { useAuth } from '@/contexts/auth-context';

export default function EditCharacterPage({ params }: { params: Promise<{ id: string }> }) {
  // Unwrap params using React.use to fix Next.js warnings
  const unwrappedParams = React.use(params);
  const router = useRouter();
  const { getToken } = useAuth();
  const [formData, setFormData] = useState<CharacterFormData>({
    name: '',
    description: '',
    profileImage: '',
    background: '',
    personality: [''],
    skills: [''],
    goals: [''],
    voiceNotes: '',
    brainDump: ''
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCharacter = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const token = await getToken();

        if (!token) {
          throw new Error('No access token found. Please log in again.');
        }

        const response = await fetch(
          `${getApiUrl()}/api/characters/mgmt/${unwrappedParams.id}`,
          {
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            }
          }
        );

        if (!response.ok) {
          throw new Error('Failed to fetch character');
        }

        const data = await response.json();

        if (!data.success) {
          throw new Error(data.message || 'Failed to fetch character');
        }

        const character = data.data;
        const metadata = character.metadata || {};
        setFormData({
          name: character.name || '',
          description: character.description || '',
          profileImage: character.profile_image || '',
          background: metadata.background || '',
          personality: metadata.personality || [''],
          skills: metadata.skills || [''],
          goals: metadata.goals || [''],
          voiceNotes: metadata.voice_notes || '',
          brainDump: ''
        });
      } catch (err) {
        console.error('Error fetching character:', err);
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
        toast({
          title: "Error",
          description: err instanceof Error ? err.message : 'Failed to load character',
          variant: "destructive"
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchCharacter();
  }, [unwrappedParams.id, router]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleListItemChange = (type: 'personality' | 'skills' | 'goals', index: number, value: string) => {
    setFormData(prev => {
      const newItems = [...(prev[type] || [''])];
      newItems[index] = value;
      return {
        ...prev,
        [type]: newItems
      };
    });
  };

  const addListItem = (type: 'personality' | 'skills' | 'goals') => {
    setFormData(prev => ({
      ...prev,
      [type]: [...(prev[type] || []), '']
    }));
  };

  const removeListItem = (type: 'personality' | 'skills' | 'goals', index: number) => {
    const items = formData[type] || [];
    if (items.length <= 1) return;
    setFormData(prev => ({
      ...prev,
      [type]: (prev[type] || []).filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      toast({
        title: "Error",
        description: "Character name is required",
        variant: "destructive"
      });
      return;
    }

    setIsSaving(true);

    try {
      // Prepare the update data
      const updateData = {
        name: formData.name,
        description: formData.description,
        profile_image: formData.profileImage,
        metadata: {
          background: formData.background || '',
          personality: (formData.personality || []).filter(item => item.trim() !== ''),
          skills: (formData.skills || []).filter(item => item.trim() !== ''),
          goals: (formData.goals || []).filter(item => item.trim() !== ''),
          voice_notes: formData.voiceNotes || ''
        }
      };

      // If brain dump is provided, process it first
      if (formData.brainDump && formData.brainDump.trim()) {
        try {
          const token = await getToken();

          if (!token) {
            throw new Error('No access token found. Please log in again.');
          }

          const processResponse = await fetch(
            `${getApiUrl()}/api/characters/process`,
            {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
              },
              body: JSON.stringify({
                character_id: unwrappedParams.id,
                brain_dump: formData.brainDump
              })
            }
          );

          if (!processResponse.ok) {
            throw new Error('Failed to process character brain dump');
          }

          const processData = await processResponse.json();

          if (!processData.success) {
            throw new Error(processData.message || 'Failed to process character brain dump');
          }

          // Add the processed metadata to the update data
          Object.assign(updateData, { metadata: processData.data });
        } catch (err) {
          console.error('Error processing brain dump:', err);
          toast({
            title: "Warning",
            description: "Failed to process character brain dump, but will continue with basic update",
            variant: "default"
          });
        }
      }

      // Get access token
      const token = await getToken();

      if (!token) {
        throw new Error('No access token found. Please log in again.');
      }

      // Update the character
      const updateResponse = await fetch(
        `${getApiUrl()}/api/characters/mgmt/${unwrappedParams.id}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(updateData)
        }
      );

      if (!updateResponse.ok) {
        throw new Error('Failed to update character');
      }

      const data = await updateResponse.json();

      if (!data.success) {
        throw new Error(data.message || 'Failed to update character');
      }

      toast({
        title: "Success",
        description: "Character updated successfully"
      });

      // Navigate back to character detail page
      router.push(`/dashboard/characters/${unwrappedParams.id}`);
    } catch (err) {
      console.error('Error updating character:', err);
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : 'Failed to update character',
        variant: "destructive"
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex-1 p-4 md:p-8">
      <div className="mx-auto grid w-full max-w-4xl gap-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button variant="default" size="icon" asChild className="mr-2">
              <Link href={`/dashboard/characters/${unwrappedParams.id}`}>
                <ArrowLeft className="h-4 w-4" />
              </Link>
            </Button>
            <h1 className="text-3xl font-bold tracking-tight">Edit Character</h1>
          </div>
        </div>

        {isLoading ? (
          <div className="flex justify-center items-center py-12">
            <Loader2 className="h-8 w-8 animate-spin mr-2" />
            <span>Loading character...</span>
          </div>
        ) : error ? (
          <div className="text-center py-8 text-muted-foreground">
            <p>Failed to load character. Please try again later.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <Card>
              <CardContent className="pt-6">
                <div className="grid md:grid-cols-3 gap-6 items-start">
                  <div className="md:col-span-1 flex flex-col items-center gap-4">
                    <Label>Character Avatar</Label>
                    <AvatarUpload
                      initialImage={formData.profileImage}
                      name={formData.name}
                      onImageUploaded={(imageUrl) => {
                        setFormData(prev => ({
                          ...prev,
                          profileImage: imageUrl
                        }));
                      }}
                      size="lg"
                      characterId={unwrappedParams.id}
                    />
                  </div>
                  <div className="md:col-span-2 space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="name">Character Name</Label>
                      <Input
                        id="name"
                        name="name"
                        placeholder="Enter character name"
                        value={formData.name}
                        onChange={handleChange}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="description">Short Description</Label>
                      <Textarea
                        id="description"
                        name="description"
                        placeholder="A brief description of your character"
                        value={formData.description}
                        onChange={handleChange}
                        rows={3}
                      />
                    </div>
                  </div>
                </div>

                {/* Background */}
                <div className="mt-6 space-y-2">
                  <Label htmlFor="background">Background</Label>
                  <Textarea
                    id="background"
                    name="background"
                    placeholder="Character's background story"
                    value={formData.background}
                    onChange={handleChange}
                    rows={6}
                  />
                </div>

                {/* Personality */}
                <div className="mt-6 space-y-2">
                  <Label>Personality Traits</Label>
                  {(formData.personality || ['']).map((trait, index) => (
                    <div key={`personality-${index}`} className="flex gap-2 items-center">
                      <Input
                        value={trait}
                        onChange={(e) => handleListItemChange('personality', index, e.target.value)}
                        placeholder="Add a personality trait"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={() => removeListItem('personality', index)}
                        disabled={(formData.personality || []).length <= 1}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18" /><path d="m6 6 12 12" /></svg>
                      </Button>
                    </div>
                  ))}
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="mt-2"
                    onClick={() => addListItem('personality')}
                  >
                    Add Personality Trait
                  </Button>
                </div>

                {/* Skills */}
                <div className="mt-6 space-y-2">
                  <Label>Skills</Label>
                  {(formData.skills || ['']).map((skill, index) => (
                    <div key={`skill-${index}`} className="flex gap-2 items-center">
                      <Input
                        value={skill}
                        onChange={(e) => handleListItemChange('skills', index, e.target.value)}
                        placeholder="Add a skill"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={() => removeListItem('skills', index)}
                        disabled={(formData.skills || []).length <= 1}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18" /><path d="m6 6 12 12" /></svg>
                      </Button>
                    </div>
                  ))}
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="mt-2"
                    onClick={() => addListItem('skills')}
                  >
                    Add Skill
                  </Button>
                </div>

                {/* Goals */}
                <div className="mt-6 space-y-2">
                  <Label>Goals</Label>
                  {(formData.goals || ['']).map((goal, index) => (
                    <div key={`goal-${index}`} className="flex gap-2 items-center">
                      <Input
                        value={goal}
                        onChange={(e) => handleListItemChange('goals', index, e.target.value)}
                        placeholder="Add a goal"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={() => removeListItem('goals', index)}
                        disabled={(formData.goals || []).length <= 1}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18" /><path d="m6 6 12 12" /></svg>
                      </Button>
                    </div>
                  ))}
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="mt-2"
                    onClick={() => addListItem('goals')}
                  >
                    Add Goal
                  </Button>
                </div>

                {/* Voice Notes */}
                <div className="mt-6 space-y-2">
                  <Label htmlFor="voiceNotes">Voice Notes</Label>
                  <Textarea
                    id="voiceNotes"
                    name="voiceNotes"
                    placeholder="How your character speaks, tone, phrases, etc."
                    value={formData.voiceNotes}
                    onChange={handleChange}
                    rows={4}
                  />
                </div>

                {/* Brain Dump (optional) */}
                <div className="mt-6 space-y-2">
                  <Label htmlFor="brainDump">Generate New Details with AI (Optional)</Label>
                  <Textarea
                    id="brainDump"
                    name="brainDump"
                    placeholder="Add new details for the AI to process and enhance your character's profile."
                    value={formData.brainDump}
                    onChange={handleChange}
                    rows={6}
                  />
                  <p className="text-sm text-muted-foreground">
                    This will generate new AI-enhanced details for your character. Leave blank to keep your manually edited details above.
                  </p>
                </div>

                <div className="mt-6 flex justify-end gap-4">
                  <Button variant="outline" asChild>
                    <Link href={`/dashboard/characters/${unwrappedParams.id}`}>Cancel</Link>
                  </Button>
                  <Button type="submit" disabled={isSaving}>
                    {isSaving ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      'Save Changes'
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </form>
        )}
      </div>
    </div>
  );
}
