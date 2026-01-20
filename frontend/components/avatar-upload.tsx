'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { storage } from '@/lib/firebase/client';
import { ref, uploadBytes, getDownloadURL } from 'firebase/storage';
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Upload, Loader2, User, X, ZoomIn, ZoomOut } from "lucide-react";
import { toast } from "@/components/ui/use-toast";
import Cropper, { Area, Point } from 'react-easy-crop';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Slider } from "@/components/ui/slider";
import getCroppedImg from '@/utils/image-utils';

interface AvatarUploadProps {
  initialImage?: string;
  name?: string;
  onImageUploaded: (imageUrl: string) => void;
  className?: string;
  size?: "sm" | "md" | "lg" | "xl";
  characterId?: string;
}

export function AvatarUpload({
  initialImage = "",
  name = "",
  onImageUploaded,
  className = "",
  size = "lg",
  characterId
}: AvatarUploadProps) {
  const { user } = useAuth();
  const [avatarUrl, setAvatarUrl] = useState<string>(initialImage);
  const [isUploading, setIsUploading] = useState(false);
  // Track preview URLs separately to avoid render loops
  const [localPreviewUrl, setLocalPreviewUrl] = useState<string | null>(null);
  
  // Cropping State
  const [imageToCrop, setImageToCrop] = useState<string | null>(null);
  const [crop, setCrop] = useState<Point>({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [croppedAreaPixels, setCroppedAreaPixels] = useState<Area | null>(null);
  const [isCropDialogOpen, setIsCropDialogOpen] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  // const { refreshToken } = useAuth(); // Removed for Firebase migration

  // Size classes mapping
  const sizeClasses = {
    sm: "h-16 w-16",
    md: "h-24 w-24",
    lg: "h-32 w-32",
    xl: "h-40 w-40"
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0 || !user) {
      return;
    }
    const file = files[0];

    // Validation
    if (!file.type.startsWith('image/')) {
      toast({
        title: "Invalid file type",
        description: "Please select an image file.",
        variant: "destructive"
      });
      return;
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB limit for source image
      toast({
        title: "File too large",
        description: "Image size should be less than 10MB.",
        variant: "destructive"
      });
      return;
    }

    // Set image to crop and open dialog
    const reader = new FileReader();
    reader.addEventListener('load', () => {
      setImageToCrop(reader.result as string);
      setIsCropDialogOpen(true);
      setZoom(1);
      setCrop({ x: 0, y: 0 });
    });
    reader.readAsDataURL(file);
  };

  const onCropComplete = useCallback((_croppedArea: Area, croppedAreaPixels: Area) => {
    setCroppedAreaPixels(croppedAreaPixels);
  }, []);

  const handleSaveCrop = async () => {
    if (!imageToCrop || !croppedAreaPixels || !user) return;

    setIsUploading(true);
    setIsCropDialogOpen(false);

    try {
      const croppedBlob = await getCroppedImg(imageToCrop, croppedAreaPixels);
      if (!croppedBlob) throw new Error("Failed to crop image");

      // Create local preview immediately
      const previewUrl = URL.createObjectURL(croppedBlob);
      setLocalPreviewUrl(previewUrl);

      // Upload to Firebase
      const extension = "jpg";
      const fileName = characterId ? `${characterId}.${extension}` : `temp_${Date.now()}.${extension}`;
      const storagePath = `avatars/${user.uid}/${fileName}`;
      const storageRef = ref(storage, storagePath);

      console.log(`Starting upload to: ${storagePath}`);
      const snapshot = await uploadBytes(storageRef, croppedBlob);
      const downloadURL = await getDownloadURL(snapshot.ref);

      console.log('Upload successful:', downloadURL);
      onImageUploaded(downloadURL);

      toast({
        title: "Image Updated",
        description: "Your character avatar has been zoomed and saved."
      });
      
      // Clear image to crop to free memory
      setImageToCrop(null);
    } catch (error) {
      console.error('Upload error:', error);
      setLocalPreviewUrl(null);
      toast({ 
        title: "Upload Failed", 
        description: "There was an error saving your cropped image.",
        variant: "destructive" 
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleButtonClick = () => {
    console.log('AvatarUpload: Button clicked');
    if (fileInputRef.current) {
      // Reset value to ensure onChange fires even if same file is selected
      fileInputRef.current.value = '';
      fileInputRef.current.click();
    } else {
      console.error('AvatarUpload: fileInputRef is null');
      toast({
        title: "Error",
        description: "Upload component not initialized correctly. Please refresh.",
        variant: "destructive"
      });
    }
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
          <AvatarFallback className="bg-muted">
            <User className="h-1/2 w-1/2 text-muted-foreground" />
          </AvatarFallback>
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
            Processing...
          </>
        ) : (
          <>
            <Upload className="mr-2 h-4 w-4" />
            Upload Image
          </>
        )}
      </Button>

      {/* Cropping Dialog */}
      <Dialog open={isCropDialogOpen} onOpenChange={setIsCropDialogOpen}>
        <DialogContent className="sm:max-w-md md:max-w-xl">
          <DialogHeader>
            <DialogTitle>Zoom & Reposition</DialogTitle>
          </DialogHeader>
          
          <div className="relative w-full h-[300px] md:h-[400px] bg-black rounded-md overflow-hidden">
            {imageToCrop && (
              <Cropper
                image={imageToCrop}
                crop={crop}
                zoom={zoom}
                aspect={1}
                cropShape="round"
                showGrid={false}
                onCropChange={setCrop}
                onCropComplete={onCropComplete}
                onZoomChange={setZoom}
              />
            )}
          </div>
          
          <div className="flex items-center gap-4 py-4 px-2">
            <ZoomOut className="h-4 w-4 text-muted-foreground" />
            <Slider
              value={[zoom * 10]}
              min={10}
              max={30}
              step={1}
              onValueChange={(vals) => setZoom(vals[0] / 10)}
              className="flex-1"
            />
            <ZoomIn className="h-4 w-4 text-muted-foreground" />
          </div>
          
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="ghost"
              onClick={() => {
                setIsCropDialogOpen(false);
                setImageToCrop(null);
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleSaveCrop} className="bg-primary text-primary-foreground">
              Confirm & Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
