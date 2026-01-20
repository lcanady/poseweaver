import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Loader2, Wand2, ChevronUp, ChevronDown, Crown } from "lucide-react";

interface DescriptionInputProps {
  prompt: string;
  onPromptChange: (value: string) => void;
  style: string;
  onStyleChange: (value: string) => void;
  focusArea: string;
  onFocusAreaChange: (value: string) => void;
  detailLevel: number;
  onDetailLevelChange: (value: number) => void;
  creativity: number;
  onCreativityChange: (value: number) => void;
  formality: number;
  onFormalityChange: (value: number) => void;
  includeEmotions: boolean;
  onIncludeEmotionsChange: (value: boolean) => void;
  includeTechnicalDetails: boolean;
  onIncludeTechnicalDetailsChange: (value: boolean) => void;
  showAdvancedSettings: boolean;
  onShowAdvancedSettingsChange: (show: boolean) => void;
  isGenerating: boolean;
  onGenerate: () => void;
  disabled: boolean;
  hasAccess: boolean;
  onUpgradeClick: () => void;
}

export const DescriptionInput = ({
  prompt,
  onPromptChange,
  style,
  onStyleChange,
  focusArea,
  onFocusAreaChange,
  detailLevel,
  onDetailLevelChange,
  creativity,
  onCreativityChange,
  formality,
  onFormalityChange,
  includeEmotions,
  onIncludeEmotionsChange,
  includeTechnicalDetails,
  onIncludeTechnicalDetailsChange,
  showAdvancedSettings,
  onShowAdvancedSettingsChange,
  isGenerating,
  onGenerate,
  disabled,
  hasAccess,
  onUpgradeClick
}: DescriptionInputProps) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Your Description Request</CardTitle>
        <CardDescription>Enter instructions for generating your image description</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Custom Prompt */}
        <div className="space-y-2">
          <Label className="text-sm">Description Instructions</Label>
          <Textarea
            placeholder="Enter specific instructions for the AI..."
            value={prompt}
            onChange={(e) => onPromptChange(e.target.value)}
            className="min-h-[120px] resize-none"
            maxLength={2000}
            disabled={disabled}
          />
          <div className="flex justify-between items-center text-xs text-muted-foreground">
            <span>{prompt.length}/2000 characters</span>
          </div>
        </div>

        {/* Basic Settings */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label className="text-sm">Style</Label>
            <Select value={style} onValueChange={onStyleChange} disabled={disabled}>
              <SelectTrigger className="h-8">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="minimal">Minimal</SelectItem>
                <SelectItem value="balanced">Balanced</SelectItem>
                <SelectItem value="elaborate">Elaborate</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="text-sm">Focus Area</Label>
            <Select value={focusArea} onValueChange={onFocusAreaChange} disabled={disabled}>
              <SelectTrigger className="h-8">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="overall">Overall Scene</SelectItem>
                <SelectItem value="people">People & Characters</SelectItem>
                <SelectItem value="objects">Objects & Items</SelectItem>
                <SelectItem value="environment">Environment</SelectItem>
                <SelectItem value="mood">Mood & Atmosphere</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Advanced Settings Toggle */}
        <div className="flex items-center justify-between">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onShowAdvancedSettingsChange(!showAdvancedSettings)}
            className="text-sm p-0 h-auto"
            disabled={disabled}
          >
            Advanced Settings
            {showAdvancedSettings ? (
              <ChevronUp className="ml-2 h-3 w-3" />
            ) : (
              <ChevronDown className="ml-2 h-3 w-3" />
            )}
          </Button>
          {!hasAccess && showAdvancedSettings && (
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Crown className="h-3 w-3" />
              Premium
            </div>
          )}
        </div>

        {/* Advanced Settings */}
        {showAdvancedSettings && (
          <div className="space-y-4 relative">
            {/* Premium Overlay */}
            {!hasAccess && (
              <div className="absolute inset-0 bg-background/80 backdrop-blur-sm z-10 rounded-lg border border-dashed border-border flex items-center justify-center">
                <div className="text-center space-y-2 p-4">
                  <Crown className="h-6 w-6 mx-auto text-muted-foreground" />
                  <p className="text-sm font-medium">Premium Feature</p>
                  <p className="text-xs text-muted-foreground">Upgrade to access advanced settings</p>
                  <Button size="sm" onClick={onUpgradeClick}>
                    Upgrade Now
                  </Button>
                </div>
              </div>
            )}

            {/* Sliders */}
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-sm">Detail Level</Label>
                  <span className="text-xs text-muted-foreground">{detailLevel}%</span>
                </div>
                <Slider
                  value={[detailLevel]}
                  onValueChange={(value) => onDetailLevelChange(value[0])}
                  max={100}
                  step={5}
                  className="w-full"
                  disabled={!hasAccess || disabled}
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-sm">Creativity</Label>
                  <span className="text-xs text-muted-foreground">{creativity}%</span>
                </div>
                <Slider
                  value={[creativity]}
                  onValueChange={(value) => onCreativityChange(value[0])}
                  max={100}
                  step={5}
                  className="w-full"
                  disabled={!hasAccess || disabled}
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-sm">Formality</Label>
                  <span className="text-xs text-muted-foreground">{formality}%</span>
                </div>
                <Slider
                  value={[formality]}
                  onValueChange={(value) => onFormalityChange(value[0])}
                  max={100}
                  step={5}
                  className="w-full"
                  disabled={!hasAccess || disabled}
                />
              </div>
            </div>

            {/* Toggles */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className="text-sm">Include Emotional Context</Label>
                <Switch
                  checked={includeEmotions}
                  onCheckedChange={onIncludeEmotionsChange}
                  disabled={!hasAccess || disabled}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label className="text-sm">Include Technical Details</Label>
                <Switch
                  checked={includeTechnicalDetails}
                  onCheckedChange={onIncludeTechnicalDetailsChange}
                  disabled={!hasAccess || disabled}
                />
              </div>
            </div>
          </div>
        )}

        {/* Generate Button */}
        <Button
          onClick={onGenerate}
          disabled={isGenerating || disabled}
          className="w-full"
          size="lg"
        >
          {isGenerating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating Description...
            </>
          ) : (
            <>
              <Wand2 className="mr-2 h-4 w-4" />
              Generate Description
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
};
