"use client"

import React, { createContext, useContext, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  User as FirebaseUser,
  onAuthStateChanged,
  signInWithPopup,
  GoogleAuthProvider,
  signOut,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  updateProfile
} from 'firebase/auth'
import { auth } from '@/lib/firebase/client'

// Extended User type to include custom fields if needed, 
// strictly mapped from Firebase for now.
export interface User {
  uid: string
  email: string | null
  displayName: string | null
  photoURL: string | null
}

interface AuthContextType {
  user: User | null
  loading: boolean
  isAuthenticated: boolean
  loginHelper: (email: string, password: string) => Promise<void>
  googleLogin: () => Promise<void>
  signupHelper: (email: string, password: string, displayName: string) => Promise<void>
  logoutHelper: () => Promise<void>
  getToken: () => Promise<string | null>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  const isAuthenticated = !!user

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      if (firebaseUser) {
        setUser({
          uid: firebaseUser.uid,
          email: firebaseUser.email,
          displayName: firebaseUser.displayName,
          photoURL: firebaseUser.photoURL
        })
      } else {
        setUser(null)
      }
      setLoading(false)
    })

    return () => unsubscribe()
  }, [])

  const googleLogin = async () => {
    try {
      const provider = new GoogleAuthProvider()
      await signInWithPopup(auth, provider)
      router.push('/dashboard')
    } catch (error) {
      console.error('Google login error:', error)
      throw error
    }
  }

  const loginHelper = async (email: string, password: string) => {
    try {
      await signInWithEmailAndPassword(auth, email, password)
      router.push('/dashboard')
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }

  const signupHelper = async (email: string, password: string, displayName: string) => {
    try {
      const result = await createUserWithEmailAndPassword(auth, email, password)
      // Update the user profile with the display name
      if (result.user) {
        await updateProfile(result.user, {
          displayName: displayName
        })
        // Force update local state since onAuthStateChanged might fire before profile update
        setUser({
          uid: result.user.uid,
          email: result.user.email,
          displayName: displayName,
          photoURL: result.user.photoURL
        })
      }
      router.push('/dashboard')
    } catch (error) {
      console.error('Signup error:', error)
      throw error
    }
  }

  const logoutHelper = async () => {
    try {
      await signOut(auth)
      setUser(null)
      router.push('/login')
    } catch (error) {
      console.error('Logout error:', error)
    }
  }

  const getToken = async () => {
    if (!auth.currentUser) return null
    return await auth.currentUser.getIdToken()
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated,
        loginHelper,
        googleLogin,
        signupHelper,
        logoutHelper,
        getToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
