import React, { useState, useEffect } from 'react';
import { Plus, MessageSquare, Users, Clock, Trash2, Send, Wand2, Copy, ChevronDown, ChevronRight } from 'lucide-react';

interface ScenePose {
  id: string;
  character_name: string;
  pose_text: string;
  pose_type: 'action' | 'dialogue' | 'narrative' | 'internal' | 'mixed';
  timestamp: string;
  enhanced_text?: string;
}

interface SceneParticipant {
  name: string;
  pose_count: number;
  last_seen?: string;
}

interface SceneFlow {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  poses: ScenePose[];
  participants: Record<string, SceneParticipant>;
  is_active: boolean;
}

interface SceneFlowProps {
  onPoseEnhanced?: (enhanced: string) => void;
}

export const SceneFlow: React.FC<SceneFlowProps> = ({ onPoseEnhanced }) => {
  const [scenes, setScenes] = useState<SceneFlow[]>([]);
  const [activeScene, setActiveScene] = useState<SceneFlow | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // New scene form
  const [showNewSceneForm, setShowNewSceneForm] = useState(false);
  const [newSceneName, setNewSceneName] = useState('');
  const [newSceneCharacter, setNewSceneCharacter] = useState('');
  
  // New pose form
  const [newPoseText, setNewPoseText] = useState('');
  const [newPoseCharacter, setNewPoseCharacter] = useState('');
  const [newPoseType, setNewPoseType] = useState<'action' | 'dialogue' | 'narrative' | 'internal' | 'mixed'>('mixed');
  
  // Bulk import form
  const [bulkPosesText, setBulkPosesText] = useState('');
  const [bulkImportFormat, setBulkImportFormat] = useState<'simple' | 'character_prefix' | 'mush_output'>('mush_output');
  
  // Enhanced poses storage
  const [enhancedPoses, setEnhancedPoses] = useState<Record<string, string>>({});
  const [expandedPoses, setExpandedPoses] = useState<Record<string, boolean>>({});
  
  // New pose enhancement state
  const [newPoseOriginal, setNewPoseOriginal] = useState('');
  const [newPoseEnhanced, setNewPoseEnhanced] = useState('');

  // Load scenes on component mount
  useEffect(() => {
    loadScenes();
  }, []);

  const loadScenes = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/scene-flow/scenes');
      const data = await response.json();
      
      if (data.success) {
        setScenes(data.scenes);
      } else {
        setError('Failed to load scenes');
      }
    } catch (err) {
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  const createScene = async () => {
    if (!newSceneName.trim() || !newSceneCharacter.trim()) {
      setError('Scene name and character name are required');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch('/api/scene-flow/scenes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: newSceneName,
          character_name: newSceneCharacter,
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        setActiveScene(data.scene);
        setNewSceneName('');
        setNewSceneCharacter('');
        setShowNewSceneForm(false);
        await loadScenes();
      } else {
        setError(data.error || 'Failed to create scene');
      }
    } catch (err) {
      setError('Failed to create scene');
    } finally {
      setLoading(false);
    }
  };

  const loadScene = async (sceneId: string) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/scene-flow/scenes/${sceneId}`);
      const data = await response.json();
      
      if (data.success) {
        setActiveScene(data.scene);
      } else {
        setError('Failed to load scene');
      }
    } catch (err) {
      setError('Failed to load scene');
    } finally {
      setLoading(false);
    }
  };

  const addPose = async () => {
    if (!activeScene || !newPoseText.trim() || !newPoseCharacter.trim()) {
      setError('Scene, pose text, and character name are required');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`/api/scene-flow/scenes/${activeScene.id}/poses`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          character_name: newPoseCharacter,
          pose_text: newPoseText,
          pose_type: newPoseType,
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        // Reload the scene to get updated poses
        await loadScene(activeScene.id);
        setNewPoseText('');
        setNewPoseCharacter('');
        clearNewPoseEnhancement();
      } else {
        setError(data.error || 'Failed to add pose');
      }
    } catch (err) {
      setError('Failed to add pose');
    } finally {
      setLoading(false);
    }
  };

  const enhancePose = async (poseId: string, poseText: string, characterName: string) => {
    if (!activeScene) return;

    try {
      setLoading(true);
      const response = await fetch(`/api/scene-flow/scenes/${activeScene.id}/enhance`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          pose_text: poseText,
          character_name: characterName,
          enhancement_style: 'balanced',
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        // Store the enhanced pose
        setEnhancedPoses(prev => ({
          ...prev,
          [poseId]: data.enhanced_pose
        }));
        
        if (onPoseEnhanced) {
          onPoseEnhanced(data.enhanced_pose);
        }
        return data.enhanced_pose;
      } else {
        setError(data.error || 'Failed to enhance pose');
      }
    } catch (err) {
      setError('Failed to enhance pose');
    } finally {
      setLoading(false);
    }
  };

  const enhanceNewPose = async () => {
    if (!activeScene || !newPoseText.trim() || !newPoseCharacter.trim()) return;

    try {
      setLoading(true);
      const response = await fetch(`/api/scene-flow/scenes/${activeScene.id}/enhance`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          pose_text: newPoseText,
          character_name: newPoseCharacter,
          enhancement_style: 'balanced',
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        // Store both original and enhanced versions
        setNewPoseOriginal(newPoseText);
        setNewPoseEnhanced(data.enhanced_pose);
        
        if (onPoseEnhanced) {
          onPoseEnhanced(data.enhanced_pose);
        }
        return data.enhanced_pose;
      } else {
        setError(data.error || 'Failed to enhance pose');
      }
    } catch (err) {
      setError('Failed to enhance pose');
    } finally {
      setLoading(false);
    }
  };

  const bulkImportPoses = async () => {
    if (!activeScene || !bulkPosesText.trim()) return;

    try {
      setLoading(true);
      const response = await fetch(`/api/scene-flow/scenes/${activeScene.id}/poses/bulk`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          poses_text: bulkPosesText,
          format: bulkImportFormat,
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        // Reload the scene to show imported poses
        await loadScene(activeScene.id);
        setBulkPosesText('');
        setError(null);
      } else {
        setError(data.error || 'Failed to import poses');
      }
    } catch (err) {
      setError('Failed to import poses');
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getPoseTypeIcon = (type: string) => {
    switch (type) {
      case 'dialogue': return <MessageSquare className="h-4 w-4" />;
      case 'action': return <Users className="h-4 w-4" />;
      default: return <MessageSquare className="h-4 w-4" />;
    }
  };

  const getPoseTypeColor = (type: string) => {
    switch (type) {
      case 'dialogue': return 'text-blue-600 bg-blue-50';
      case 'action': return 'text-green-600 bg-green-50';
      case 'narrative': return 'text-purple-600 bg-purple-50';
      case 'internal': return 'text-orange-600 bg-orange-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (err) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
    }
  };

  const togglePoseExpansion = (poseId: string) => {
    setExpandedPoses(prev => ({
      ...prev,
      [poseId]: !prev[poseId]
    }));
  };

  const clearNewPoseEnhancement = () => {
    setNewPoseOriginal('');
    setNewPoseEnhanced('');
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-700">{error}</p>
          <button 
            onClick={() => setError(null)}
            className="text-red-600 hover:text-red-800 text-sm mt-2"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Scene Flow</h2>
          <p className="text-gray-600">Manage conversation-like pose flows with context</p>
        </div>
        <button
          onClick={() => setShowNewSceneForm(true)}
          className="btn-primary flex items-center space-x-2"
        >
          <Plus className="h-4 w-4" />
          <span>New Scene</span>
        </button>
      </div>

      {/* Scene List */}
      {!activeScene && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {scenes.map((scene) => (
            <div
              key={scene.id}
              onClick={() => loadScene(scene.id)}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md cursor-pointer transition-shadow"
            >
              <h3 className="font-medium text-gray-900 mb-2">{scene.name}</h3>
              <div className="space-y-1 text-sm text-gray-600">
                <div className="flex items-center space-x-1">
                  <MessageSquare className="h-3 w-3" />
                  <span>{scene.poses?.length || 0} poses</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Users className="h-3 w-3" />
                  <span>{Object.keys(scene.participants || {}).length} participants</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Clock className="h-3 w-3" />
                  <span>Updated {new Date(scene.updated_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* New Scene Form */}
      {showNewSceneForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Scene</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Scene Name
              </label>
              <input
                type="text"
                value={newSceneName}
                onChange={(e) => setNewSceneName(e.target.value)}
                className="input-field"
                placeholder="Enter scene name..."
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Character Name
              </label>
              <input
                type="text"
                value={newSceneCharacter}
                onChange={(e) => setNewSceneCharacter(e.target.value)}
                className="input-field"
                placeholder="Enter your character name..."
              />
            </div>
            <div className="flex space-x-3">
              <button
                onClick={createScene}
                disabled={loading}
                className="btn-primary"
              >
                Create Scene
              </button>
              <button
                onClick={() => setShowNewSceneForm(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Active Scene */}
      {activeScene && (
        <div className="space-y-6">
          {/* Scene Header */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-medium text-gray-900">{activeScene.name}</h3>
              <button
                onClick={() => setActiveScene(null)}
                className="btn-secondary text-sm"
              >
                Back to Scenes
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
              <div className="flex items-center space-x-1">
                <MessageSquare className="h-4 w-4" />
                <span>{activeScene.poses.length} poses</span>
              </div>
              <div className="flex items-center space-x-1">
                <Users className="h-4 w-4" />
                <span>{Object.keys(activeScene.participants).length} participants</span>
              </div>
              <div className="flex items-center space-x-1">
                <Clock className="h-4 w-4" />
                <span>Created {new Date(activeScene.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>

          {/* Pose History - Compact Layout */}
          <div className="bg-white border border-gray-200 rounded-lg">
            <div className="p-4 border-b border-gray-200">
              <h4 className="font-medium text-gray-900">Pose History ({activeScene.poses.length})</h4>
            </div>
            <div className="max-h-[60vh] overflow-y-auto p-4">
              {activeScene.poses.map((pose) => {
                const isExpanded = expandedPoses[pose.id];
                const hasEnhanced = enhancedPoses[pose.id];
                
                return (
                  <div key={pose.id} className="mb-4 border border-gray-200 rounded-lg overflow-hidden">
                    {/* Pose Header - Always Visible */}
                    <div className="bg-gray-50 p-3 border-b border-gray-200">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <button
                            onClick={() => togglePoseExpansion(pose.id)}
                            className="flex items-center space-x-2 hover:bg-gray-100 rounded px-2 py-1 transition-colors"
                          >
                            {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                            <span className="font-medium text-gray-900">{pose.character_name}</span>
                          </button>
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${getPoseTypeColor(pose.pose_type)}`}>
                            {getPoseTypeIcon(pose.pose_type)}
                            <span className="ml-1">{pose.pose_type}</span>
                          </span>
                          <span className="text-xs text-gray-500">{formatTimestamp(pose.timestamp)}</span>
                          {hasEnhanced && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                              <Wand2 className="h-3 w-3 mr-1" />
                              Enhanced
                            </span>
                          )}
                        </div>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => enhancePose(pose.id, pose.pose_text, pose.character_name)}
                            disabled={loading}
                            className="btn-secondary text-sm flex items-center space-x-1"
                          >
                            <Wand2 className="h-3 w-3" />
                            <span>{hasEnhanced ? 'Re-enhance' : 'Enhance'}</span>
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Pose Content - Collapsible */}
                    {isExpanded && (
                      <div className="p-4 space-y-4">
                        {/* Original Pose */}
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <h5 className="text-sm font-medium text-gray-700">Original</h5>
                            <button
                              onClick={() => copyToClipboard(pose.pose_text)}
                              className="text-gray-500 hover:text-gray-700 p-1 rounded hover:bg-gray-100"
                              title="Copy original pose"
                            >
                              <Copy className="h-4 w-4" />
                            </button>
                          </div>
                          <div className="bg-gray-50 border border-gray-200 rounded-md p-3 text-sm text-gray-800 whitespace-pre-wrap">
                            {pose.pose_text}
                          </div>
                        </div>

                        {/* Enhanced Pose */}
                        {hasEnhanced && (
                          <div>
                            <div className="flex items-center justify-between mb-2">
                              <h5 className="text-sm font-medium text-green-700">Enhanced</h5>
                              <button
                                onClick={() => copyToClipboard(enhancedPoses[pose.id])}
                                className="text-green-600 hover:text-green-800 p-1 rounded hover:bg-green-50"
                                title="Copy enhanced pose"
                              >
                                <Copy className="h-4 w-4" />
                              </button>
                            </div>
                            <div className="bg-green-50 border border-green-200 rounded-md p-3 text-sm text-gray-800 whitespace-pre-wrap">
                              {enhancedPoses[pose.id]}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
              {activeScene.poses.length === 0 && (
                <p className="text-gray-500 text-center py-8">No poses yet. Add the first pose below!</p>
              )}
            </div>
          </div>

          {/* Quick Context Builder - Compact */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-medium text-blue-900">Quick Context Builder</h4>
              <div className="flex items-center space-x-2">
                <select
                  value={bulkImportFormat}
                  onChange={(e) => setBulkImportFormat(e.target.value as 'simple' | 'character_prefix' | 'mush_output')}
                  className="text-sm border border-blue-300 rounded px-2 py-1 bg-white"
                >
                  <option value="mush_output">MUSH Output</option>
                  <option value="character_prefix">Name: pose</option>
                  <option value="simple">Simple</option>
                </select>
                <button
                  onClick={bulkImportPoses}
                  disabled={loading || !bulkPosesText.trim()}
                  className="btn-primary text-sm flex items-center space-x-1"
                >
                  <Plus className="h-3 w-3" />
                  <span>Import</span>
                </button>
                <button
                  onClick={() => setBulkPosesText('')}
                  disabled={loading || !bulkPosesText.trim()}
                  className="btn-secondary text-sm flex items-center space-x-1"
                >
                  <Trash2 className="h-3 w-3" />
                  <span>Clear</span>
                </button>
              </div>
            </div>
            <textarea
              value={bulkPosesText}
              onChange={(e) => setBulkPosesText(e.target.value)}
              placeholder="Paste MUSH output to import recent poses..."
              className="w-full border border-blue-300 rounded px-3 py-2 text-sm resize-none bg-white"
              rows={3}
              disabled={loading}
            />
          </div>

          {/* Add Your Pose */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h4 className="font-medium text-gray-900 mb-4">Add Your Pose</h4>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Your Character Name
                  </label>
                  <input
                    type="text"
                    value={newPoseCharacter}
                    onChange={(e) => setNewPoseCharacter(e.target.value)}
                    className="input-field"
                    placeholder="Your character name..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Pose Type
                  </label>
                  <select
                    value={newPoseType}
                    onChange={(e) => setNewPoseType(e.target.value as any)}
                    className="input-field"
                  >
                    <option value="mixed">Mixed</option>
                    <option value="action">Action</option>
                    <option value="dialogue">Dialogue</option>
                    <option value="narrative">Narrative</option>
                    <option value="internal">Internal Thoughts</option>
                  </select>
                </div>
              </div>
              {!newPoseEnhanced ? (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Your Pose
                  </label>
                  <textarea
                    value={newPoseText}
                    onChange={(e) => setNewPoseText(e.target.value)}
                    className="textarea-field min-h-[100px]"
                    placeholder="Enter your pose to enhance with scene context..."
                  />
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Original Pose */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="block text-sm font-medium text-gray-700">
                        Original Pose
                      </label>
                      <button
                        onClick={() => copyToClipboard(newPoseOriginal)}
                        className="text-gray-500 hover:text-gray-700 p-1 rounded hover:bg-gray-100"
                        title="Copy original pose"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                    </div>
                    <div className="bg-gray-50 border border-gray-200 rounded-md p-3 text-sm text-gray-800 whitespace-pre-wrap min-h-[100px]">
                      {newPoseOriginal}
                    </div>
                  </div>

                  {/* Enhanced Pose */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="block text-sm font-medium text-green-700">
                        Enhanced Pose
                      </label>
                      <button
                        onClick={() => copyToClipboard(newPoseEnhanced)}
                        className="text-green-600 hover:text-green-800 p-1 rounded hover:bg-green-50"
                        title="Copy enhanced pose"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                    </div>
                    <div className="bg-green-50 border border-green-200 rounded-md p-3 text-sm text-gray-800 whitespace-pre-wrap min-h-[100px]">
                      {newPoseEnhanced}
                    </div>
                  </div>
                </div>
              )}
              
              <div className="flex space-x-4">
                {!newPoseEnhanced ? (
                  <>
                    <button
                      onClick={addPose}
                      disabled={loading || !newPoseText.trim() || !newPoseCharacter.trim()}
                      className="btn-primary flex items-center space-x-2"
                    >
                      <Send className="h-4 w-4" />
                      <span>Add Pose</span>
                    </button>
                    <button
                      onClick={enhanceNewPose}
                      disabled={loading || !newPoseText.trim() || !newPoseCharacter.trim()}
                      className="btn-secondary flex items-center space-x-2"
                    >
                      <Wand2 className="h-4 w-4" />
                      <span>Enhance with Scene Context</span>
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => {
                        setNewPoseText(newPoseEnhanced);
                        addPose();
                      }}
                      disabled={loading}
                      className="btn-primary flex items-center space-x-2"
                    >
                      <Send className="h-4 w-4" />
                      <span>Add Enhanced Pose</span>
                    </button>
                    <button
                      onClick={() => {
                        setNewPoseText(newPoseOriginal);
                        addPose();
                      }}
                      disabled={loading}
                      className="btn-secondary flex items-center space-x-2"
                    >
                      <Send className="h-4 w-4" />
                      <span>Add Original Pose</span>
                    </button>
                    <button
                      onClick={clearNewPoseEnhancement}
                      disabled={loading}
                      className="btn-secondary flex items-center space-x-2"
                    >
                      <Trash2 className="h-4 w-4" />
                      <span>Start Over</span>
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {loading && (
        <div className="text-center py-4">
          <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <p className="text-gray-600 mt-2">Loading...</p>
        </div>
      )}
    </div>
  );
}; 