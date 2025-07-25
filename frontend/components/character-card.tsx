import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { 
  MoreHorizontal, 
  Eye, 
  Edit, 
  Share2, 
  ExternalLink,
  Calendar,
  Clock,
  Settings
} from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { DeleteCharacterDialog } from "./delete-character-dialog"
import { CharacterShareModal } from "./character-share-modal"
import { CharacterSettingsModal } from "./character-settings-modal"
import type { Character } from "@/lib/types"
import Link from "next/link"

interface CharacterCardProps {
  character: Character
}

export function CharacterCard({ character }: CharacterCardProps) {
  // Convert character data to match the Character interface used in other components
  const characterForModals = {
    id: character.id,
    name: character.name,
    description: character.description,
    profile_image: character.avatarUrl,
    created_at: (character as any).created_at || undefined,
    last_used: character.lastUsed,
    metadata: {
      background: '',
      personality: [],
      skills: [],
      goals: [],
      relationships: '',
      voice_notes: ''
    }
  };

  return (
    <Card className="group hover:shadow-md transition-all duration-200 border-border/50 hover:border-border">
      <CardHeader className="pb-3">
        <div className="flex items-start gap-4">
          <Avatar className="h-16 w-16 border-2 border-border/20">
            <AvatarImage src={character.avatarUrl || "/placeholder.svg"} alt={character.name} />
            <AvatarFallback className="text-lg font-semibold">
              {character.name.charAt(0)}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <CardTitle className="text-xl truncate">{character.name}</CardTitle>
                <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                  {(character as any).created_at && (
                    <div className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {new Date((character as any).created_at).toLocaleDateString()}
                    </div>
                  )}
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {character.lastUsed}
                  </div>
                </div>
              </div>
              
              {/* Actions Dropdown */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48">
                  <DropdownMenuItem asChild>
                    <Link href={`/dashboard/characters/${character.id}`} className="flex items-center">
                      <Eye className="h-4 w-4 mr-2" />
                      View Details
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href={`/dashboard/characters/${character.id}/edit`} className="flex items-center">
                      <Edit className="h-4 w-4 mr-2" />
                      Edit Character
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href={`/character/${character.id}`} className="flex items-center">
                      <ExternalLink className="h-4 w-4 mr-2" />
                      Public Profile
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <CharacterSettingsModal character={characterForModals}>
                    <DropdownMenuItem onSelect={(e) => e.preventDefault()}>
                      <Settings className="h-4 w-4 mr-2" />
                      Character Settings
                    </DropdownMenuItem>
                  </CharacterSettingsModal>
                  <CharacterShareModal character={characterForModals}>
                    <DropdownMenuItem onSelect={(e) => e.preventDefault()}>
                      <Share2 className="h-4 w-4 mr-2" />
                      Share Character
                    </DropdownMenuItem>
                  </CharacterShareModal>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem 
                    className="text-destructive focus:text-destructive"
                    onSelect={(e) => {
                      e.preventDefault();
                      // Delete functionality will be handled by the DeleteCharacterDialog
                    }}
                  >
                    Delete Character
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0 pb-4">
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground line-clamp-3 leading-relaxed">
            {character.description || "No description provided"}
          </p>
          
          <div className="flex items-center justify-between">
            <Badge variant="outline" className="text-xs">
              Character Profile
            </Badge>
            <div className="flex items-center gap-1">
              <div className="h-2 w-2 rounded-full bg-green-500" />
              <span className="text-xs text-muted-foreground">Active</span>
            </div>
          </div>
        </div>
      </CardContent>
      
      <Separator />
      
      <CardFooter className="pt-4 pb-4">
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" asChild>
              <Link href={`/dashboard/characters/${character.id}`}>
                <Eye className="h-3 w-3 mr-1" />
                View
              </Link>
            </Button>
            <Button variant="outline" size="sm" asChild>
              <Link href={`/dashboard/characters/${character.id}/edit`}>
                <Edit className="h-3 w-3 mr-1" />
                Edit
              </Link>
            </Button>
          </div>
          
          <div className="flex items-center gap-1">
            <CharacterShareModal character={characterForModals}>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <Share2 className="h-3 w-3" />
              </Button>
            </CharacterShareModal>
          </div>
        </div>
      </CardFooter>
    </Card>
  )
}
