'use client';

import { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Loader2,
  GitGraph,
  AlertCircle,
  CheckCircle2,
  Clock,
  ArrowRight
} from "lucide-react"
import Link from "next/link"
import { toast } from "@/components/ui/use-toast"
import { getApiUrl } from '@/utils/api-utils';
import { useAuth } from '@/contexts/auth-context';
import type { Scene } from '@/types/scene';

interface PlotThread {
  id: string;
  title: string;
  description: string;
  status: 'active' | 'resolved' | 'abandoned';
  importance: number;
  created_at: string;
  updated_at: string;
}

export default function PlotTrackerPage() {
  const { getToken } = useAuth();
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [selectedSceneId, setSelectedSceneId] = useState<string | null>(null);
  const [threads, setThreads] = useState<PlotThread[]>([]);
  const [isLoadingScenes, setIsLoadingScenes] = useState(true);
  const [isLoadingThreads, setIsLoadingThreads] = useState(false);

  const fetchWithAuth = async (url: string, options: RequestInit = {}) => {
    try {
      const token = await getToken();
      if (!token) throw new Error('No access token found.');
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
    const fetchScenes = async () => {
      try {
        const response = await fetchWithAuth(`${getApiUrl()}/api/scenes`);
        if (response.ok) {
          const data = await response.json();
          setScenes(data.data || []);
          if (data.data && data.data.length > 0) {
            setSelectedSceneId(data.data[0].id);
          }
        }
      } catch (err) {
        console.error('Error fetching scenes:', err);
      } finally {
        setIsLoadingScenes(false);
      }
    };
    fetchScenes();
  }, []);

  useEffect(() => {
    if (!selectedSceneId) return;

    const fetchThreads = async () => {
      setIsLoadingThreads(true);
      try {
        const response = await fetchWithAuth(`${getApiUrl()}/api/character-plot/plot-threads/${selectedSceneId}`);
        if (response.ok) {
          const data = await response.json();
          setThreads(data.data || []);
        } else {
          setThreads([]);
        }
      } catch (err) {
        console.error('Error fetching threads:', err);
        setThreads([]);
      } finally {
        setIsLoadingThreads(false);
      }
    };
    fetchThreads();
  }, [selectedSceneId]);

  return (
    <div className="flex-1 p-4 md:p-8">
      <div className="mx-auto grid w-full max-w-7xl gap-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Plot Tracker</h1>
            <p className="text-muted-foreground mt-1">Track storylines, character arcs, and narrative threads.</p>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium">Select Story:</span>
            <Select value={selectedSceneId || ''} onValueChange={setSelectedSceneId}>
              <SelectTrigger className="w-[250px]">
                <SelectValue placeholder="Select a story..." />
              </SelectTrigger>
              <SelectContent>
                {scenes.map(scene => (
                  <SelectItem key={scene.id} value={scene.id}>
                    {scene.name || scene.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {isLoadingScenes ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin" />
          </div>
        ) : scenes.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <GitGraph className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold">No stories found</h3>
              <p className="text-muted-foreground mb-6">You need to create a story before you can track its plot.</p>
              <Button asChild>
                <Link href="/dashboard/stories/create">Create your first story</Link>
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6">
            {isLoadingThreads ? (
              <div className="flex justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : threads.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold">No plot threads identified</h3>
                  <p className="text-muted-foreground">The AI hasn't identified any plot threads for this story yet. Threads are automatically extracted as you write poses.</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {threads.map(thread => (
                  <Card key={thread.id} className="overflow-hidden">
                    <CardHeader className="pb-2">
                      <div className="flex justify-between items-start">
                        <Badge variant={
                          thread.status === 'active' ? 'default' :
                            thread.status === 'resolved' ? 'outline' : 'secondary'
                        } className="mb-2">
                          {thread.status}
                        </Badge>
                        <div className="flex items-center gap-1 text-xs text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          {new Date(thread.updated_at).toLocaleDateString()}
                        </div>
                      </div>
                      <CardTitle className="text-lg">{thread.title}</CardTitle>
                      <CardDescription className="line-clamp-2">{thread.description}</CardDescription>
                    </CardHeader>
                    <CardContent className="pb-4">
                      <div className="flex items-center justify-between text-sm">
                        <span>Importance</span>
                        <div className="flex gap-1">
                          {[1, 2, 3, 4, 5].map(i => (
                            <div
                              key={i}
                              className={`h-2 w-4 rounded-full ${i <= (thread.importance * 5) ? 'bg-primary' : 'bg-muted'}`}
                            />
                          ))}
                        </div>
                      </div>
                    </CardContent>
                    <div className="p-4 bg-muted/30 border-t flex justify-between items-center">
                      <span className="text-xs font-medium uppercase text-muted-foreground">View Timeline</span>
                      <ArrowRight className="h-4 w-4 text-muted-foreground" />
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
