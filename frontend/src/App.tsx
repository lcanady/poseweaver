import React, { useState } from 'react';
import { User, Search, Wand2, MessageCircle, Upload } from 'lucide-react';
import { CharacterBrainDump } from './components/CharacterBrainDump';
import { PoseContextAnalysis } from './components/PoseContextAnalysis';
import { PoseEditor } from './components/PoseEditor';
import { SceneFlow } from './components/SceneFlow';
import MushParser from './components/MushParser';

type Tab = 'character' | 'context' | 'editor' | 'scene-flow' | 'mush-parser';

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

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('character');
  const [character, setCharacter] = useState<CharacterProfile | null>(null);
  const [context, setContext] = useState<PoseContext | null>(null);

  const tabs = [
    { id: 'character' as Tab, name: 'Character Brain Dump', icon: User },
    { id: 'context' as Tab, name: 'Pose Context Analysis', icon: Search },
    { id: 'editor' as Tab, name: 'Pose Editor', icon: Wand2 },
    { id: 'scene-flow' as Tab, name: 'Scene Flow', icon: MessageCircle },
    { id: 'mush-parser' as Tab, name: 'MUSH Parser', icon: Upload },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <h1 className="text-2xl font-bold text-gray-900">
              MUSH Pose Editor
            </h1>
            <p className="text-sm text-gray-600">
              AI-powered writing assistant for roleplayers
            </p>
          </div>
        </div>
      </header>

      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{tab.name}</span>
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      {(character || context) && (
        <div className="bg-blue-50 border-b border-blue-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
            <div className="flex items-center space-x-4 text-sm">
              <span className="font-medium text-blue-900">Active Session:</span>
              {character && (
                <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-md">
                  Character: {character.name}
                </span>
              )}
              {context && (
                <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-md">
                  Context: {context.narrative_tone} scene
                </span>
              )}
            </div>
          </div>
        </div>
      )}
      
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {activeTab === 'character' && (
            <CharacterBrainDump
              onCharacterCreated={(newCharacter) => {
                setCharacter(newCharacter);
                setActiveTab('context');
              }}
            />
          )}

          {activeTab === 'context' && (
            <PoseContextAnalysis
              onContextAnalyzed={(newContext) => {
                setContext(newContext);
                setActiveTab('editor');
              }}
            />
          )}

          {activeTab === 'editor' && (
            <PoseEditor
              character={character || undefined}
              context={context || undefined}
              onPoseEnhanced={(enhancement) => {
                console.log('Pose enhanced:', enhancement);
              }}
            />
          )}

          {activeTab === 'scene-flow' && (
            <SceneFlow
              onPoseEnhanced={(enhancement) => {
                console.log('Scene pose enhanced:', enhancement);
              }}
            />
          )}

          {activeTab === 'mush-parser' && (
            <MushParser />
          )}
        </div>
      </main>
    </div>
  );
}

export default App 