import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { useState } from 'react'
import { Loader2 } from "lucide-react"
import { toast } from "@/components/ui/use-toast"
import { getApiUrl } from '@/utils/api-utils';

interface DeleteCharacterDialogProps {
  characterId: string;
  characterName: string;
}

export function DeleteCharacterDialog({ characterId, characterName }: DeleteCharacterDialogProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  
  const handleDelete = async () => {
    if (!characterId) return;
    
    setIsDeleting(true);
    
    try {
      // Get access token from localStorage
      const accessToken = localStorage.getItem('access_token');
      
      if (!accessToken) {
        throw new Error('No access token found. Please log in.');
      }
      
      const response = await fetch(
        `${getApiUrl()}/api/characters/mgmt/${characterId}`,
        {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`
          }
        }
      );
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to delete character');
      }
      
      toast({
        title: "Success",
        description: `${characterName} has been deleted successfully.`,
      });
      
      // Close the dialog and refresh the page to update the character list
      setIsOpen(false);
      setTimeout(() => window.location.reload(), 500);
      
    } catch (error) {
      console.error('Error deleting character:', error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : 'Failed to delete character',
        variant: "destructive"
      });
    } finally {
      setIsDeleting(false);
    }
  };
  
  return (
    <AlertDialog open={isOpen} onOpenChange={setIsOpen}>
      <AlertDialogTrigger asChild>
        <Button variant="destructive">Delete</Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
          <AlertDialogDescription>
            This action cannot be undone. This will permanently delete the character profile for{" "}
            <span className="font-semibold text-foreground">{characterName}</span> and all associated data.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
          <AlertDialogAction 
            onClick={handleDelete} 
            disabled={isDeleting}
          >
            {isDeleting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Deleting...
              </>
            ) : (
              'Delete'
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
