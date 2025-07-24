import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Settings as SettingsIcon, ChevronDown, ChevronUp, Crown, Save, Lock } from "lucide-react";
import { CustomSlider } from "./custom-slider";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useState, useEffect } from "react";
import { useToast } from "@/components/ui/use-toast";

interface EnhancementSettingsProps {
  // Style and presets
  enhancementStyle: string;
  onStyleChange: (style: string) => void;
  narrativeTone: string;
  onNarrativeToneChange: (tone: string) => void;
  
  // Slider values
  detailLevel: number;
  onDetailLevelChange: (value: number) => void;
  creativityLevel: number;
  onCreativityLevelChange: (value: number) => void;
  sensoryFocus: number;
  onSensoryFocusChange: (value: number) => void;
  emotionalDepth: number;
  onEmotionalDepthChange: (value: number) => void;
  
  // Switch values
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
  
  // UI state
  showAdvancedSettings: boolean;
  onShowAdvancedSettingsChange: (show: boolean) => void;
  
  // Subscription and paywall
  subscriptionStatus?: string;
  onUpgradeClick?: () => void;
}

export const EnhancementSettings = ({
  enhancementStyle,
  onStyleChange,
  narrativeTone,
  onNarrativeToneChange,
  detailLevel,
  onDetailLevelChange,
  creativityLevel,
  onCreativityLevelChange,
  sensoryFocus,
  onSensoryFocusChange,
  emotionalDepth,
  onEmotionalDepthChange,
  includeInternalThoughts,
  onIncludeInternalThoughtsChange,
  emphasizeActions,
  onEmphasizeActionsChange,
  preserveOriginalTone,
  onPreserveOriginalToneChange,
  addEnvironmentalDetails,
  onAddEnvironmentalDetailsChange,
  characterControlCheck,
  onCharacterControlCheckChange,
  showAdvancedSettings,
  onShowAdvancedSettingsChange,
  subscriptionStatus = 'free',
  onUpgradeClick
}: EnhancementSettingsProps) => {
  const [showSavePresetDialog, setShowSavePresetDialog] = useState(false);
  const [presetName, setPresetName] = useState('');
  const [savedPresets, setSavedPresets] = useState<any[]>([]);
  const { toast } = useToast();
  
  // Check if user has paid subscription
  const isPaidUser = ['basic', 'pro', 'premium', 'admin'].includes(subscriptionStatus);
  const isAdvancedSettingsLocked = !isPaidUser && showAdvancedSettings;
  
  // Load saved presets on component mount
  useEffect(() => {
    if (isPaidUser) {
      try {
        const existingPresets = JSON.parse(localStorage.getItem('enhancement-presets') || '[]');
        setSavedPresets(existingPresets);
      } catch (error) {
        console.error('Error loading presets:', error);
      }
    }
  }, [isPaidUser]);
  
  const selectStyle = (style: string) => {
    onStyleChange(style);
    
    // Update slider values based on style preset
    switch(style) {
      case 'subtle':
        onDetailLevelChange(30);
        onCreativityLevelChange(40);
        onSensoryFocusChange(20);
        onEmotionalDepthChange(25);
        break;
      case 'balanced':
        onDetailLevelChange(50);
        onCreativityLevelChange(60);
        onSensoryFocusChange(40);
        onEmotionalDepthChange(45);
        break;
      case 'dramatic':
        onDetailLevelChange(80);
        onCreativityLevelChange(85);
        onSensoryFocusChange(70);
        onEmotionalDepthChange(75);
        break;
    }
  };
  
  const savePreset = async () => {
    if (!presetName.trim()) {
      toast({
        title: "Error",
        description: "Please enter a preset name",
        variant: "destructive"
      });
      return;
    }
    
    const preset = {
      name: presetName,
      enhancementStyle,
      narrativeTone,
      detailLevel,
      creativityLevel,
      sensoryFocus,
      emotionalDepth,
      includeInternalThoughts,
      emphasizeActions,
      preserveOriginalTone,
      addEnvironmentalDetails,
      characterControlCheck
    };
    
    try {
      // TODO: Save to backend API
      // For now, save to localStorage
      const existingPresets = JSON.parse(localStorage.getItem('enhancement-presets') || '[]');
      const updatedPresets = [...existingPresets, preset];
      localStorage.setItem('enhancement-presets', JSON.stringify(updatedPresets));
      setSavedPresets(updatedPresets);
      
      toast({
        title: "Preset Saved",
        description: `"${presetName}" has been saved successfully`
      });
      
      setPresetName('');
      setShowSavePresetDialog(false);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save preset",
        variant: "destructive"
      });
    }
  };
  
  const loadPreset = (preset: any) => {
    onStyleChange(preset.enhancementStyle);
    onNarrativeToneChange(preset.narrativeTone);
    onDetailLevelChange(preset.detailLevel);
    onCreativityLevelChange(preset.creativityLevel);
    onSensoryFocusChange(preset.sensoryFocus);
    onEmotionalDepthChange(preset.emotionalDepth);
    onIncludeInternalThoughtsChange(preset.includeInternalThoughts);
    onEmphasizeActionsChange(preset.emphasizeActions);
    onPreserveOriginalToneChange(preset.preserveOriginalTone);
    onAddEnvironmentalDetailsChange(preset.addEnvironmentalDetails);
    onCharacterControlCheckChange(preset.characterControlCheck);
    
    toast({
      title: "Preset Loaded",
      description: `"${preset.name}" settings have been applied`
    });
  };
  
  const handleAdvancedSettingsToggle = () => {
    if (!isPaidUser && !showAdvancedSettings) {
      // Show paywall for free users trying to access advanced settings
      if (onUpgradeClick) {
        onUpgradeClick();
      }
      return;
    }
    onShowAdvancedSettingsChange(!showAdvancedSettings);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h4 className="font-medium text-sm">Enhancement Settings</h4>
        <div className="flex items-center gap-2">
          {isPaidUser && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowSavePresetDialog(true)}
              className="text-xs"
            >
              <Save className="mr-1 h-3 w-3" />
              Save Preset
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleAdvancedSettingsToggle}
            className="text-xs"
          >
            <SettingsIcon className="mr-1 h-3 w-3" />
            {!isPaidUser && (
              <Lock className="mr-1 h-3 w-3" />
            )}
            {showAdvancedSettings ? (
              <>
                Hide Advanced <ChevronUp className="ml-1 h-3 w-3" />
              </>
            ) : (
              <>
                Show Advanced <ChevronDown className="ml-1 h-3 w-3" />
              </>
            )}
          </Button>
        </div>
      </div>
      
      {/* Style Presets */}
      <div className="space-y-3">
        <div className="flex gap-2">
          {['subtle', 'balanced', 'dramatic'].map((style) => (
            <Button
              key={style}
              variant={enhancementStyle === style ? "default" : "outline"}
              size="sm"
              onClick={() => selectStyle(style)}
              className="capitalize flex-1"
            >
              {style}
            </Button>
          ))}
        </div>
        
        {/* Saved Presets for Paid Users */}
        {isPaidUser && savedPresets.length > 0 && (
          <div className="space-y-2">
            <Label className="text-xs font-medium">Saved Presets</Label>
            <div className="flex flex-wrap gap-2">
              {savedPresets.map((preset, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  onClick={() => loadPreset(preset)}
                  className="text-xs h-7"
                >
                  {preset.name}
                </Button>
              ))}
            </div>
          </div>
        )}
      </div>
      
      {/* Basic Settings */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label className="text-xs">Detail Level</Label>
          <CustomSlider
            value={detailLevel}
            onChange={onDetailLevelChange}
            className="w-full"
          />
          <div className="text-xs text-muted-foreground text-center">{detailLevel}%</div>
        </div>
        
        <div className="space-y-2">
          <Label className="text-xs">Creativity</Label>
          <CustomSlider
            value={creativityLevel}
            onChange={onCreativityLevelChange}
            className="w-full"
            color="secondary"
          />
          <div className="text-xs text-muted-foreground text-center">{creativityLevel}%</div>
        </div>
      </div>
      
      {/* Advanced Settings */}
      {showAdvancedSettings && (
        <div className="space-y-6 pt-4 border-t border-border/50 relative">
          {/* Additional Sliders */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-xs">Sensory Focus</Label>
              <CustomSlider
                value={sensoryFocus}
                onChange={onSensoryFocusChange}
                className="w-full"
                color="accent"
              />
              <div className="text-xs text-muted-foreground text-center">{sensoryFocus}%</div>
            </div>
            
            <div className="space-y-2">
              <Label className="text-xs">Emotional Depth</Label>
              <CustomSlider
                value={emotionalDepth}
                onChange={onEmotionalDepthChange}
                className="w-full"
              />
              <div className="text-xs text-muted-foreground text-center">{emotionalDepth}%</div>
            </div>
          </div>
          
          {/* Narrative Tone */}
          <div className="space-y-2">
            <Label className="text-xs">Narrative Tone</Label>
            <Select value={narrativeTone} onValueChange={onNarrativeToneChange}>
              <SelectTrigger className="h-8">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="neutral">Neutral</SelectItem>
                <SelectItem value="dramatic">Dramatic</SelectItem>
                <SelectItem value="casual">Casual</SelectItem>
                <SelectItem value="formal">Formal</SelectItem>
                <SelectItem value="poetic">Poetic</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          {/* Enhancement Switches */}
          <div className="grid grid-cols-1 gap-3">
            <div className="flex items-center justify-between">
              <Label className="text-xs">Include Internal Thoughts</Label>
              <Switch
                checked={includeInternalThoughts}
                onCheckedChange={onIncludeInternalThoughtsChange}
              />
            </div>
            
            <div className="flex items-center justify-between">
              <Label className="text-xs">Emphasize Actions</Label>
              <Switch
                checked={emphasizeActions}
                onCheckedChange={onEmphasizeActionsChange}
              />
            </div>
            
            <div className="flex items-center justify-between">
              <Label className="text-xs">Preserve Original Tone</Label>
              <Switch
                checked={preserveOriginalTone}
                onCheckedChange={onPreserveOriginalToneChange}
              />
            </div>
            
            <div className="flex items-center justify-between">
              <Label className="text-xs">Add Environmental Details</Label>
              <Switch
                checked={addEnvironmentalDetails}
                onCheckedChange={onAddEnvironmentalDetailsChange}
              />
            </div>
            
            <div className="flex items-center justify-between">
              <Label className="text-xs">Character Control Check</Label>
              <Switch
                checked={characterControlCheck}
                onCheckedChange={onCharacterControlCheckChange}
              />
            </div>
          </div>
          
          {/* Paywall Overlay for Free Users */}
          {isAdvancedSettingsLocked && (
            <div className="absolute inset-0 bg-background/80 backdrop-blur-sm rounded-lg flex items-center justify-center">
              <div className="text-center p-6 max-w-sm">
                <Crown className="h-8 w-8 text-amber-500 mx-auto mb-3" />
                <h3 className="font-semibold text-lg mb-2">Advanced Settings</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Unlock advanced pose enhancement controls and save custom presets with a paid subscription.
                </p>
                <Button 
                  onClick={onUpgradeClick}
                  className="w-full"
                  size="sm"
                >
                  <Crown className="mr-2 h-4 w-4" />
                  Upgrade Now
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Save Preset Dialog */}
      <Dialog open={showSavePresetDialog} onOpenChange={setShowSavePresetDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Save Enhancement Preset</DialogTitle>
            <DialogDescription>
              Save your current enhancement settings as a preset for quick access later.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Label htmlFor="preset-name" className="text-sm font-medium">
              Preset Name
            </Label>
            <Input
              id="preset-name"
              value={presetName}
              onChange={(e) => setPresetName(e.target.value)}
              placeholder="e.g., Dramatic Combat, Subtle Romance"
              className="mt-2"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSavePresetDialog(false)}>
              Cancel
            </Button>
            <Button onClick={savePreset}>
              <Save className="mr-2 h-4 w-4" />
              Save Preset
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
