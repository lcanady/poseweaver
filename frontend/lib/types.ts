export interface Character {
  id: string
  name: string
  description: string
  avatarUrl: string
  lastUsed: string
}

export interface Scene {
  id: string
  title: string // maps to name from backend
  lastPose: string // derived from most recent pose
  characters: string[] // derived from participants
  status: "Ongoing" | "Completed" // derived from is_active
  lastUpdated: string // maps to updated_at from backend
}
