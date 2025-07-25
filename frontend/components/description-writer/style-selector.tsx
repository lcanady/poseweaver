'use client'

import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '../../lib/utils'
import { 
  Zap, 
  Scale, 
  Sparkles 
} from 'lucide-react'

interface StyleOption {
  id: string
  name: string
  description: string
  typical_length: string
  icon: React.ComponentType<{ className?: string }>
  color: string
}

const STYLE_OPTIONS: StyleOption[] = [
  {
    id: 'minimal',
    name: 'Minimal',
    description: 'Concise but vivid descriptions focusing on key elements',
    typical_length: '2-4 sentences',
    icon: Zap,
    color: 'text-blue-600'
  },
  {
    id: 'balanced',
    name: 'Balanced',
    description: 'Comprehensive detail balancing features, clothing, and posture',
    typical_length: '4-8 sentences',
    icon: Scale,
    color: 'text-green-600'
  },
  {
    id: 'elaborate',
    name: 'Elaborate',
    description: 'Rich, detailed descriptions with extensive visual information',
    typical_length: '8-15+ sentences',
    icon: Sparkles,
    color: 'text-purple-600'
  }
]

interface StyleSelectorProps {
  value: string
  onChange: (style: string) => void
  disabled?: boolean
}

export function StyleSelector({ value, onChange, disabled = false }: StyleSelectorProps) {
  return (
    <div className="grid grid-cols-1 gap-3">
      {STYLE_OPTIONS.map((option) => {
        const Icon = option.icon
        const isSelected = value === option.id
        
        return (
          <Card
            key={option.id}
            className={cn(
              "p-4 cursor-pointer transition-all border-2",
              isSelected 
                ? "border-primary bg-primary/5 shadow-md" 
                : "border-border hover:border-primary/50 hover:bg-muted/50",
              disabled && "opacity-50 cursor-not-allowed"
            )}
            onClick={() => !disabled && onChange(option.id)}
          >
            <div className="flex items-start gap-3">
              <div className={cn(
                "p-2 rounded-lg",
                isSelected ? "bg-primary/20" : "bg-muted"
              )}>
                <Icon className={cn(
                  "h-5 w-5",
                  isSelected ? "text-primary" : option.color
                )} />
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-medium">{option.name}</h3>
                  <Badge variant="secondary" className="text-xs">
                    {option.typical_length}
                  </Badge>
                </div>
                
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {option.description}
                </p>
              </div>
              
              {isSelected && (
                <div className="flex-shrink-0">
                  <div className="w-2 h-2 bg-primary rounded-full"></div>
                </div>
              )}
            </div>
          </Card>
        )
      })}
    </div>
  )
}
