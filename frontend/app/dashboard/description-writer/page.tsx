'use client'

import { useState, useCallback, useEffect } from 'react'
import { useAuth } from '@/contexts/auth-context'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { toast } from 'sonner'

// Import modular components
import { ImageUpload } from '@/components/description-writer/image-upload'
import { DescriptionInput } from '@/components/description-writer/description-input'
import { DescriptionOutput } from '@/components/description-writer/description-output'
import { DescriptionVersionHistory } from '@/components/description-writer/description-version-history'
import { DescriptionRefinement } from '@/components/description-writer/description-refinement'
import { UsageDisplay } from '@/components/pose-enhancer/usage-display'
import { InlinePaywall } from '@/components/pose-enhancer/inline-paywall'

interface DescriptionVersion {
  id: string
  description: string
  timestamp: Date
  style: string
  focusArea: string
  metadata?: DescriptionMetadata
}

interface DescriptionMetadata {
  style: string
  word_count: number
  processing_time_ms: number
  model_used: string
  timestamp: string
}

export default function DescriptionWriterPage() {
  const { user } = useAuth()
  const currentUserId = user?._id || null
  
  // Image state
  const [selectedImage, setSelectedImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  
  // Input state
  const [prompt, setPrompt] = useState('')
  const [style, setStyle] = useState('balanced')
  const [focusArea, setFocusArea] = useState('overall')
  
  // Advanced settings
  const [detailLevel, setDetailLevel] = useState(70)
  const [creativity, setCreativity] = useState(50)
  const [formality, setFormality] = useState(60)
  const [includeEmotions, setIncludeEmotions] = useState(false)
  const [includeTechnicalDetails, setIncludeTechnicalDetails] = useState(false)
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false)
  
  // Generation state
  const [isGenerating, setIsGenerating] = useState(false)
  const [currentDescription, setCurrentDescription] = useState('')
  const [descriptionVersions, setDescriptionVersions] = useState<DescriptionVersion[]>([])
  const [currentVersionIndex, setCurrentVersionIndex] = useState(-1)
  
  // Refinement state
  const [refinementSuggestion, setRefinementSuggestion] = useState('')
  const [isRefining, setIsRefining] = useState(false)
  
  // Copy format state
  const [copyFormat, setCopyFormat] = useState('standard')
  
  // Usage state - real usage info from backend
  const [usageInfo, setUsageInfo] = useState<any>({
    available_generations: 15,
    monthly_limit: 20,
    current_usage: 5,
    extra_generations: 0,
    subscription_status: 'free'
  })
  
  // Fetch current usage info
  const fetchUsageInfo = useCallback(async () => {
    if (!currentUserId) return
    
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/purchase/usage-status?user_id=${currentUserId}`
      )
      
      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          setUsageInfo(data.usage_info)
        }
      }
    } catch (error) {
      console.error('Error fetching usage info:', error)
    }
  }, [currentUserId])
  
  // Fetch usage info on mount and when user changes
  useEffect(() => {
    fetchUsageInfo()
  }, [fetchUsageInfo])
  
  // Handle image selection
  const handleImageSelect = useCallback((file: File) => {
    setSelectedImage(file)
    const reader = new FileReader()
    reader.onload = (e) => {
      setImagePreview(e.target?.result as string)
    }
    reader.readAsDataURL(file)
  }, [])
  
  const handleImageRemove = useCallback(() => {
    setSelectedImage(null)
    setImagePreview(null)
  }, [])
  
  // Generate description
  const generateDescription = useCallback(async () => {
    if (!selectedImage || !prompt.trim()) {
      toast.error('Please select an image and enter instructions')
      return
    }
    
    if (usageInfo.subscription_status === 'free' && usageInfo.available_generations <= 0) {
      toast.error('Usage limit reached. Please upgrade to continue.')
      return
    }
    
    setIsGenerating(true)
    
    try {
      const formData = new FormData()
      formData.append('image', selectedImage)
      formData.append('prompt', prompt)
      formData.append('style', style)
      
      // Map focus area to backend expected format
      let focusAreas = ''
      switch (focusArea) {
        case 'people':
          focusAreas = 'people,characters,faces'
          break
        case 'objects':
          focusAreas = 'objects,items,details'
          break
        case 'environment':
          focusAreas = 'environment,background,setting'
          break
        case 'mood':
          focusAreas = 'mood,atmosphere,lighting'
          break
        default:
          focusAreas = 'overall,general'
      }
      formData.append('focus_areas', focusAreas)
      
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'
      const accessToken = localStorage.getItem('access_token')
      
      const headers: Record<string, string> = {}
      if (accessToken) {
        headers['Authorization'] = `Bearer ${accessToken}`
      }
      
      const response = await fetch(`${apiUrl}/api/description/generate`, {
        method: 'POST',
        body: formData,
        headers,
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      const description = data.description
      
      // Calculate metadata
      const wordCount = description.split(' ').length
      
      const metadata: DescriptionMetadata = {
        style,
        word_count: wordCount,
        processing_time_ms: 0, // Will be updated from backend response if available
        model_used: 'qwen-2.5-vl',
        timestamp: new Date().toISOString()
      }
      
      // Create new version
      const newVersion: DescriptionVersion = {
        id: Date.now().toString(),
        description,
        timestamp: new Date(),
        style,
        focusArea,
        metadata
      }
      
      setCurrentDescription(description)
      setDescriptionVersions(prev => [newVersion, ...prev])
      setCurrentVersionIndex(0)
      
      // Update usage info from response if available
      if (data.usage_info) {
        setUsageInfo(data.usage_info)
      } else {
        // Fallback: manually update usage
        setUsageInfo((prev: any) => ({
          ...prev,
          available_generations: Math.max(0, prev.available_generations - 1),
          current_usage: prev.current_usage + 1
        }))
      }
      
      toast.success('Description generated successfully!')
    } catch (error) {
      console.error('Error generating description:', error)
      toast.error('Failed to generate description. Please try again.')
    } finally {
      setIsGenerating(false)
    }
  }, [selectedImage, prompt, style, focusArea, detailLevel, creativity, formality, includeEmotions, includeTechnicalDetails, usageInfo, currentUserId])
  
  // Handle refinement
  const handleRefineDescription = useCallback(async () => {
    if (!currentDescription || !refinementSuggestion.trim()) {
      toast.error('Please enter refinement instructions')
      return
    }
    
    setIsRefining(true)
    
    try {
      const formData = new FormData()
      if (selectedImage) formData.append('image', selectedImage)
      formData.append('prompt', `${currentDescription}\n\nRefinement request: ${refinementSuggestion}`)
      formData.append('style', style)
      
      // Map focus area to backend expected format
      let focusAreas = ''
      switch (focusArea) {
        case 'people':
          focusAreas = 'people,characters,faces'
          break
        case 'objects':
          focusAreas = 'objects,items,details'
          break
        case 'environment':
          focusAreas = 'environment,background,setting'
          break
        case 'mood':
          focusAreas = 'mood,atmosphere,lighting'
          break
        default:
          focusAreas = 'overall,general'
      }
      formData.append('focus_areas', focusAreas)
      
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'
      const accessToken = localStorage.getItem('access_token')
      
      const headers: Record<string, string> = {}
      if (accessToken) {
        headers['Authorization'] = `Bearer ${accessToken}`
      }
      
      const response = await fetch(`${apiUrl}/api/description/generate`, {
        method: 'POST',
        body: formData,
        headers,
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      const refinedDescription = data.description
      
      // Calculate metadata
      const wordCount = refinedDescription.split(' ').length
      
      const metadata: DescriptionMetadata = {
        style,
        word_count: wordCount,
        processing_time_ms: 0, // Will be updated from backend response if available
        model_used: 'qwen-2.5-vl',
        timestamp: new Date().toISOString()
      }
      
      // Create refined version
      const refinedVersion: DescriptionVersion = {
        id: Date.now().toString(),
        description: refinedDescription,
        timestamp: new Date(),
        style,
        focusArea,
        metadata
      }
      
      setCurrentDescription(refinedDescription)
      setDescriptionVersions(prev => [refinedVersion, ...prev])
      setCurrentVersionIndex(0)
      setRefinementSuggestion('')
      
      // Update usage info from response if available
      if (data.usage_info) {
        setUsageInfo(data.usage_info)
      }
      
      toast.success('Description refined successfully!')
    } catch (error) {
      console.error('Error refining description:', error)
      toast.error('Failed to refine description. Please try again.')
    } finally {
      setIsRefining(false)
    }
  }, [currentDescription, refinementSuggestion, selectedImage, style, focusArea, detailLevel, creativity, formality, currentUserId])
  
  // Handle version selection
  const handleVersionSelect = useCallback((index: number) => {
    const version = descriptionVersions[index]
    if (version) {
      setCurrentDescription(version.description)
      setCurrentVersionIndex(index)
    }
  }, [descriptionVersions])
  
  // Handle copy
  const handleCopy = useCallback(async () => {
    if (!currentDescription) return
    
    let textToCopy = currentDescription
    
    switch (copyFormat) {
      case 'markdown':
        textToCopy = `# Image Description\n\n${currentDescription}`
        break
      case 'plain':
        textToCopy = currentDescription.replace(/[*_~`]/g, '')
        break
      case 'quoted':
        textToCopy = `"${currentDescription}"`
        break
    }
    
    try {
      await navigator.clipboard.writeText(textToCopy)
      toast.success('Copied to clipboard!')
    } catch (error) {
      toast.error('Failed to copy to clipboard')
    }
  }, [currentDescription, copyFormat])
  
  // Handle download
  const handleDownload = useCallback(() => {
    if (!currentDescription) return
    
    const blob = new Blob([currentDescription], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `description-${Date.now()}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    toast.success('Description downloaded!')
  }, [currentDescription])
  
  // Handle upgrade click
  const handleUpgradeClick = useCallback(() => {
    // Navigate to upgrade page or show upgrade modal
    toast.info('Upgrade functionality would be implemented here')
  }, [])
  
  const currentMetadata = descriptionVersions[currentVersionIndex]?.metadata
  
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 mb-8">
        <div className="lg:col-span-3">
          <h1 className="text-3xl font-bold">Description Writer</h1>
          <p className="text-muted-foreground mt-1">
            Generate detailed descriptions of your images using AI
          </p>
        </div>
        <div className="lg:col-span-1">
          <UsageDisplay 
            usageInfo={usageInfo}
          />
        </div>
      </div>
      
      {/* Main Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-3 space-y-6">
          {/* Image Upload */}
          <ImageUpload
            onImageSelect={handleImageSelect}
            onImageRemove={handleImageRemove}
            selectedImage={selectedImage}
            imagePreview={imagePreview}
            disabled={isGenerating || isRefining}
          />
          
          {/* Description Input */}
          <DescriptionInput
            prompt={prompt}
            onPromptChange={setPrompt}
            style={style}
            onStyleChange={setStyle}
            focusArea={focusArea}
            onFocusAreaChange={setFocusArea}
            detailLevel={detailLevel}
            onDetailLevelChange={setDetailLevel}
            creativity={creativity}
            onCreativityChange={setCreativity}
            formality={formality}
            onFormalityChange={setFormality}
            includeEmotions={includeEmotions}
            onIncludeEmotionsChange={setIncludeEmotions}
            includeTechnicalDetails={includeTechnicalDetails}
            onIncludeTechnicalDetailsChange={setIncludeTechnicalDetails}
            showAdvancedSettings={showAdvancedSettings}
            onShowAdvancedSettingsChange={setShowAdvancedSettings}
            isGenerating={isGenerating}
            onGenerate={generateDescription}
            disabled={!selectedImage || isGenerating || isRefining}
            hasAccess={usageInfo.subscription_status !== 'free'}
            onUpgradeClick={handleUpgradeClick}
          />
          
          {/* Output */}
          {currentDescription && (
            <DescriptionOutput
              description={currentDescription}
              copyFormat={copyFormat}
              onCopyFormatChange={setCopyFormat}
              onCopy={handleCopy}
              onDownload={handleDownload}
              metadata={currentMetadata}
            />
          )}
        </div>
        
        {/* Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          {/* Refinement */}
          {currentDescription && (
            <DescriptionRefinement
              refinementSuggestion={refinementSuggestion}
              onRefinementSuggestionChange={setRefinementSuggestion}
              isRefining={isRefining}
              onRefineDescription={handleRefineDescription}
              hasDescription={!!currentDescription}
              disabled={isGenerating || isRefining}
            />
          )}
          
          {/* Version History */}
          {descriptionVersions.length > 0 && (
            <DescriptionVersionHistory
              versions={descriptionVersions}
              currentVersionIndex={currentVersionIndex}
              onVersionSelect={handleVersionSelect}
            />
          )}
          
          {/* Tips */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Tips</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-xs text-muted-foreground">
              <p>• Be specific about what you want described</p>
              <p>• Choose the right style for your use case</p>
              <p>• Use refinement to improve results</p>
              <p>• Try different focus areas for variety</p>
            </CardContent>
          </Card>
        </div>
      </div>
      
      {/* Paywall */}
      {usageInfo.subscription_status === 'free' && usageInfo.available_generations <= 0 && (
        <InlinePaywall
          subscriptionStatus={usageInfo.subscription_status}
          onPurchaseComplete={() => fetchUsageInfo()}
        />
      )}
    </div>
  )
}
