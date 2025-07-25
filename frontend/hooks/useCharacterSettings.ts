import { useState, useEffect } from 'react';

export interface CharacterSettings {
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
  personality_emphasis: number;
}

export const defaultCharacterSettings: CharacterSettings = {
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

export function useCharacterSettings(characterId: string) {
  const [settings, setSettings] = useState<CharacterSettings>(defaultCharacterSettings);
  const [isLoading, setIsLoading] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Load character settings from localStorage (in future, this would be from API)
  useEffect(() => {
    if (!characterId) return;
    
    const savedSettings = localStorage.getItem(`character_settings_${characterId}`);
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings({ ...defaultCharacterSettings, ...parsed });
      } catch (error) {
        console.error('Failed to parse character settings:', error);
        setSettings(defaultCharacterSettings);
      }
    } else {
      setSettings(defaultCharacterSettings);
    }
    setHasUnsavedChanges(false);
  }, [characterId]);

  const updateSetting = <K extends keyof CharacterSettings>(
    key: K, 
    value: CharacterSettings[K]
  ) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    setHasUnsavedChanges(true);
    return newSettings;
  };

  const saveSettings = async (): Promise<boolean> => {
    if (!characterId) return false;
    
    setIsLoading(true);
    try {
      // Save to localStorage (in future, this would be an API call)
      localStorage.setItem(`character_settings_${characterId}`, JSON.stringify(settings));
      setHasUnsavedChanges(false);
      return true;
    } catch (error) {
      console.error('Failed to save settings:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const resetToDefaults = () => {
    setSettings(defaultCharacterSettings);
    setHasUnsavedChanges(true);
  };

  const getSettingsForEnhancement = () => {
    return {
      enhancementStyle: settings.default_enhancement_style,
      narrativeTone: settings.default_narrative_tone,
      detailLevel: settings.default_detail_level,
      creativityLevel: settings.default_creativity_level,
      sensoryFocus: settings.default_sensory_focus,
      emotionalDepth: settings.default_emotional_depth,
      includeInternalThoughts: settings.default_include_internal_thoughts,
      emphasizeActions: settings.default_emphasize_actions,
      preserveOriginalTone: settings.default_preserve_original_tone,
      addEnvironmentalDetails: settings.default_add_environmental_details,
      characterControlCheck: settings.default_character_control_check,
    };
  };

  return {
    settings,
    setSettings,
    updateSetting,
    saveSettings,
    resetToDefaults,
    getSettingsForEnhancement,
    isLoading,
    hasUnsavedChanges
  };
}
