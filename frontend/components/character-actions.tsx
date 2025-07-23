import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Edit, Trash, Loader2 } from "lucide-react";
import { useCharacterActions } from "@/hooks/useCharacterActions";

interface CharacterActionsProps {
  characterId: string;
}

export function CharacterActions({ characterId }: CharacterActionsProps) {
  const { deleteCharacter, isDeleting } = useCharacterActions();

  const handleDelete = () => {
    deleteCharacter(characterId);
  };

  return (
    <div className="flex gap-2">
      <Button variant="outline" asChild>
        <Link href={`/dashboard/characters/${characterId}/edit`}>
          <Edit className="mr-2 h-4 w-4" />
          Edit
        </Link>
      </Button>
      <Button variant="destructive" onClick={handleDelete} disabled={isDeleting}>
        {isDeleting ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Deleting...
          </>
        ) : (
          <>
            <Trash className="mr-2 h-4 w-4" />
            Delete
          </>
        )}
      </Button>
    </div>
  );
}