import React, { useState } from 'react';
import { AlertCircle, Loader2, Search, Lightbulb, Clock } from 'lucide-react';

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

interface PoseContextAnalysisProps {
  onContextAnalyzed?: (context: PoseContext, suggestions: string[]) => void;
}

export const PoseContextAnalysis: React.FC<PoseContextAnalysisProps> = ({
  onContextAnalyzed
}) => {
  const [poseText, setPoseText] = useState('');
  const [characterName, setCharacterName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<{
    context: PoseContext;
    suggestions: string[];
  } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!poseText.trim()) {
      setError('Please enter a pose to analyze');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/context/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          pose_text: poseText,
          character_name: characterName || undefined
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to analyze pose context');
      }

      if (data.success && data.context) {
        const result = {
          context: data.context,
          suggestions: data.suggestions || []
        };
        setAnalysis(result);
        onContextAnalyzed?.(result.context, result.suggestions);
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
    setPoseText('');
    setCharacterName('');
    setAnalysis(null);
    setError(null);
  };

  const getUrgencyColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'critical': return 'text-red-600 bg-red-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Pose Context Analysis
        </h2>
        <p className="text-gray-600">
          Analyze poses from other players to identify key elements 
          that should influence your character's response.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="pose-text" className="block text-sm font-medium text-gray-700 mb-2">
            Pose to Analyze
          </label>
          <textarea
            id="pose-text"
            value={poseText}
            onChange={(e) => setPoseText(e.target.value)}
            placeholder="Paste the pose from another player that you want to analyze for context and response opportunities..."
            className="textarea-field min-h-[150px]"
            disabled={loading}
          />
        </div>

        <div>
          <label htmlFor="character-name" className="block text-sm font-medium text-gray-700 mb-2">
            Your Character Name (Optional)
          </label>
          <input
            id="character-name"
            type="text"
            value={characterName}
            onChange={(e) => setCharacterName(e.target.value)}
            placeholder="Enter your character's name for personalized analysis"
            className="input-field"
            disabled={loading}
          />
        </div>

        {error && (
          <div className="flex items-center space-x-2 text-red-600 bg-red-50 p-3 rounded-md">
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        <div className="flex space-x-3">
          <button
            type="submit"
            disabled={loading || !poseText.trim()}
            className="btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
            <span>{loading ? 'Analyzing...' : 'Analyze Context'}</span>
          </button>

          {(analysis || poseText) && (
            <button
              type="button"
              onClick={handleClear}
              className="btn-secondary"
              disabled={loading}
            >
              Clear
            </button>
          )}
        </div>
      </form>

      {analysis && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-6">
          <div className="flex items-center space-x-2 text-blue-600 mb-4">
            <Search className="h-5 w-5" />
            <h3 className="text-lg font-semibold">Context Analysis Results</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Scene Elements</h4>
                <div className="space-y-3">
                  {analysis.context.actions.length > 0 && (
                    <div>
                      <span className="text-sm font-medium text-gray-700">Actions:</span>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {analysis.context.actions.map((action, index) => (
                          <span
                            key={index}
                            className="px-2 py-1 bg-blue-100 text-blue-800 rounded-md text-xs"
                          >
                            {action}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {analysis.context.emotions.length > 0 && (
                    <div>
                      <span className="text-sm font-medium text-gray-700">Emotions:</span>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {analysis.context.emotions.map((emotion, index) => (
                          <span
                            key={index}
                            className="px-2 py-1 bg-pink-100 text-pink-800 rounded-md text-xs"
                          >
                            {emotion}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {analysis.context.environmental_details.length > 0 && (
                    <div>
                      <span className="text-sm font-medium text-gray-700">Environment:</span>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {analysis.context.environmental_details.map((detail, index) => (
                          <span
                            key={index}
                            className="px-2 py-1 bg-green-100 text-green-800 rounded-md text-xs"
                          >
                            {detail}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-2">Scene Context</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center space-x-2">
                    <Clock className="h-4 w-4 text-gray-500" />
                    <span className="font-medium">Timing:</span>
                    <span className="text-gray-600">{analysis.context.scene_timing}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="font-medium">Urgency:</span>
                    <span className={`px-2 py-1 rounded-md text-xs ${getUrgencyColor(analysis.context.urgency_level)}`}>
                      {analysis.context.urgency_level}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="font-medium">Tone:</span>
                    <span className="text-gray-600">{analysis.context.narrative_tone}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              {analysis.context.character_interactions.length > 0 && (
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Character Interactions</h4>
                  <div className="flex flex-wrap gap-1">
                    {analysis.context.character_interactions.map((interaction, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-purple-100 text-purple-800 rounded-md text-xs"
                      >
                        {interaction}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {analysis.context.response_hooks.length > 0 && (
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Response Opportunities</h4>
                  <div className="space-y-2">
                    {analysis.context.response_hooks.map((hook, index) => (
                      <div
                        key={index}
                        className="p-2 bg-yellow-50 border border-yellow-200 rounded-md text-sm text-yellow-800"
                      >
                        {hook}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {analysis.suggestions.length > 0 && (
                <div>
                  <div className="flex items-center space-x-2 mb-2">
                    <Lightbulb className="h-4 w-4 text-amber-500" />
                    <h4 className="font-medium text-gray-900">Response Suggestions</h4>
                  </div>
                  <div className="space-y-2">
                    {analysis.suggestions.map((suggestion, index) => (
                      <div
                        key={index}
                        className="p-2 bg-blue-50 border border-blue-200 rounded-md text-sm text-blue-800"
                      >
                        {suggestion}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="pt-4 border-t border-gray-200">
            <button
              onClick={() => {
                const analysisJson = JSON.stringify(analysis, null, 2);
                navigator.clipboard.writeText(analysisJson);
              }}
              className="btn-secondary text-sm"
            >
              Copy Analysis Data
            </button>
          </div>
        </div>
      )}
    </div>
  );
}; 