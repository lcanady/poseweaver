import OpenAI from 'openai';
import { FirestoreScene, FirestorePose } from '@/lib/types/firestore-schema';
import { dataService } from './data-service';

export interface SummaryOptions {
  focus?: 'comprehensive' | 'character' | 'plot' | 'environment';
  characterId?: string;
  maxLength?: number;
  includeDetails?: boolean;
  formalStyle?: boolean;
  chronological?: boolean;
  highlightKeyEvents?: boolean;
}

export interface SceneSummary {
  sceneId: string;
  summaryText: string;
  summaryType: string;
  createdAt: string;
  focusCharacterId?: string;
  metadata?: any;
}

export class SummaryService {
  private openai: OpenAI;

  constructor() {
    this.openai = new OpenAI({
      baseURL: 'https://openrouter.ai/api/v1',
      apiKey: process.env.OPENROUTER_API_KEY,
      defaultHeaders: {
        'HTTP-Referer': process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
        'X-Title': 'PoseWeaver',
      },
    });
  }

  async generateSummary(
    sceneId: string,
    options: SummaryOptions = {}
  ): Promise<SceneSummary | null> {
    try {
        const data = await dataService.getSceneWithPoses(sceneId);
        if (!data) return null;
        
        const { scene, poses } = data;
        
        // Build context string from scene and poses
        let context = `Scene: ${scene.name}\nDescription: ${scene.description}\n`;
        context += `Participants: ${scene.participants.join(', ')}\n\n`;
        context += `Content:\n`;
        
        poses.forEach((pose, index) => {
            const poseText = pose.poseType === 'action' ? `*${pose.content}*` : `"${pose.content}"`;
            context += `${index + 1}. [${pose.characterName}] (${pose.poseType}): ${poseText}\n`;
        });
        
        const systemMessage = this.getSystemMessage(options);
        const userMessage = `Generate summary for the following scene:\n\n${context}`;

        const completion = await this.openai.chat.completions.create({
            model: 'google/gemini-2.0-flash-001',
            messages: [
                { role: 'system', content: systemMessage },
                { role: 'user', content: userMessage }
            ],
            temperature: 0.7,
            max_tokens: options.maxLength ? options.maxLength * 2 : 1000
        });

        return {
            sceneId,
            summaryText: completion.choices[0]?.message?.content || '',
            summaryType: options.focus || 'comprehensive',
            createdAt: new Date().toISOString(),
            focusCharacterId: options.characterId
        };

    } catch (error) {
        console.error('Summary Generation Error:', error);
        return null;
    }
  }

  private getSystemMessage(options: SummaryOptions): string {
      let prompt = `You are a skilled narrative summarizer for roleplaying scenes. Create a clear, engaging summary.`;
      
      if (options.focus === 'character') {
          prompt += ` Focus on the specified character's actions and development.`;
      } else if (options.focus === 'plot') {
          prompt += ` Focus on plot developments and narrative arcs.`;
      } else if (options.focus === 'environment') {
          prompt += ` Focus on environmental details and atmosphere.`;
      } else {
          prompt += ` Create a comprehensive overview.`;
      }
      
      return prompt;
  }
}

export const summaryService = new SummaryService();
