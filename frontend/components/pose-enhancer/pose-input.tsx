import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Loader2, Wand2 } from "lucide-react";
import { EnhancementSettings } from "./enhancement-settings";

interface PoseInputProps {
  poseInput: string;
  onPoseInputChange: (value: string) => void;
  isEnhancing: boolean;
  onEnhancePose: () => void;
  
  // Enhancement settings props
  enhancementStyle: string;
  onStyleChange: (style: string) => void;
  narrativeTone: string;
  onNarrativeToneChange: (tone: string) => void;
  detailLevel: number;
  onDetailLevelChange: (value: number) => void;
  creativityLevel: number;
  onCreativityLevelChange: (value: number) => void;
  sensoryFocus: number;
  onSensoryFocusChange: (value: number) => void;
  emotionalDepth: number;
  onEmotionalDepthChange: (value: number) => void;
  includeInternalThoughts: boolean;
  onIncludeInternalThoughtsChange: (value: boolean) => void;
  emphasizeActions: boolean;
  onEmphasizeActionsChange: (value: boolean) => void;
  preserveOriginalTone: boolean;
  onPreserveOriginalToneChange: (value: boolean) => void;
  addEnvironmentalDetails: boolean;
  onAddEnvironmentalDetailsChange: (value: boolean) => void;
  characterControlCheck: boolean;
  onCharacterControlCheckChange: (value: boolean) => void;
  showAdvancedSettings: boolean;
  onShowAdvancedSettingsChange: (show: boolean) => void;
  
  // Subscription and paywall
  subscriptionStatus?: string;
  onUpgradeClick?: () => void;
}

export const PoseInput = ({
  poseInput,
  onPoseInputChange,
  isEnhancing,
  onEnhancePose,
  ...enhancementProps
}: PoseInputProps) => {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Your Pose</CardTitle>
            <CardDescription>Enter the pose you want to enhance</CardDescription>
          </div>
          <div className="text-sm text-muted-foreground">
            {poseInput.length}/2000 characters
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <Textarea 
          placeholder="Enter the pose you want to enhance..."
          value={poseInput}
          onChange={(e) => onPoseInputChange(e.target.value)}
          className="min-h-[160px] resize-none"
          maxLength={2000}
        />
        
        {/* Enhancement Settings */}
        <EnhancementSettings 
          {...enhancementProps}
          subscriptionStatus={enhancementProps.subscriptionStatus}
          onUpgradeClick={enhancementProps.onUpgradeClick}
        />
        
        {/* Enhance Button */}
        <Button 
          onClick={onEnhancePose}
          disabled={!poseInput.trim() || isEnhancing}
          className="w-full"
          size="lg"
        >
          {isEnhancing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Enhancing...
            </>
          ) : (
            <>
              <Wand2 className="mr-2 h-4 w-4" />
              Enhance Pose
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
};
