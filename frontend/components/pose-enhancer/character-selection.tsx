import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Settings } from "lucide-react";
import { Character } from "@/hooks/useCharacter";
import { useCharacterSettings } from "@/hooks/useCharacterSettings";

interface CharacterSelectionProps {
  characters: Character[];
  selectedCharacterId: string;
  onCharacterSelect: (characterId: string) => void;
  isLoadingCharacters: boolean;
}

export const CharacterSelection = ({
  characters,
  selectedCharacterId,
  onCharacterSelect,
  isLoadingCharacters
}: CharacterSelectionProps) => {
  const selectedCharacter = characters.find(char => char.id === selectedCharacterId);
  const { settings: characterSettings } = useCharacterSettings(selectedCharacterId);
  
  // Check if character has custom settings (different from defaults)
  const hasCustomSettings = selectedCharacterId && (
    characterSettings.default_enhancement_style !== 'balanced' ||
    characterSettings.default_narrative_tone !== 'neutral' ||
    characterSettings.default_detail_level !== 50 ||
    characterSettings.default_creativity_level !== 60 ||
    characterSettings.enhancement_notes.trim() !== '' ||
    characterSettings.preferred_writing_style.trim() !== ''
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Character Selection</CardTitle>
        <CardDescription>Choose your character for pose enhancement</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label>Character</Label>
          <Select value={selectedCharacterId} onValueChange={onCharacterSelect}>
            <SelectTrigger>
              <SelectValue placeholder="Select a character..." />
            </SelectTrigger>
            <SelectContent>
              {isLoadingCharacters ? (
                <SelectItem value="loading" disabled>Loading characters...</SelectItem>
              ) : characters.length === 0 ? (
                <SelectItem value="none" disabled>No characters found</SelectItem>
              ) : (
                characters.map((character) => (
                  <SelectItem key={character.id} value={character.id}>
                    {character.name}
                  </SelectItem>
                ))
              )}
            </SelectContent>
          </Select>
        </div>
        
        {/* Character Preview */}
        {selectedCharacter && (
          <div className="bg-muted/50 rounded-lg p-4 border border-border/50">
            <div className="flex items-center mb-3">
              <div className="w-10 h-10 bg-secondary rounded-full flex items-center justify-center mr-3 overflow-hidden">
                {selectedCharacter.profile_image ? (
                  <img 
                    src={selectedCharacter.profile_image} 
                    alt={selectedCharacter.name}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      // Fallback to initials if image fails to load
                      const target = e.target as HTMLImageElement;
                      target.style.display = 'none';
                      const parent = target.parentElement;
                      if (parent) {
                        parent.innerHTML = `<span class="text-secondary-foreground font-medium">${selectedCharacter.name.charAt(0).toUpperCase()}</span>`;
                      }
                    }}
                  />
                ) : (
                  <span className="text-secondary-foreground font-medium">
                    {selectedCharacter.name.charAt(0).toUpperCase()}
                  </span>
                )}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <div className="font-medium">{selectedCharacter.name}</div>
                  {hasCustomSettings && (
                    <Badge variant="secondary" className="text-xs">
                      <Settings className="h-3 w-3 mr-1" />
                      Custom Settings
                    </Badge>
                  )}
                </div>
                <div className="text-sm text-muted-foreground">Selected for pose enhancement</div>
                {hasCustomSettings && (
                  <div className="text-xs text-muted-foreground mt-1">
                    Style: {characterSettings.default_enhancement_style} • 
                    Tone: {characterSettings.default_narrative_tone}
                  </div>
                )}
              </div>
            </div>
            <p className="text-sm text-muted-foreground">
              {selectedCharacter.description || 'No description available'}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
