import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { DeleteCharacterDialog } from "./delete-character-dialog"
import type { Character } from "@/lib/types"
import Link from "next/link"

interface CharacterCardProps {
  character: Character
}

export function CharacterCard({ character }: CharacterCardProps) {
  return (
    <Card className="flex flex-col">
      <CardHeader className="flex flex-row items-start gap-4 space-y-0">
        <Avatar className="h-12 w-12">
          <AvatarImage src={character.avatarUrl || "/placeholder.svg"} alt={character.name} />
          <AvatarFallback>{character.name.charAt(0)}</AvatarFallback>
        </Avatar>
        <div className="flex-1">
          <CardTitle>{character.name}</CardTitle>
          <CardDescription>Last used: {character.lastUsed}</CardDescription>
        </div>
      </CardHeader>
      <CardContent className="flex-grow">
        <p className="text-sm text-muted-foreground line-clamp-3">{character.description}</p>
      </CardContent>
      <CardFooter className="flex justify-end gap-2">
        <Button variant="outline" asChild>
          <Link href={`/dashboard/characters/${character.id}`}>Edit</Link>
        </Button>
        <DeleteCharacterDialog characterId={character.id} characterName={character.name} />
      </CardFooter>
    </Card>
  )
}
