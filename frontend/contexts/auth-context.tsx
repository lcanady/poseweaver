"use client"

import React, { createContext, useContext, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { getApiUrl } from '@/utils/api-utils'

interface User {
  id?: number
  _id?: string  // MongoDB ObjectId
  email: string
  display_name: string
  bio?: string
  avatar_url?: string
  is_active: boolean
  is_admin?: boolean  // Admin flag for admin access
  created_at: string
  updated_at: string
  last_login?: string
}

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string, displayName: string) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<boolean>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)



export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  const isAuthenticated = !!user

  // Load user from session on mount
  useEffect(() => {
    const initAuth = async () => {
      try {
        // Try to get user from session
        await getCurrentUser()
      } catch (error) {
        console.error('Failed to load user:', error)
      } finally {
        setIsLoading(false)
      }
    }

    initAuth()
  }, [])

  const getCurrentUser = async () => {
    try {
      // Get token from localStorage for JWT auth
      const token = localStorage.getItem('access_token');
      
      // If no token, user is not authenticated - don't make API call
      if (!token) {
        setUser(null);
        return;
      }
      
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      };
      
      // Use JWT token-based authentication
      const response = await fetch(`${getApiUrl()}/api/auth/me`, {
        headers,
      })

      if (!response.ok) {
        // If unauthorized, clear the invalid token
        if (response.status === 401) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          setUser(null);
          return;
        }
        
        // For other errors, try to get error details
        const errorText = await response.text();
        let errorData = {};
        
        try {
          if (errorText) {
            errorData = JSON.parse(errorText);
          }
        } catch (parseError) {
          // Ignore JSON parse errors for error responses
        }
        
        throw new Error(`Failed to get user: ${response.status} ${response.statusText}`);
      }

      const data = await response.json()
      if (!data.user) {
        throw new Error('User data missing in response');
      }
      
      setUser(data.user)
    } catch (error) {
      // Only log actual errors, not authentication failures
      if (error instanceof Error && !error.message.includes('401')) {
        console.error('Auth error details:', error);
      }
      throw error;
    }
  }

  const login = async (email: string, password: string) => {
    setIsLoading(true)
    try {
      const response = await fetch(`${getApiUrl()}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Login failed')
      }

      const data = await response.json()
      
      // Store tokens in localStorage for API auth
      if (data.access_token) {
        localStorage.setItem('access_token', data.access_token);
      }
      
      if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token);
      }
      
      // Set user from response
      setUser(data.user)
      
      // Redirect to dashboard
      router.push('/dashboard')
    } catch (error) {
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const signup = async (email: string, password: string, displayName: string) => {
    setIsLoading(true)
    try {
      const response = await fetch(`${getApiUrl()}/api/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          email, 
          password, 
          display_name: displayName 
        }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Signup failed')
      }

      const data = await response.json()
      
      // Store tokens in localStorage for API auth
      if (data.access_token) {
        localStorage.setItem('access_token', data.access_token);
      }
      
      if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token);
      }
      
      // Set user from response
      setUser(data.user)
      
      // Redirect to dashboard
      router.push('/dashboard')
    } catch (error) {
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      // Get token from localStorage for JWT auth
      const token = localStorage.getItem('access_token');
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      await fetch(`${getApiUrl()}/api/auth/logout`, {
        method: 'POST',
        headers
      })
    } catch (error) {
      console.error('Logout request failed:', error)
    } finally {
      // Clear tokens from localStorage
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      
      // Clear local state regardless of API call success
      setUser(null)
      router.push('/login')
    }
  }

  const refreshToken = async () => {
    try {
      // Get the refresh token from localStorage (as stored during login/signup)
      const refreshToken = localStorage.getItem('refresh_token');
      
      if (!refreshToken) {
        console.error('No refresh token available in localStorage');
        throw new Error('No refresh token available');
      }

      const response = await fetch(`${getApiUrl()}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${refreshToken}` // Send refresh token in header
        }
      })

      if (!response.ok) {
        throw new Error(`Failed to refresh token: ${response.status}`);
      }

      // Parse the response to get the new tokens
      const data = await response.json();
      
      // Store the new tokens in localStorage
      if (data.access_token) {
        localStorage.setItem('access_token', data.access_token);
      }
      
      if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token);
      }
      
      // Return success
      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      // If refresh fails, clear tokens and user state
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      throw error;
    }
  }

  const refreshUser = async () => {
    try {
      await getCurrentUser()
    } catch (error) {
      console.error('Failed to refresh user:', error)
      throw error
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated,
        login,
        signup,
        logout,
        refreshToken,
        refreshUser,
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