import OpenAI from 'openai';
import { FirestoreCharacter } from '@/lib/types/firestore-schema';

export interface CharacterProfile {
    name: string;
    background: string;
    personality: string[];
    skills: string[];
    goals: string[];
    relationships: { [key: string]: string };
    voice_notes: string;
}

export class CharacterService {
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

  /**
   * Process a character brain dump into a structured profile.
   */
  async processBrainDump(brainDump: string, existingCharacter?: CharacterProfile): Promise<CharacterProfile> {
    try {
        const systemMessage = this.getSystemMessage(existingCharacter);
        const userMessage = `
        Analyze the following character description and extract structured information:

        ${brainDump}

        Please respond with a valid JSON object containing:
        - name: Character's full name (string)
        - background: History/Life story (string)
        - personality: List of traits (array of strings)
        - skills: List of abilities (array of strings)
        - goals: List of motivations (array of strings)
        - relationships: Dictionary of name:relationship (object)
        - voice_notes: How they speak (string)
        `;

        const completion = await this.openai.chat.completions.create({
            model: 'google/gemini-2.0-flash-001',
            messages: [
                { role: 'system', content: systemMessage },
                { role: 'user', content: userMessage }
            ],
            response_format: { type: 'json_object' },
            temperature: 0.3,
            max_tokens: 4000
        });

        const content = completion.choices[0]?.message?.content || '{}';
        const parsed = JSON.parse(content);
        
        // Basic validation/casting
        return {
            name: parsed.name || 'Unknown',
            background: parsed.background || '',
            personality: Array.isArray(parsed.personality) ? parsed.personality : [],
            skills: Array.isArray(parsed.skills) ? parsed.skills : [],
            goals: Array.isArray(parsed.goals) ? parsed.goals : [],
            relationships: typeof parsed.relationships === 'object' ? parsed.relationships : {},
            voice_notes: parsed.voice_notes || ''
        };

    } catch (error: any) {
        console.error('Character Processing Error:', error);
        throw new Error(`Failed to process character: ${error.message}`);
    }
  }

  private getSystemMessage(existing?: CharacterProfile): string {
      let base = `You are an expert character analyst for MUSH roleplay. Your task is to analyze character descriptions and extract structured information.
      
      Extract fields: name, background, personality, skills, goals, relationships, voice_notes.
      Return strictly as JSON.`;

      if (existing) {
          base += `\n\nUPDATING EXISTING CHARACTER: ${JSON.stringify(existing)}\nMerge new info with existing data.`;
      }

      return base;
  }
}

export const characterService = new CharacterService();
