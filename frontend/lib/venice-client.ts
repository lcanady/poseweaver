/**
 * Client-side Venice.ai API client for scene dump processing
 */

export interface VeniceProcessingOptions {
  apiKey: string
  enhancementStyle?: 'balanced' | 'dramatic' | 'subtle'
  includeContinuityAnalysis?: boolean
}

export interface ProcessedPose {
  id?: string
  character_name: string
  pose_text: string
  pose_type: 'action' | 'dialogue' | 'narrative' | 'internal' | 'mixed'
  timestamp: string
  mentions?: string[]
  enhanced_text?: string
}

export interface VeniceProcessingResult {
  success: boolean
  poses: ProcessedPose[]
  error?: string
  continuityAnalysis?: any
  enhancedPoses?: any[]
}

export class VeniceClient {
  private apiKey: string
  private baseUrl: string = 'https://api.venice.ai/api/v1'

  constructor(apiKey: string) {
    this.apiKey = apiKey
  }

  /**
   * Parse MUSH output into structured poses
   */
  private parseMushOutput(mushOutput: string, characterName: string): ProcessedPose[] {
    const poses: ProcessedPose[] = []
    const lines = mushOutput.split('\n').map(line => line.trim()).filter(Boolean)
    
    let currentCharacter = characterName
    let currentPose = ''
    let poseType: ProcessedPose['pose_type'] = 'action'
    
    for (const line of lines) {
      // Skip OOC comments and headers
      if (line.startsWith('<') || line.startsWith('---') || line.startsWith('Contents:')) {
        continue
      }
      
      // Character name detection
      const nameMatch = line.match(/^([A-Z][a-zA-Z]+)(?:\s+(?:says?|asks?|tells?|whispers?|shouts?)|:)(.*)/)
      if (nameMatch) {
        // Save previous pose if exists
        if (currentPose.trim()) {
          poses.push({
            character_name: currentCharacter,
            pose_text: currentPose.trim(),
            pose_type: poseType,
            timestamp: new Date().toISOString(),
            mentions: this.extractMentions(currentPose)
          })
        }
        
        // Start new pose
        currentCharacter = nameMatch[1]
        currentPose = nameMatch[2] || ''
        poseType = line.includes('says') || line.includes('asks') ? 'dialogue' : 'action'
      } else if (line.match(/^[A-Z][a-zA-Z]+\s+/)) {
        // Action pose
        if (currentPose.trim()) {
          poses.push({
            character_name: currentCharacter,
            pose_text: currentPose.trim(),
            pose_type: poseType,
            timestamp: new Date().toISOString(),
            mentions: this.extractMentions(currentPose)
          })
        }
        
        const actionMatch = line.match(/^([A-Z][a-zA-Z]+)\s+(.*)/)
        if (actionMatch) {
          currentCharacter = actionMatch[1]
          currentPose = actionMatch[2]
          poseType = 'action'
        }
      } else if (currentPose) {
        // Continue current pose
        currentPose += ' ' + line
      } else {
        // Start new pose with current character
        currentPose = line
      }
    }
    
    // Add final pose
    if (currentPose.trim()) {
      poses.push({
        character_name: currentCharacter,
        pose_text: currentPose.trim(),
        pose_type: poseType,
        timestamp: new Date().toISOString(),
        mentions: this.extractMentions(currentPose)
      })
    }
    
    return poses
  }

  /**
   * Extract character mentions from pose text
   */
  private extractMentions(text: string): string[] {
    const mentions: string[] = []
    const mentionPatterns = [
      /\b([A-Z][a-zA-Z]+)(?=\s+(?:looks?|turns?|moves?|walks?|approaches?))/g,
      /(?:to|at|with)\s+([A-Z][a-zA-Z]+)/g
    ]
    
    for (const pattern of mentionPatterns) {
      let match
      while ((match = pattern.exec(text)) !== null) {
        const name = match[1]
        if (name && !mentions.includes(name)) {
          mentions.push(name)
        }
      }
    }
    
    return mentions
  }

  /**
   * Enhance poses using Venice.ai API
   */
  private async enhancePoses(poses: ProcessedPose[], style: string = 'balanced'): Promise<ProcessedPose[]> {
    if (!this.apiKey || this.apiKey === 'test-key' || this.apiKey === 'your_venice_api_key_here') {
      // Return poses without enhancement if no valid API key
      return poses
    }

    try {
      const enhancedPoses = await Promise.all(
        poses.map(async (pose) => {
          try {
            const prompt = `Enhance this roleplay pose while maintaining the original meaning and character voice. Style: ${style}. Original: "${pose.pose_text}"`
            
            const response = await fetch(`${this.baseUrl}/chat/completions`, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                model: 'gpt-4',
                messages: [
                  {
                    role: 'system',
                    content: 'You are an expert roleplay writer. Enhance poses while preserving character voice and meaning. Keep enhancements natural and engaging.'
                  },
                  {
                    role: 'user',
                    content: prompt
                  }
                ],
                max_tokens: 200,
                temperature: 0.7
              })
            })

            if (response.ok) {
              const data = await response.json()
              const enhancedText = data.choices?.[0]?.message?.content?.trim()
              
              return {
                ...pose,
                enhanced_text: enhancedText || pose.pose_text
              }
            } else {
              return pose
            }
          } catch (error) {
            console.warn('Failed to enhance pose:', error)
            return pose
          }
        })
      )

      return enhancedPoses
    } catch (error) {
      console.warn('Enhancement failed, returning original poses:', error)
      return poses
    }
  }

  /**
   * Process scene dump with full parsing and optional enhancement
   */
  async processSceneDump(
    mushOutput: string,
    characterName: string,
    options: Partial<VeniceProcessingOptions> = {}
  ): Promise<VeniceProcessingResult> {
    try {
      // Parse the MUSH output
      let poses = this.parseMushOutput(mushOutput, characterName)
      
      if (poses.length === 0) {
        return {
          success: false,
          poses: [],
          error: 'No poses found in the provided text'
        }
      }

      // Enhance poses if API key is available and style is specified
      if (options.enhancementStyle && this.apiKey) {
        poses = await this.enhancePoses(poses, options.enhancementStyle)
      }

      return {
        success: true,
        poses: poses,
        continuityAnalysis: options.includeContinuityAnalysis ? {
          generated_at: new Date().toISOString(),
          character_count: new Set(poses.map(p => p.character_name)).size,
          pose_count: poses.length,
          dialogue_ratio: poses.filter(p => p.pose_type === 'dialogue').length / poses.length
        } : undefined
      }

    } catch (error) {
      console.error('Scene dump processing failed:', error)
      return {
        success: false,
        poses: [],
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      }
    }
  }
} 