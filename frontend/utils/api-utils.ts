/**
 * Utility functions for API calls with dynamic URL detection
 */

/**
 * Get the API base URL dynamically based on the current environment
 * This works for both localhost development and production deployment
 */
export function getApiUrl(): string {
  // If NEXT_PUBLIC_API_URL is set, use it (for production or explicit configuration)
  if (process.env.NEXT_PUBLIC_API_URL) {
    console.log('[getApiUrl] Using NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL);
    return process.env.NEXT_PUBLIC_API_URL;
  }
  
  // For client-side requests
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const port = window.location.port;
    
    // If we're accessing through port 80 (nginx proxy), use relative URLs
    if (port === '80' || port === '') {
      const apiUrl = `http://${hostname}`;
      console.log('[getApiUrl] Production mode - using nginx proxy:', apiUrl);
      return apiUrl;
    }
    
    // If we're on port 3000 (development), use direct backend connection
    if (port === '3000' && (hostname === 'localhost' || hostname === '127.0.0.1')) {
      const apiUrl = 'http://localhost:5001';
      console.log('[getApiUrl] Development mode - using direct backend:', apiUrl);
      return apiUrl;
    }
    
    // For other cases, assume we should use the current origin
    const apiUrl = window.location.origin;
    console.log('[getApiUrl] Using current origin:', apiUrl);
    return apiUrl;
  }
  
  // Fallback for server-side rendering - use nginx proxy
  console.log('[getApiUrl] Server-side fallback - using nginx proxy: http://nginx');
  return 'http://nginx';
}

/**
 * Make an authenticated API request with dynamic URL detection
 */
export async function apiRequest(endpoint: string, options: RequestInit = {}) {
  const baseUrl = getApiUrl();
  const url = `${baseUrl}${endpoint}`;
  
  // Get access token from localStorage if available
  const accessToken = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  
  // Merge headers with authentication
  const headers = {
    'Content-Type': 'application/json',
    ...(accessToken && { 'Authorization': `Bearer ${accessToken}` }),
    ...options.headers,
  };
  
  return fetch(url, {
    ...options,
    headers,
  });
}

/**
 * Make an authenticated API request with credentials
 */
export async function apiRequestWithCredentials(endpoint: string, options: RequestInit = {}) {
  const baseUrl = getApiUrl();
  const url = `${baseUrl}${endpoint}`;
  
  // Get access token from localStorage if available
  const accessToken = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  
  // Merge headers with authentication
  const headers = {
    'Content-Type': 'application/json',
    ...(accessToken && { 'Authorization': `Bearer ${accessToken}` }),
    ...options.headers,
  };
  
  return fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  });
}
