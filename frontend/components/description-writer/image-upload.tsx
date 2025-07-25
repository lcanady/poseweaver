'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Upload, 
  X, 
  Image as ImageIcon, 
  AlertCircle,
  FileImage
} from 'lucide-react'
import { cn } from "../lib"

interface ImageUploadProps {
  onImageSelect: (file: File) => void
  onImageRemove: () => void
  selectedImage: File | null
  imagePreview: string | null
  disabled?: boolean
}

const SUPPORTED_FORMATS = ['jpg', 'jpeg', 'png', 'webp', 'gif']
const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10MB

export function ImageUpload({
  onImageSelect,
  onImageRemove,
  selectedImage,
  imagePreview,
  disabled = false
}: ImageUploadProps) {
  const [dragError, setDragError] = useState<string | null>(null)

  const validateFile = (file: File): string | null => {
    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return `File too large. Maximum size is ${MAX_FILE_SIZE / (1024 * 1024)}MB`
    }

    // Check file type
    const fileExtension = file.name.split('.').pop()?.toLowerCase()
    if (!fileExtension || !SUPPORTED_FORMATS.includes(fileExtension)) {
      return `Unsupported format. Supported formats: ${SUPPORTED_FORMATS.join(', ')}`
    }

    return null
  }

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    setDragError(null)

    if (rejectedFiles.length > 0) {
      setDragError('Invalid file type or size')
      return
    }

    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0]
      const error = validateFile(file)
      
      if (error) {
        setDragError(error)
        return
      }

      onImageSelect(file)
    }
  }, [onImageSelect])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png', '.webp', '.gif']
    },
    maxFiles: 1,
    maxSize: MAX_FILE_SIZE,
    disabled
  })

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  if (selectedImage && imagePreview) {
    return (
      <Card className="relative">
        <div className="relative">
          <img
            src={imagePreview}
            alt="Selected image"
            className="w-full h-96 object-cover rounded-lg"
          />
          <div className="absolute inset-0 bg-black/40 opacity-0 hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center">
            <Button
              variant="destructive"
              size="sm"
              onClick={onImageRemove}
              disabled={disabled}
            >
              <X className="h-4 w-4 mr-2" />
              Remove
            </Button>
          </div>
        </div>
        
        <div className="p-4 border-t">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileImage className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium truncate max-w-48">
                {selectedImage.name}
              </span>
            </div>
            <Badge variant="secondary" className="text-xs">
              {formatFileSize(selectedImage.size)}
            </Badge>
          </div>
        </div>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <Card
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed transition-colors cursor-pointer h-96 flex items-center justify-center ",
          isDragActive && "border-primary bg-primary/5",
          dragError && "border-destructive bg-destructive/5",
          disabled && "opacity-50 cursor-not-allowed"
        )}
      >
        <input {...getInputProps()} />
        <div className="p-8 text-center">
          <div className="flex flex-col items-center gap-4">
            {isDragActive ? (
              <>
                <Upload className="h-12 w-12 text-primary animate-bounce" />
                <div>
                  <p className="text-lg font-medium text-primary">
                    Drop your image here
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Release to upload
                  </p>
                </div>
              </>
            ) : (
              <>
                <ImageIcon className="h-12 w-12 text-muted-foreground" />
                <div>
                  <p className="text-lg font-medium">
                    Drag & drop an image here
                  </p>
                  <p className="text-sm text-muted-foreground mb-4">
                    or click to browse files
                  </p>
                  <Button variant="outline" disabled={disabled}>
                    <Upload className="h-4 w-4 mr-2" />
                    Choose Image
                  </Button>
                </div>
              </>
            )}
          </div>
        </div>
      </Card>

      {dragError && (
        <div className="flex items-center gap-2 text-sm text-destructive">
          <AlertCircle className="h-4 w-4" />
          {dragError}
        </div>
      )}

      <div className="text-xs text-muted-foreground space-y-1">
        <p>Supported formats: {SUPPORTED_FORMATS.join(', ').toUpperCase()}</p>
        <p>Maximum file size: {MAX_FILE_SIZE / (1024 * 1024)}MB</p>
      </div>
    </div>
  )
}
