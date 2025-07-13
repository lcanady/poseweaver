import React, { useState } from 'react';
import { AlertCircle, Loader2, Wand2, Copy, RotateCcw } from 'lucide-react';

interface CharacterProfile {
  name: string;
  background: string;
  personality: string[];
  skills: string[];
  goals: string[];
  relationships: Record<string, string>;
  voice_notes: string;
}

interface PoseContext {
  actions: string[];
  emotions: string[];
  environmental_details: string[];
  character_interactions: string[];
  response_hooks: string[];
  scene_timing: string;
  urgency_level: string;
  narrative_tone: string;
}

interface PoseEnhancement {
  original_pose: string;
  enhanced_pose: string;
  enhancement_notes: string[];
  sensory_details: string[];
  character_voice_elements: string[];
  narrative_techniques: string[];
}

interface PoseEditorProps {
  character?: CharacterProfile;
  context?: PoseContext;
  onPoseEnhanced?: (enhancement: PoseEnhancement) => void;
}

export const PoseEditor: React.FC<PoseEditorProps> = ({
  character,
  context,
  onPoseEnhanced
}) => {
  const [originalPose, setOriginalPose] = useState('');
  const [enhancementStyle, setEnhancementStyle] = useState<'minimal' | 'balanced' | 'elaborate'>('balanced');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [enhancement, setEnhancement] = useState<PoseEnhancement | null>(null);
  const [variations, setVariations] = useState<PoseEnhancement[]>([]);
  const [showVariations, setShowVariations] = useState(false);

  const handleEnhance = async () => {
    if (!originalPose.trim()) {
      setError('Please enter a pose to enhance');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/pose/enhance', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          original_pose: originalPose,
          character: character || undefined,
          context: context || undefined,
          enhancement_style: enhancementStyle
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to enhance pose');
      }

      if (data.success && data.enhanced_pose) {
        // Create a simplified enhancement object for display
        const simpleEnhancement: PoseEnhancement = {
          original_pose: originalPose,
          enhanced_pose: data.enhanced_pose,
          enhancement_notes: [],
          sensory_details: [],
          character_voice_elements: [],
          narrative_techniques: []
        };
        setEnhancement(simpleEnhancement);
        onPoseEnhanced?.(simpleEnhancement);
      } else {
        throw new Error('Invalid response format');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateVariations = async () => {
    if (!originalPose.trim()) {
      setError('Please enter a pose to generate variations');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/pose/variations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          original_pose: originalPose,
          character: character || undefined,
          count: 3
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to generate variations');
      }

      if (data.success && data.variations) {
        setVariations(data.variations);
        setShowVariations(true);
      } else {
        throw new Error('Invalid response format');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setOriginalPose('');
    setEnhancement(null);
    setVariations([]);
    setShowVariations(false);
    setError(null);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const getStyleDescription = (style: string) => {
    switch (style) {
      case 'minimal': return 'Subtle enhancements, maintains original structure';
      case 'balanced': return 'Rich details with character voice elements';
      case 'elaborate': return 'Immersive narrative with extensive detail';
      default: return '';
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Pose Editor
        </h2>
        <p className="text-gray-600">
          Transform basic actions into rich, detailed narratives while 
          maintaining character voice consistency.
        </p>
      </div>

      {(character || context) && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-medium text-blue-900 mb-2">Active Context</h3>
          <div className="flex flex-wrap gap-2 text-sm">
            {character && (
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-md">
                Character: {character.name}
              </span>
            )}
            {context && (
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-md">
                Scene Context Available
              </span>
            )}
          </div>
        </div>
      )}

      <div className="space-y-4">
        <div>
          <label htmlFor="original-pose" className="block text-sm font-medium text-gray-700 mb-2">
            Original Pose
          </label>
          <textarea
            id="original-pose"
            value={originalPose}
            onChange={(e) => setOriginalPose(e.target.value)}
            placeholder="Enter your basic pose or action that you want to enhance..."
            className="textarea-field min-h-[120px]"
            disabled={loading}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Enhancement Style
          </label>
          <div className="space-y-2">
            {(['minimal', 'balanced', 'elaborate'] as const).map((style) => (
              <label key={style} className="flex items-center space-x-2">
                <input
                  type="radio"
                  name="enhancement-style"
                  value={style}
                  checked={enhancementStyle === style}
                  onChange={(e) => setEnhancementStyle(e.target.value as any)}
                  disabled={loading}
                  className="text-blue-600"
                />
                <span className="text-sm">
                  <span className="font-medium capitalize">{style}</span>
                  <span className="text-gray-500 ml-1">- {getStyleDescription(style)}</span>
                </span>
              </label>
            ))}
          </div>
        </div>

        {error && (
          <div className="flex items-center space-x-2 text-red-600 bg-red-50 p-3 rounded-md">
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        <div className="flex space-x-3">
          <button
            onClick={handleEnhance}
            disabled={loading || !originalPose.trim()}
            className="btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Wand2 className="h-4 w-4" />
            )}
            <span>{loading ? 'Enhancing...' : 'Enhance Pose'}</span>
          </button>

          <button
            onClick={handleGenerateVariations}
            disabled={loading || !originalPose.trim()}
            className="btn-secondary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RotateCcw className="h-4 w-4" />
            )}
            <span>{loading ? 'Generating...' : 'Generate Variations'}</span>
          </button>

          {(enhancement || originalPose) && (
            <button
              onClick={handleClear}
              className="btn-secondary"
              disabled={loading}
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {enhancement && !showVariations && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-green-600">
              <Wand2 className="h-5 w-5" />
              <h3 className="text-lg font-semibold">Enhanced Pose</h3>
            </div>
            <button
              onClick={() => copyToClipboard(enhancement.enhanced_pose)}
              className="btn-secondary text-sm flex items-center space-x-1"
            >
              <Copy className="h-4 w-4" />
              <span>Copy</span>
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Original</h4>
              <div className="p-3 bg-gray-50 rounded-md text-sm text-gray-700 whitespace-pre-wrap">
                {enhancement.original_pose}
              </div>
            </div>

            <div>
              <h4 className="font-medium text-gray-900 mb-2">Enhanced</h4>
              <div className="p-3 bg-green-50 border border-green-200 rounded-md text-sm text-gray-800 whitespace-pre-wrap">
                {enhancement.enhanced_pose}
              </div>
            </div>
          </div>
        </div>
      )}

      {showVariations && variations.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Pose Variations</h3>
            <button
              onClick={() => setShowVariations(false)}
              className="btn-secondary text-sm"
            >
              Back to Enhancement
            </button>
          </div>

          {variations.map((variation, index) => (
            <div key={index} className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-gray-900">
                  Variation {index + 1} ({['Minimal', 'Balanced', 'Elaborate'][index] || 'Custom'})
                </h4>
                <button
                  onClick={() => copyToClipboard(variation.enhanced_pose)}
                  className="btn-secondary text-sm flex items-center space-x-1"
                >
                  <Copy className="h-4 w-4" />
                  <span>Copy</span>
                </button>
              </div>
              <div className="p-3 bg-gray-50 rounded-md text-sm text-gray-800 whitespace-pre-wrap">
                {variation.enhanced_pose}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}; 