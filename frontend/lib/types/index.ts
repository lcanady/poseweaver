
// Re-export Firestore types
export * from './firestore-schema';
export * from './mush-parser';

// Re-export types from the root types directory
// We need to use relative paths carefully. 
// Since this file is in frontend/lib/types/index.ts, and other types are in frontend/types/
export * from '../../types/scene';
export * from '../../types/context';
// export * from '../../types/character-tracking'; // Circular dependency risk if we're not careful, but usually fine for types

// Define Character interface used in UI components (which differs slightly from FirestoreCharacter)
export interface Character {
  id: string;
  name: string;
  description: string;
  avatarUrl?: string; // Mapped from profileImage in some places
  lastUsed?: string;
  // created_at is often accessed via casting in the code
}
