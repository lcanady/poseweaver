const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'

interface ApiOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  headers?: Record<string, string>
  body?: any
  requireAuth?: boolean
}

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function apiRequest<T = any>(
  endpoint: string,
  options: ApiOptions = {}
): Promise<T> {
  const {
    method = 'GET',
    headers = {},
    body,
    requireAuth = true,
  } = options

  const config: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
  }

  // Add authentication header if required
  if (requireAuth) {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${token}`,
      }
    }
  }

  // Add body if provided
  if (body) {
    config.body = JSON.stringify(body)
  }

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config)

    // Handle 401 errors - token might be expired
    if (response.status === 401 && requireAuth) {
      // Try to refresh token
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const refreshResponse = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${refreshToken}`,
            },
          })

          if (refreshResponse.ok) {
            const refreshData = await refreshResponse.json()
            localStorage.setItem('access_token', refreshData.access_token)
            localStorage.setItem('refresh_token', refreshData.refresh_token)

            // Retry original request with new token
            config.headers = {
              ...config.headers,
              Authorization: `Bearer ${refreshData.access_token}`,
            }
            
            const retryResponse = await fetch(`${API_BASE_URL}${endpoint}`, config)
            if (retryResponse.ok) {
              return await retryResponse.json()
            }
          }
        } catch (refreshError) {
          console.error('Token refresh failed:', refreshError)
        }
      }

      // If refresh failed, clear tokens and redirect to login
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
      throw new ApiError(401, 'Authentication required')
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new ApiError(response.status, errorData.error || 'Request failed')
    }

    return await response.json()
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(500, 'Network error')
  }
}

// Convenience methods
export const api = {
  get: <T = any>(endpoint: string, options?: Omit<ApiOptions, 'method'>) =>
    apiRequest<T>(endpoint, { ...options, method: 'GET' }),

  post: <T = any>(endpoint: string, data?: any, options?: Omit<ApiOptions, 'method' | 'body'>) =>
    apiRequest<T>(endpoint, { ...options, method: 'POST', body: data }),

  put: <T = any>(endpoint: string, data?: any, options?: Omit<ApiOptions, 'method' | 'body'>) =>
    apiRequest<T>(endpoint, { ...options, method: 'PUT', body: data }),

  delete: <T = any>(endpoint: string, options?: Omit<ApiOptions, 'method'>) =>
    apiRequest<T>(endpoint, { ...options, method: 'DELETE' }),
}

// Export the ApiError class for use in components
export { ApiError }

// Scene-related API functions
export const scenesApi = {
  // Get all scenes for the current user
  getScenes: () => api.get('/api/scenes'),
  
  // Get a specific scene by ID
  getScene: (id: string) => api.get(`/api/scenes/${id}`),
  
  // Create a new scene
  createScene: (sceneData: any) => api.post('/api/scenes', sceneData),
  
  // Update a scene
  updateScene: (id: string, sceneData: any) => api.put(`/api/scenes/${id}`, sceneData),
  
  // Delete a scene
  deleteScene: (id: string) => api.delete(`/api/scenes/${id}`),
} 