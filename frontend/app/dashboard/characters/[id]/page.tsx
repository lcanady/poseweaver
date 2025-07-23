'use client';

import React from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useCharacter } from "@/hooks/useCharacter";
import { CharacterHeader } from "@/components/character-header";
import { CharacterMetadata } from "@/components/character-metadata";
import { CharacterActions } from "@/components/character-actions";
import { LoadingState } from "@/components/loading-state";
import { ErrorState } from "@/components/error-state";

export default function CharacterDetailPage({ params }: { params: Promise<{ id: string }> }) {
  // Unwrap params using React.use to fix Next.js warnings
  const unwrappedParams = React.use(params);
  const { character, isLoading, error } = useCharacter(unwrappedParams.id);

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
            <CharacterActions characterId={unwrappedParams.id} />
          )}
        </div>
        
        {isLoading ? (
          <LoadingState message="Loading character..." />
        ) : error ? (
          <ErrorState message="Failed to load character. Please try again later." />
        ) : character ? (
          <Card>
            <CharacterHeader character={character} />
            <CardContent>
              <CharacterMetadata character={character} />
            </CardContent>
          </Card>
        ) : (
          <ErrorState message="Character not found." />
        )}
      </div>
    </div>
  );
}
