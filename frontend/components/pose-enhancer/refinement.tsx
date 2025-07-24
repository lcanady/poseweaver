import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Loader2, Sparkles } from "lucide-react";

interface RefinementProps {
  editSuggestion: string;
  onEditSuggestionChange: (value: string) => void;
  isRefining: boolean;
  onRefineWithSuggestion: () => void;
  hasEnhancedPose: boolean;
}

export const Refinement = ({
  editSuggestion,
  onEditSuggestionChange,
  isRefining,
  onRefineWithSuggestion,
  hasEnhancedPose
}: RefinementProps) => {
  if (!hasEnhancedPose) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Refinement Suggestions</CardTitle>
        <CardDescription className="text-xs">
          Suggest specific changes to improve the enhanced pose
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label className="text-xs">Edit Suggestion</Label>
          <Textarea
            placeholder="e.g., 'Add more emotional depth to the character's reaction' or 'Include more sensory details about the environment'"
            value={editSuggestion}
            onChange={(e) => onEditSuggestionChange(e.target.value)}
            className="min-h-[80px] resize-none text-sm"
            maxLength={500}
          />
          <div className="text-xs text-muted-foreground text-right">
            {editSuggestion.length}/500 characters
          </div>
        </div>
        
        <Button
          onClick={onRefineWithSuggestion}
          disabled={!editSuggestion.trim() || isRefining}
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
