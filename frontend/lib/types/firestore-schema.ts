import { Timestamp } from 'firebase/firestore';

// Basic User Interface mirroring the Firestore structure
export interface FirestoreUser {
  uid: string;
  email: string;
  displayName?: string;
  photoURL?: string;
  bio?: string;
  role: 'user' | 'admin';
  isActive: boolean;
  
  // Subscription
  subscriptionStatus: 'free' | 'basic' | 'pro' | 'premium' | 'expired' | 'admin';
  subscriptionExpiresAt?: Timestamp;
  stripeCustomerId?: string;
  
  // Usage
  poseGenerationsUsed: number;
  poseGenerationsResetDate?: Timestamp;
  extraPoseGenerations: number;
  
  // Settings
  settings: {
    theme: string;
    notifications: {
      emailUpdates: boolean;
      poseGenerationAlerts: boolean;
      subscriptionReminders: boolean;
      featureAnnouncements: boolean;
    };
    privacy: {
      profileVisibility: string;
      analyticsTracking: boolean;
      dataCollection: boolean;
    };
    preferences: {
      defaultEnhancementStyle: string;
      autoSavePoses: boolean;
      showAdvancedSettings: boolean;
      characterLimitWarnings: boolean;
    };
  };

  createdAt: Timestamp;
  updatedAt: Timestamp;
}

export interface FirestoreCharacter {
  id?: string; // Document ID
  userId: string;
  name: string;
  description?: string;
  profileImage?: string;
  tags: string[];
  isActive: boolean;
  
  lastPlayed?: Timestamp;
  playCount: number;
  
  // Character specific settings/metadata
  voiceNotes?: string;
  background?: string;
  personality?: string[];
  skills?: string[];
  
  createdAt: Timestamp;
  updatedAt: Timestamp;
}



export interface FirestorePose {
    id?: string;
    characterName: string;
    content: string;
    poseType: 'action' | 'dialogue' | 'mixed';
    isOoc?: boolean;
    timestamp: Timestamp;
    createdAt: Timestamp;
    enhancedText?: string;
}

export interface FirestoreScene {
  id?: string;
  ownerId: string;
  name: string;
  description?: string;
  isActive: boolean;
  status?: string;
  
  // State
  participants: string[]; // user IDs or character names
  location?: string;
  
  poseCount?: number;
  lastActivity?: Timestamp;
  
  createdAt: Timestamp;
  updatedAt: Timestamp;
}
