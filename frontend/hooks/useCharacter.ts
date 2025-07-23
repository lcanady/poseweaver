import { useState, useEffect } from 'react';
import { toast } from "@/components/ui/use-toast";

export interface Character {
  id: string;
  name: string;
  description: string;
  profile_image?: string;
  metadata?: {
    background?: string;
    personality?: string[];
    skills?: string[];
    goals?: string[];
    voice_notes?: string;
  };
  created_at?: string;
  last_used?: string;
}

export function useCharacter(characterId: string) {
  const [character, setCharacter] = useState<Character | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCharacter = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        const accessToken = localStorage.getItem('access_token');
        
        if (!accessToken) {
          throw new Error('No access token found. Please log in again.');
        }
        
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/characters/mgmt/${characterId}`, 
          {
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${accessToken}`
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
        
        setCharacter(data.data);
      } catch (err) {
        console.error('Error fetching character:', err);
        const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
        setError(errorMessage);
        toast({
          title: "Error",
          description: errorMessage,
          variant: "destructive"
        });
      } finally {
        setIsLoading(false);
      }
    };
    
    if (characterId) {
      fetchCharacter();
    }
  }, [characterId]);

  return { character, isLoading, error, refetch: () => setCharacter(null) };
}