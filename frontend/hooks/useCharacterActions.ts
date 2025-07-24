import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from "@/components/ui/use-toast";
import { getApiUrl } from '@/utils/api-utils';

export function useCharacterActions() {
  const router = useRouter();
  const [isDeleting, setIsDeleting] = useState(false);

  const deleteCharacter = async (characterId: string) => {
    if (!confirm('Are you sure you want to delete this character? This action cannot be undone.')) {
      return false;
    }

    setIsDeleting(true);
    
    try {
      const accessToken = localStorage.getItem('access_token');
      
      if (!accessToken) {
        throw new Error('No access token found. Please log in again.');
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
        throw new Error('Failed to delete character');
      }
      
      toast({
        title: "Character deleted",
        description: "Character has been successfully deleted."
      });
      
      router.push('/dashboard/characters');
      return true;
    } catch (err) {
      console.error('Error deleting character:', err);
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : 'Failed to delete character',
        variant: "destructive"
      });
      return false;
    } finally {
      setIsDeleting(false);
    }
  };

  return { deleteCharacter, isDeleting };
}