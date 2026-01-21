'use client';

import { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Search as SearchIcon,
  Loader2,
  FileText,
  Users,
  Calendar,
  Sparkles,
  ArrowRight
} from "lucide-react"
import { toast } from "@/components/ui/use-toast"
import { getApiUrl } from '@/utils/api-utils';
import { useAuth } from '@/contexts/auth-context';
import Link from 'next/link';

interface SearchResult {
  item_id: string;
  item_type: 'scene' | 'pose' | 'character';
  content_preview: string;
  relevance_score: number;
  timestamp: string;
  metadata: {
    scene_name?: string;
    character_name?: string;
    pose_type?: string;
  };
}

export default function SearchPage() {
  const { getToken } = useAuth();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [activeTab, setActiveTab] = useState('all');

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    try {
      const token = await getToken();
      const response = await fetch(`${getApiUrl()}/api/search-summary/search/scenes?q=${encodeURIComponent(query)}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        // The search endpoint might return different formats, let's normalize
        const transformedResults = (data.data || []).map((item: any) => ({
          item_id: item.id || item.item_id,
          item_type: item.item_type || 'scene',
          content_preview: item.description || item.content_preview || '',
          relevance_score: item.relevance_score || 0,
          timestamp: item.updated_at || item.timestamp || new Date().toISOString(),
          metadata: {
            scene_name: item.name || item.title || item.metadata?.scene_name
          }
        }));
        setResults(transformedResults);
      } else {
        toast({
          title: "Search failed",
          description: "Could not complete the search. Please try again.",
          variant: "destructive"
        });
      }
    } catch (err) {
      console.error('Search error:', err);
    } finally {
      setIsSearching(false);
    }
  };

  const filteredResults = activeTab === 'all' 
    ? results 
    : results.filter(r => r.item_type === activeTab);

  return (
    <div className="flex-1 p-4 md:p-8">
      <div className="mx-auto grid w-full max-w-7xl gap-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Search & Summary</h1>
          <p className="text-muted-foreground mt-1">Intelligent search across all your stories and characters.</p>
        </div>

        <form onSubmit={handleSearch} className="flex gap-4">
          <div className="relative flex-1">
            <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search for plot points, characters, or specific dialogue..."
              className="pl-10 h-12 text-lg"
            />
          </div>
          <Button type="submit" size="lg" disabled={isSearching}>
            {isSearching ? <Loader2 className="h-5 w-5 animate-spin mr-2" /> : <SearchIcon className="h-5 w-5 mr-2" />}
            Search
          </Button>
        </form>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList>
            <TabsTrigger value="all">All Results</TabsTrigger>
            <TabsTrigger value="scene">Stories</TabsTrigger>
            <TabsTrigger value="character">Characters</TabsTrigger>
            <TabsTrigger value="pose">Poses</TabsTrigger>
          </TabsList>

          <div className="mt-8">
            {isSearching ? (
              <div className="flex justify-center py-12">
                <Loader2 className="h-12 w-12 animate-spin text-primary" />
              </div>
            ) : filteredResults.length > 0 ? (
              <div className="grid gap-6">
                {filteredResults.map((result, idx) => (
                  <Card key={`${result.item_id}-${idx}`} className="hover:shadow-md transition-shadow">
                    <CardHeader className="pb-2">
                      <div className="flex justify-between items-start">
                        <div className="flex items-center gap-2">
                          {result.item_type === 'scene' && <FileText className="h-4 w-4 text-primary" />}
                          {result.item_type === 'character' && <Users className="h-4 w-4 text-purple-500" />}
                          {result.item_type === 'pose' && <Sparkles className="h-4 w-4 text-amber-500" />}
                          <Badge variant="outline" className="capitalize">{result.item_type}</Badge>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          Match Score: {Math.round(result.relevance_score * 100)}%
                        </span>
                      </div>
                      <CardTitle className="text-xl mt-2">
                        {result.metadata.scene_name || result.metadata.character_name || 'Untitled Result'}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-muted-foreground line-clamp-3 mb-4 italic">
                        "{result.content_preview}"
                      </p>
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-1 text-xs text-muted-foreground">
                          <Calendar className="h-3 w-3" />
                          {new Date(result.timestamp).toLocaleDateString()}
                        </div>
                        <Button variant="ghost" size="sm" asChild>
                          <Link href={result.item_type === 'scene' ? `/dashboard/stories` : `/dashboard/characters`}>
                            View Details <ArrowRight className="h-4 w-4 ml-2" />
                          </Link>
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : query && (
              <div className="text-center py-12 text-muted-foreground">
                <p className="text-xl">No results found for "{query}"</p>
                <p>Try different keywords or check your spelling.</p>
              </div>
            )}
          </div>
        </Tabs>
      </div>
    </div>
  );
}
