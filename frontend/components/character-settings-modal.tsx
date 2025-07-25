'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Settings } from "lucide-react";
import { Character } from "@/hooks/useCharacter";
import { CharacterSettings } from "@/components/character-settings";

interface CharacterSettingsModalProps {
  character: Character;
  children?: React.ReactNode;
}

export function CharacterSettingsModal({ character, children }: CharacterSettingsModalProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {children || (
          <Button variant="outline" className="w-full justify-start">
            <Settings className="h-4 w-4 mr-2" />
            Character Settings
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Character Settings - {character.name}</DialogTitle>
          <DialogDescription>
            Configure enhancement preferences and default settings for this character.
          </DialogDescription>
        </DialogHeader>
        <CharacterSettings 
          character={character} 
          onSettingsChange={() => {
            // Settings are automatically saved in the component
          }}
        />
      </DialogContent>
    </Dialog>
  );
}
