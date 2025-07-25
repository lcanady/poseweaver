'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { 
  Settings, 
  Save, 
  RotateCcw, 
  Palette, 
  Brain, 
  Heart, 
  Eye, 
  MessageSquare,
  Zap,
  Shield
} from "lucide-react";
import { Character } from "@/hooks/useCharacter";

interface CharacterSettings {
  // Enhancement Preferences
  default_enhancement_style: 'minimal' | 'balanced' | 'elaborate';
  default_narrative_tone: 'neutral' | 'dramatic' | 'casual' | 'formal' | 'humorous';
  
  // Default Enhancement Options
  default_detail_level: number;
  default_creativity_level: number;
  default_sensory_focus: number;
  default_emotional_depth: number;
  
  // Feature Toggles
  default_include_internal_thoughts: boolean;
  default_emphasize_actions: boolean;
  default_preserve_original_tone: boolean;
  default_add_environmental_details: boolean;
  default_character_control_check: boolean;
  
  // Character-Specific Enhancement Notes
  enhancement_notes: string;
  preferred_writing_style: string;
  
  // Voice & Style Overrides
  voice_emphasis: 'dialogue' | 'action' | 'internal' | 'balanced';
  personality_emphasis: number; // How much to emphasize personality traits
}

interface CharacterSettingsProps {
  character: Character;
  onSettingsChange?: (settings: CharacterSettings) => void;
  className?: string;
}

const defaultSettings: CharacterSettings = {
  default_enhancement_style: 'balanced',
  default_narrative_tone: 'neutral',
  default_detail_level: 50,
  default_creativity_level: 60,
  default_sensory_focus: 40,
  default_emotional_depth: 45,
  default_include_internal_thoughts: false,
  default_emphasize_actions: true,
  default_preserve_original_tone: true,
  default_add_environmental_details: false,
  default_character_control_check: true,
  enhancement_notes: '',
  preferred_writing_style: '',
  voice_emphasis: 'balanced',
  personality_emphasis: 70
};

