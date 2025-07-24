'use client'

import { useState, useCallback, useEffect } from 'react'
import { useAuth } from '@/contexts/auth-context'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { toast } from 'sonner'
import { 
  Upload, 
  Image as ImageIcon, 
  Wand2, 
  Copy, 
  Download,
  Loader2,
  FileText,
  Sparkles,
  Eye,
  Crown
} from 'lucide-react'
import { ImageUpload } from '@/components/description-writer/image-upload'
import { DescriptionResult } from '@/components/description-writer/description-result'
import { StyleSelector } from '@/components/description-writer/style-selector'
import { UsageDisplay } from '@/components/pose-enhancer/usage-display'
import { InlinePaywall } from '@/components/pose-enhancer/inline-paywall'

interface DescriptionResponse {
  success: boolean
  description?: string
  metadata?: {
    style: string
    prompt_used: string
    model_used: string
    word_count: number
    processing_time_ms: number
    timestamp: string
  }
  usage_info?: {
    generations_used: number
    generations_limit: number
    subscription_status: string
  }
  error?: string
}

export default function DescriptionWriterPage() {
  const { user } = useAuth()
  const [selectedImage, setSelectedImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [prompt, setPrompt] = useState('')
  const [style, setStyle] = useState('balanced')
  const [focusAreas, setFocusAreas] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [result, setResult] = useState<DescriptionResponse | null>(null)
  const [showPaywall, setShowPaywall] = useState(false)
  const [usageInfo, setUsageInfo] = useState<any>(null)

  // Check if user has access to description writer
  const hasAccess = user && ['basic', 'pro', 'premium', 'admin'].includes(usageInfo?.subscription_status || '')

  const handleImageSelect = useCallback((file: File) => {
    setSelectedImage(file)
    
    // Create preview URL
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

  // Fetch usage info on component mount
  useEffect(() => {
    const fetchUsageInfo = async () => {
      if (!user?._id) return
      
      try {
        const accessToken = localStorage.getItem('access_token')
        if (!accessToken) return
        
        const response = await fetch('/api/purchase/usage-status', {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
          },
          credentials: 'include'
        })
        
        if (response.ok) {
          const data = await response.json()
          setUsageInfo(data)
        }
      } catch (error) {
        console.error('Error fetching usage info:', error)
      }
    }
    
    fetchUsageInfo()
  }, [user?._id])

  const handleGenerate = async () => {
    if (!selectedImage || !prompt.trim()) {
      toast.error('Please select an image and enter a prompt')
      return
    }

    if (!hasAccess) {
      setShowPaywall(true)
      return
    }

    setIsGenerating(true)
    setResult(null)

    try {
      const formData = new FormData()
      formData.append('image', selectedImage)
      formData.append('prompt', prompt.trim())
      formData.append('style', style)
      if (focusAreas.trim()) {
        formData.append('focus_areas', focusAreas.trim())
      }

      const response = await fetch('/api/description/generate', {
        method: 'POST',
        body: formData,
        credentials: 'include'
      })

      const data: DescriptionResponse = await response.json()

      if (data.success) {
        setResult(data)
        toast.success('Description generated successfully!')
      } else {
        if (response.status === 402) {
          setShowPaywall(true)
        } else {
          toast.error(data.error || 'Failed to generate description')
        }
      }
    } catch (error) {
      console.error('Error generating description:', error)
      toast.error('Failed to generate description')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleCopyDescription = () => {
    if (result?.description) {
      navigator.clipboard.writeText(result.description)
      toast.success('Description copied to clipboard!')
    }
  }

  const handleDownloadDescription = () => {
    if (result?.description) {
      const blob = new Blob([result.description], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `description-${Date.now()}.txt`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      toast.success('Description downloaded!')
    }
  }

  if (showPaywall) {
    return (
      <InlinePaywall 
        onBack={() => setShowPaywall(false)}
        currentFeature="Description Writer"
      />
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Eye className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Description Writer</h1>
            <p className="text-muted-foreground">
              Generate detailed physical descriptions from images using AI
            </p>
          </div>
        </div>

        {/* Free user notice */}
        {!hasAccess && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-2 text-amber-800">
              <Crown className="h-5 w-5" />
              <span className="font-medium">Premium Feature</span>
            </div>
            <p className="text-amber-700 mt-1">
              The Description Writer is available to Basic and Pro subscribers. 
              <Button 
                variant="link" 
                className="text-amber-800 p-0 h-auto font-medium"
                onClick={() => setShowPaywall(true)}
              >
                Upgrade now
              </Button> to unlock this feature.
            </p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column - Input */}
        <div className="lg:col-span-2 space-y-6">
          {/* Image Upload */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ImageIcon className="h-5 w-5" />
                Upload Image
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ImageUpload
                onImageSelect={handleImageSelect}
                onImageRemove={handleImageRemove}
                selectedImage={selectedImage}
                imagePreview={imagePreview}
                disabled={!hasAccess}
              />
            </CardContent>
          </Card>

          {/* Prompt Input */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Description Prompt
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="Describe what you want the AI to focus on in the image. For example: 'Describe the person's clothing and physical appearance in detail' or 'Focus on the facial features and expression'"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={4}
                disabled={!hasAccess}
              />
              
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Description Style
                  </label>
                  <StyleSelector
                    value={style}
                    onChange={setStyle}
                    disabled={!hasAccess}
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Focus Areas (Optional)
                  </label>
                  <Textarea
                    placeholder="Comma-separated areas to focus on (e.g., facial features, clothing, posture, background)"
                    value={focusAreas}
                    onChange={(e) => setFocusAreas(e.target.value)}
                    rows={2}
                    disabled={!hasAccess}
                  />
                </div>
              </div>

              <Button
                onClick={handleGenerate}
                disabled={!selectedImage || !prompt.trim() || isGenerating || !hasAccess}
                className="w-full"
                size="lg"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating Description...
                  </>
                ) : (
                  <>
                    <Wand2 className="mr-2 h-4 w-4" />
                    Generate Description
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Results & Usage */}
        <div className="space-y-6">
          {/* Usage Display */}
          {hasAccess && (
            <UsageDisplay />
          )}

          {/* Results */}
          {result && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5" />
                  Generated Description
                </CardTitle>
              </CardHeader>
              <CardContent>
                <DescriptionResult
                  result={result}
                  onCopy={handleCopyDescription}
                  onDownload={handleDownloadDescription}
                />
              </CardContent>
            </Card>
          )}

          {/* Tips */}
          <Card>
            <CardHeader>
              <CardTitle>Tips for Better Descriptions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div>
                <strong>Be Specific:</strong> Instead of "describe this person," try "describe their facial features and clothing style"
              </div>
              <div>
                <strong>Set the Context:</strong> Mention if it's for creative writing, character creation, or accessibility
              </div>
              <div>
                <strong>Use Focus Areas:</strong> List specific elements you want emphasized
              </div>
              <div>
                <strong>Choose the Right Style:</strong> Minimal for key points, Elaborate for rich detail
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
