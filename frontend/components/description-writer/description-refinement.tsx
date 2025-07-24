'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Loader2, Sparkles } from 'lucide-react'

interface DescriptionRefinementProps {
  refinementSuggestion: string
  onRefinementSuggestionChange: (value: string) => void
  isRefining: boolean
  onRefineDescription: () => void
  hasDescription: boolean
  disabled?: boolean
}

export const DescriptionRefinement = ({
  refinementSuggestion,
  onRefinementSuggestionChange,
  isRefining,
  onRefineDescription,
  hasDescription,
  disabled = false
}: DescriptionRefinementProps) => {
  if (!hasDescription) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Refinement Suggestions</CardTitle>
        <CardDescription className="text-xs">
          Suggest specific changes to improve the generated description
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label className="text-xs">Refinement Instructions</Label>
          <Textarea
            placeholder="e.g., 'Add more emotional depth to the character descriptions' or 'Include more sensory details about the environment'"
            value={refinementSuggestion}
            onChange={(e) => onRefinementSuggestionChange(e.target.value)}
            className="min-h-[80px] resize-none text-sm"
            maxLength={500}
            disabled={disabled}
          />
          <div className="text-xs text-muted-foreground text-right">
            {refinementSuggestion.length}/500 characters
          </div>
        </div>
        
        <Button
          onClick={onRefineDescription}
          disabled={!refinementSuggestion.trim() || isRefining || disabled}
          size="sm"
          className="w-full"
        >
          {isRefining ? (
            <>
              <Loader2 className="mr-2 h-3 w-3 animate-spin" />
              Refining...
            </>
          ) : (
            <>
              <Sparkles className="mr-2 h-3 w-3" />
              Apply Refinement
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
};
