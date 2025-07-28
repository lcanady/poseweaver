import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Trash2, Copy, Calendar } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import { apiRequest } from "@/utils/api-utils";

interface SavedPose {
  id: string;
  original_pose: string;
  enhanced_pose: string;
  enhancement_settings: any;
  tags: string[];
  timestamp: string;
}

interface SavedPosesProps {
  characterId: string;
  onPoseSelect?: (pose: SavedPose) => void;
}

export const SavedPoses = ({ characterId, onPoseSelect }: SavedPosesProps) => {
  const [poses, setPoses] = useState<SavedPose[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    if (characterId) {
      fetchSavedPoses();
    }
  }, [characterId]);

  const fetchSavedPoses = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiRequest(`/api/characters/${characterId}/saved-poses`);
      const data = await response.json();
      
      if (data.success) {
        setPoses(data.poses || []);
      } else {
        throw new Error(data.error || 'Failed to fetch saved poses');
      }
    } catch (err) {
      console.error('Error fetching saved poses:', err);
      setError(err instanceof Error ? err.message : 'Failed to load saved poses');
    } finally {
      setLoading(false);
    }
  };

  const deletePose = async (poseId: string) => {
    try {
      const response = await apiRequest(`/api/characters/${characterId}/saved-poses/${poseId}`, {
        method: 'DELETE'
      });
      
      const data = await response.json();
      if (data.success) {
        setPoses(poses.filter(pose => pose.id !== poseId));
        toast({
          title: "Pose deleted",
          description: "Saved pose has been removed"
        });
      } else {
        throw new Error(data.error || 'Failed to delete pose');
      }
    } catch (err) {
      console.error('Error deleting pose:', err);
      toast({
        title: "Failed to delete pose",
        description: err instanceof Error ? err.message : "An unexpected error occurred",
        variant: "destructive"
      });
    }
  };

  const copyPose = (pose: SavedPose) => {
    navigator.clipboard.writeText(pose.enhanced_pose);
    toast({
      title: "Copied to clipboard",
      description: "Enhanced pose copied successfully"
    });
  };

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Saved Poses</CardTitle>
          <CardDescription>Loading saved poses...</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Saved Poses</CardTitle>
          <CardDescription className="text-destructive">{error}</CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={fetchSavedPoses} variant="outline" size="sm">
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Saved Poses ({poses.length})</CardTitle>
        <CardDescription>
          Enhanced poses saved for character training
        </CardDescription>
      </CardHeader>
      <CardContent>
        {poses.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <p>No saved poses yet.</p>
            <p className="text-sm">Enhanced poses you save will appear here.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {poses.map((pose) => (
              <div
                key={pose.id}
                className="border rounded-lg p-4 space-y-3 hover:bg-muted/30 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Calendar className="h-3 w-3" />
                    {formatDate(pose.timestamp)}
                  </div>
                  <div className="flex gap-1">
                    <Button
                      onClick={() => copyPose(pose)}
                      size="sm"
                      variant="ghost"
                      className="h-6 w-6 p-0"
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                    <Button
                      onClick={() => deletePose(pose.id)}
                      size="sm"
                      variant="ghost"
                      className="h-6 w-6 p-0 text-destructive hover:text-destructive"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>

                <div className="space-y-2">
                  <div>
                    <div className="text-xs font-medium text-muted-foreground mb-1">
                      Original:
                    </div>
                    <div className="text-sm bg-muted/50 rounded p-2 border">
                      {pose.original_pose}
                    </div>
                  </div>
                  
                  <div>
                    <div className="text-xs font-medium text-muted-foreground mb-1">
                      Enhanced:
                    </div>
                    <div className="text-sm bg-muted/30 rounded p-2 border">
                      {pose.enhanced_pose}
                    </div>
                  </div>
                </div>

                {pose.tags && pose.tags.length > 0 && (
                  <div className="flex gap-1 flex-wrap">
                    {pose.tags.map((tag, index) => (
                      <Badge key={index} variant="secondary" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                )}

                {onPoseSelect && (
                  <Button
                    onClick={() => onPoseSelect(pose)}
                    size="sm"
                    variant="outline"
                    className="w-full"
                  >
                    Use for Training
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
