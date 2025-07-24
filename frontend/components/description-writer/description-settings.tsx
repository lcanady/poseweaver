'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { ChevronDown, ChevronUp, Crown, FileText, Lock } from 'lucide-react'

interface DescriptionSettingsProps {
  prompt: string
  onPromptChange: (prompt: string) => void
  style: string
  onStyleChange: (style: string) => void
  focusAreas: string
  onFocusAreasChange: (areas: string) => void
  detailLevel: number
  onDetailLevelChange: (level: number) => void
  creativityLevel: number
  onCreativityLevelChange: (level: number) => void
  formalityLevel: number
  onFormalityLevelChange: (level: number) => void
  includeSensoryDetails: boolean
  onIncludeSensoryDetailsChange: (include: boolean) => void
  includeEmotionalCues: boolean
  onIncludeEmotionalCuesChange: (include: boolean) => void
  showAdvancedSettings: boolean
  onShowAdvancedSettingsChange: (show: boolean) => void
  hasAccess: boolean
  onUpgradeClick: () => void
  disabled?: boolean
}

export function DescriptionSettings({
  prompt,
  onPromptChange,
  style,
  onStyleChange,
  focusAreas,
  onFocusAreasChange,
  detailLevel,
  onDetailLevelChange,
  creativityLevel,
  onCreativityLevelChange,
  formalityLevel,
  onFormalityLevelChange,
  includeSensoryDetails,
  onIncludeSensoryDetailsChange,
  includeEmotionalCues,
  onIncludeEmotionalCuesChange,
  showAdvancedSettings,
  onShowAdvancedSettingsChange,
  hasAccess,
  onUpgradeClick,
  disabled = false
}: DescriptionSettingsProps) {
  const styleDescriptions = {
    minimal: "Concise, key details only",
    balanced: "Moderate detail, well-rounded",
    elaborate: "Rich, comprehensive descriptions"
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Description Settings</CardTitle>
        <CardDescription>Customize how your descriptions are generated</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Prompt Input */}
        <div className="space-y-2">
          <Label className="text-sm">Custom Instructions</Label>
          <Textarea
            placeholder="Describe what you want the AI to focus on in the image. For example: 'Describe the person's clothing and physical appearance in detail' or 'Focus on the facial features and expression'"
            value={prompt}
            onChange={(e) => onPromptChange(e.target.value)}
            className="min-h-[80px] resize-none text-sm"
            maxLength={500}
          />
          <div className="text-xs text-muted-foreground text-right">
            {prompt.length}/500 characters
          </div>
        </div>

        {/* Basic Settings */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label className="text-sm">Style</Label>
            <Select value={style} onValueChange={onStyleChange}>
              <SelectTrigger className="h-8">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(styleDescriptions).map(([key, description]) => (
                  <SelectItem key={key} value={key}>
                    <div className="flex flex-col">
                      <span className="capitalize font-medium">{key}</span>
                      <span className="text-xs text-muted-foreground">{description}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="text-sm">Focus Areas</Label>
            <Select value={focusAreas} onValueChange={onFocusAreasChange}>
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
                  disabled={!hasAccess}
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-sm">Creativity</Label>
                  <span className="text-xs text-muted-foreground">{creativityLevel}%</span>
                </div>
                <Slider
                  value={[creativityLevel]}
                  onValueChange={(value) => onCreativityLevelChange(value[0])}
                  max={100}
                  step={5}
                  className="w-full"
                  disabled={!hasAccess}
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-sm">Formality</Label>
                  <span className="text-xs text-muted-foreground">{formalityLevel}%</span>
                </div>
                <Slider
                  value={[formalityLevel]}
                  onValueChange={(value) => onFormalityLevelChange(value[0])}
                  max={100}
                  step={5}
                  className="w-full"
                  disabled={!hasAccess}
                />
              </div>
            </div>

            {/* Toggles */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className="text-sm">Include Emotional Context</Label>
                <Switch
                  checked={includeEmotionalCues}
                  onCheckedChange={onIncludeEmotionalCuesChange}
                  disabled={!hasAccess}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label className="text-sm">Include Sensory Details</Label>
                <Switch
                  checked={includeSensoryDetails}
                  onCheckedChange={onIncludeSensoryDetailsChange}
                  disabled={!hasAccess}
                />
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
