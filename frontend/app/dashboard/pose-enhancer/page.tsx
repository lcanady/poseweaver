"use client";

import { useState, useEffect } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Loader2, Sparkles, UserCircle2, Settings, Sliders } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/components/ui/use-toast";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Character } from "@/hooks/useCharacter";

export default function PoseEnhancerPage() {
  const [sceneDump, setSceneDump] = useState("");
  const [characterContext, setCharacterContext] = useState("");
  const [characterName, setCharacterName] = useState("");
  const [poseInput, setPoseInput] = useState("");
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [enhancedPose, setEnhancedPose] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [selectedCharacterId, setSelectedCharacterId] = useState<string>("");
  const [isLoadingCharacters, setIsLoadingCharacters] = useState(true);
  
  // Enhancement control states
  const [enhancementStyle, setEnhancementStyle] = useState("balanced");
  const [detailLevel, setDetailLevel] = useState([50]); // 0-100
  const [creativityLevel, setCreativityLevel] = useState([60]); // 0-100
  const [sensoryFocus, setSensoryFocus] = useState([40]); // 0-100
  const [emotionalDepth, setEmotionalDepth] = useState([50]); // 0-100
  const [narrativeTone, setNarrativeTone] = useState("neutral");
  const [includeInternalThoughts, setIncludeInternalThoughts] = useState(false);
  const [emphasizeActions, setEmphasizeActions] = useState(true);
  const [preserveOriginalTone, setPreserveOriginalTone] = useState(true);
  const [addEnvironmentalDetails, setAddEnvironmentalDetails] = useState(false);
  
  // Copy format options
  const [copyFormat, setCopyFormat] = useState("standard");
  
  // Version control and edit suggestions
  const [poseVersions, setPoseVersions] = useState<Array<{id: string, pose: string, timestamp: Date, editSuggestion?: string}>>([]);
  const [currentVersionIndex, setCurrentVersionIndex] = useState(0);
  const [editSuggestion, setEditSuggestion] = useState("");
  const [isRefining, setIsRefining] = useState(false);
  const [showVersionHistory, setShowVersionHistory] = useState(false);
  
  const { toast } = useToast();

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
          description: char.description || '',
          profile_image: char.profile_image || '/placeholder.svg?width=40&height=40',
          metadata: char.metadata || {
            background: char.background || '',
            personality: char.personality || [],
            skills: char.skills || [],
            goals: char.goals || [],
            voice_notes: char.voice_notes || ''
          }
        }));
        
        setCharacters(formattedCharacters);
      } catch (err) {
        console.error('Error fetching characters:', err);
        toast({
          title: "Error",
          description: err instanceof Error ? err.message : 'Failed to load characters',
          variant: "destructive"
        });
      } finally {
        setIsLoadingCharacters(false);
      }
    };
    
    fetchCharacters();
  }, [toast]);

  // Handle character selection
  const handleCharacterSelect = (characterId: string) => {
    setSelectedCharacterId(characterId);
    
    // If user selects manual entry, reset fields
    if (characterId === "manual") {
      setCharacterName("");
      setCharacterContext("");
      return;
    }
    
    const selectedCharacter = characters.find(char => char.id === characterId);
    
    if (selectedCharacter) {
      setCharacterName(selectedCharacter.name);
      
      // Create context from character metadata
      const metadata = selectedCharacter.metadata;
      let contextParts = [];
      
      if (selectedCharacter.description) {
        contextParts.push(`Description: ${selectedCharacter.description}`);
      }
      
      if (metadata?.background) {
        contextParts.push(`Background: ${metadata.background}`);
      }
      
      if (metadata?.personality && metadata.personality.length > 0) {
        contextParts.push(`Personality: ${metadata.personality.join(', ')}`);
      }
      
      if (metadata?.skills && metadata.skills.length > 0) {
        contextParts.push(`Skills: ${metadata.skills.join(', ')}`);
      }
      
      if (metadata?.goals && metadata.goals.length > 0) {
        contextParts.push(`Goals: ${metadata.goals.join(', ')}`);
      }
      
      if (metadata?.voice_notes) {
        contextParts.push(`Voice: ${metadata.voice_notes}`);
      }
      
      setCharacterContext(contextParts.join('\n\n'));
    }
  };

  const handleEnhancePose = async () => {
    if (!poseInput.trim()) {
      setError("Please provide a pose to enhance.");
      return;
    }

    if (selectedCharacterId === "manual" && !characterName.trim()) {
      setError("Please provide your character name.");
      return;
    }

    setIsEnhancing(true);
    setError(null);
    setEnhancedPose(null);

    try {
      // Create a payload with all the relevant information
      // We'll try the old way but just include the pose input directly
      const currentCharName = characterName || "Character";
      
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001";
      const response = await fetch(`${apiUrl}/api/pose/enhance`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(localStorage.getItem("access_token")
            ? { Authorization: `Bearer ${localStorage.getItem("access_token")}` }
            : {}),
        },
        body: JSON.stringify({
          original_pose: poseInput,
          character: characterContext ? {
            name: currentCharName,
            background: characterContext,
            personality: [],
            skills: [],
            goals: [],
            relationships: {},
            voice_notes: ""
          } : null,
          context: sceneDump ? {
            actions: [],
            emotions: [],
            environmental_details: [sceneDump],
            character_interactions: [],
            response_hooks: [],
            scene_timing: "present",
            urgency_level: "medium",
            narrative_tone: narrativeTone
          } : null,
          enhancement_style: enhancementStyle,
          enhancement_options: {
            detail_level: detailLevel[0],
            creativity_level: creativityLevel[0],
            sensory_focus: sensoryFocus[0],
            emotional_depth: emotionalDepth[0],
            narrative_tone: narrativeTone,
            include_internal_thoughts: includeInternalThoughts,
            emphasize_actions: emphasizeActions,
            preserve_original_tone: preserveOriginalTone,
            add_environmental_details: addEnvironmentalDetails
          }
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: `HTTP error ${response.status}` }));
        throw new Error(errorData.message || "Failed to enhance pose.");
      }

      const data = await response.json().catch(() => null);
      console.log('API Response:', data);
      
      // Check for any usable response content
      if (data) {
        // If we get an enhanced pose directly, use it
        if (data.enhanced_pose) {
          // Clear previous versions and start fresh
          setPoseVersions([]);
          setCurrentVersionIndex(0);
          // Add the enhanced pose as the first version
          addPoseVersion(data.enhanced_pose);
          toast({
            title: "Pose Enhanced",
            description: "Your pose has been successfully enhanced.",
          });
          return;
        }
        // If we get poses array, try to find the right one
        if (data.poses && data.poses.length > 0) {
          const enhancedPoses = data.poses.filter((p: any) => p.enhanced_content);
          
          if (enhancedPoses.length > 0) {
            // Use the first enhanced pose
            const enhancedPoseContent = enhancedPoses[0].enhanced_content;
            setEnhancedPose(enhancedPoseContent);
            toast({
              title: "Pose Enhanced",
              description: "Your pose has been enhanced successfully.",
            });
            return;
          } else if (data.poses[0].content) {
            // Fallback to regular content if no enhanced content
            setEnhancedPose(data.poses[0].content);
            toast({
              title: "Pose Processed",
              description: "Processed your pose but no enhancement was available.",
            });
            return;
          }
        }
        
        // If we get a raw text response
        if (typeof data === 'string' || data.text || data.content || data.result) {
          const content = data.text || data.content || data.result || data;
          setEnhancedPose(typeof content === 'string' ? content : JSON.stringify(content));
          toast({
            title: "Pose Processed",
            description: "Successfully processed your pose.",
          });
          return;
        }
      }
      
      // If we couldn't extract any useful response, just return the input
      console.warn('Could not extract enhanced pose from API response:', data);
      setEnhancedPose(poseInput);
      toast({
        title: "Using Original Pose",
        description: "Could not enhance the pose. Using the original input.",
        variant: "destructive"
      });
    } catch (err: any) {
      console.error("Pose enhancement error:", err);
      setError(err.message || "An error occurred while enhancing your pose.");
      
      // Fallback to the original pose on error
      setEnhancedPose(poseInput);
      toast({
        title: "Using Original Pose",
        description: "An error occurred. Using your original pose.",
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
    
    setPoseVersions(prev => [...prev, newVersion]);
    setCurrentVersionIndex(prev => prev + 1);
    setEnhancedPose(pose);
  };
  
  // Helper function to switch to a different version
  const switchToVersion = (index: number) => {
    if (index >= 0 && index < poseVersions.length) {
      setCurrentVersionIndex(index);
      setEnhancedPose(poseVersions[index].pose);
    }
  };
  
  // Helper function to get current pose (either from versions or enhancedPose)
  const getCurrentPose = () => {
    if (poseVersions.length > 0 && currentVersionIndex < poseVersions.length) {
      return poseVersions[currentVersionIndex].pose;
    }
    return enhancedPose;
  };

  const formatTextForCopy = (text: string, format: string): string => {
    // First, fix any literal \n\n characters that should be actual newlines
    let formattedText = text.replace(/\\n\\n/g, '\n\n').replace(/\\n/g, '\n');
    
    switch (format) {
      case "mush":
        // Replace newlines with %r for MUSH
        return formattedText.replace(/\n/g, '%r');
      case "mux":
        // Replace newlines with %r for MUX (same as MUSH)
        return formattedText.replace(/\n/g, '%r');
      case "moo":
        // Replace newlines with %n for MOO
        return formattedText.replace(/\n/g, '%n');
      case "html":
        // Replace newlines with <br> for HTML
        return formattedText.replace(/\n/g, '<br>');
      case "standard":
      default:
        // Keep standard newlines
        return formattedText;
    }
  };

  const handleCopy = () => {
    const currentPose = getCurrentPose();
    if (currentPose) {
      const formattedText = formatTextForCopy(currentPose, copyFormat);
      navigator.clipboard.writeText(formattedText);
      toast({
        title: "Copied to clipboard",
        description: `The enhanced pose has been copied with ${copyFormat} formatting.`,
      });
    }
  };
  
  const handleRefineWithSuggestion = async () => {
    if (!editSuggestion.trim() || !getCurrentPose()) {
      toast({
        title: "Error",
        description: "Please provide an edit suggestion.",
        variant: "destructive"
      });
      return;
    }
    
    setIsRefining(true);
    setError(null);
    
    try {
      const currentCharName = characterName || "Character";
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001";
      
      const response = await fetch(`${apiUrl}/api/pose/refine`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(localStorage.getItem("access_token")
            ? { Authorization: `Bearer ${localStorage.getItem("access_token")}` }
            : {}),
        },
        body: JSON.stringify({
          current_pose: getCurrentPose(),
          edit_suggestion: editSuggestion,
          original_pose: poseInput,
          character: characterContext ? {
            name: currentCharName,
            background: characterContext,
            personality: [],
            skills: [],
            goals: [],
            relationships: {},
            voice_notes: ""
          } : null,
          context: sceneDump ? {
            actions: [],
            emotions: [],
            environmental_details: [sceneDump],
            character_interactions: [],
            response_hooks: [],
            scene_timing: "present",
            urgency_level: "medium",
            narrative_tone: narrativeTone
          } : null,
          enhancement_style: enhancementStyle,
          enhancement_options: {
            detail_level: detailLevel[0],
            creativity_level: creativityLevel[0],
            sensory_focus: sensoryFocus[0],
            emotional_depth: emotionalDepth[0],
            narrative_tone: narrativeTone,
            include_internal_thoughts: includeInternalThoughts,
            emphasize_actions: emphasizeActions,
            preserve_original_tone: preserveOriginalTone,
            add_environmental_details: addEnvironmentalDetails
          }
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: `HTTP error ${response.status}` }));
        throw new Error(errorData.message || "Failed to refine pose.");
      }
      
      const data = await response.json().catch(() => null);
      
      if (data && data.refined_pose) {
        // Add the refined pose as a new version
        addPoseVersion(data.refined_pose, editSuggestion);
        setEditSuggestion(""); // Clear the suggestion after successful refinement
        
        toast({
          title: "Pose Refined",
          description: "Your pose has been refined based on your suggestions.",
        });
      } else {
        throw new Error("No refined pose returned from server.");
      }
    } catch (err: any) {
      console.error("Pose refinement error:", err);
      setError(err.message || "An error occurred while refining your pose.");
      
      toast({
        title: "Refinement Failed",
        description: "Could not refine the pose. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsRefining(false);
    }
  };

  return (
    <div className="container mx-auto py-6">
      <h1 className="text-3xl font-bold mb-6">Pose Enhancer</h1>
      <p className="text-muted-foreground mb-6">
        Extract and enhance poses from scene dumps with character context.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              Input
            </CardTitle>
            <CardDescription>
              Paste your scene dump and provide character information
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Select Character</Label>
              <Select 
                value={selectedCharacterId} 
                onValueChange={handleCharacterSelect}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Choose a character profile" />
                </SelectTrigger>
                <SelectContent>
                  {isLoadingCharacters ? (
                    <SelectItem value="loading" disabled>
                      <div className="flex items-center">
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Loading characters...
                      </div>
                    </SelectItem>
                  ) : characters.length > 0 ? (
                    characters.map(character => (
                      <SelectItem key={character.id} value={character.id}>
                        {character.name}
                      </SelectItem>
                    ))
                  ) : (
                    <SelectItem value="none" disabled>
                      No characters found
                    </SelectItem>
                  )}
                  <SelectItem value="manual">Enter character manually</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            {selectedCharacterId === "manual" && (
              <div className="space-y-2">
                <Label htmlFor="character-name">Your Character Name</Label>
                <Input
                  id="character-name"
                  placeholder="Enter the name of your character"
                  value={characterName}
                  onChange={(e) => setCharacterName(e.target.value)}
                />
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="scene-dump">Scene Context</Label>
              <Textarea
                id="scene-dump"
                placeholder="Paste scene context or scene dump here..."
                className="min-h-[150px]"
                value={sceneDump}
                onChange={(e) => setSceneDump(e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="character-context">
                Character Context (Optional)
              </Label>
              <Textarea
                id="character-context"
                placeholder="Provide additional context about your character..."
                className="min-h-[100px]"
                value={characterContext}
                onChange={(e) => setCharacterContext(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="pose-input">Your Pose to Enhance</Label>
              <Textarea
                id="pose-input"
                placeholder="Enter the pose you want to enhance..."
                className="min-h-[100px]"
                value={poseInput}
                onChange={(e) => setPoseInput(e.target.value)}
              />
            </div>

            <Separator className="my-4" />
            
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Settings className="h-4 w-4" />
                <Label className="text-sm font-medium">Enhancement Controls</Label>
              </div>
              
              <Tabs defaultValue="basic" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="basic">Basic</TabsTrigger>
                  <TabsTrigger value="advanced">Advanced</TabsTrigger>
                </TabsList>
                
                <TabsContent value="basic" className="space-y-4">
                  <div className="space-y-2">
                    <Label>Enhancement Style</Label>
                    <Select value={enhancementStyle} onValueChange={setEnhancementStyle}>
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
                    <Label>Detail Level: {detailLevel[0]}%</Label>
                    <Slider
                      value={detailLevel}
                      onValueChange={setDetailLevel}
                      max={100}
                      step={5}
                      className="w-full"
                    />
                    <p className="text-xs text-muted-foreground">
                      How much descriptive detail to add
                    </p>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Creativity Level: {creativityLevel[0]}%</Label>
                    <Slider
                      value={creativityLevel}
                      onValueChange={setCreativityLevel}
                      max={100}
                      step={5}
                      className="w-full"
                    />
                    <p className="text-xs text-muted-foreground">
                      How creative and varied the language should be
                    </p>
                  </div>
                </TabsContent>
                
                <TabsContent value="advanced" className="space-y-4">
                  <div className="space-y-2">
                    <Label>Sensory Focus: {sensoryFocus[0]}%</Label>
                    <Slider
                      value={sensoryFocus}
                      onValueChange={setSensoryFocus}
                      max={100}
                      step={5}
                      className="w-full"
                    />
                    <p className="text-xs text-muted-foreground">
                      Emphasis on sensory details (sight, sound, touch, etc.)
                    </p>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Emotional Depth: {emotionalDepth[0]}%</Label>
                    <Slider
                      value={emotionalDepth}
                      onValueChange={setEmotionalDepth}
                      max={100}
                      step={5}
                      className="w-full"
                    />
                    <p className="text-xs text-muted-foreground">
                      How much emotional nuance to include
                    </p>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Narrative Tone</Label>
                    <Select value={narrativeTone} onValueChange={setNarrativeTone}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="dramatic">Dramatic</SelectItem>
                        <SelectItem value="neutral">Neutral</SelectItem>
                        <SelectItem value="casual">Casual</SelectItem>
                        <SelectItem value="poetic">Poetic</SelectItem>
                        <SelectItem value="intense">Intense</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="internal-thoughts">Include Internal Thoughts</Label>
                      <Switch
                        id="internal-thoughts"
                        checked={includeInternalThoughts}
                        onCheckedChange={setIncludeInternalThoughts}
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <Label htmlFor="emphasize-actions">Emphasize Actions</Label>
                      <Switch
                        id="emphasize-actions"
                        checked={emphasizeActions}
                        onCheckedChange={setEmphasizeActions}
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <Label htmlFor="preserve-tone">Preserve Original Tone</Label>
                      <Switch
                        id="preserve-tone"
                        checked={preserveOriginalTone}
                        onCheckedChange={setPreserveOriginalTone}
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <Label htmlFor="environmental-details">Add Environmental Details</Label>
                      <Switch
                        id="environmental-details"
                        checked={addEnvironmentalDetails}
                        onCheckedChange={setAddEnvironmentalDetails}
                      />
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </div>

            <Button
              onClick={handleEnhancePose}
              disabled={isEnhancing || !poseInput.trim() || (selectedCharacterId === "manual" && !characterName.trim())}
              className="w-full"
            >
              {isEnhancing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Enhancing...
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Enhance Pose
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              Enhanced Pose
            </CardTitle>
            <CardDescription>
              The enhanced version of your character's pose
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {getCurrentPose() ? (
              <div className="space-y-4">
                {/* Version Control Header */}
                {poseVersions.length > 0 && (
                  <div className="flex items-center justify-between border-b pb-2">
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium">Enhanced Pose</h3>
                      <span className="text-sm text-muted-foreground">
                        Version {currentVersionIndex + 1} of {poseVersions.length}
                      </span>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowVersionHistory(!showVersionHistory)}
                    >
                      {showVersionHistory ? "Hide" : "Show"} History
                    </Button>
                  </div>
                )}
                
                {/* Version History Panel */}
                {showVersionHistory && poseVersions.length > 1 && (
                  <div className="bg-muted/50 p-3 rounded-md space-y-2">
                    <h4 className="text-sm font-medium">Version History</h4>
                    <div className="space-y-1 max-h-32 overflow-y-auto">
                      {poseVersions.map((version, index) => (
                        <div
                          key={version.id}
                          className={`flex items-center justify-between p-2 rounded text-sm cursor-pointer transition-colors ${
                            index === currentVersionIndex
                              ? "bg-primary text-primary-foreground"
                              : "bg-background hover:bg-muted"
                          }`}
                          onClick={() => switchToVersion(index)}
                        >
                          <div>
                            <span className="font-medium">Version {index + 1}</span>
                            {version.editSuggestion && (
                              <span className="text-xs opacity-75 ml-2">
                                (Edit: {version.editSuggestion.substring(0, 30)}...)
                              </span>
                            )}
                          </div>
                          <span className="text-xs opacity-75">
                            {version.timestamp.toLocaleTimeString()}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Enhanced Pose Display */}
                <div className="bg-muted p-4 rounded-md whitespace-pre-wrap">
                  {getCurrentPose()}
                </div>
                
                {/* Edit Suggestion Section */}
                <div className="space-y-3 border-t pt-4">
                  <div className="space-y-2">
                    <Label htmlFor="edit-suggestion">Suggest Improvements</Label>
                    <Textarea
                      id="edit-suggestion"
                      placeholder="Describe what you'd like to change or improve about this pose..."
                      value={editSuggestion}
                      onChange={(e) => setEditSuggestion(e.target.value)}
                      className="min-h-[80px]"
                    />
                  </div>
                  <Button
                    onClick={handleRefineWithSuggestion}
                    disabled={isRefining || !editSuggestion.trim()}
                    className="w-full"
                  >
                    {isRefining ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Refining Pose...
                      </>
                    ) : (
                      "Refine with Suggestions"
                    )}
                  </Button>
                </div>
                
                {/* Copy Section */}
                <div className="space-y-2 border-t pt-4">
                  <div className="flex items-center gap-2">
                    <Label htmlFor="copy-format" className="text-sm">Copy Format:</Label>
                    <Select value={copyFormat} onValueChange={setCopyFormat}>
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="standard">Standard</SelectItem>
                        <SelectItem value="mush">MUSH (%r)</SelectItem>
                        <SelectItem value="mux">MUX (%r)</SelectItem>
                        <SelectItem value="moo">MOO (%n)</SelectItem>
                        <SelectItem value="html">HTML (&lt;br&gt;)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button onClick={handleCopy} variant="outline" className="w-full">
                    Copy to Clipboard
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                {isEnhancing ? (
                  <div className="flex flex-col items-center">
                    <Loader2 className="h-10 w-10 animate-spin mb-2" />
                    <p>Enhancing your pose...</p>
                  </div>
                ) : (
                  <p>
                    Enhanced pose will appear here after processing your scene
                    dump.
                  </p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Separator className="my-8" />

      <div className="text-sm text-muted-foreground">
        <h3 className="text-lg font-medium mb-2">How it works</h3>
        <ol className="list-decimal pl-5 space-y-1">
          <li>Select your character from your saved profiles or enter manually</li>
          <li>Paste scene context to provide situational background (optional)</li>
          <li>Character context will be automatically filled from your profile</li>
          <li>Enter the pose you want to enhance</li>
          <li>Click "Enhance Pose" to generate a richer version of your pose</li>
        </ol>
      </div>
    </div>
  );
}
