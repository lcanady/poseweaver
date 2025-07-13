import React, { useState } from 'react';
import { AlertCircle, Loader2, User, FileText } from 'lucide-react';

interface CharacterProfile {
  name: string;
  background: string;
  personality: string[];
  skills: string[];
  goals: string[];
  relationships: Record<string, string>;
  voice_notes: string;
}

interface CharacterBrainDumpProps {
  onCharacterCreated?: (character: CharacterProfile) => void;
}

export const CharacterBrainDump: React.FC<CharacterBrainDumpProps> = ({
  onCharacterCreated
}) => {
  const [brainDump, setBrainDump] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [character, setCharacter] = useState<CharacterProfile | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!brainDump.trim()) {
      setError('Please enter a character description');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/characters/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          brain_dump: brainDump
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to process character');
      }

      if (data.success && data.character) {
        setCharacter(data.character);
        onCharacterCreated?.(data.character);
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
    setBrainDump('');
    setCharacter(null);
    setError(null);
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Character Brain Dump
        </h2>
        <p className="text-gray-600">
          Describe your character in any way you like. Our AI will extract 
          structured information to help you develop them further.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="brain-dump" className="block text-sm font-medium text-gray-700 mb-2">
            Character Description
          </label>
          <textarea
            id="brain-dump"
            value={brainDump}
            onChange={(e) => setBrainDump(e.target.value)}
            placeholder="Tell us about your character... their background, personality, goals, relationships, or anything else that comes to mind. Be as detailed or as brief as you like!"
            className="textarea-field min-h-[200px]"
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
            disabled={loading || !brainDump.trim()}
            className="btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <User className="h-4 w-4" />
            )}
            <span>{loading ? 'Processing...' : 'Process Character'}</span>
          </button>

          {(character || brainDump) && (
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

      {character && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
          <div className="flex items-center space-x-2 text-green-600 mb-4">
            <FileText className="h-5 w-5" />
            <h3 className="text-lg font-semibold">Character Profile Generated</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Basic Information</h4>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="font-medium">Name:</span> {character.name}
                </div>
                <div>
                  <span className="font-medium">Background:</span>
                  <p className="mt-1 text-gray-600">{character.background}</p>
                </div>
                <div>
                  <span className="font-medium">Voice Notes:</span>
                  <p className="mt-1 text-gray-600">{character.voice_notes}</p>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-medium text-gray-900 mb-2">Characteristics</h4>
              <div className="space-y-3 text-sm">
                <div>
                  <span className="font-medium">Personality:</span>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {character.personality.map((trait, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-blue-100 text-blue-800 rounded-md text-xs"
                      >
                        {trait}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <span className="font-medium">Skills:</span>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {character.skills.map((skill, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-green-100 text-green-800 rounded-md text-xs"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <span className="font-medium">Goals:</span>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {character.goals.map((goal, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-purple-100 text-purple-800 rounded-md text-xs"
                      >
                        {goal}
                      </span>
                    ))}
                  </div>
                </div>

                {Object.keys(character.relationships).length > 0 && (
                  <div>
                    <span className="font-medium">Relationships:</span>
                    <div className="mt-1 space-y-1">
                      {Object.entries(character.relationships).map(([name, relationship], index) => (
                        <div key={index} className="text-xs text-gray-600">
                          <span className="font-medium">{name}:</span> {relationship}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-gray-200">
            <button
              onClick={() => {
                const characterJson = JSON.stringify(character, null, 2);
                navigator.clipboard.writeText(characterJson);
              }}
              className="btn-secondary text-sm"
            >
              Copy Character Data
            </button>
          </div>
        </div>
      )}
    </div>
  );
}; 