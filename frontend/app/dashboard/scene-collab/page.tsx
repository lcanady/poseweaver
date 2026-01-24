'use client';

import { CollaborativeScene } from '@/components/collaborative-scene';
import { useSearchParams } from 'next/navigation';
import { Suspense, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';

function SceneCollabContent() {
  const searchParams = useSearchParams();
  const sceneId = searchParams.get('scene');
  
  const [characterName, setCharacterName] = useState('');
  const [hasJoined, setHasJoined] = useState(false);

  if (!sceneId) {
    return (
      <div className="flex items-center justify-center h-full">
        <Card className="p-8 max-w-md">
          <h2 className="text-xl font-bold mb-4">No Scene Selected</h2>
          <p className="text-muted-foreground">
            Please select a scene from your scenes list to start collaborating.
          </p>
        </Card>
      </div>
    );
  }

  if (!hasJoined) {
    return (
      <div className="flex items-center justify-center h-full">
        <Card className="p-8 max-w-md w-full">
          <h2 className="text-2xl font-bold mb-6">Join Scene</h2>
          <div className="space-y-4">
            <div>
              <Label htmlFor="characterName">Character Name</Label>
              <Input
                id="characterName"
                value={characterName}
                onChange={(e) => setCharacterName(e.target.value)}
                placeholder="Enter your character name"
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && characterName.trim()) {
                    setHasJoined(true);
                  }
                }}
              />
            </div>
            <Button
              onClick={() => setHasJoined(true)}
              disabled={!characterName.trim()}
              className="w-full"
            >
              Join Scene
            </Button>
          </div>
          <div className="mt-6 p-4 bg-muted rounded-lg">
            <h3 className="font-semibold mb-2">Commands Available:</h3>
            <ul className="text-sm space-y-1 text-muted-foreground">
              <li><code className="bg-background px-1 rounded">/roll 1d20</code> - Roll a 20-sided die</li>
              <li><code className="bg-background px-1 rounded">/roll 2d6+3</code> - Roll with modifiers</li>
            </ul>
          </div>
        </Card>
      </div>
    );
  }

  return <CollaborativeScene sceneId={sceneId} characterName={characterName} />;
}

export default function SceneCollabPage() {
  return (
    <Suspense fallback={
      <div className="flex-1 flex justify-center items-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    }>
      <SceneCollabContent />
    </Suspense>
  );
}
