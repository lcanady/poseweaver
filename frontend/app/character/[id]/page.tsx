'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { 
  ArrowLeft, 
  User, 
  BookOpen, 
  Zap,
  TrendingUp,
  Target,
  Calendar,
  Share2,
  ExternalLink,
  Home,
  Users,
  Feather
} from "lucide-react";
import { useCharacter } from "@/hooks/useCharacter";
import { LoadingState } from "@/components/loading-state";
import { ErrorState } from "@/components/error-state";

export default function PublicCharacterProfilePage({ params }: { params: Promise<{ id: string }> }) {
  // Unwrap params using React.use to fix Next.js warnings
  const unwrappedParams = React.use(params);
  const { character, isLoading, error } = useCharacter(unwrappedParams.id);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        {/* Site Header */}
        <header className="border-b bg-card">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <Link href="/" className="flex items-center space-x-2">
                <div className="h-10 w-10 bg-primary rounded-full flex items-center justify-center">
                  <Feather className="h-5 w-5 text-primary-foreground" />
                </div>
                <span className="text-xl font-bold">PoseWeaver</span>
              </Link>
              <nav className="flex items-center space-x-4">
                <Button variant="ghost" size="sm" asChild>
                  <Link href="/">
                    <Home className="h-4 w-4 mr-2" />
                    Home
                  </Link>
                </Button>
              </nav>
            </div>
          </div>
        </header>
        
        <div className="container mx-auto px-4 py-8">
          <LoadingState message="Loading character profile..." />
        </div>
      </div>
    );
  }

  if (error || !character) {
    return (
      <div className="min-h-screen bg-background">
        {/* Site Header */}
        <header className="border-b bg-card">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <Link href="/" className="flex items-center space-x-2">
                <div className="h-10 w-10 bg-primary rounded-full flex items-center justify-center">
                  <Feather className="h-5 w-5 text-primary-foreground" />
                </div>
                <span className="text-xl font-bold">PoseWeaver</span>
              </Link>
              <nav className="flex items-center space-x-4">
                <Button variant="ghost" size="sm" asChild>
                  <Link href="/">
                    <Home className="h-4 w-4 mr-2" />
                    Home
                  </Link>
                </Button>
              </nav>
            </div>
          </div>
        </header>
        
        <div className="container mx-auto px-4 py-8">
          <ErrorState message={error || "Character not found."} />
        </div>
      </div>
    );
  }

  const { metadata } = character;

  // Filter out sensitive information for public view
  const publicPersonalityTraits = metadata?.personality?.slice(0, 6) || []; // Limit to 6 traits
  const publicSkills = metadata?.skills?.slice(0, 8) || []; // Limit to 8 skills
  const publicGoals = metadata?.goals?.slice(0, 3) || []; // Limit to 3 goals

  return (
    <div className="min-h-screen bg-background">
      {/* Site Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-2">
              <div className="h-10 w-10 bg-primary rounded-full flex items-center justify-center">
                <Feather className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-bold">PoseWeaver</span>
            </Link>
            <nav className="flex items-center space-x-4">
              <Button variant="ghost" size="sm" asChild>
                <Link href="/">
                  <Home className="h-4 w-4 mr-2" />
                  Home
                </Link>
              </Button>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/dashboard/characters">
                  <Users className="h-4 w-4 mr-2" />
                  Characters
                </Link>
              </Button>
            </nav>
          </div>
        </div>
      </header>
      
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" asChild>
              <Link href="/dashboard/characters">
                <ArrowLeft className="h-4 w-4" />
              </Link>
            </Button>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Character Profile</h1>
              <p className="text-muted-foreground">Public character information</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              <Share2 className="h-4 w-4 mr-2" />
              Share Profile
            </Button>
          </div>
        </div>

        <div className="space-y-8">
          {/* Character Overview Card */}
          <Card>
            <CardHeader>
              <div className="flex items-start gap-6">
                <Avatar className="h-24 w-24">
                  <AvatarImage 
                    src={character.profile_image || "/placeholder.svg?width=96&height=96"} 
                    alt={character.name} 
                  />
                  <AvatarFallback className="text-2xl">
                    {character.name.charAt(0)}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <CardTitle className="text-3xl">{character.name}</CardTitle>
                    <Badge variant="outline">Public Profile</Badge>
                  </div>
                  <CardDescription className="text-base mb-4">
                    {character.description || "A character in the world of roleplay"}
                  </CardDescription>
                  <div className="flex items-center gap-6 text-sm text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4" />
                      Created {character.created_at ? new Date(character.created_at).toLocaleDateString() : 'Unknown'}
                    </div>
                  </div>
                </div>
              </div>
            </CardHeader>
          </Card>

          {/* Public Character Information */}
          <div className="space-y-6">
            {/* Basic Background (Limited) */}
            {metadata?.background && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <User className="h-5 w-5" />
                    Background
                  </CardTitle>
                  <CardDescription>
                    Public character background and history
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="bg-muted/30 border border-border/50 rounded-lg p-4">
                    <p className="text-sm whitespace-pre-wrap leading-relaxed">
                      {/* Truncate background to first 300 characters for public view */}
                      {metadata.background.length > 300 
                        ? metadata.background.substring(0, 300) + "..." 
                        : metadata.background
                      }
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Public Personality Traits (Limited) */}
            {publicPersonalityTraits.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Zap className="h-5 w-5" />
                    Personality Highlights
                  </CardTitle>
                  <CardDescription>
                    Key personality traits and characteristics
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                    {publicPersonalityTraits.map((trait: string, index: number) => (
                      <div key={index} className="bg-muted/30 border border-border/50 rounded-lg p-3">
                        <p className="text-sm font-medium">{trait}</p>
                      </div>
                    ))}
                  </div>
                  {(metadata?.personality?.length || 0) > 6 && (
                    <p className="text-xs text-muted-foreground mt-3 text-center">
                      And {(metadata?.personality?.length || 0) - 6} more traits...
                    </p>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Public Skills (Limited) */}
            {publicSkills.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    Notable Skills
                  </CardTitle>
                  <CardDescription>
                    Known abilities and competencies
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {publicSkills.map((skill: string, index: number) => (
                      <div key={index} className="flex items-center gap-3 bg-muted/30 border border-border/50 rounded-lg p-3">
                        <div className="h-2 w-2 rounded-full bg-primary" />
                        <p className="text-sm">{skill}</p>
                      </div>
                    ))}
                  </div>
                  {(metadata?.skills?.length || 0) > 8 && (
                    <p className="text-xs text-muted-foreground mt-3 text-center">
                      And {(metadata?.skills?.length || 0) - 8} more skills...
                    </p>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Public Goals (Very Limited) */}
            {publicGoals.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Target className="h-5 w-5" />
                    Known Aspirations
                  </CardTitle>
                  <CardDescription>
                    Public goals and motivations
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {publicGoals.map((goal: string, index: number) => (
                      <div key={index} className="bg-muted/30 border border-border/50 rounded-lg p-4">
                        <p className="text-sm leading-relaxed">
                          {/* Truncate goals to 150 characters for public view */}
                          {goal.length > 150 ? goal.substring(0, 150) + "..." : goal}
                        </p>
                      </div>
                    ))}
                  </div>
                  {(metadata?.goals?.length || 0) > 3 && (
                    <p className="text-xs text-muted-foreground mt-3 text-center">
                      And other private aspirations...
                    </p>
                  )}
                </CardContent>
              </Card>
            )}
          </div>

          {/* Public Profile Info */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5" />
                Profile Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Profile Type</span>
                    <span className="font-medium">Public Character</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Personality Traits</span>
                    <span className="font-medium">
                      {publicPersonalityTraits.length} shown
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Skills Listed</span>
                    <span className="font-medium">
                      {publicSkills.length} shown
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Public Goals</span>
                    <span className="font-medium">
                      {publicGoals.length} shown
                    </span>
                  </div>
                </div>
                
                <div className="bg-muted/30 border border-border/50 rounded-lg p-4">
                  <h4 className="font-medium mb-2">About Public Profiles</h4>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    This is a public view of the character showing only general information. 
                    Detailed background, personal relationships, and private character notes 
                    are not displayed to maintain character privacy.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Footer */}
          <div className="text-center py-8">
            <p className="text-sm text-muted-foreground">
              This is a public character profile. Some information may be limited or abbreviated.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
