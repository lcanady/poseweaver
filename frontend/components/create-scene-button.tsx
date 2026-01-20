import { useState, useEffect } from 'react';
import { useAuth } from "@/contexts/auth-context";
import { Button } from "@/components/ui/button";
import { PlusCircle } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getApiUrl } from '@/utils/api-utils';
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
  const { getToken } = useAuth();

  useEffect(() => {
    const checkForCharacters = async () => {
      setIsLoading(true);
      try {
        const token = await getToken();
        if (!token) {
          setHasCharacters(false);
          setIsLoading(false);
          return;
        }

        const response = await fetch(`${getApiUrl()}/api/characters/mgmt`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch characters');
        }

        const data = await response.json();
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
  }, [getToken]);

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
