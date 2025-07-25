'use client'

import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { 
  Copy, 
  Download, 
  Clock, 
  FileText, 
  Cpu,
  Calendar
} from 'lucide-react'
import { cn } from '../../lib/utils'

interface DescriptionResultProps {
  result: {
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
      current_usage: number
      monthly_limit: number
      subscription_status: string
    }
  }
  onCopy: () => void
  onDownload: () => void
}

export function DescriptionResult({ result, onCopy, onDownload }: DescriptionResultProps) {
  if (!result.success || !result.description || !result.metadata) {
    return null
  }

  const { description, metadata } = result
  
  const formatTimestamp = (timestamp: string): string => {
    try {
      return new Date(timestamp).toLocaleString()
    } catch {
      return 'Unknown'
    }
  }

  const formatProcessingTime = (ms: number): string => {
    if (ms < 1000) {
      return `${ms}ms`
    } else {
      return `${(ms / 1000).toFixed(1)}s`
    }
  }

  const getStyleColor = (style: string): string => {
    switch (style) {
      case 'minimal':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'balanced':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'elaborate':
        return 'bg-purple-100 text-purple-800 border-purple-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  return (
    <div className="space-y-4">
      {/* Action Buttons */}
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onCopy}
          className="flex-1"
        >
          <Copy className="h-4 w-4 mr-2" />
          Copy
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onDownload}
          className="flex-1"
        >
          <Download className="h-4 w-4 mr-2" />
          Download
        </Button>
      </div>

      {/* Description Text */}
      <Card className="p-4">
        <div className="prose prose-sm max-w-none">
          <div className="whitespace-pre-wrap text-sm leading-relaxed">
            {description}
          </div>
        </div>
      </Card>

      {/* Metadata */}
      <Card className="p-4">
        <div className="space-y-3">
          <h4 className="font-medium text-sm flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Generation Details
          </h4>
          
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Style:</span>
                <Badge 
                  variant="outline" 
                  className={cn("text-xs", getStyleColor(metadata.style))}
                >
                  {metadata.style.charAt(0).toUpperCase() + metadata.style.slice(1)}
                </Badge>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Words:</span>
                <span className="font-medium">{metadata.word_count}</span>
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  Time:
                </span>
                <span className="font-medium">
                  {formatProcessingTime(metadata.processing_time_ms)}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground flex items-center gap-1">
                  <Cpu className="h-3 w-3" />
                  Model:
                </span>
                <span className="font-medium text-xs">
                  {metadata.model_used}
                </span>
              </div>
            </div>
          </div>

          <Separator />
          
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Calendar className="h-3 w-3" />
              Generated: {formatTimestamp(metadata.timestamp)}
            </div>
            
            <div className="text-xs text-muted-foreground">
              <span className="font-medium">Prompt:</span> {metadata.prompt_used}
            </div>
          </div>
        </div>
      </Card>

      {/* Usage Info */}
      {result.usage_info && (
        <Card className="p-4">
          <div className="space-y-2">
            <h4 className="font-medium text-sm">Usage Information</h4>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Generations Used:</span>
              <span className="font-medium">
                {result.usage_info.current_usage} / {result.usage_info.monthly_limit}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Subscription:</span>
              <Badge variant="secondary" className="text-xs">
                {result.usage_info.subscription_status.charAt(0).toUpperCase() + 
                 result.usage_info.subscription_status.slice(1)}
              </Badge>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}
