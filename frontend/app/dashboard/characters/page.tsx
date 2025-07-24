'use client';

import { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { PlusCircle, Loader2, Crown, AlertTriangle } from "lucide-react"
import { CharacterCard } from "@/components/character-card"
import Link from "next/link"
import { toast } from "@/components/ui/use-toast"

// Define the Character type to match the one from lib/types.ts
interface Character {
  id: string;
  name: string;
  description: string;
  avatarUrl: string; // Making this required to match the imported type
  lastUsed: string; // Making this required to match the imported type
  created_at?: string;
}

interface SubscriptionMeta {
  character_limit: number;
  subscription_status: string;
  needs_upgrade: boolean;
}

export default function CharactersPage() {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [subscriptionMeta, setSubscriptionMeta] = useState<SubscriptionMeta | null>(null);

  // Function to fetch with token refresh capabilities
  const fetchWithRefresh = async (url: string, options: RequestInit = {}) => {
    // Get access token from localStorage
    const accessToken = localStorage.getItem('access_token');
    
    if (!accessToken) {
      throw new Error('No access token found. Please log in.');
    }
    
    // Prepare headers with authorization
    const headers = {
      ...options.headers,
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`,
    };
    
    // First attempt with current token
    let response = await fetch(url, { ...options, headers });
    
    // If unauthorized, try refreshing token
    if (response.status === 401) {
      console.log('Access token expired. Attempting to refresh...');
      const refreshToken = localStorage.getItem('refresh_token');
      
      if (!refreshToken) {
        throw new Error('No refresh token found. Please log in again.');
      }
      
      // Call refresh endpoint
      const refreshResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${refreshToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!refreshResponse.ok) {
        // If refresh fails, clear tokens and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        throw new Error('Session expired. Please log in again.');
      }
      
      // Get new tokens from refresh response
      const tokens = await refreshResponse.json();
      localStorage.setItem('access_token', tokens.access_token);
      
      // Retry original request with new token
      headers.Authorization = `Bearer ${tokens.access_token}`;
      response = await fetch(url, { ...options, headers });
    }
    
    // If still unauthorized after refresh attempt, redirect to login
    if (response.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
      throw new Error('Authentication failed. Please log in again.');
    }
    
    return response;
  };

  useEffect(() => {
    const fetchCharacters = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        // Use JWT token authentication
        const response = await fetchWithRefresh(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/characters/mgmt`
        );
        
        if (!response.ok) {
          throw new Error(`Failed to fetch characters: ${response.status}`);
        }
        
        const data = await response.json();
    
    // Debug: Log the raw response data
    console.log('API Response:', data);
    
    // Handle different response formats
    if (data.success === false) {
      console.error('API response indicates failure:', data);
      throw new Error(data.message || 'Failed to fetch characters');
    }
    
    // Extract subscription metadata
    if (data.meta) {
      setSubscriptionMeta({
        character_limit: data.meta.character_limit,
        subscription_status: data.meta.subscription_status,
        needs_upgrade: data.meta.needs_upgrade
      });
    }
    
    // Check if we have character data in the expected format
    const charactersData = data.data || data.characters || (Array.isArray(data) ? data : []);
    console.log('Characters data to process:', charactersData);
    
        // Transform the data to match our Character interface
        const formattedCharacters = charactersData.map((char: any) => ({
          id: char._id || char.id,
          name: char.name,
          description: char.description,
          avatarUrl: char.profile_image || '/placeholder.svg?width=40&height=40',
          // Format the date to a relative time string
          lastUsed: char.last_used ? new Date(char.last_used).toLocaleDateString() : 'Never used',
          created_at: char.created_at
        }));
        
        setCharacters(formattedCharacters);
      } catch (err) {
        console.error('Error fetching characters:', err);
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
        toast({
          title: "Error",
          description: err instanceof Error ? err.message : 'Failed to load characters',
          variant: "destructive"
        });
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchCharacters();
  }, []);

  return (
    <div className="flex-1 p-4 md:p-8">
      <div className="mx-auto grid w-full max-w-7xl gap-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Your Characters</h1>
            <div className="flex items-center gap-2 mt-1">
              <p className="text-muted-foreground">Manage your cast of characters for the AI to embody.</p>
              {subscriptionMeta && subscriptionMeta.character_limit !== -1 && (
                <Badge variant="outline" className="text-xs">
                  {characters.length}/{subscriptionMeta.character_limit} characters
                </Badge>
              )}
            </div>
          </div>
          <Button 
            asChild 
            disabled={subscriptionMeta?.needs_upgrade && characters.length >= (subscriptionMeta?.character_limit || 3)}
          >
            <Link href="/dashboard/characters/create">
              <PlusCircle className="mr-2 h-4 w-4" />
              Add New Character
            </Link>
          </Button>
        </div>

        {/* Upgrade Hero for Free/Expired Users */}
        {subscriptionMeta?.needs_upgrade && (
          <Card className="border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Crown className="h-5 w-5 text-amber-600" />
                <CardTitle className="text-amber-900">
                  {subscriptionMeta.subscription_status === 'expired' 
                    ? 'Premium Subscription Expired' 
                    : 'Unlock Unlimited Characters'
                  }
                </CardTitle>
              </div>
              <CardDescription className="text-amber-700">
                {subscriptionMeta.subscription_status === 'expired'
                  ? `Your premium subscription has expired. You can only access your first ${subscriptionMeta.character_limit} characters.`
                  : `You're currently limited to ${subscriptionMeta.character_limit} characters. Upgrade to premium for unlimited character creation and access.`
                }
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4">
                <Button className="bg-amber-600 hover:bg-amber-700">
                  <Crown className="mr-2 h-4 w-4" />
                  Upgrade to Premium
                </Button>
                <div className="text-sm text-amber-700">
                  <strong>Premium benefits:</strong> Unlimited characters, priority support, and more features
                </div>
              </div>
            </CardContent>
          </Card>
        )}
        {isLoading ? (
          <div className="flex justify-center items-center py-12">
            <Loader2 className="h-8 w-8 animate-spin mr-2" />
            <span>Loading characters...</span>
          </div>
        ) : error ? (
          <div className="text-center py-8 text-muted-foreground">
            <p>Failed to load characters. Please try again later.</p>
          </div>
        ) : characters.length === 0 ? (
          <div className="text-center py-8">
            <h2 className="text-xl font-semibold mb-2">No characters yet</h2>
            <p className="text-muted-foreground mb-6">Create your first character to get started</p>
            <Button asChild>
              <Link href="/dashboard/characters/create">
                <PlusCircle className="mr-2 h-4 w-4" />
                Create Your First Character
              </Link>
            </Button>
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            {characters.map((character) => (
              <CharacterCard key={character.id} character={character} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
