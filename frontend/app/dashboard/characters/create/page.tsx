'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { useRouter } from 'next/navigation';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import Link from "next/link";
import { Loader2, Crown, AlertTriangle } from "lucide-react";
import { toast } from "@/components/ui/use-toast";
import { AvatarUpload } from "@/components/avatar-upload";
import { getApiUrl } from '@/utils/api-utils';

export default function CreateCharacterPage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { refreshToken } = useAuth();
  const [characterLimitError, setCharacterLimitError] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isFormDisabled, setIsFormDisabled] = useState(false);
  const [subscriptionMeta, setSubscriptionMeta] = useState<any>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    brainDump: '',
    profileImage: '',
  });

  // Function to fetch with token refresh capabilities (reusable)
  const fetchWithRefresh = async (url: string, method: string = 'GET', body: any = null, retryCount = 0) => {
    try {
      const currentToken = localStorage.getItem('access_token');
      
      const options: RequestInit = {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${currentToken}`
        }
      };
      
      if (body) {
        options.body = JSON.stringify(body);
      }
      
      const response = await fetch(url, options);
      
      // If unauthorized and we haven't retried yet, refresh token and retry
      if (response.status === 401 && retryCount < 1) {
        console.log(`Token expired for ${url}, attempting refresh...`);
        await refreshToken();
        return fetchWithRefresh(url, method, body, retryCount + 1);
      }
      
      // Handle error responses
      if (!response.ok) {
        const errorData = await response.json().catch(async () => {
          const errorText = await response.text().catch(() => 'Could not read response text');
          return { message: errorText };
        });
        
        // Check for character limit error
        if (response.status === 403 && errorData.needs_upgrade) {
          throw { 
            type: 'CHARACTER_LIMIT',
            data: errorData
          };
        }
        
        throw new Error(errorData.message || `Failed to fetch from ${url}: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`Error in fetchWithRefresh (${url}):`, error);
      throw error;
    }
  };

  // Check character limits on page load
  useEffect(() => {
    const checkCharacterLimits = async () => {
      try {
        setIsLoading(true);
        
        // Fetch current characters to check limits
        const data = await fetchWithRefresh(
          `${getApiUrl()}/api/characters/mgmt`
        );
        
        // Extract subscription metadata
        if (data.meta) {
          setSubscriptionMeta(data.meta);
          
          // Check if user has reached their character limit
          const currentCount = data.data ? data.data.length : 0;
          const characterLimit = data.meta.character_limit;
          const needsUpgrade = data.meta.needs_upgrade;
          
          if (needsUpgrade && characterLimit !== -1 && currentCount >= characterLimit) {
            setIsFormDisabled(true);
            setCharacterLimitError({
              message: `You've reached the character limit (${characterLimit} characters). Upgrade to premium for unlimited characters.`,
              character_limit: characterLimit,
              current_count: currentCount,
              needs_upgrade: needsUpgrade,
              subscription_status: data.meta.subscription_status
            });
          }
        }
      } catch (error) {
        console.error('Error checking character limits:', error);
        // If there's an error, allow form to be used (fail open)
      } finally {
        setIsLoading(false);
      }
    };
    
    checkCharacterLimits();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { id, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [id]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Check if form is disabled due to character limits
    if (isFormDisabled) {
      toast({
        title: "Character limit reached",
        description: "Please upgrade to premium to create more characters.",
        variant: "destructive"
      });
      return;
    }
    
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

      // Process brain dump to create character using JWT authentication
      // Keep it simple - just send the brain_dump field
      const brainDumpPayload = {
        brain_dump: formData.brainDump || ''
      };
      
      console.log('Brain dump payload:', brainDumpPayload);
      
      const processedData = await fetchWithRefresh(
        `${getApiUrl()}/api/characters/process`,
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
        `${getApiUrl()}/api/characters/mgmt`,
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
      
    } catch (error: any) {
      console.error('Error creating character:', error);
      
      // Handle character limit error specifically
      if (error.type === 'CHARACTER_LIMIT') {
        setCharacterLimitError(error.data);
        toast({
          title: "Character limit reached",
          description: error.data.message,
          variant: "destructive"
        });
      } else {
        toast({
          title: "Error creating character",
          description: error instanceof Error ? error.message : "An unknown error occurred",
          variant: "destructive"
        });
      }
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

        {/* Character Limit Error Hero */}
        {characterLimitError && (
          <Card className="border-red-200 bg-gradient-to-r from-red-50 to-orange-50">
            <CardHeader>
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-red-600" />
                <CardTitle className="text-red-900">Character Limit Reached</CardTitle>
              </div>
              <CardDescription className="text-red-700">
                {characterLimitError.message}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4">
                <Button className="bg-amber-600 hover:bg-amber-700">
                  <Crown className="mr-2 h-4 w-4" />
                  Upgrade to Premium
                </Button>
                <div className="text-sm text-red-700">
                  <strong>Current limit:</strong> {characterLimitError.character_limit} characters
                  <br />
                  <strong>You have:</strong> {characterLimitError.current_count} characters
                </div>
              </div>
            </CardContent>
          </Card>
        )}
        <form onSubmit={handleSubmit}>
          <Card className={isFormDisabled ? "opacity-50" : ""}>
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
                      disabled={isFormDisabled || isLoading}
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
                      disabled={isFormDisabled || isLoading}
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
                  disabled={isFormDisabled || isLoading}
                  required
                />
              </div>
            </CardContent>
          </Card>
          <div className="flex justify-end gap-2 mt-6">
            <Button variant="outline" asChild>
              <Link href="/dashboard/characters">Cancel</Link>
            </Button>
            <Button type="submit" disabled={isSubmitting || isFormDisabled || isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Checking limits...
                </>
              ) : isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : isFormDisabled ? (
                'Character Limit Reached'
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
