"use client"

import { PostEditor } from "@/components/post-editor"
import { SceneAnalysis } from "@/components/scene-analysis"
import { CharacterCheckWrapper } from "@/components/character-check-wrapper"
import { useState, useEffect, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { useToast } from "@/hooks/use-toast"
import type { PoseContext, ResponseSuggestion } from "@/types/context"

function SceneWeaverContent() {
  const [sceneContext, setSceneContext] = useState<PoseContext | null>(null);
  const [suggestions, setSuggestions] = useState<ResponseSuggestion[]>([]);
  const [contextLoading, setContextLoading] = useState(false);
  const [contextError, setContextError] = useState<string | null>(null);
  const [autoLoadSceneId, setAutoLoadSceneId] = useState<string | null>(null);
  const [seedPostText, setSeedPostText] = useState<((text: string) => void) | null>(null);
  
  const searchParams = useSearchParams();
  const { toast } = useToast();
  
  // Check for scene parameter in URL
  useEffect(() => {
    const sceneId = searchParams.get('scene');
    if (sceneId) {
      setAutoLoadSceneId(sceneId);
    }
  }, [searchParams]);

  // Handler for receiving scene context updates from PostEditor
  const handleSceneContextUpdate = (
    context: PoseContext | null,
    newSuggestions: ResponseSuggestion[],
    loading: boolean,
    error: string | null
  ) => {
    setSceneContext(context);
    setSuggestions(newSuggestions);
    setContextLoading(loading);
    setContextError(error);
  };

  // Handler for receiving the seed function from PostEditor
  const handleSeedPostText = (seedFunction: (text: string) => void) => {
    setSeedPostText(() => seedFunction);
  };

  // Handler for suggestion clicks
  const handleSuggestionClick = (suggestion: ResponseSuggestion) => {
    if (seedPostText) {
      seedPostText(suggestion.text);
      toast({
        title: "Suggestion Applied",
        description: "The suggestion has been added to your post editor.",
      });
    }
  };

  return (
    <CharacterCheckWrapper>
      <div className="flex-1 p-4 md:p-8">
        <div className="mx-auto grid w-full max-w-7xl items-start gap-8 xl:grid-cols-[1fr_350px]">
          <div className="grid auto-rows-max items-start gap-8">
            <PostEditor 
              onContextUpdate={handleSceneContextUpdate} 
              autoLoadSceneId={autoLoadSceneId}
              onSeedPostText={handleSeedPostText}
            />
          </div>
          <div className="hidden xl:grid auto-rows-max items-start gap-8 sticky top-4 h-fit">
            <SceneAnalysis 
              context={sceneContext} 
              suggestions={suggestions} 
              isLoading={contextLoading} 
              error={contextError} 
            />
          </div>
        </div>
      </div>
    </CharacterCheckWrapper>
  )
}

export default function SceneWeaverPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <SceneWeaverContent />
    </Suspense>
  )
}
