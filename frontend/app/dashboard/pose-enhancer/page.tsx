"use client";

import { useState, useEffect } from "react";
import { useToast } from "@/components/ui/use-toast";
import { useAuth } from "@/contexts/auth-context";
import { Character } from "@/hooks/useCharacter";

// Import modular components
import { CharacterSelection } from "@/components/pose-enhancer/character-selection";
import { SceneContext } from "@/components/pose-enhancer/scene-context";
import { PoseInput } from "@/components/pose-enhancer/pose-input";
import { EnhancedOutput } from "@/components/pose-enhancer/enhanced-output";
import { VersionHistory } from "@/components/pose-enhancer/version-history";
import { Refinement } from "@/components/pose-enhancer/refinement";
import { EnhancementAnalysis } from "@/components/pose-enhancer/enhancement-analysis";
import { UsageDisplay } from "@/components/pose-enhancer/usage-display";
import { InlinePaywall } from "@/components/pose-enhancer/inline-paywall";

interface PoseVersion {
  id: string;
  pose: string;
  timestamp: Date;
  editSuggestion?: string;
}

export default function PoseEnhancerPage() {
  const [sceneDump, setSceneDump] = useState("");
  const [poseInput, setPoseInput] = useState("");
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [enhancedPose, setEnhancedPose] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [selectedCharacterId, setSelectedCharacterId] = useState<string>("");
  const [isLoadingCharacters, setIsLoadingCharacters] = useState(true);
  
  // Enhancement control states
  const [enhancementStyle, setEnhancementStyle] = useState("balanced");
  const [detailLevel, setDetailLevel] = useState(50);
  const [creativityLevel, setCreativityLevel] = useState(60);
  const [sensoryFocus, setSensoryFocus] = useState(40);
  const [emotionalDepth, setEmotionalDepth] = useState(45);
  const [narrativeTone, setNarrativeTone] = useState("neutral");
  const [includeInternalThoughts, setIncludeInternalThoughts] = useState(false);
  const [emphasizeActions, setEmphasizeActions] = useState(true);
  const [preserveOriginalTone, setPreserveOriginalTone] = useState(true);
  const [addEnvironmentalDetails, setAddEnvironmentalDetails] = useState(false);
  const [characterControlCheck, setCharacterControlCheck] = useState(true);
  
  // Copy format options
  const [copyFormat, setCopyFormat] = useState("standard");
  
  // Version control and edit suggestions
  const [poseVersions, setPoseVersions] = useState<PoseVersion[]>([]);
  const [currentVersionIndex, setCurrentVersionIndex] = useState(0);
  const [editSuggestion, setEditSuggestion] = useState("");
  const [isRefining, setIsRefining] = useState(false);
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);
  
  // Usage tracking and paywall states
  const [usageInfo, setUsageInfo] = useState<any>({
    available_generations: 15,
    monthly_limit: 20,
    current_usage: 5,
    extra_generations: 0,
    subscription_status: 'free'
  });
  const [showPaywall, setShowPaywall] = useState(false);
  // Get authenticated user from auth context
  const { user } = useAuth();
  const currentUserId = user?._id || null;
  
  const { toast } = useToast();

  // Get current user ID from token


  // Fetch character profiles when component mounts
  useEffect(() => {
    const fetchCharacters = async () => {
      setIsLoadingCharacters(true);
      
      try {
        const accessToken = localStorage.getItem('access_token');
        
        if (!accessToken) {
          throw new Error('No access token found. Please log in.');
        }
        
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/characters/mgmt`, 
          {
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${accessToken}`
            }
          }
        );
        
        if (!response.ok) {
          throw new Error(`Failed to fetch characters: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Handle different response formats
        const charactersData = data.data || data.characters || (Array.isArray(data) ? data : []);
        
        // Transform the data to match our Character interface
        const formattedCharacters = charactersData.map((char: any) => ({
          id: char._id || char.id,
          name: char.name,
          description: char.description || char.background || '',
          profile_image: char.profile_image || char.avatar_image || char.image || '',
          background: char.background || '',
          personality: char.personality || '',
          skills: char.skills || '',
          goals: char.goals || '',
          relationships: char.relationships || '',
          voice_notes: char.voice_notes || ''
        }));
        
        setCharacters(formattedCharacters);
      } catch (err) {
        console.error('Error fetching characters:', err);
        setError(err instanceof Error ? err.message : 'Failed to load characters');
      } finally {
        setIsLoadingCharacters(false);
      }
    };
    
    fetchCharacters();
  }, []);

  // Handle pose enhancement
  const handleEnhancePose = async () => {
    if (!poseInput.trim()) {
      toast({
        title: "Error",
        description: "Please enter a pose to enhance.",
        variant: "destructive"
      });
      return;
    }

    setIsEnhancing(true);
    setError(null);

    try {
      const selectedCharacter = characters.find(char => char.id === selectedCharacterId);
      const accessToken = localStorage.getItem('access_token');
      
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      };

      if (accessToken) {
        headers['Authorization'] = `Bearer ${accessToken}`;
      }

      // Prepare character data
      const characterData = selectedCharacter ? {
        name: selectedCharacter.name,
        background: selectedCharacter.metadata?.background || '',
        personality: Array.isArray(selectedCharacter.metadata?.personality) 
          ? selectedCharacter.metadata.personality 
          : (selectedCharacter.metadata?.personality ? [selectedCharacter.metadata.personality] : []),
        skills: Array.isArray(selectedCharacter.metadata?.skills) 
          ? selectedCharacter.metadata.skills 
          : (selectedCharacter.metadata?.skills ? [selectedCharacter.metadata.skills] : []),
        goals: Array.isArray(selectedCharacter.metadata?.goals) 
          ? selectedCharacter.metadata.goals 
          : (selectedCharacter.metadata?.goals ? [selectedCharacter.metadata.goals] : []),
        relationships: typeof selectedCharacter.metadata?.relationships === 'object' && selectedCharacter.metadata?.relationships !== null
          ? selectedCharacter.metadata.relationships 
          : {},
        voice_notes: selectedCharacter.metadata?.voice_notes || ''
      } : null;

      // Prepare context data
      const contextData = {
        actions: [],
        emotions: [],
        environmental_details: sceneDump ? [sceneDump] : [],
        character_interactions: [],
        response_hooks: [],
        scene_timing: 'present',
        urgency_level: 'medium',
        narrative_tone: narrativeTone || 'neutral'
      };

      const requestPayload = {
        original_pose: poseInput,
        character: characterData,
        context: contextData,
        enhancement_style: enhancementStyle,
        enhancement_options: {
          include_environmental_details: addEnvironmentalDetails,
          detail_level: detailLevel,
          creativity_level: creativityLevel,
          sensory_focus: sensoryFocus,
          emotional_depth: emotionalDepth,
          include_internal_thoughts: includeInternalThoughts,
          emphasize_actions: emphasizeActions,
          preserve_original_tone: preserveOriginalTone,
          character_control_check: characterControlCheck
        },
        user_id: currentUserId // Add user ID for usage tracking
      };
      
      console.log('Sending request with user_id:', currentUserId);
      console.log('Full request payload:', requestPayload);
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/pose/enhance`, {
        method: 'POST',
        headers,
        body: JSON.stringify(requestPayload)
      });

      if (!response.ok) {
        if (response.status === 402) {
          // Payment required - user hit generation limit
          const errorData = await response.json();
          setUsageInfo(errorData.usage_info);
          setShowPaywall(true);
          throw new Error(errorData.error || 'Generation limit reached');
        }
        throw new Error(`Enhancement failed: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        setEnhancedPose(data.enhanced_pose);
        addPoseVersion(data.enhanced_pose);
        setError(null);
        
        // Update usage info from response
        if (data.usage_info) {
          setUsageInfo(data.usage_info);
        }
      } else {
        throw new Error(data.error || 'Enhancement failed');
      }

    } catch (err) {
      console.error('Error enhancing pose:', err);
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      setError(errorMessage);
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
    } finally {
      setIsEnhancing(false);
    }
  };

  // Helper function to add a new pose version
  const addPoseVersion = (pose: string, editSuggestion?: string) => {
    const newVersion = {
      id: Date.now().toString(),
      pose,
      timestamp: new Date(),
      editSuggestion
    };
    setPoseVersions(prev => [newVersion, ...prev]);
    setCurrentVersionIndex(0);
  };

  // Helper function to get current pose
  const getCurrentPose = () => {
    if (poseVersions.length > 0 && poseVersions[currentVersionIndex]) {
      return poseVersions[currentVersionIndex].pose;
    }
    return enhancedPose;
  };

  // Format text for copying
  const formatTextForCopy = (text: string, format: string): string => {
    switch (format) {
      case "mush":
      case "mux":
        return text.replace(/\n/g, "%r");
      case "moo":
        return text.replace(/\n/g, "%n");
      case "html":
        return text.replace(/\n/g, "<br>");
      default:
        return text;
    }
  };

  // Handle copy to clipboard
  const handleCopy = () => {
    const textToCopy = getCurrentPose();
    if (textToCopy) {
      const formattedText = formatTextForCopy(textToCopy, copyFormat);
      navigator.clipboard.writeText(formattedText);
      toast({
        title: "Copied!",
        description: "Enhanced pose copied to clipboard.",
      });
    }
  };

  // Handle refinement with suggestions
  const handleRefineWithSuggestion = async () => {
    if (!editSuggestion.trim() || !getCurrentPose()) {
      toast({
        title: "Error",
        description: "Please enter a refinement suggestion.",
        variant: "destructive"
      });
      return;
    }

    setIsRefining(true);

    try {
      const currentCharacter = characters.find(char => char.id === selectedCharacterId);
      const accessToken = localStorage.getItem('access_token');
      
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      };

      if (accessToken) {
        headers['Authorization'] = `Bearer ${accessToken}`;
      }

      // Prepare character data for backend
      const characterData = currentCharacter ? {
        name: currentCharacter.name,
        background: currentCharacter.metadata?.background || '',
        personality: Array.isArray(currentCharacter.metadata?.personality) 
          ? currentCharacter.metadata.personality 
          : (currentCharacter.metadata?.personality ? [currentCharacter.metadata.personality] : []),
        skills: Array.isArray(currentCharacter.metadata?.skills) 
          ? currentCharacter.metadata.skills 
          : (currentCharacter.metadata?.skills ? [currentCharacter.metadata.skills] : []),
        goals: Array.isArray(currentCharacter.metadata?.goals) 
          ? currentCharacter.metadata.goals 
          : (currentCharacter.metadata?.goals ? [currentCharacter.metadata.goals] : []),
        relationships: typeof currentCharacter.metadata?.relationships === 'object' && currentCharacter.metadata?.relationships !== null
          ? currentCharacter.metadata.relationships 
          : {},
        voice_notes: currentCharacter.metadata?.voice_notes || ''
      } : null;

      // Prepare context data for backend
      const contextData = {
        actions: [],
        emotions: [],
        environmental_details: sceneDump ? [sceneDump] : [],
        character_interactions: [],
        response_hooks: [],
        scene_timing: 'present',
        urgency_level: 'medium',
        narrative_tone: 'neutral'
      };

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/pose/refine`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          current_pose: getCurrentPose(), // Backend expects current_pose, not original_pose
          edit_suggestion: editSuggestion,
          character: characterData, // Send character object, not just name
          context: contextData, // Send context object, not just scene_context
          user_id: currentUserId // Add user ID for usage tracking
        })
      });

      if (!response.ok) {
        if (response.status === 402) {
          // Payment required - user hit generation limit
          const errorData = await response.json();
          setUsageInfo(errorData.usage_info);
          setShowPaywall(true);
          throw new Error(errorData.error || 'Generation limit reached');
        }
        throw new Error(`Refinement failed: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        setEnhancedPose(data.refined_pose);
        addPoseVersion(data.refined_pose, editSuggestion);
        setEditSuggestion(""); // Clear the suggestion after successful refinement
        setError(null);
        
        // Update usage info from response
        if (data.usage_info) {
          setUsageInfo(data.usage_info);
        }
      } else {
        throw new Error(data.error || 'Refinement failed');
      }

    } catch (err) {
      console.error('Error refining pose:', err);
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
    } finally {
      setIsRefining(false);
    }
  };

  // Handle version selection
  const handleVersionSelect = (index: number) => {
    setCurrentVersionIndex(index);
    if (poseVersions[index]) {
      setEnhancedPose(poseVersions[index].pose);
    }
  };

  // Handle upgrade button click
  const handleUpgrade = () => {
    setShowPaywall(true);
  };

  // Handle purchase extra generations
  const handlePurchaseExtra = () => {
    setShowPaywall(true);
  };

  // Handle purchase completion
  const handlePurchaseComplete = (generationsAdded: number) => {
    // Refresh usage info after purchase
    if (currentUserId) {
      fetchUsageInfo();
    }
    
    toast({
      title: "Purchase Successful!",
      description: `${generationsAdded} generations added to your account`,
    });
  };

  // Fetch current usage info
  const fetchUsageInfo = async () => {
    if (!currentUserId) return;
    
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/purchase/usage-status?user_id=${currentUserId}`
      );
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setUsageInfo(data.usage_info);
        }
      }
    } catch (error) {
      console.error('Error fetching usage info:', error);
    }
  };

  // Fetch usage info when user ID is available
  useEffect(() => {
    if (currentUserId) {
      fetchUsageInfo();
    }
  }, [currentUserId]);

  // Show inline paywall when user hits limits
  if (showPaywall) {
    return (
      <div className="flex-1 p-4 md:p-8">
        <div className="mx-auto max-w-7xl">
          <div className="mb-8 text-center">
            <button 
              onClick={() => setShowPaywall(false)}
              className="text-sm text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-2"
            >
              ← Back to Pose Enhancer
            </button>
          </div>
          <InlinePaywall
            subscriptionStatus={usageInfo?.subscription_status || 'free'}
            onPurchaseComplete={handlePurchaseComplete}
            userId={currentUserId || undefined}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-4 md:p-8">
      {/* Page Header with Usage Display */}
      <div className="mx-auto max-w-7xl mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Pose Enhancer</h1>
            <p className="text-muted-foreground mt-1">Transform your basic poses into rich, immersive narratives</p>
          </div>
          <UsageDisplay
            usageInfo={usageInfo}
            onUpgrade={handleUpgrade}
            onPurchaseExtra={handlePurchaseExtra}
            className="w-[350px] flex-shrink-0"
          />
        </div>
      </div>
      
      <div className="mx-auto grid w-full max-w-7xl items-start gap-8 xl:grid-cols-[1fr_350px]">
        
        {/* Main Content Area (Left) */}
        <div className="grid auto-rows-max items-start gap-8">
          
          {/* Character Selection */}
          <CharacterSelection
            characters={characters}
            selectedCharacterId={selectedCharacterId}
            onCharacterSelect={setSelectedCharacterId}
            isLoadingCharacters={isLoadingCharacters}
          />

          {/* Scene Context */}
          <SceneContext
            sceneDump={sceneDump}
            onSceneDumpChange={setSceneDump}
          />

          {/* Pose Input with Enhancement Settings */}
          <PoseInput
            poseInput={poseInput}
            onPoseInputChange={setPoseInput}
            isEnhancing={isEnhancing}
            onEnhancePose={handleEnhancePose}
            enhancementStyle={enhancementStyle}
            onStyleChange={setEnhancementStyle}
            narrativeTone={narrativeTone}
            onNarrativeToneChange={setNarrativeTone}
            detailLevel={detailLevel}
            onDetailLevelChange={setDetailLevel}
            creativityLevel={creativityLevel}
            onCreativityLevelChange={setCreativityLevel}
            sensoryFocus={sensoryFocus}
            onSensoryFocusChange={setSensoryFocus}
            emotionalDepth={emotionalDepth}
            onEmotionalDepthChange={setEmotionalDepth}
            includeInternalThoughts={includeInternalThoughts}
            onIncludeInternalThoughtsChange={setIncludeInternalThoughts}
            emphasizeActions={emphasizeActions}
            onEmphasizeActionsChange={setEmphasizeActions}
            preserveOriginalTone={preserveOriginalTone}
            onPreserveOriginalToneChange={setPreserveOriginalTone}
            addEnvironmentalDetails={addEnvironmentalDetails}
            onAddEnvironmentalDetailsChange={setAddEnvironmentalDetails}
            characterControlCheck={characterControlCheck}
            onCharacterControlCheckChange={setCharacterControlCheck}
            showAdvancedSettings={showAdvancedSettings}
            onShowAdvancedSettingsChange={setShowAdvancedSettings}
            subscriptionStatus={usageInfo?.subscription_status}
            onUpgradeClick={() => setShowPaywall(true)}
          />

          {/* Enhanced Output */}
          <EnhancedOutput
            enhancedPose={getCurrentPose()}
            copyFormat={copyFormat}
            onCopyFormatChange={setCopyFormat}
            onCopy={handleCopy}
          />
          
          {/* Enhancement Analysis - Moved to main area */}
          <EnhancementAnalysis
            enhancedPose={getCurrentPose()}
            originalPose={poseInput}
            enhancementSettings={{
              detailLevel,
              creativityLevel,
              sensoryFocus,
              emotionalDepth,
              enhancementStyle,
              narrativeTone
            }}
          />

        </div>

        {/* Sidebar (Right) - Streamlined */}
        <div className="grid auto-rows-max items-start gap-6 sticky top-8">
          
          {/* Refinement - Most important for workflow */}
          <Refinement
            editSuggestion={editSuggestion}
            onEditSuggestionChange={setEditSuggestion}
            isRefining={isRefining}
            onRefineWithSuggestion={handleRefineWithSuggestion}
            hasEnhancedPose={!!getCurrentPose()}
          />
          
          {/* Version History - Compact */}
          <VersionHistory
            poseVersions={poseVersions}
            currentVersionIndex={currentVersionIndex}
            onVersionSelect={handleVersionSelect}
          />

        </div>
      </div>

    </div>
  );
}
