"use client"

import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { 
  Trash, 
  Edit, 
  ChevronDown,
  ChevronUp,
  Plus,
  Save,
  X,
  Eye
} from 'lucide-react'
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger,
  DialogFooter
} from '@/components/ui/dialog'
import { scenePosesService } from '@/services/scene-poses-service'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface ScenePose {
  id: string;
  character_name: string;
  content: string;
  pose_type: string;
  is_ooc: boolean;
  timestamp: string;
  word_count?: number;
  analysis_data?: Record<string, any>;
}

interface ScenePosesListProps {
  sceneId: string;
  title?: string;
  onPoseClick?: (pose: ScenePose) => void;
  onUpdateSuccess?: () => void;
}

export function ScenePosesList({ 
  sceneId, 
  title = "Scene Poses", 
  onPoseClick,
  onUpdateSuccess
}: ScenePosesListProps) {
  const [poses, setPoses] = useState<ScenePose[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingPose, setEditingPose] = useState<ScenePose | null>(null);
  const [newPose, setNewPose] = useState<{
    character_name: string;
    content: string;
    is_ooc: boolean;
  } | null>(null);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [poseToDelete, setPoseToDelete] = useState<ScenePose | null>(null);
  const [expandedPoses, setExpandedPoses] = useState<Record<string, boolean>>({});

  // Load poses on component mount
  useEffect(() => {
    loadPoses();
  }, [sceneId]);

  // Function to load poses
  const loadPoses = async () => {
    try {
      setLoading(true);
      setError(null);
      const poseData = await scenePosesService.getPoses(sceneId);
      setPoses(poseData);
    } catch (err) {
      setError('Failed to load poses');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Toggle pose expansion
  const togglePoseExpansion = (poseId: string) => {
    setExpandedPoses(prev => ({
      ...prev,
      [poseId]: !prev[poseId]
    }));
  };

  // Handle pose edit
  const handleEditPose = (pose: ScenePose) => {
    setEditingPose({...pose});
    setIsEditDialogOpen(true);
  };

  // Handle pose delete
  const handleDeletePose = (pose: ScenePose) => {
    setPoseToDelete(pose);
    setIsDeleteDialogOpen(true);
  };

  // Save edited pose
  const saveEditedPose = async () => {
    if (!editingPose) return;
    
    try {
      setLoading(true);
      await scenePosesService.updatePose(
        sceneId,
        editingPose.id,
        {
          content: editingPose.content,
          is_ooc: editingPose.is_ooc
        }
      );
      
      // Update local state (optimistic update)
      setPoses(currentPoses => 
        currentPoses.map(p => 
          p.id === editingPose.id ? editingPose : p
        )
      );
      
      setIsEditDialogOpen(false);
      if (onUpdateSuccess) onUpdateSuccess();
    } catch (err) {
      setError('Failed to update pose');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Add new pose
  const addNewPose = async () => {
    if (!newPose || !newPose.character_name || !newPose.content) return;
    
    try {
      setLoading(true);
      const poseId = await scenePosesService.createPose(
        sceneId,
        {
          character_name: newPose.character_name,
          content: newPose.content,
          is_ooc: newPose.is_ooc
        }
      );
      
      // Add optimistic temporary pose (will be replaced on next load)
      const tempPose: ScenePose = {
        id: poseId,
        character_name: newPose.character_name,
        content: newPose.content,
        pose_type: 'MIXED',
        is_ooc: newPose.is_ooc,
        timestamp: new Date().toISOString()
      };
      
      setPoses(currentPoses => [tempPose, ...currentPoses]);
      setIsAddDialogOpen(false);
      setNewPose(null);
      if (onUpdateSuccess) onUpdateSuccess();
    } catch (err) {
      setError('Failed to add pose');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Delete pose
  const confirmDeletePose = async () => {
    if (!poseToDelete) return;
    
    try {
      setLoading(true);
      await scenePosesService.deletePose(sceneId, poseToDelete.id);
      
      // Update local state (optimistic delete)
      setPoses(currentPoses => 
        currentPoses.filter(p => p.id !== poseToDelete.id)
      );
      
      setIsDeleteDialogOpen(false);
      setPoseToDelete(null);
      if (onUpdateSuccess) onUpdateSuccess();
    } catch (err) {
      setError('Failed to delete pose');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Get character initials for avatar
  const getCharacterInitials = (name: string): string => {
    return name
      .split(' ')
      .map(part => part.charAt(0).toUpperCase())
      .slice(0, 2)
      .join('');
  };

  // Get truncated content for unexpanded view
  const getTruncatedContent = (content: string, maxLength = 100): string => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-md font-medium">
          {title} ({poses.length})
        </CardTitle>
        <div className="flex items-center gap-2">
          <Button
            variant="outline" 
            size="sm"
            onClick={() => {
              setNewPose({ 
                character_name: '', 
                content: '',
                is_ooc: false 
              });
              setIsAddDialogOpen(true);
            }}
          >
            <Plus className="mr-1 h-4 w-4" /> Add Pose
          </Button>
          {poses.length > 10 && (
            <Button variant="outline" size="sm">View All</Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="bg-destructive/20 text-destructive p-3 mb-3 rounded-md">
            {error}
          </div>
        )}
        
        {loading && poses.length === 0 ? (
          <div className="flex justify-center items-center h-40">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : poses.length === 0 ? (
          <div className="text-center p-8 text-muted-foreground">
            No poses found. Add a pose to get started.
          </div>
        ) : (
          <ScrollArea className="h-[400px]">
            <div className="space-y-1">
              {poses.map((pose) => (
                <div 
                  key={pose.id} 
                  className={cn(
                    "border rounded-md p-3 transition-all",
                    pose.is_ooc ? "bg-muted/30" : "bg-background"
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div 
                      className="flex items-center gap-2 cursor-pointer" 
                      onClick={() => togglePoseExpansion(pose.id)}
                    >
                      <Avatar className="h-8 w-8">
                        <AvatarFallback>{getCharacterInitials(pose.character_name)}</AvatarFallback>
                      </Avatar>
                      <div>
                        <div className="font-medium">{pose.character_name}</div>
                        {pose.is_ooc && (
                          <Badge variant="outline" className="text-xs">OOC</Badge>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEditPose(pose)}
                        title="Edit pose"
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeletePose(pose)}
                        title="Delete pose"
                      >
                        <Trash className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => togglePoseExpansion(pose.id)}
                        title={expandedPoses[pose.id] ? "Collapse" : "Expand"}
                      >
                        {expandedPoses[pose.id] ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                  
                  <div className="mt-2 text-sm">
                    {expandedPoses[pose.id] ? (
                      <div className="whitespace-pre-wrap">{pose.content}</div>
                    ) : (
                      <div 
                        className="cursor-pointer"
                        onClick={() => togglePoseExpansion(pose.id)}
                      >
                        {getTruncatedContent(pose.content)}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>

      {/* Add Pose Dialog */}
      <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Add New Pose</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label htmlFor="character-name" className="text-sm font-medium">Character Name</label>
              <Input 
                id="character-name"
                value={newPose?.character_name || ''}
                onChange={(e) => setNewPose(prev => prev ? {...prev, character_name: e.target.value} : null)}
                placeholder="Enter character name"
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="pose-content" className="text-sm font-medium">Pose Content</label>
              <Textarea 
                id="pose-content"
                value={newPose?.content || ''}
                onChange={(e) => setNewPose(prev => prev ? {...prev, content: e.target.value} : null)}
                placeholder="Enter pose content"
                rows={5}
              />
            </div>
            <div className="flex items-center space-x-2">
              <input 
                type="checkbox" 
                id="is-ooc"
                checked={newPose?.is_ooc || false}
                onChange={(e) => setNewPose(prev => prev ? {...prev, is_ooc: e.target.checked} : null)}
              />
              <label htmlFor="is-ooc" className="text-sm font-medium">Out of Character (OOC)</label>
            </div>
          </div>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setIsAddDialogOpen(false)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button 
              onClick={addNewPose} 
              disabled={loading || !newPose?.character_name || !newPose?.content}
            >
              {loading ? (
                <span className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Adding...
                </span>
              ) : 'Add Pose'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Pose Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Pose</DialogTitle>
          </DialogHeader>
          {editingPose && (
            <div className="space-y-4 py-4">
              <div className="flex items-center gap-2">
                <Avatar className="h-8 w-8">
                  <AvatarFallback>{getCharacterInitials(editingPose.character_name)}</AvatarFallback>
                </Avatar>
                <div className="font-medium">{editingPose.character_name}</div>
              </div>
              <div className="space-y-2">
                <label htmlFor="edit-pose-content" className="text-sm font-medium">Pose Content</label>
                <Textarea 
                  id="edit-pose-content"
                  value={editingPose.content || ''}
                  onChange={(e) => setEditingPose({...editingPose, content: e.target.value})}
                  placeholder="Enter pose content"
                  rows={6}
                />
              </div>
              <div className="flex items-center space-x-2">
                <input 
                  type="checkbox" 
                  id="edit-is-ooc"
                  checked={editingPose.is_ooc || false}
                  onChange={(e) => setEditingPose({...editingPose, is_ooc: e.target.checked})}
                />
                <label htmlFor="edit-is-ooc" className="text-sm font-medium">Out of Character (OOC)</label>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setIsEditDialogOpen(false)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button 
              onClick={saveEditedPose} 
              disabled={loading || !editingPose?.content}
            >
              {loading ? (
                <span className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Saving...
                </span>
              ) : 'Save Changes'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Delete Pose</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <p className="text-sm">
              Are you sure you want to delete this pose by {poseToDelete?.character_name}? This action cannot be undone.
            </p>
            {poseToDelete && (
              <div className="mt-4 p-3 bg-muted rounded-md text-sm">
                <p className="font-medium">Preview:</p>
                <p className="text-muted-foreground italic">{getTruncatedContent(poseToDelete.content, 150)}</p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setIsDeleteDialogOpen(false)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button 
              variant="destructive"
              onClick={confirmDeletePose} 
              disabled={loading}
            >
              {loading ? (
                <span className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Deleting...
                </span>
              ) : 'Delete Pose'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
