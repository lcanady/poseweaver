'use client';

import { useState, useRef, useEffect } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Upload, Loader2 } from "lucide-react";
import { toast } from "@/components/ui/use-toast";

interface AvatarUploadProps {
  initialImage?: string;
  name?: string;
  onImageUploaded: (imageUrl: string) => void;
  className?: string;
  size?: "sm" | "md" | "lg" | "xl";
}

export function AvatarUpload({ 
  initialImage = "/placeholder.svg", 
  name = "", 
  onImageUploaded,
  className = "",
  size = "lg"
}: AvatarUploadProps) {
  const [avatarUrl, setAvatarUrl] = useState<string>(initialImage);
  const [isUploading, setIsUploading] = useState(false);
  // Track preview URLs separately to avoid render loops
  const [localPreviewUrl, setLocalPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { refreshToken } = useAuth();

  // Size classes mapping
  const sizeClasses = {
    sm: "h-16 w-16",
    md: "h-24 w-24",
    lg: "h-32 w-32",
    xl: "h-40 w-40"
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    
    // Validate file type
    const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      toast({
        title: "Invalid file type",
        description: "Please upload a JPG, PNG, GIF, or WebP image.",
        variant: "destructive"
      });
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast({
        title: "File too large",
        description: "Please upload an image smaller than 5MB.",
        variant: "destructive"
      });
      return;
    }
    
    // Create local preview URL after validation
    const objectUrl = URL.createObjectURL(file);
    setLocalPreviewUrl(objectUrl);
    
    setIsUploading(true);

    try {
      // Create form data for upload
      const formData = new FormData();
      formData.append('file', file);

      // Upload to backend with token refresh logic
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const uploadWithRetry = async (retryCount = 0) => {
        // Get the latest token
        const currentToken = localStorage.getItem('access_token');
        
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/uploads/avatar`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${currentToken}`
          },
          body: formData
        });
        
        // If unauthorized and we haven't retried yet, refresh token and retry
        if (response.status === 401 && retryCount < 1) {
          console.log('Token expired for avatar upload, attempting refresh...');
          await refreshToken();
          return uploadWithRetry(retryCount + 1);
        }
        
        if (!response.ok) {
          throw new Error(`Failed to upload image: ${response.status}`);
        }
        
        return await response.json();
      };

      const data = await uploadWithRetry();
      
      if (!data.success) {
        throw new Error(data.message || 'Upload failed');
      }

      // Update avatar URL and clear the local preview
      setLocalPreviewUrl(null);
      setAvatarUrl(data.file_url);
      
      // Notify parent component
      onImageUploaded(data.file_url);
      
      toast({
        title: "Upload successful",
        description: "Your avatar image has been uploaded."
      });
    } catch (error) {
      console.error('Error uploading avatar:', error);
      toast({
        title: "Upload failed",
        description: error instanceof Error ? error.message : "Failed to upload image",
        variant: "destructive"
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  // Update avatarUrl when initialImage changes
  useEffect(() => {
    if (!localPreviewUrl) {
      setAvatarUrl(initialImage);
    }
  }, [initialImage, localPreviewUrl]);

  // Use effect to handle changes to localPreviewUrl
  useEffect(() => {
    // Only update avatarUrl when localPreviewUrl changes and is not null
    if (localPreviewUrl) {
      setAvatarUrl(localPreviewUrl);
    }
    
    // Cleanup function to revoke object URLs when component unmounts or URL changes
    return () => {
      if (localPreviewUrl && localPreviewUrl.startsWith('blob:')) {
        URL.revokeObjectURL(localPreviewUrl);
      }
    };
  }, [localPreviewUrl]);
  
  return (
    <div className="flex flex-col items-center gap-4">
      {/* Use direct img tag for local preview URLs */}
      {avatarUrl && avatarUrl.startsWith('blob:') ? (
        <div className={`overflow-hidden rounded-full ${sizeClasses[size]}`}>
          <img 
            src={avatarUrl} 
            alt={name || "Avatar"} 
            className="w-full h-full object-cover"
          />
        </div>
      ) : (
        <Avatar className={`${sizeClasses[size]} ${className}`}>
          <AvatarImage src={avatarUrl} alt={name || "Avatar"} />
          <AvatarFallback>{name ? name.charAt(0).toUpperCase() : "A"}</AvatarFallback>
        </Avatar>
      )}
      
      <input 
        type="file" 
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="image/jpeg,image/png,image/gif,image/webp"
        className="hidden"
      />
      
      <Button 
        type="button" 
        variant="outline" 
        onClick={handleButtonClick}
        disabled={isUploading}
      >
        {isUploading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Uploading...
          </>
        ) : (
          <>
            <Upload className="mr-2 h-4 w-4" />
            Upload Image
          </>
        )}
      </Button>
    </div>
  );
}