export function CharacterSettings({ character, onSettingsChange, className }: CharacterSettingsProps) {
  const [settings, setSettings] = useState<CharacterSettings>(defaultSettings);
  const [isLoading, setIsLoading] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Load character settings from localStorage (in future, this would be from API)
  useEffect(() => {
    const savedSettings = localStorage.getItem(`character_settings_${character.id}`);
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings({ ...defaultSettings, ...parsed });
      } catch (error) {
        console.error('Failed to parse character settings:', error);
      }
    }
  }, [character.id]);

  const updateSetting = <K extends keyof CharacterSettings>(
    key: K, 
    value: CharacterSettings[K]
  ) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    setHasUnsavedChanges(true);
    onSettingsChange?.(newSettings);
  };

  const saveSettings = async () => {
    setIsLoading(true);
    try {
      // Save to localStorage (in future, this would be an API call)
      localStorage.setItem(`character_settings_${character.id}`, JSON.stringify(settings));
      setHasUnsavedChanges(false);
      toast.success('Character settings saved successfully');
    } catch (error) {
      console.error('Failed to save settings:', error);
      toast.error('Failed to save settings');
    } finally {
      setIsLoading(false);
    }
  };

  const resetToDefaults = () => {
    setSettings(defaultSettings);
    setHasUnsavedChanges(true);
    toast.info('Settings reset to defaults');
  };

  return (
    <div className={className}>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              <CardTitle>Enhancement Settings</CardTitle>
            </div>
            {hasUnsavedChanges && (
              <Badge variant="secondary">Unsaved Changes</Badge>
            )}
          </div>
          <CardDescription>
            Configure default enhancement preferences for {character.name}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          
          {/* Style Preferences */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Palette className="h-4 w-4" />
              <Label className="text-base font-medium">Style Preferences</Label>
            </div>
            
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="enhancement-style">Default Enhancement Style</Label>
                <Select 
                  value={settings.default_enhancement_style} 
                  onValueChange={(value: 'minimal' | 'balanced' | 'elaborate') => 
                    updateSetting('default_enhancement_style', value)
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="minimal">Minimal - Light touch-ups</SelectItem>
                    <SelectItem value="balanced">Balanced - Moderate enhancement</SelectItem>
                    <SelectItem value="elaborate">Elaborate - Rich, detailed prose</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="narrative-tone">Default Narrative Tone</Label>
                <Select 
                  value={settings.default_narrative_tone} 
                  onValueChange={(value: any) => updateSetting('default_narrative_tone', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="neutral">Neutral</SelectItem>
                    <SelectItem value="dramatic">Dramatic</SelectItem>
                    <SelectItem value="casual">Casual</SelectItem>
                    <SelectItem value="formal">Formal</SelectItem>
                    <SelectItem value="humorous">Humorous</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          <Separator />

          {/* Enhancement Levels */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Brain className="h-4 w-4" />
              <Label className="text-base font-medium">Enhancement Levels</Label>
            </div>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Detail Level</Label>
                  <span className="text-sm text-muted-foreground">{settings.default_detail_level}%</span>
                </div>
                <Slider
                  value={[settings.default_detail_level]}
                  onValueChange={([value]) => updateSetting('default_detail_level', value)}
                  max={100}
                  step={5}
                  className="w-full"
                />
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Creativity Level</Label>
                  <span className="text-sm text-muted-foreground">{settings.default_creativity_level}%</span>
                </div>
                <Slider
                  value={[settings.default_creativity_level]}
                  onValueChange={([value]) => updateSetting('default_creativity_level', value)}
                  max={100}
                  step={5}
                  className="w-full"
                />
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Sensory Focus</Label>
                  <span className="text-sm text-muted-foreground">{settings.default_sensory_focus}%</span>
                </div>
                <Slider
                  value={[settings.default_sensory_focus]}
                  onValueChange={([value]) => updateSetting('default_sensory_focus', value)}
                  max={100}
                  step={5}
                  className="w-full"
                />
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Emotional Depth</Label>
                  <span className="text-sm text-muted-foreground">{settings.default_emotional_depth}%</span>
                </div>
                <Slider
                  value={[settings.default_emotional_depth]}
                  onValueChange={([value]) => updateSetting('default_emotional_depth', value)}
                  max={100}
                  step={5}
                  className="w-full"
                />
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Personality Emphasis</Label>
                  <span className="text-sm text-muted-foreground">{settings.personality_emphasis}%</span>
                </div>
                <Slider
                  value={[settings.personality_emphasis]}
                  onValueChange={([value]) => updateSetting('personality_emphasis', value)}
                  max={100}
                  step={5}
                  className="w-full"
                />
              </div>
            </div>
          </div>

          <Separator />

          {/* Feature Toggles */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4" />
              <Label className="text-base font-medium">Feature Preferences</Label>
            </div>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Include Internal Thoughts</Label>
                  <p className="text-sm text-muted-foreground">Add character's inner dialogue</p>
                </div>
                <Switch
                  checked={settings.default_include_internal_thoughts}
                  onCheckedChange={(checked) => updateSetting('default_include_internal_thoughts', checked)}
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Emphasize Actions</Label>
                  <p className="text-sm text-muted-foreground">Focus on physical actions and movement</p>
                </div>
                <Switch
                  checked={settings.default_emphasize_actions}
                  onCheckedChange={(checked) => updateSetting('default_emphasize_actions', checked)}
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Preserve Original Tone</Label>
                  <p className="text-sm text-muted-foreground">Maintain the original pose's mood</p>
                </div>
                <Switch
                  checked={settings.default_preserve_original_tone}
                  onCheckedChange={(checked) => updateSetting('default_preserve_original_tone', checked)}
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Add Environmental Details</Label>
                  <p className="text-sm text-muted-foreground">Include scene and setting descriptions</p>
                </div>
                <Switch
                  checked={settings.default_add_environmental_details}
                  onCheckedChange={(checked) => updateSetting('default_add_environmental_details', checked)}
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Character Control Check</Label>
                  <p className="text-sm text-muted-foreground">Prevent controlling other characters</p>
                </div>
                <Switch
                  checked={settings.default_character_control_check}
                  onCheckedChange={(checked) => updateSetting('default_character_control_check', checked)}
                />
              </div>
            </div>
          </div>

          <Separator />

          {/* Voice & Style */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              <Label className="text-base font-medium">Voice & Style</Label>
            </div>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="voice-emphasis">Voice Emphasis</Label>
                <Select 
                  value={settings.voice_emphasis} 
                  onValueChange={(value: any) => updateSetting('voice_emphasis', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="balanced">Balanced - Equal focus</SelectItem>
                    <SelectItem value="dialogue">Dialogue - Speech focused</SelectItem>
                    <SelectItem value="action">Action - Movement focused</SelectItem>
                    <SelectItem value="internal">Internal - Thoughts focused</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="preferred-style">Preferred Writing Style</Label>
                <Input
                  id="preferred-style"
                  placeholder="e.g., concise, flowery, technical, poetic..."
                  value={settings.preferred_writing_style}
                  onChange={(e) => updateSetting('preferred_writing_style', e.target.value)}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="enhancement-notes">Enhancement Notes</Label>
                <Textarea
                  id="enhancement-notes"
                  placeholder="Special instructions for enhancing this character's poses..."
                  value={settings.enhancement_notes}
                  onChange={(e) => updateSetting('enhancement_notes', e.target.value)}
                  rows={3}
                />
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-4">
            <Button variant="outline" onClick={resetToDefaults}>
              <RotateCcw className="h-4 w-4 mr-2" />
              Reset to Defaults
            </Button>
            
            <Button onClick={saveSettings} disabled={isLoading || !hasUnsavedChanges}>
              <Save className="h-4 w-4 mr-2" />
              {isLoading ? 'Saving...' : 'Save Settings'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
