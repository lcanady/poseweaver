'use client';

import { useState, useEffect } from 'react';
import React from 'react';
import { useRouter } from 'next/navigation';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";
import { Loader2, ArrowLeft, Edit, Trash } from "lucide-react";
import { toast } from "@/components/ui/use-toast";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface Character {
  id: string;
  name: string;
  description: string;
  profile_image?: string;
  metadata?: any;
  created_at?: string;
  last_used?: string;
}

export default function CharacterDetailPage({ params }: { params: Promise<{ id: string }> }) {
  // Unwrap params using React.use to fix Next.js warnings
  const unwrappedParams = React.use(params);
  const router = useRouter();
  const [character, setCharacter] = useState<Character | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const fetchCharacter = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        // Get access token from localStorage
        const accessToken = localStorage.getItem('access_token');
        
        if (!accessToken) {
          throw new Error('No access token found. Please log in again.');
        }
        
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/characters/mgmt/${unwrappedParams.id}`, 
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

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this character? This action cannot be undone.')) {
      return;
    }

    setIsDeleting(true);
    
    try {
      // Get access token from localStorage
      const accessToken = localStorage.getItem('access_token');
      
      if (!accessToken) {
        throw new Error('No access token found. Please log in again.');
      }
      
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/characters/mgmt/${unwrappedParams.id}`, 
        {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`
          }
        }
      );
      
      if (!response.ok) {
        throw new Error('Failed to delete character');
      }
      
      toast({
        title: "Character deleted",
        description: "Character has been successfully deleted."
      });
      
      router.push('/dashboard/characters');
    } catch (err) {
      console.error('Error deleting character:', err);
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : 'Failed to delete character',
        variant: "destructive"
      });
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="flex-1 p-4 md:p-8">
      <div className="mx-auto grid w-full max-w-4xl gap-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" asChild>
              <Link href="/dashboard/characters">
                <ArrowLeft className="h-4 w-4" />
              </Link>
            </Button>
            <h1 className="text-3xl font-bold tracking-tight">Character Details</h1>
          </div>
          
          {!isLoading && character && (
            <div className="flex gap-2">
              <Button variant="outline" asChild>
                <Link href={`/dashboard/characters/${unwrappedParams.id}/edit`}>
                  <Edit className="mr-2 h-4 w-4" />
                  Edit
                </Link>
              </Button>
              <Button variant="destructive" onClick={handleDelete} disabled={isDeleting}>
                {isDeleting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash className="mr-2 h-4 w-4" />
                    Delete
                  </>
                )}
              </Button>
            </div>
          )}
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
        ) : character ? (
          <>
            <Card>
              <CardHeader className="flex flex-row items-center gap-4">
                <Avatar className="h-20 w-20">
                  <AvatarImage 
                    src={character.profile_image || "/placeholder.svg?width=80&height=80"} 
                    alt={character.name} 
                  />
                  <AvatarFallback>{character.name.charAt(0)}</AvatarFallback>
                </Avatar>
                <div>
                  <CardTitle className="text-2xl">{character.name}</CardTitle>
                  <p className="text-muted-foreground">
                    Created: {character.created_at ? new Date(character.created_at).toLocaleDateString() : 'Unknown'}
                  </p>
                  {character.last_used && (
                    <p className="text-muted-foreground">
                      Last used: {new Date(character.last_used).toLocaleDateString()}
                    </p>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold mb-2">Description</h3>
                  <p>{character.description}</p>
                </div>
                
                {character.metadata && (
                  <>
                    {character.metadata.background && (
                      <div>
                        <h3 className="text-lg font-semibold mb-2">Background</h3>
                        <p className="whitespace-pre-wrap">{character.metadata.background}</p>
                      </div>
                    )}
                    
                    {character.metadata.personality && character.metadata.personality.length > 0 && (
                      <div>
                        <h3 className="text-lg font-semibold mb-2">Personality</h3>
                        <ul className="list-disc pl-5 space-y-1">
                          {character.metadata.personality.map((trait: string, index: number) => (
                            <li key={index}>{trait}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {character.metadata.skills && character.metadata.skills.length > 0 && (
                      <div>
                        <h3 className="text-lg font-semibold mb-2">Skills</h3>
                        <ul className="list-disc pl-5 space-y-1">
                          {character.metadata.skills.map((skill: string, index: number) => (
                            <li key={index}>{skill}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {character.metadata.goals && character.metadata.goals.length > 0 && (
                      <div>
                        <h3 className="text-lg font-semibold mb-2">Goals</h3>
                        <ul className="list-disc pl-5 space-y-1">
                          {character.metadata.goals.map((goal: string, index: number) => (
                            <li key={index}>{goal}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {character.metadata.voice_notes && (
                      <div>
                        <h3 className="text-lg font-semibold mb-2">Voice Notes</h3>
                        <p className="whitespace-pre-wrap">{character.metadata.voice_notes}</p>
                      </div>
                    )}
                  </>
                )}
              </CardContent>
            </Card>
          </>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            <p>Character not found.</p>
          </div>
        )}
      </div>
    </div>
  );
}
