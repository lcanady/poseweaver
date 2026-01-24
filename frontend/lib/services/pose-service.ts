import OpenAI from 'openai';
import { adminDb } from '@/lib/firebase/admin';
import { FirestoreUser } from '@/lib/types/firestore-schema';
import { ParsedScene } from '@/lib/types/mush-parser';
import { dataService } from './data-service';

// Types for Pose Service
export interface PoseEnhancementParams {
  originalPose: string;
  characterId?: string; // If using character profile
  sceneContext?: string; // If using scene context
  enhancementStyle?: 'minimal' | 'balanced' | 'elaborate';
  userId?: string; // To fetch user settings/character
}

export interface PoseEnhancementResult {
  originalPose: string;
  enhancedPose: string;
  validationWarnings: string[];
  enhancementNotes: string[];
}

export class PoseService {
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
   * Main method to enhance a pose
   */
  async enhancePose(params: PoseEnhancementParams): Promise<PoseEnhancementResult> {
    const { originalPose, enhancementStyle = 'balanced', characterId, userId, sceneContext: rawSceneContext } = params;

    // 1. Fetch Character Data if provided
    let characterContext = '';
    if (userId && characterId) {
        try {
            // Import dynamically to avoid circular dependency issues if any, or just import at top if clean.
            // Using direct import since we'll add it to top of file.
            const character = await dataService.getCharacter(userId, characterId);
            if (character) {
                characterContext = `
                CHARACTER CONTEXT:
                Name: ${character.name}
                Description: ${character.description || ''}
                Background: ${character.background || ''}
                Personality: ${character.personality ? character.personality.join(', ') : ''}
                Voice Notes: ${character.voiceNotes || ''}
                `;
            }
        } catch (error) {
            console.warn('Failed to fetch character for pose enhancement:', error);
        }
    }

    // 2. Build System Message (Standard Roleplay Enhancement)
    const systemMessage = this.getSystemMessage('roleplay_enhancement');

    // 3. Build User Message
    const sceneContext = rawSceneContext ? `SCENE CONTEXT:\n${rawSceneContext}` : '';
    
    // Analyze paragraph structure to enforce output format
    const originalParagraphs = originalPose.split('\n\n');
    let originalParagraphCount = 0;
    
    // Better paragraph counting (filtering empty)
    for (const p of originalParagraphs) {
        if (p.trim().length > 0) originalParagraphCount++;
    }
    if (originalParagraphCount === 0) originalParagraphCount = 1;
    
    const userMessage = `
        Transform the following roleplay pose using minimal scene dressing, focusing on direct action and essential elements only:

        ORIGINAL POSE:
        ${originalPose}

        ${characterContext}
        ${sceneContext}
        
        ENHANCEMENT STYLE: ${enhancementStyle}
        
        🚨 CRITICAL ROLEPLAY RULES - MAIN CHARACTER ONLY 🚨:
        - ONLY enhance actions, thoughts, and reactions of the MAIN CHARACTER
        - NEVER pose for other characters, NPCs, or control their actions/dialogue
        - Focus on the main character's perspective, internal thoughts, and sensory experiences
        - NEVER describe mutual experiences, shared moments, or "both characters" doing anything
        
        MANDATORY FORMATTING RULES:
        1. Count paragraphs in original: ${originalParagraphCount}
        2. Your response MUST have ${originalParagraphCount} paragraphs
        3. Use \\n\\n between EVERY paragraph
        4. NEVER write wall of text - system will auto-reject
        5. Each original paragraph = one enhanced paragraph
        
        Respond with ONLY the enhanced pose text. NO thinking tags, NO metadata.
    `;

    try {
      const completion = await this.openai.chat.completions.create({
        model: 'cognitivecomputations/dolphin-mistral-24b-venice-edition:free', // Default model
        messages: [
            { role: 'system', content: systemMessage },
            { role: 'user', content: userMessage }
        ],
        temperature: 0.8,
        max_tokens: 4000
      });

      let enhancedPose = completion.choices[0]?.message?.content || '';
      
      // Basic cleaning (remove <think> tags if any remain)
      enhancedPose = enhancedPose.replace(/<think>[\s\S]*?<\/think>/g, '').trim();

      // Basic validation (check paragraph count match roughly)
      const warnings: string[] = [];
      const enhancedBreakCount = (enhancedPose.match(/\n\n/g) || []).length;
      const originalBreakCount = originalParagraphCount - 1; 
      
      if (Math.abs(enhancedBreakCount - originalBreakCount) > 1) {
          warnings.push('Paragraph structure may not match original.');
      }

      return {
        originalPose,
        enhancedPose,
        validationWarnings: warnings,
        enhancementNotes: []
      };

    } catch (error: any) {
      console.error('OpenRouter API Error:', error);
      throw new Error(`Pose enhancement failed: ${error.message}`);
    }
  }

  private getSystemMessage(useCase: string): string {
    // Ported from model_config.py
    if (useCase === 'roleplay_enhancement') {
        return `You are a skilled roleplay writer specializing in MUSH pose enhancement. Transform basic actions into clear, engaging prose that captures direct experience without excessive flourish.
        
        FUNDAMENTAL ROLEPLAY ETIQUETTE:
        - ONLY enhance the MAIN CHARACTER's actions, thoughts, and reactions
        - NEVER pose for other characters, NPCs, or control their behavior
        - NEVER make other characters speak, react, or move
        - Focus ONLY on the main character's direct experience and perspective
        
        WRITING STYLE - BALANCED AND DIRECT:
        - Write with clarity and purpose, avoiding excessive flowery language
        - Use concrete, specific details rather than abstract metaphors
        - Focus on clear action and genuine emotion over elaborate descriptions
        
        BURSTINESS & PERPLEXITY REQUIREMENTS:
        - Create HIGH BURSTINESS: Mix very short and very long sentences unpredictably
        - Use HIGH PERPLEXITY: Choose unexpected but fitting word combinations
        - Avoid predictable AI patterns - surprise with sentence structure
        
        Your goal is to create prose that feels natural, engaging, and focused on direct action and experience.`;
    }
    return '';
  }
}

export const poseService = new PoseService();
