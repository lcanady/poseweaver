import { useState, useEffect } from 'react';
import { useAuth } from "@/contexts/auth-context";
import { Button } from "@/components/ui/button";
import { PlusCircle } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from "@/components/ui/dialog";

interface CreateSceneButtonProps {
  variant?: "default" | "outline" | "secondary" | "ghost" | "link" | "destructive";
  size?: "default" | "sm" | "lg" | "icon";
  className?: string;
}

export function CreateSceneButton({ 
  variant = "default", 
  size = "default",
  className = ""
}: CreateSceneButtonProps) {
  const [hasCharacters, setHasCharacters] = useState<boolean | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const router = useRouter();
  const { refreshToken } = useAuth();

  useEffect(() => {
    const checkForCharacters = async () => {
      setIsLoading(true);
      try {
        const token = localStorage.getItem('access_token');
        if (!token) {
          setHasCharacters(false);
          setIsLoading(false);
          return;
        }

        // Use the character management API to check if user has characters
        const fetchWithRefresh = async (retryCount = 0) => {
          try {
            // Get the latest token from localStorage
            const currentToken = localStorage.getItem('access_token');
            
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/characters/mgmt`, {
              headers: {
                'Authorization': `Bearer ${currentToken}`,
                'Content-Type': 'application/json',
              },
            });

            if (response.status === 401 && retryCount < 1) {
              console.log('Token expired, attempting refresh...');
              // Try to refresh the token
              await refreshToken();
              // Retry the request
              return await fetchWithRefresh(retryCount + 1);
            }

            if (!response.ok) {
              throw new Error('Failed to fetch characters');
            }

            return await response.json();
          } catch (error) {
            console.error('Error in fetchWithRefresh:', error);
            throw error;
          }
        };

        const data = await fetchWithRefresh();
        // Check if user has any characters
        setHasCharacters(data.success && data.data && data.data.length > 0);
      } catch (err) {
        console.error('Error checking for characters:', err);
        setHasCharacters(false);
      } finally {
        setIsLoading(false);
      }
    };

    checkForCharacters();
  }, [refreshToken]);  // Added refreshToken to dependency array

  const handleClick = (e: React.MouseEvent) => {
    if (!hasCharacters) {
      e.preventDefault();
      setShowDialog(true);
    }
    // If they have characters, the Link will work normally
  };

  const handleCreateCharacter = () => {
    setShowDialog(false);
    router.push('/dashboard/characters/create');
  };

  return (
    <>
      <Button 
        asChild 
        variant={variant} 
        size={size} 
        className={className}
        disabled={isLoading}
      >
        <Link href="/dashboard/scene-weaver" onClick={handleClick}>
          <PlusCircle className="mr-2 h-4 w-4" />
          Start New Scene
        </Link>
      </Button>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create a Character First</DialogTitle>
            <DialogDescription>
              You need to create at least one character before you can start a new scene.
              Characters are essential for roleplaying and storytelling in scenes.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateCharacter}>Create Character</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
