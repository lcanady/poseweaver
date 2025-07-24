import { useState, useCallback } from 'react'
import { useToast } from '@/hooks/use-toast'
import { useAuth } from '@/contexts/auth-context'
import { getApiUrl } from '@/utils/api-utils';

// Discord format regex patterns
const DISCORD_USER_PATTERN = /^([^\u2014]+)\s+\u2014\s+(\d+\/\d+\/\d+,\s+\d+:\d+\s+[AP]M)/
const DISCORD_POSE_BLOCK_PATTERN = /^([^\u2014]+)\s+\u2014\s+(\d+\/\d+\/\d+,\s+\d+:\d+\s+[AP]M)([\s\S]*?)(?=(?:[^\u2014]+\s+\u2014\s+\d+\/\d+\/\d+,\s+\d+:\d+\s+[AP]M)|$)/gm

export interface ProcessedPose {
  id?: string
  character_name: string
  pose_text: string
  pose_type: 'action' | 'dialogue' | 'narrative' | 'internal' | 'mixed'
  timestamp: string
  mentions?: string[]
}

export interface SceneDumpProcessingResult {
  success: boolean
  poses: ProcessedPose[]
  importedCount: number
  error?: string
  sceneId?: string

  enhancedPoses?: any[]
}

interface UseSceneDumpProcessorOptions {
  autoProcess?: boolean
  includeEnhancement?: boolean

  processingFormat?: 'simple' | 'character_prefix' | 'mush_output' | 'discord'
}

interface UseSceneDumpProcessorReturn {
  processSceneDump: (
    sceneDumpText: string,
    sceneId?: string,
    options?: UseSceneDumpProcessorOptions
  ) => Promise<SceneDumpProcessingResult>
  isProcessing: boolean
  lastResult: SceneDumpProcessingResult | null
  error: string | null
  clearError: () => void
}

