'use client';

import { useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from "@/components/ui/button";
import { Loader2 } from 'lucide-react';
import { getApiUrl } from '@/utils/api-utils';

interface CharacterCheckWrapperProps {
  children: ReactNode;
  redirectPath?: string;
}

export function CharacterCheckWrapper({ 
  children, 
  redirectPath = '/dashboard/characters/create' 
}: CharacterCheckWrapperProps) {
  const [hasCharacters, setHasCharacters] = useState<boolean | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const checkForCharacters = async () => {
      setIsLoading(true);
      try {
        const token = localStorage.getItem('access_token');
        if (!token) {
          // If not logged in, redirect to login
          router.push('/login');
          return;
        }

        // Use the character management API to check if user has characters
        const response = await fetch(`${getApiUrl()}/api/characters/mgmt`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch characters');
        }

        const data = await response.json();
        // Check if user has any characters
        const hasAnyCharacters = data.success && data.data && data.data.length > 0;
        setHasCharacters(hasAnyCharacters);
        
        // If no characters, redirect to character creation
        if (!hasAnyCharacters) {
          router.push(redirectPath);
        }
      } catch (err) {
        console.error('Error checking for characters:', err);
        setHasCharacters(false);
        // On error, redirect to character creation to be safe
        router.push(redirectPath);
      } finally {
        setIsLoading(false);
      }
    };

    checkForCharacters();
  }, [router, redirectPath]);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin mb-4" />
        <p className="text-muted-foreground">Checking character information...</p>
      </div>
    );
  }

  // Only render children if user has characters
  return hasCharacters ? <>{children}</> : null;
}
