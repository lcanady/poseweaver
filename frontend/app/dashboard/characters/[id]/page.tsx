'use client';

import React from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import Link from "next/link";
import { 
  ArrowLeft, 
  Edit, 
  Calendar, 
  Clock, 
  User, 
  BookOpen, 
  Target, 
  Zap,
  TrendingUp,
  Settings,
  Download,
  Share2,
  ExternalLink
} from "lucide-react";
import { useCharacter } from "@/hooks/useCharacter";
import { LoadingState } from "@/components/loading-state";
import { ErrorState } from "@/components/error-state";
import { CharacterSettingsModal } from "@/components/character-settings-modal";
import { CharacterShareModal } from "@/components/character-share-modal";

export default function CharacterDetailPage({ params }: { params: Promise<{ id: string }> }) {
  // Unwrap params using React.use to fix Next.js warnings
  const unwrappedParams = React.use(params);
  const { character, isLoading, error } = useCharacter(unwrappedParams.id);

  if (isLoading) {
    return (
      <div className="flex-1 p-4 md:p-8">
        <div className="mx-auto w-full max-w-7xl">
          <LoadingState message="Loading character..." />
        </div>
      </div>
    );
  }

  if (error || !character) {
    return (
      <div className="flex-1 p-4 md:p-8">
        <div className="mx-auto w-full max-w-7xl">
          <ErrorState message={error || "Character not found."} />
        </div>
      </div>
    );
  }

  const { metadata } = character;

  return (
    <div className="flex-1 p-4 md:p-8">
      <div className="mx-auto w-full max-w-7xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" asChild>
              <Link href="/dashboard/characters">
                <ArrowLeft className="h-4 w-4" />
              </Link>
            </Button>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Character Details</h1>
              <p className="text-muted-foreground">Manage and view character information</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" asChild>
              <Link href={`/character/${unwrappedParams.id}`}>
                <ExternalLink className="h-4 w-4 mr-2" />
                View Public Profile
              </Link>
            </Button>
            <CharacterShareModal character={character}>
              <Button variant="outline" size="sm">
                <Share2 className="h-4 w-4 mr-2" />
                Share
              </Button>
            </CharacterShareModal>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Button size="sm" asChild>
              <Link href={`/dashboard/characters/${unwrappedParams.id}/edit`}>
                <Edit className="h-4 w-4 mr-2" />
                Edit Character
              </Link>
            </Button>
          </div>
        </div>

        <div className="grid gap-8 xl:grid-cols-[1fr_350px]">
          {/* Main Content */}
          <div className="space-y-8">
            {/* Character Overview Card */}
            <Card>
              <CardHeader>
                <div className="flex items-start gap-6">
                  <Avatar className="h-24 w-24">
                    <AvatarImage 
                      src={character.profile_image} 
                      alt={character.name} 
                    />
                    <AvatarFallback className="bg-muted">
                      <User className="h-1/2 w-1/2 text-muted-foreground" />
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <CardTitle className="text-3xl">{character.name}</CardTitle>
                      <Badge variant="secondary">Active</Badge>
                    </div>
                    <CardDescription className="text-base mb-4">
                      {character.description || "No description provided"}
                    </CardDescription>
                    <div className="flex items-center gap-6 text-sm text-muted-foreground">
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4" />
                        Created {character.created_at ? new Date(character.created_at).toLocaleDateString() : 'Unknown'}
                      </div>
                      {character.last_used && (
                        <div className="flex items-center gap-2">
                          <Clock className="h-4 w-4" />
                          Last used {new Date(character.last_used).toLocaleDateString()}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </CardHeader>
            </Card>

            {/* Character Information Cards */}
            <div className="space-y-6">
              {/* Background */}
              {metadata?.background && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <User className="h-5 w-5" />
                      Background
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="bg-muted/30 border border-border/50 rounded-lg p-4">
                      <p className="text-sm whitespace-pre-wrap leading-relaxed">
                        {metadata.background}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Voice Notes */}
              {metadata?.voice_notes && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BookOpen className="h-5 w-5" />
                      Voice & Style
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="bg-muted/30 border border-border/50 rounded-lg p-4">
                      <p className="text-sm whitespace-pre-wrap leading-relaxed">
                        {metadata.voice_notes}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Personality Traits */}
            {metadata?.personality && metadata.personality.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Zap className="h-5 w-5" />
                    Personality Traits
                  </CardTitle>
                  <CardDescription>
                    Key personality characteristics and behavioral patterns
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                    {metadata.personality.map((trait: string, index: number) => (
                      <div key={index} className="bg-muted/30 border border-border/50 rounded-lg p-3">
                        <p className="text-sm font-medium">{trait}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Skills & Abilities */}
            {metadata?.skills && metadata.skills.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    Skills & Abilities
                  </CardTitle>
                  <CardDescription>
                    Character competencies and special abilities
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {metadata.skills.map((skill: string, index: number) => (
                      <div key={index} className="flex items-center gap-3 bg-muted/30 border border-border/50 rounded-lg p-3">
                        <div className="h-2 w-2 rounded-full bg-primary" />
                        <p className="text-sm">{skill}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Goals & Motivations */}
            {metadata?.goals && metadata.goals.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Target className="h-5 w-5" />
                    Goals & Motivations
                  </CardTitle>
                  <CardDescription>
                    Character objectives and driving forces
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {metadata.goals.map((goal: string, index: number) => (
                      <div key={index} className="bg-muted/30 border border-border/50 rounded-lg p-4">
                        <p className="text-sm leading-relaxed">{goal}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6 sticky top-8">
            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <CharacterSettingsModal character={character}>
                  <Button variant="outline" className="w-full justify-start">
                    <Settings className="h-4 w-4 mr-2" />
                    Character Settings
                  </Button>
                </CharacterSettingsModal>
                <Button variant="outline" className="w-full justify-start" asChild>
                  <Link href={`/character/${unwrappedParams.id}`}>
                    <ExternalLink className="h-4 w-4 mr-2" />
                    View Public Profile
                  </Link>
                </Button>
                <Separator />
                <Button variant="outline" className="w-full justify-start">
                  <Download className="h-4 w-4 mr-2" />
                  Export Data
                </Button>
                <CharacterShareModal character={character}>
                  <Button variant="outline" className="w-full justify-start">
                    <Share2 className="h-4 w-4 mr-2" />
                    Share Character
                  </Button>
                </CharacterShareModal>
              </CardContent>
            </Card>

            {/* Character Statistics */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Usage Statistics</CardTitle>
                <CardDescription>
                  Character activity and usage metrics
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Total Poses</span>
                    <span className="text-sm font-medium">--</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">This Month</span>
                    <span className="text-sm font-medium">--</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Last Activity</span>
                    <span className="text-sm font-medium">
                      {character.last_used 
                        ? new Date(character.last_used).toLocaleDateString()
                        : 'Never'
                      }
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Character Info Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Personality Traits</span>
                    <span className="font-medium">
                      {metadata?.personality?.length || 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Skills Listed</span>
                    <span className="font-medium">
                      {metadata?.skills?.length || 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Goals Defined</span>
                    <span className="font-medium">
                      {metadata?.goals?.length || 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Profile Complete</span>
                    <Badge variant="secondary" className="text-xs">
                      {metadata?.background && (metadata?.personality?.length || 0) > 0 && (metadata?.skills?.length || 0) > 0 
                        ? 'Complete' 
                        : 'Partial'
                      }
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
