import { adminDb } from '@/lib/firebase/admin';
import { FirestoreUser, FirestoreCharacter, FirestoreScene, FirestorePose } from '@/lib/types/firestore-schema';
import { FieldValue, Timestamp } from 'firebase-admin/firestore';

export class DataService {
  private usersCollection = adminDb.collection('users');
  private scenesCollection = adminDb.collection('scenes');

  /**
   * Users
   */
  async getUser(uid: string): Promise<FirestoreUser | null> {
    const doc = await this.usersCollection.doc(uid).get();
    if (!doc.exists) return null;
    return doc.data() as FirestoreUser;
  }

  async createUser(uid: string, data: Partial<FirestoreUser>): Promise<void> {
    // Merge provided data with defaults
    const now = Timestamp.now();
    const newUser: FirestoreUser = {
      uid,
      email: data.email || '',
      displayName: data.displayName || '',
      role: 'user',
      isActive: true,
      subscriptionStatus: 'free',
      poseGenerationsUsed: 0,
      extraPoseGenerations: 0,
      settings: data.settings || {
        theme: 'system',
        notifications: {
          emailUpdates: true,
          poseGenerationAlerts: false,
          subscriptionReminders: true,
          featureAnnouncements: true
        },
        privacy: {
          profileVisibility: 'private',
          analyticsTracking: true,
          dataCollection: true
        },
        preferences: {
          defaultEnhancementStyle: 'balanced',
          autoSavePoses: true,
          showAdvancedSettings: false,
          characterLimitWarnings: true
        }
      },
      createdAt: now as any,
      updatedAt: now as any,
      ...data
    };

    await this.usersCollection.doc(uid).set(newUser);
  }

  async updateUser(uid: string, data: Partial<FirestoreUser>): Promise<void> {
    const updateData = {
      ...data,
      updatedAt: Timestamp.now()
    };
    await this.usersCollection.doc(uid).update(updateData);
  }

  /**
   * Characters (Subcollection of Users)
   */
  async getCharacters(userId: string): Promise<FirestoreCharacter[]> {
    const snapshot = await this.usersCollection.doc(userId).collection('characters').get();
    return snapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data()
    })) as FirestoreCharacter[];
  }

  async getCharacter(userId: string, characterId: string): Promise<FirestoreCharacter | null> {
    const doc = await this.usersCollection.doc(userId).collection('characters').doc(characterId).get();
    if (!doc.exists) return null;
    return { id: doc.id, ...doc.data() } as FirestoreCharacter;
  }

  async createCharacter(userId: string, data: Omit<FirestoreCharacter, 'id' | 'userId' | 'createdAt' | 'updatedAt'>): Promise<string> {
    const now = Timestamp.now();
    const newChar = {
      ...data,
      userId,
      createdAt: now as any,
      updatedAt: now as any,
      isActive: true,
      playCount: 0
    };
    
    // Check limits logic should be in a domain service, but simple count check could be here
    // For now, just create
    const docRef = await this.usersCollection.doc(userId).collection('characters').add(newChar);
    return docRef.id;
  }

  async updateCharacter(userId: string, characterId: string, data: Partial<FirestoreCharacter>): Promise<void> {
     const updateData = {
      ...data,
      updatedAt: Timestamp.now()
    };
    await this.usersCollection.doc(userId).collection('characters').doc(characterId).update(updateData);
  }

  async deleteCharacter(userId: string, characterId: string): Promise<void> {
    await this.usersCollection.doc(userId).collection('characters').doc(characterId).delete();
  }

  /**
   * Scenes
   */
  async createScene(ownerId: string, data: Omit<FirestoreScene, 'id' | 'ownerId' | 'createdAt' | 'updatedAt'>): Promise<string> {
      const now = Timestamp.now();
      const newScene = {
          ...data,
          ownerId,
          createdAt: now as any,
          updatedAt: now as any,
          isActive: true
      };
      const docRef = await this.scenesCollection.add(newScene);
      return docRef.id;
  }
  
  async getScene(sceneId: string): Promise<FirestoreScene | null> {
      const doc = await this.scenesCollection.doc(sceneId).get();
      if (!doc.exists) return null;
      return { id: doc.id, ...doc.data() } as FirestoreScene;
  }

    
    /**
     * Get a scene and its poses
     */
    /**
     * Get a scene and its poses
     */
    async getSceneWithPoses(sceneId: string): Promise<{ scene: FirestoreScene, poses: FirestorePose[] } | null> {
        try {
            const sceneDoc = await this.scenesCollection.doc(sceneId).get();
            
            if (!sceneDoc.exists) return null;
            
            const scene = { id: sceneDoc.id, ...sceneDoc.data() } as FirestoreScene;
            
            const posesSnapshot = await this.scenesCollection.doc(sceneId).collection('poses').orderBy('timestamp', 'asc').get();
            
            const poses = posesSnapshot.docs.map(doc => ({ 
                id: doc.id, 
                ...doc.data() 
            } as any as FirestorePose));
            
            return { scene, poses };
        } catch (error) {
            console.error('Error fetching scene with poses:', error);
            return null;
        }
    }
}

export const dataService = new DataService();
