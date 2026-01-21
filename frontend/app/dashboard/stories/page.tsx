'use client';

import { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  PlusCircle,
  Loader2,
  Search,
  Filter,
  BookOpen,
  Calendar,
  Sparkles
} from "lucide-react"
import { SceneCard } from "@/components/scene-card"
import Link from "next/link"
import { toast } from "@/components/ui/use-toast"
import { getApiUrl } from '@/utils/api-utils';
import { useAuth } from '@/contexts/auth-context';
import type { Scene } from '@/types/scene';

export default function StoriesPage() {
  const { getToken } = useAuth();
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [filteredScenes, setFilteredScenes] = useState<Scene[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('recent');

  const fetchWithAuth = async (url: string, options: RequestInit = {}) => {
    try {
      const token = await getToken();
      if (!token) throw new Error('No access token found. Please log in.');

      const headers = {
        ...options.headers,
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      };

      return await fetch(url, { ...options, headers });
    } catch (error) {
      console.error("Fetch error:", error);
      throw error;
    }
  };

  useEffect(() => {
    let filtered = scenes.filter(scene =>
      (scene.name || scene.title || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (scene.description || '').toLowerCase().includes(searchQuery.toLowerCase())
    );

    switch (sortBy) {
      case 'name':
        filtered.sort((a, b) => (a.name || a.title || '').localeCompare(b.name || b.title || ''));
        break;
      case 'oldest':
        filtered.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
        break;
      case 'recent':
      default:
        filtered.sort((a, b) => new Date(b.updated_at || b.created_at).getTime() - new Date(a.updated_at || a.created_at).getTime());
        break;
    }

    setFilteredScenes(filtered);
  }, [scenes, searchQuery, sortBy]);

  useEffect(() => {
    const fetchScenes = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetchWithAuth(`${getApiUrl()}/api/scenes`);
        if (!response.ok) throw new Error(`Failed to fetch scenes: ${response.status}`);

        const data = await response.json();
        if (data.success === false) throw new Error(data.message || 'Failed to fetch scenes');

        setScenes(data.data || []);
      } catch (err) {
        console.error('Error fetching scenes:', err);
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
        toast({
          title: "Error",
          description: err instanceof Error ? err.message : 'Failed to load scenes',
          variant: "destructive"
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchScenes();
  }, []);

  return (
    <div className="flex-1 p-4 md:p-8">
      <div className="mx-auto grid w-full max-w-7xl gap-8">
        <div className="flex flex-col gap-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Your Stories</h1>
              <p className="text-muted-foreground mt-1">Manage and continue your roleplay scenes.</p>
            </div>
            <Button asChild>
              <Link href="/dashboard/stories/create">
                <PlusCircle className="mr-2 h-4 w-4" />
                New Story
              </Link>
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Stories</CardTitle>
                <BookOpen className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{scenes.length}</div>
                <p className="text-xs text-muted-foreground">Across all categories</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active This Session</CardTitle>
                <Sparkles className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {scenes.filter(s => s.status === 'Ongoing').length}
                </div>
                <p className="text-xs text-muted-foreground">Ongoing story arcs</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Poses</CardTitle>
                <Calendar className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {scenes.reduce((acc, s) => acc + (s.pose_count || 0), 0)}
                </div>
                <p className="text-xs text-muted-foreground">Contributions across stories</p>
              </CardContent>
            </Card>
          </div>

          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search stories by name or description..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="recent">Recently Updated</SelectItem>
                  <SelectItem value="oldest">Oldest First</SelectItem>
                  <SelectItem value="name">Name (A-Z)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="flex justify-center items-center py-12">
            <Loader2 className="h-8 w-8 animate-spin mr-2" />
            <span>Loading stories...</span>
          </div>
        ) : error ? (
          <div className="text-center py-8 text-muted-foreground">
            <p>Failed to load stories. Please try again later.</p>
          </div>
        ) : scenes.length === 0 ? (
          <div className="text-center py-8">
            <h2 className="text-xl font-semibold mb-2">No stories yet</h2>
            <p className="text-muted-foreground mb-6">Start your first roleplay scene to get started</p>
            <Button asChild>
              <Link href="/dashboard/stories/create">
                <PlusCircle className="mr-2 h-4 w-4" />
                Create Your First Story
              </Link>
            </Button>
          </div>
        ) : filteredScenes.length === 0 ? (
          <div className="text-center py-8">
            <div className="mx-auto w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
              <Search className="h-8 w-8 text-muted-foreground" />
            </div>
            <h2 className="text-xl font-semibold mb-2">No stories found</h2>
            <p className="text-muted-foreground mb-4">
              Try adjusting your search terms.
            </p>
            <Button variant="outline" onClick={() => setSearchQuery('')}>
              Clear Search
            </Button>
          </div>
        ) : (
          <div className="grid gap-6">
            {filteredScenes.map((scene) => (
              <SceneCard key={scene.id} scene={scene as any} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
