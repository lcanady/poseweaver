'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { useRouter } from 'next/navigation';
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import { toast } from "@/components/ui/use-toast";
import { AvatarUpload } from "@/components/avatar-upload";

export default function CreateCharacterPage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { refreshToken } = useAuth();
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    brainDump: '',
    profileImage: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { id, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [id]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name || !formData.brainDump) {
      toast({
        title: "Missing information",
        description: "Please provide a character name and brain dump.",
        variant: "destructive"
      });
      return;
    }

    setIsSubmitting(true);

    try {
      // Get the latest token
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      // Implement fetch with token refresh logic
      const fetchWithRefresh = async (url: string, method: string, body: any, retryCount = 0) => {
        try {
          const currentToken = localStorage.getItem('access_token');
          
          // Debug the request payload
          console.log(`Request to ${url}:`, {
            method,
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer [token]' },
            body: body
          });
          
          const bodyJson = JSON.stringify(body);
          console.log('Request body (JSON):', bodyJson);
          
          const response = await fetch(url, {
            method,
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${currentToken}`
            },
            body: bodyJson
          });
          
          // Log response status
          console.log(`Response from ${url}:`, {
            status: response.status,
            statusText: response.statusText
          });
          
          // If unauthorized and we haven't retried yet, refresh token and retry
          if (response.status === 401 && retryCount < 1) {
            console.log(`Token expired for ${url}, attempting refresh...`);
            await refreshToken();
            return fetchWithRefresh(url, method, body, retryCount + 1);
          }
          
          // Handle error responses and try to get response text
          if (!response.ok) {
            const errorText = await response.text().catch(() => 'Could not read response text');
            console.error(`Error response from ${url}:`, errorText);
            throw new Error(`Failed to fetch from ${url}: ${response.status} - ${errorText}`);
          }
          
          const data = await response.json();
          console.log(`Successful response from ${url}:`, data);
          return data;
        } catch (error) {
          console.error(`Error in fetchWithRefresh (${url}):`, error);
          throw error;
        }
      };

      // Process brain dump to create character using JWT authentication
      // Keep it simple - just send the brain_dump field
      const brainDumpPayload = {
        brain_dump: formData.brainDump || ''
      };
      
      console.log('Brain dump payload:', brainDumpPayload);
      
      const processedData = await fetchWithRefresh(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/characters/process`,
        'POST',
        brainDumpPayload
      );
      
      if (!processedData.success) {
        throw new Error(processedData.error || 'Failed to process character');
      }

      // Now create the character with the processed data
      const characterData = {
        name: formData.name,
        description: formData.description || processedData.character.background.substring(0, 150),
        profile_image: formData.profileImage || '',
        metadata: processedData.character
      };

      // Use the same fetchWithRefresh function for creating the character
      const result = await fetchWithRefresh(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/characters/mgmt`,
        'POST',
        characterData
      );
      
      if (!result.success) {
        throw new Error(result.message || 'Failed to create character');
      }

      toast({
        title: "Character created",
        description: `${formData.name} has been successfully created.`
      });

      // Redirect to characters page
      router.push('/dashboard/characters');
      
    } catch (error) {
      console.error('Error creating character:', error);
      toast({
        title: "Error creating character",
        description: error instanceof Error ? error.message : "An unknown error occurred",
        variant: "destructive"
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex-1 p-4 md:p-8">
      <div className="mx-auto grid w-full max-w-4xl gap-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Create New Character</h1>
          <p className="text-muted-foreground mt-1">
            Breathe life into a new persona. The more detail you provide, the better the AI can embody them.
          </p>
        </div>
        <form onSubmit={handleSubmit}>
          <Card>
            <CardContent className="p-6 grid gap-8">
              <div className="grid md:grid-cols-3 gap-6 items-start">
                <div className="md:col-span-1 flex flex-col items-center gap-4">
                  <Label>Character Avatar</Label>
                  <AvatarUpload
                    initialImage={formData.profileImage || "/placeholder.svg?width=128&height=128"}
                    name={formData.name}
                    onImageUploaded={(imageUrl) => {
                      setFormData(prev => ({
                        ...prev,
                        profileImage: imageUrl
                      }));
                    }}
                    size="lg"
                  />
                </div>
                <div className="md:col-span-2 space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Character Name</Label>
                    <Input 
                      id="name" 
                      placeholder="e.g., Jax, the Cyber-Noir Detective" 
                      value={formData.name}
                      onChange={handleChange}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="description">Short Description / Tagline</Label>
                    <Input 
                      id="description" 
                      placeholder="A cynical ex-cop with a cybernetic eye..." 
                      value={formData.description}
                      onChange={handleChange}
                    />
                  </div>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="brainDump">Character Brain Dump</Label>
                <p className="text-sm text-muted-foreground">
                  This is the most important part. Describe their personality, history, goals, fears, mannerisms, speaking
                  style, and anything else that defines them.
                </p>
                <Textarea
                  id="brainDump"
                  placeholder="Jax is world-weary and cynical on the surface, but underneath lies a strong, albeit tarnished, sense of justice. He speaks in short, clipped sentences and often uses noir-style metaphors. He has a prosthetic left eye that glows faintly in the dark..."
                  className="min-h-[300px]"
                  value={formData.brainDump}
                  onChange={handleChange}
                  required
                />
              </div>
            </CardContent>
          </Card>
          <div className="flex justify-end gap-2 mt-6">
            <Button variant="outline" asChild>
              <Link href="/dashboard/characters">Cancel</Link>
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                'Save Character'
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
