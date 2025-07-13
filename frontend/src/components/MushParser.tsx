import React, { useState } from 'react';
import { Upload, FileText, Zap, Eye, HelpCircle, CheckCircle, AlertCircle } from 'lucide-react';

interface ParsedPose {
  character_name: string;
  content: string;
  pose_type: string;
  is_ooc: boolean;
  timestamp?: string;
}

interface ParsedScene {
  room_description?: string;
  characters_present?: string[];
  your_character?: string;
  total_poses: number;
}

interface EnhancedPose {
  original: string;
  enhanced?: string;
  pose_type: string;
  timestamp?: string;
  is_ooc: boolean;
  error?: string;
}

interface MushParseResult {
  parsed_scene: ParsedScene;
  your_poses: ParsedPose[];
  enhanced_poses: EnhancedPose[];
  scene_context: string;
  error?: string;
}

const MushParser: React.FC = () => {
  const [mushOutput, setMushOutput] = useState('');
  const [yourCharacterName, setYourCharacterName] = useState('');
  const [enhancementStyle, setEnhancementStyle] = useState('balanced');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<MushParseResult | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [showHelp, setShowHelp] = useState(false);

  const handlePreview = async () => {
    if (!mushOutput.trim() || !yourCharacterName.trim()) {
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('/api/mush/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          mush_output: mushOutput,
          your_character_name: yourCharacterName,
        }),
      });

      const data = await response.json();
      if (response.ok) {
        setResult({
          parsed_scene: data.parsed_scene,
          your_poses: data.your_poses,
          enhanced_poses: [],
          scene_context: data.scene_context,
        });
        setShowPreview(true);
      } else {
        setResult({
          parsed_scene: { total_poses: 0 },
          your_poses: [],
          enhanced_poses: [],
          scene_context: '',
          error: data.error || 'Failed to preview MUSH output',
        });
      }
    } catch (error) {
      setResult({
        parsed_scene: { total_poses: 0 },
        your_poses: [],
        enhanced_poses: [],
        scene_context: '',
        error: 'Network error occurred',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleEnhance = async () => {
    if (!mushOutput.trim() || !yourCharacterName.trim()) {
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('/api/mush/enhance', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          mush_output: mushOutput,
          your_character_name: yourCharacterName,
          enhancement_style: enhancementStyle,
        }),
      });

      const data = await response.json();
      if (response.ok) {
        setResult(data);
        setShowPreview(false);
      } else {
        setResult({
          parsed_scene: { total_poses: 0 },
          your_poses: [],
          enhanced_poses: [],
          scene_context: '',
          error: data.error || 'Failed to enhance poses',
        });
      }
    } catch (error) {
      setResult({
        parsed_scene: { total_poses: 0 },
        your_poses: [],
        enhanced_poses: [],
        scene_context: '',
        error: 'Network error occurred',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    setMushOutput('');
    setYourCharacterName('');
    setResult(null);
    setShowPreview(false);
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <Upload className="w-6 h-6 text-blue-600" />
            <h1 className="text-2xl font-bold text-gray-900">MUSH Output Parser</h1>
          </div>
          <button
            onClick={() => setShowHelp(!showHelp)}
            className="flex items-center space-x-2 text-gray-600 hover:text-blue-600 transition-colors"
          >
            <HelpCircle className="w-5 h-5" />
            <span>Help</span>
          </button>
        </div>

        {showHelp && (
          <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h3 className="font-semibold text-blue-900 mb-2">How to use MUSH Parser:</h3>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Copy and paste your MUSH game output into the text area</li>
              <li>• Enter your exact character name as it appears in the output</li>
              <li>• Click "Preview" to see what poses will be extracted</li>
              <li>• Click "Enhance" to get AI-enhanced versions with scene context</li>
              <li>• The parser supports room descriptions, character lists, and timestamps</li>
            </ul>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                MUSH Output
              </label>
              <textarea
                value={mushOutput}
                onChange={(e) => setMushOutput(e.target.value)}
                placeholder="Paste your MUSH game output here..."
                className="w-full h-64 p-3 border border-gray-300 rounded-md resize-none font-mono text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Character Name
              </label>
              <input
                type="text"
                value={yourCharacterName}
                onChange={(e) => setYourCharacterName(e.target.value)}
                placeholder="Enter your character name exactly as it appears"
                className="w-full p-3 border border-gray-300 rounded-md"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Enhancement Style
              </label>
              <select
                value={enhancementStyle}
                onChange={(e) => setEnhancementStyle(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-md"
              >
                <option value="balanced">Balanced</option>
                <option value="detailed">Detailed</option>
                <option value="subtle">Subtle</option>
              </select>
            </div>

            <div className="flex space-x-3">
              <button
                onClick={handlePreview}
                disabled={isLoading || !mushOutput.trim() || !yourCharacterName.trim()}
                className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Eye className="w-4 h-4" />
                <span>Preview</span>
              </button>

              <button
                onClick={handleEnhance}
                disabled={isLoading || !mushOutput.trim() || !yourCharacterName.trim()}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Zap className="w-4 h-4" />
                <span>{isLoading ? 'Processing...' : 'Enhance'}</span>
              </button>

              <button
                onClick={handleClear}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors"
              >
                Clear
              </button>
            </div>
          </div>

          <div className="space-y-4">
            {result && (
              <div className="space-y-4">
                {result.error && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                    <div className="flex items-center space-x-2">
                      <AlertCircle className="w-5 h-5 text-red-600" />
                      <span className="text-red-800 font-medium">Error</span>
                    </div>
                    <p className="text-red-700 mt-1">{result.error}</p>
                  </div>
                )}

                {result.parsed_scene && (
                  <div className="p-4 bg-green-50 border border-green-200 rounded-md">
                    <div className="flex items-center space-x-2 mb-2">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      <span className="text-green-800 font-medium">Parsing Results</span>
                    </div>
                    <div className="text-sm text-green-700 space-y-1">
                      <p>Total poses found: {result.parsed_scene.total_poses}</p>
                      <p>Your poses found: {result.your_poses.length}</p>
                      {result.parsed_scene.characters_present && (
                        <p>Characters: {result.parsed_scene.characters_present.join(', ')}</p>
                      )}
                    </div>
                  </div>
                )}

                {result.your_poses.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="font-medium text-gray-900">Your Poses:</h3>
                    {result.your_poses.map((pose, index) => (
                      <div key={index} className="p-3 bg-gray-50 border border-gray-200 rounded-md">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-medium text-gray-600 uppercase">
                            {pose.pose_type} {pose.is_ooc && '(OOC)'}
                          </span>
                          {pose.timestamp && (
                            <span className="text-xs text-gray-500">{pose.timestamp}</span>
                          )}
                        </div>
                        <p className="text-sm text-gray-800 whitespace-pre-wrap">
                          {pose.character_name} {pose.content}
                        </p>
                      </div>
                    ))}
                  </div>
                )}

                {result.enhanced_poses.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="font-medium text-gray-900">Enhanced Poses:</h3>
                    {result.enhanced_poses.map((pose, index) => (
                      <div key={index} className="space-y-3">
                        <div className="p-3 bg-gray-50 border border-gray-200 rounded-md">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-medium text-gray-600">ORIGINAL</span>
                            <span className="text-xs text-gray-500">
                              {pose.pose_type} {pose.is_ooc && '(OOC)'}
                            </span>
                          </div>
                          <p className="text-sm text-gray-800 whitespace-pre-wrap">{pose.original}</p>
                        </div>

                        {pose.enhanced ? (
                          <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-xs font-medium text-blue-600">ENHANCED</span>
                              {pose.timestamp && (
                                <span className="text-xs text-blue-500">{pose.timestamp}</span>
                              )}
                            </div>
                            <p className="text-sm text-blue-900 whitespace-pre-wrap">{pose.enhanced}</p>
                          </div>
                        ) : pose.error ? (
                          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                            <span className="text-xs font-medium text-red-600">ERROR</span>
                            <p className="text-sm text-red-700">{pose.error}</p>
                          </div>
                        ) : null}
                      </div>
                    ))}
                  </div>
                )}

                {result.scene_context && (
                  <div className="mt-4">
                    <h3 className="font-medium text-gray-900 mb-2">Scene Context Used:</h3>
                    <div className="p-3 bg-gray-50 border border-gray-200 rounded-md">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">{result.scene_context}</p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MushParser; 