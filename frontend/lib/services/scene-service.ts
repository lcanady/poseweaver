import { db } from '@/lib/firebase/client';
import { 
    collection, 
    addDoc, 
    doc, 
    updateDoc, 
    query, 
    where, 
    orderBy, 
    limit, 
    getDocs, 
    serverTimestamp, 
    increment,
    onSnapshot,
    DocumentSnapshot
} from 'firebase/firestore';
import { FirestoreScene, FirestorePose } from '@/lib/types/firestore-schema';
import { dataService } from './data-service';

export interface SceneCreationParams {
    name: string;
    description: string;
    ownerId: string;
}

export interface PoseCreationParams {
    sceneId: string;
    characterName: string;
    content: string;
    poseType: 'action' | 'dialogue' | 'mixed';
    isOoc?: boolean;
    userId?: string; // Determine which character made the pose
}

export class SceneService {
    
    /**
     * Create a new scene
     */
    async createScene(params: SceneCreationParams): Promise<string> {
        try {
            return await dataService.createScene(params.ownerId, {
                name: params.name,
                description: params.description,
                participants: [params.ownerId], // Owner is initial participant
                status: 'active',
                isActive: true
            });
        } catch (error) {
            console.error('Error creating scene:', error);
            throw error;
        }
    }

    /**
     * Get active scenes for a user
     */
    async getUserScenes(userId: string): Promise<FirestoreScene[]> {
        // This logic is partially in DataService, but here we might want specific filters
        // For now, let's use DataService for basic retrieval
        // TODO: Implement complex query in DataService or here if needed
        // Since DataService currently only has basic CRUD, we might extend it or put logic here.
        // Let's put logic here for now as it's "Business Logic" layer.
        
        try {
            const scenesRef = collection(db, 'scenes');
            const q = query(
                scenesRef, 
                where('ownerId', '==', userId),
                where('status', '==', 'active'),
                orderBy('lastActivity', 'desc')
            );
            
            const snapshot = await getDocs(q);
            return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() } as FirestoreScene));
        } catch (error) {
            console.error('Error fetching user scenes:', error);
            return [];
        }
    }

    /**
     * Add a pose to a scene
     */
    async addPose(params: PoseCreationParams): Promise<string> {
        const { sceneId, characterName, content, poseType, isOoc } = params;
        
        try {
            // 1. Create the pose
            const posesRef = collection(db, 'scenes', sceneId, 'poses');
            const newPose: any = {
                characterName,
                content,
                poseType,
                isOoc: isOoc || false,
                timestamp: serverTimestamp(),
                createdAt: serverTimestamp()
            };
            
            const docRef = await addDoc(posesRef, newPose);
            
            // 2. Update scene activity
            const sceneRef = doc(db, 'scenes', sceneId);
            await updateDoc(sceneRef, {
                lastActivity: serverTimestamp(),
                poseCount: increment(1)
            });
            // Note: server-side increment is cleaner, but for now we'll just let Firestore handle timestamp
            // Proper increment requires `increment(1)` from firebase/firestore
            
            return docRef.id;
        } catch (error) {
            console.error('Error adding pose:', error);
            throw error;
        }
    }
    
    /**
     * Subscribe to poses for a scene (Real-time)
     */
    subscribeToPoses(sceneId: string, callback: (poses: FirestorePose[]) => void): () => void {
        const posesRef = collection(db, 'scenes', sceneId, 'poses');
        const q = query(posesRef, orderBy('timestamp', 'asc')); // Chronological order
        
        return onSnapshot(q, (snapshot) => {
            const poses = snapshot.docs.map(doc => ({ 
                id: doc.id, 
                ...doc.data(),
                // Convert timestamp to Date/string handling logic might be needed for UI
            } as any as FirestorePose)); 
            callback(poses);
        });
    }

    /**
     * Subscribe to scene list (Real-time)
     */
    subscribeToSceneList(userId: string, callback: (scenes: FirestoreScene[]) => void): () => void {
        const scenesRef = collection(db, 'scenes');
        const q = query(
            scenesRef, 
            where('participants', 'array-contains', userId),
            where('status', '==', 'active'),
            orderBy('lastActivity', 'desc')
        );
        
        return onSnapshot(q, (snapshot) => {
            const scenes = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() } as FirestoreScene));
            callback(scenes);
        });
    }
}

export const sceneService = new SceneService();
