import OpenAI from 'openai';

// Shared types could move to a separate file, but defining here for now
export interface PoseContext {
  actions: string[];
  emotions: string[];
  environmental_details: string[];
  character_interactions: string[];
  response_hooks: string[];
  scene_timing: string;
  urgency_level: string;
  narrative_tone: string;
  // Optional extras
  poses?: any[];
  contextText?: string;
  setting?: string;
  active_characters?: string[];
}

export class ContextService {
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
   * Analyze a pose to extract context for response crafting.
   */
  async analyzePoseContext(poseText: string, characterName?: string): Promise<PoseContext> {
    try {
        const systemMessage = this.getSystemMessage();
        const userMessage = `
        Analyze the following roleplay pose and extract structured context information:

        ${poseText}
        
        ${characterName ? `Analyzing from the perspective of character: ${characterName}` : ""}

        Please respond with a valid JSON object containing:
        - actions: List of physical actions and movements
        - emotions: List of emotional states and feelings expressed
        - environmental_details: List of setting and environmental elements
        - character_interactions: List of character interaction types
        - response_hooks: List of elements that invite responses
        - scene_timing: Overall timing context (immediate, ongoing, delayed)
        - urgency_level: How urgent the situation feels (low, medium, high, critical)
        - narrative_tone: The overall tone (serious, playful, tense, etc.)
        `;

        const completion = await this.openai.chat.completions.create({
            model: 'google/gemini-2.0-flash-001',
            messages: [
                { role: 'system', content: systemMessage },
                { role: 'user', content: userMessage }
            ],
            response_format: { type: 'json_object' }, // Enforce JSON
            temperature: 0.3,
            max_tokens: 1000
        });

        const content = completion.choices[0]?.message?.content || '{}';
        const parsed = JSON.parse(content);
        
        // Basic validation/sanitization could go here
        return {
            actions: parsed.actions || [],
            emotions: parsed.emotions || [],
            environmental_details: parsed.environmental_details || [],
            character_interactions: parsed.character_interactions || [],
            response_hooks: parsed.response_hooks || [],
            scene_timing: parsed.scene_timing || 'present',
            urgency_level: parsed.urgency_level || 'medium',
            narrative_tone: parsed.narrative_tone || 'neutral'
        };

    } catch (error: any) {
        console.error('Context Analysis Error:', error);
        throw new Error(`Failed to analyze context: ${error.message}`);
    }
  }

  private getSystemMessage(): string {
      return `You are an expert roleplay scene analyst specializing in MUSH pose context analysis. Your role is to analyze poses from other players and identify key elements that should influence character responses.
      
      Key guidelines:
      - Identify direct actions, dialogue, and environmental details
      - Detect emotional undertones and relationship dynamics
      - Highlight response hooks and narrative opportunities
      
      Focus on extracting actionable information that helps players craft appropriate and engaging responses.`;
  }
}

export const contextService = new ContextService();
