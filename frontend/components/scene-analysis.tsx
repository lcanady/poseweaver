"use client"

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Lightbulb, MessageSquareQuote, AlertCircle, ChevronDown, ChevronRight, Loader2 } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { useState } from "react"
import type { PoseContext, ResponseSuggestion } from "@/types/context"

type SceneAnalysisProps = {
  context: PoseContext | null;
  suggestions: ResponseSuggestion[];
  isLoading: boolean;
  error: string | null;
}

export function SceneAnalysis({ context, suggestions = [], isLoading = false, error }: SceneAnalysisProps) {
  const [expandedSections, setExpandedSections] = useState<{
    responseHooks: boolean;
    actions: boolean;
    emotions: boolean;
  }>({
    responseHooks: false,
    actions: false,
    emotions: false,
  });

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // If loading, show skeleton UI
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Loader2 className="h-5 w-5 animate-spin" />
            Scene Analysis
          </CardTitle>
          <CardDescription>Analyzing scene context and generating suggestions...</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Loading badges */}
          <div className="flex items-center gap-2">
            <Skeleton className="h-6 w-20" />
            <Skeleton className="h-6 w-32" />
          </div>
          
          {/* Loading sections */}
          <div className="space-y-4">
            <div>
              <Skeleton className="h-4 w-24 mb-2" />
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6" />
                <Skeleton className="h-4 w-4/6" />
              </div>
            </div>
            <div>
              <Skeleton className="h-4 w-28 mb-2" />
              <div className="space-y-2">
                <Skeleton className="h-4 w-4/5" />
                <Skeleton className="h-4 w-3/5" />
              </div>
            </div>
            <div>
              <Skeleton className="h-4 w-32 mb-2" />
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-2/3" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            </div>
          </div>
          
          {/* Progress indicator */}
          <div className="mt-4 p-3 rounded-md bg-blue-50 dark:bg-blue-900/30">
            <div className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
              <span className="text-sm text-blue-700 dark:text-blue-300">
                Processing scene context and extracting response opportunities...
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  // If error, show error state
  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Scene Analysis</CardTitle>
          <CardDescription>An error occurred during analysis.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="p-4 rounded-lg bg-red-50 text-red-600 flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            <p>{error}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // If no context yet, show empty state
  if (!context) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Scene Analysis</CardTitle>
          <CardDescription>Add scene text and a post to generate analysis.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">Click the "Enhance Post" button to analyze the scene context.</p>
        </CardContent>
      </Card>
    )
  }

  // With context, show streamlined analysis
  return (
    <Card className="overflow-auto max-h-[calc(100vh-8rem)]">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">Scene Analysis</CardTitle>
        <div className="flex flex-wrap gap-2 mt-2">
          <Badge variant="secondary" className="text-xs">
            {context.narrative_tone || context.tone || 'Neutral'}
          </Badge>
          <Badge variant={(context.urgency || context.urgency_level) === 'low' ? 'secondary' : 
                        (context.urgency || context.urgency_level) === 'medium' ? 'outline' : 'destructive'}
                className="text-xs">
            {((context.urgency || context.urgency_level) || 'Medium').charAt(0).toUpperCase() + 
             ((context.urgency || context.urgency_level) || 'medium').slice(1)} Urgency
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 pt-0">
        {/* Top Response Hooks - Most Important */}
        {context.responseHooks?.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
              <Lightbulb className="h-4 w-4 text-primary" />
              Key Response Opportunities
            </h3>
            <div className="space-y-1">
              {(expandedSections.responseHooks ? context.responseHooks : context.responseHooks.slice(0, 3)).map((hook: string, index: number) => (
                <div key={`hook-${index}`} className="text-xs bg-muted/50 rounded px-2 py-1">
                  {hook}
                </div>
              ))}
              {context.responseHooks.length > 3 && (
                <button
                  onClick={() => toggleSection('responseHooks')}
                  className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 mt-1"
                >
                  {expandedSections.responseHooks ? (
                    <>
                      <ChevronDown className="h-3 w-3" />
                      Show less
                    </>
                  ) : (
                    <>
                      <ChevronRight className="h-3 w-3" />
                      +{context.responseHooks.length - 3} more
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        )}

        {/* Compact Key Information */}
        <div className="grid grid-cols-1 gap-3 text-xs">
                     {/* Actions - Top 2 */}
           {context.actions?.length > 0 && (
             <div>
               <h4 className="font-medium text-muted-foreground mb-1">Recent Actions</h4>
               <div className="space-y-1">
                 {(expandedSections.actions ? context.actions : context.actions.slice(0, 2)).map((action: string, index: number) => (
                   <div key={`action-${index}`} className="text-foreground">• {action}</div>
                 ))}
                 {context.actions.length > 2 && (
                   <button
                     onClick={() => toggleSection('actions')}
                     className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 mt-1"
                   >
                     {expandedSections.actions ? (
                       <>
                         <ChevronDown className="h-3 w-3" />
                         Show less
                       </>
                     ) : (
                       <>
                         <ChevronRight className="h-3 w-3" />
                         +{context.actions.length - 2} more
                       </>
                     )}
                   </button>
                 )}
               </div>
             </div>
           )}

                     {/* Emotions - Top 3 */}
           {context.emotions?.length > 0 && (
             <div>
               <h4 className="font-medium text-muted-foreground mb-1">Emotions</h4>
               <div className="flex flex-wrap gap-1">
                 {(expandedSections.emotions ? context.emotions : context.emotions.slice(0, 3)).map((emotion: string, index: number) => (
                   <Badge key={`emotion-${index}`} variant="outline" className="text-xs py-0 px-1">
                     {emotion}
                   </Badge>
                 ))}
                 {context.emotions.length > 3 && (
                   <button
                     onClick={() => toggleSection('emotions')}
                     className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 ml-1"
                   >
                     {expandedSections.emotions ? (
                       <>
                         <ChevronDown className="h-3 w-3" />
                         Show less
                       </>
                     ) : (
                       <>
                         <ChevronRight className="h-3 w-3" />
                         +{context.emotions.length - 3}
                       </>
                     )}
                   </button>
                 )}
               </div>
             </div>
           )}

          {/* Setting - Condensed */}
          {context.setting && (
            <div>
              <h4 className="font-medium text-muted-foreground mb-1">Setting</h4>
              <div className="text-foreground line-clamp-2">{context.setting}</div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