export function useSceneDumpProcessor(): UseSceneDumpProcessorReturn {
  const [isProcessing, setIsProcessing] = useState(false)
  const [lastResult, setLastResult] = useState<SceneDumpProcessingResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()
  const { user, isLoading, isAuthenticated, refreshToken } = useAuth()

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  // Helper function to extract a character name from scene dump text
  const extractCharacterName = useCallback((text: string): string => {
    // Try to extract character name from Discord format first
    const discordMatch = DISCORD_USER_PATTERN.exec(text);
    if (discordMatch) {
      return discordMatch[1].trim(); // Return the username part (trimmed)
    }
    
    // Try to extract character name from content
    const firstSentenceMatch = /^([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?\s+(?:is|was|has|had|seems|looks|moves|walks|sits|stands|takes)/m.exec(text);
    if (firstSentenceMatch) {
      return firstSentenceMatch[1]; // Return the actual character name
    }
    
    // For now, just return the user's display name or a generic name
    return user?.display_name?.split(' ')[0] || 'Player';
  }, [user])
  
  // Helper function to detect if content is in Discord format
  const isDiscordFormat = useCallback((text: string): boolean => {
    // Check if text contains at least one line in Discord format
    // Example: "FaeWitch — 7/21/24, 3:46 PM"
    return DISCORD_USER_PATTERN.test(text);
  }, [])
  
  // Helper function to parse Discord-formatted content
  const parseDiscordContent = useCallback((text: string): ProcessedPose[] => {
    const poses: ProcessedPose[] = [];
    let match;
    
    // Reset regex state
    DISCORD_POSE_BLOCK_PATTERN.lastIndex = 0;
    
    // Match each Discord pose block
    while ((match = DISCORD_POSE_BLOCK_PATTERN.exec(text)) !== null) {
      const [, username, timestamp, content] = match;
      
      if (username && content) {
        // Parse timestamp into ISO format
        let isoTimestamp: string;
        try {
          // Format: "7/21/24, 3:46 PM" -> ISO string
          const dtMatch = /^(\d+)\/(\d+)\/(\d+),\s+(\d+):(\d+)\s+([AP]M)$/.exec(timestamp);
          if (dtMatch) {
            const [, month, day, year, hour, minute, ampm] = dtMatch;
            const fullYear = year.length === 2 ? `20${year}` : year;
            const hour24 = ampm === 'PM' && hour !== '12' ? parseInt(hour) + 12 : 
                         (ampm === 'AM' && hour === '12' ? 0 : parseInt(hour));
            
            const dt = new Date(
              parseInt(fullYear),
              parseInt(month) - 1, // JavaScript months are 0-indexed
              parseInt(day),
              hour24,
              parseInt(minute)
            );
            isoTimestamp = dt.toISOString();
          } else {
            isoTimestamp = new Date().toISOString();
          }
        } catch (e) {
          isoTimestamp = new Date().toISOString();
        }
        
        // Clean up content
        const cleanContent = content.trim();
        
        // Determine pose type based on content
        const poseType = determineDiscordPoseType(cleanContent);
        
        poses.push({
          character_name: username.trim(),
          pose_text: cleanContent,
          pose_type: poseType,
          timestamp: isoTimestamp
        });
      }
    }
    
    return poses;
  }, [])
  
  // Helper function to determine pose type based on content
  const determineDiscordPoseType = useCallback((content: string): ProcessedPose['pose_type'] => {
    // Count quotation marks to detect dialogue
    const quoteCount = (content.match(/"/g) || []).length;
    
    // Check for first-person narrative
    const firstPerson = /\b(I|I'm|I'd|I'll|I've)\b/i.test(content);
    
    // Look for dialogue indicators
    const hasDialogue = quoteCount >= 2 || /\b(says|said|asks|exclaims)\b/i.test(content);
    
    // Check for action descriptions
    const hasAction = /[*\-_!]|\b(moves|walks|runs|grabs|takes|holds|reaches)\b|\b(she|he|they)\s/i.test(content);
    
    // Check for emotional or internal thought indicators
    const hasInternal = /\b(feels|thinks|remembers|wonders|thought|feel|desire)\b/i.test(content);
    
    // Determine pose type based on content analysis
    if (hasDialogue && hasAction && hasInternal) {
      return 'mixed';
    } else if (hasDialogue && hasAction) {
      return 'mixed';
    } else if (hasDialogue) {
      return 'dialogue';
    } else if (hasInternal && firstPerson) {
      return 'internal';
    } else if (hasAction) {
      return 'action';
    } else {
      return 'narrative';
    }
  }, [])

  // Helper function to make authenticated API call with retry on 401
  const makeAuthenticatedRequest = useCallback(async (url: string, requestOptions: RequestInit): Promise<Response> => {
    let response = await fetch(url, requestOptions)
    
    // If 401, try to refresh token and retry once
    if (response.status === 401 && requestOptions.headers) {
      console.log('Access token expired, attempting refresh...')
      try {
        await refreshToken()
        
        // Get the new token and retry
        const newToken = localStorage.getItem('access_token')
        if (newToken) {
          const updatedHeaders = {
            ...requestOptions.headers as Record<string, string>,
            'Authorization': `Bearer ${newToken}`
          }
          
          response = await fetch(url, {
            ...requestOptions,
            headers: updatedHeaders
          })
        }
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError)
        // Token refresh failed, user needs to log in again
        throw new Error('Session expired. Please log in again.')
      }
    }
    
    return response
  }, [refreshToken])

  const processSceneDump = useCallback(async (
    sceneDumpText: string,
    sceneId?: string,
    options: UseSceneDumpProcessorOptions = {}
  ): Promise<SceneDumpProcessingResult> => {
    const {
      includeEnhancement = false,

      processingFormat = 'mush_output'
    } = options

    if (!sceneDumpText?.trim()) {
      const result = {
        success: false,
        poses: [],
        importedCount: 0,
        error: 'Scene dump text is required'
      }
      setLastResult(result)
      setError(result.error!)
      return result
    }

    // Check authentication state with better error messages
    if (isLoading) {
      const result = {
        success: false,
        poses: [],
        importedCount: 0,
        error: 'Authentication is loading, please wait...'
      }
      setLastResult(result)
      setError(result.error!)
      return result
    }

    // Check authentication state
    const userId = user?.id || user?._id
    if (!isAuthenticated || !userId) {
      console.log('Auth check failed:', { isAuthenticated, hasUser: !!user, userId, userIdField: user?.id, userIdMongo: user?._id })
      const result = {
        success: false,
        poses: [],
        importedCount: 0,
        error: 'Please log in to use scene dump processing'
      }
      setLastResult(result)
      setError(result.error!)
      return result
    }

    // Check for access token (after auth validation)
    let token: string | null = null
    if (typeof window !== 'undefined') {
      token = localStorage.getItem('access_token')
    }
    
    if (!token) {
      const result = {
        success: false,
        poses: [],
        importedCount: 0,
        error: 'Authentication token not found. Please log in again.'
      }
      setLastResult(result)
      setError(result.error!)
      return result
    }

    // Validate scene ID if provided
    if (sceneId && typeof window !== 'undefined') {
      console.log('Validating scene ID:', sceneId)
      try {
        const sceneResponse = await fetch(
          `${getApiUrl()}/api/scenes/${sceneId}`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        )

        if (!sceneResponse.ok) {
          let errorMsg = `Scene ${sceneId} not found`
          if (sceneResponse.status === 403) {
            errorMsg = `Access denied to scene ${sceneId}. Please check if you own this scene.`
          } else if (sceneResponse.status === 404) {
            errorMsg = `Scene ${sceneId} not found. You may need to save the scene first.`
          }

          const result = {
            success: false,
            poses: [],
            importedCount: 0,
            error: errorMsg
          }
          setLastResult(result)
          setError(result.error!)
          return result
        }

        const sceneData = await sceneResponse.json()
        console.log('Scene validation successful:', sceneData.data?.name)
      } catch (sceneError) {
        console.error('Scene validation error:', sceneError)
        const result = {
          success: false,
          poses: [],
          importedCount: 0,
          error: `Failed to validate scene ${sceneId}. Please check your connection and try again.`
        }
        setLastResult(result)
        setError(result.error!)
        return result
      }
    }

    setIsProcessing(true)
    setError(null)

    try {
      // First, check if this is Discord format and handle it specially if so
      let discordPoses: ProcessedPose[] = []
      const isDiscordFormatted = isDiscordFormat(sceneDumpText)
      
      if (isDiscordFormatted) {
        console.log('Detected Discord format - using specialized parser')
        discordPoses = parseDiscordContent(sceneDumpText)
        console.log(`Parsed ${discordPoses.length} poses from Discord format`)
      }
      
      // If we have enhancement enabled, use the advanced endpoint
      if (includeEnhancement) {
        // Let the LLM handle the parsing unless we already parsed Discord content
        const yourCharacterName = extractCharacterName(sceneDumpText);
        
        const requestBody = {
          // Always include raw_text if we don't have successfully parsed poses
          raw_text: (!isDiscordFormatted || discordPoses.length === 0) ? sceneDumpText : undefined,
          mush_output: (isDiscordFormatted && discordPoses.length > 0) ? JSON.stringify(discordPoses) : undefined,
          your_character_name: yourCharacterName,
          scene_id: sceneId,
          user_id: userId.toString(),
          store_all_poses: true,

          enhancement_style: 'balanced',
          use_llm_parsing: (!isDiscordFormatted || discordPoses.length === 0), // Use LLM parsing if Discord parsing failed
          format: isDiscordFormatted ? 'discord' : processingFormat,
          poses: (isDiscordFormatted && discordPoses.length > 0) ? discordPoses : undefined // Only include poses if we successfully parsed Discord content
        }

        // Debug logging
        console.log('Scene dump processing request:', {
          endpoint: '/api/mush/enhance',
          bodySize: JSON.stringify(requestBody).length,
          character_name: requestBody.your_character_name,
          user_id: requestBody.user_id,
          scene_id: requestBody.scene_id,
          has_token: !!token,
          is_discord_format: isDiscordFormatted,
          discord_poses_count: discordPoses.length
        })

        const response = await makeAuthenticatedRequest(
          `${getApiUrl()}/api/mush/enhance`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(requestBody)
          }
        )

        const data = await response.json()

        if (!response.ok) {
          console.error('Scene dump processing failed:', {
            status: response.status,
            statusText: response.statusText,
            response: data
          })
          
          // Better error extraction from response
          let errorMessage: string;
          if (data) {
            if (typeof data === 'string') {
              errorMessage = data;
            } else if (typeof data === 'object') {
              errorMessage = data.error || data.message || data.details || data.statusText || 
                `HTTP error! status: ${response.status} (${response.statusText || 'Unknown error'})`;
            } else {
              errorMessage = `HTTP error! status: ${response.status} (${response.statusText || 'Unknown error'})`;
            }
          } else {
            errorMessage = `HTTP error! status: ${response.status} (${response.statusText || 'Unknown error'})`;
          }
          
          throw new Error(errorMessage)
        }

        // The enhance endpoint has a different response structure
        if (data.parsed_scene) {
          const result: SceneDumpProcessingResult = {
            success: true,
            poses: data.parsed_scene?.poses || [],
            importedCount: data.parsed_scene?.poses?.length || 0,
            sceneId: sceneId, // Use the provided sceneId since the enhance endpoint doesn't return it

            enhancedPoses: data.enhanced_poses || []
          }

          setLastResult(result)
          
          // Now we need to manually store the poses in the scene
          if (sceneId && result.poses.length > 0) {
            try {
              // Store poses in the scene using the bulk import endpoint
              const bulkImportResponse = await makeAuthenticatedRequest(
                `${getApiUrl()}/api/scene-flow/scenes/${sceneId}/poses/bulk`,
                {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                  },
                  body: JSON.stringify({
                    poses: result.poses.map(pose => ({
                      character_name: pose.character_name,
                      pose_text: pose.pose_text,
                      pose_type: pose.pose_type,
                      timestamp: pose.timestamp
                    })),
                    use_llm_parsing: false // No need for LLM parsing as we already have parsed poses
                  })
                }
              )
              
              if (bulkImportResponse.ok) {
                const bulkImportData = await bulkImportResponse.json();
                if (bulkImportData.success) {
                  result.importedCount = bulkImportData.imported_count || result.poses.length;
                  
                  // Trigger a refresh of the scene-weaver poses view
                  // This uses a custom event that the scene-weaver component will listen for
                  if (typeof window !== 'undefined') {
                    // Create and dispatch a custom event to notify scene-weaver to refresh
                    const refreshEvent = new CustomEvent('scene-poses-updated', { 
                      detail: { 
                        sceneId,
                        posesCount: result.importedCount,
                        timestamp: new Date().toISOString()
                      } 
                    });
                    window.dispatchEvent(refreshEvent);
                    
                    // Also update localStorage to trigger updates in other components
                    localStorage.setItem('scene-poses-updated', JSON.stringify({
                      sceneId,
                      posesCount: result.importedCount,
                      timestamp: new Date().toISOString()
                    }));
                    
                    // Dispatch a storage event for same-tab updates
                    window.dispatchEvent(new StorageEvent('storage', {
                      key: 'scene-poses-updated',
                      newValue: JSON.stringify({
                        sceneId,
                        posesCount: result.importedCount,
                        timestamp: new Date().toISOString()
                      }),
                      storageArea: localStorage
                    }));
                  }
                }
              }
            } catch (importError) {
              console.error('Error storing poses:', importError);
            }
          }
          
          toast({
            title: "Scene Dump Processed Successfully",
            description: `Imported ${result.importedCount} poses.`
          })

          return result
        } else {
          throw new Error(data.error || 'Processing failed')
        }
      } else {
        // Use the simpler bulk import endpoint
        if (!sceneId) {
          throw new Error('Scene ID is required for bulk import')
        }

        // If we already parsed Discord content, use it directly
        if (isDiscordFormatted && discordPoses.length > 0) {
          // Use the bulk import endpoint with pre-parsed poses
          const bulkImportResponse = await makeAuthenticatedRequest(
            `${getApiUrl()}/api/scene-flow/scenes/${sceneId}/poses/bulk`,
            {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
              },
              body: JSON.stringify({
                poses: discordPoses,
                use_llm_parsing: false, // No need for LLM parsing since we pre-parsed
                format: 'discord' // Mark as Discord format
              })
            }
          )

          if (!bulkImportResponse.ok) {
            throw new Error(`HTTP error! status: ${bulkImportResponse.status}`)
          }

          const data = await bulkImportResponse.json()

          if (data.success) {
            const result: SceneDumpProcessingResult = {
              success: true,
              poses: discordPoses,
              importedCount: data.imported_count || discordPoses.length,
              sceneId: sceneId
            }

            setLastResult(result)
            
            // Trigger a refresh of the scene-weaver poses view
            if (typeof window !== 'undefined' && sceneId) {
              // Create and dispatch a custom event to notify scene-weaver to refresh
              const refreshEvent = new CustomEvent('scene-poses-updated', { 
                detail: { 
                  sceneId,
                  posesCount: result.importedCount,
                  timestamp: new Date().toISOString()
                } 
              });
              window.dispatchEvent(refreshEvent);
              
              // Also update localStorage to trigger updates in other components
              localStorage.setItem('scene-poses-updated', JSON.stringify({
                sceneId,
                posesCount: result.importedCount,
                timestamp: new Date().toISOString()
              }));
              
              // Dispatch a storage event for same-tab updates
              window.dispatchEvent(new StorageEvent('storage', {
                key: 'scene-poses-updated',
                newValue: JSON.stringify({
                  sceneId,
                  posesCount: result.importedCount,
                  timestamp: new Date().toISOString()
                }),
                storageArea: localStorage
              }));
            }
            
            toast({
              title: "Discord Poses Imported Successfully",
              description: `Added ${result.importedCount} poses extracted from Discord chat to the scene.`
            })

            return result
          } else {
            throw new Error(data.error || 'Import failed')
          }
        } else {
          // Let the LLM handle the parsing of non-Discord format
          const response = await makeAuthenticatedRequest(
            `${getApiUrl()}/api/scene-flow/scenes/${sceneId}/poses/bulk`,
            {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
              },
              body: JSON.stringify({
                raw_text: sceneDumpText, // Send the raw text
                use_llm_parsing: true, // Flag to indicate that we want to use LLM parsing
                format: processingFormat // Keep the format for backward compatibility
              })
            }
          )

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
          }

          const data = await response.json()

          if (data.success) {
            const result: SceneDumpProcessingResult = {
              success: true,
              poses: data.poses || [],
              importedCount: data.imported_count || 0,
              sceneId: sceneId
            }

            setLastResult(result)
            
            // Trigger a refresh of the scene-weaver poses view
            if (typeof window !== 'undefined' && sceneId) {
              // Create and dispatch a custom event to notify scene-weaver to refresh
              const refreshEvent = new CustomEvent('scene-poses-updated', { 
                detail: { 
                  sceneId,
                  posesCount: result.importedCount,
                  timestamp: new Date().toISOString()
                } 
              });
              window.dispatchEvent(refreshEvent);
              
              // Also update localStorage to trigger updates in other components
              localStorage.setItem('scene-poses-updated', JSON.stringify({
                sceneId,
                posesCount: result.importedCount,
                timestamp: new Date().toISOString()
              }));
              
              // Dispatch a storage event for same-tab updates
              window.dispatchEvent(new StorageEvent('storage', {
                key: 'scene-poses-updated',
                newValue: JSON.stringify({
                  sceneId,
                  posesCount: result.importedCount,
                  timestamp: new Date().toISOString()
                }),
                storageArea: localStorage
              }));
            }
            
            toast({
              title: "Poses Imported Successfully",
              description: `Added ${result.importedCount} poses to the scene.`
            })

            return result
          } else {
            throw new Error(data.error || 'Import failed')
          }
        }
      }
    } catch (err) {
      // Enhanced error handling
      console.error('Scene dump processing error:', err);
      
      // Extract a meaningful error message
      let errorMessage: string;
      
      if (err instanceof Error) {
        errorMessage = err.message;
        // Handle empty error objects in error message
        if (errorMessage.includes('{}') || errorMessage === 'Error: {}' || errorMessage === '{}') {
          errorMessage = 'Processing failed: The server returned an empty response. Please try again or contact support.';
        }
      } else if (typeof err === 'string') {
        errorMessage = err;
      } else if (err && typeof err === 'object') {
        // Try to extract error info from object
        const errorObj = err as any;
        errorMessage = errorObj.error || errorObj.message || errorObj.statusText || 
                      (errorObj.status ? `Server error: ${errorObj.status}` : 'Unknown error occurred');
      } else {
        errorMessage = 'Unknown error occurred during scene processing';
      }
      
      const result: SceneDumpProcessingResult = {
        success: false,
        poses: [],
        importedCount: 0,
        error: errorMessage
      }

      setLastResult(result)
      setError(errorMessage)

      toast({
        title: "Processing Failed",
        description: errorMessage,
        variant: "destructive"
      })

      return result
    } finally {
      setIsProcessing(false)
    }
  }, [toast, user, extractCharacterName, isAuthenticated, isLoading, refreshToken, makeAuthenticatedRequest, isDiscordFormat, parseDiscordContent])

  return {
    processSceneDump,
    isProcessing,
    lastResult,
    error,
    clearError
  }
}
