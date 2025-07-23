import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { CardHeader, CardTitle } from "@/components/ui/card";
import { Character } from "@/hooks/useCharacter";

interface CharacterHeaderProps {
  character: Character;
}

export function CharacterHeader({ character }: CharacterHeaderProps) {
  return (
    <CardHeader className="flex flex-row items-center gap-4">
      <Avatar className="h-20 w-20">
        <AvatarImage 
          src={character.profile_image || "/placeholder.svg?width=80&height=80"} 
          alt={character.name} 
        />
        <AvatarFallback>{character.name.charAt(0)}</AvatarFallback>
      </Avatar>
      <div>
        <CardTitle className="text-2xl">{character.name}</CardTitle>
        <p className="text-muted-foreground">
          Created: {character.created_at ? new Date(character.created_at).toLocaleDateString() : 'Unknown'}
        </p>
        {character.last_used && (
          <p className="text-muted-foreground">
            Last used: {new Date(character.last_used).toLocaleDateString()}
          </p>
        )}
      </div>
    </CardHeader>
  );
}