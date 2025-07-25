/**
 * Utility functions for API calls with dynamic URL detection
 */

/**
 * Get the API base URL dynamically based on the current environment
 * This works for both localhost and network access
 */
export function getApiUrl(): string {
  // If NEXT_PUBLIC_API is set, use it (for production or explicit configuration)
  if (process.env.NEXT_PUBLIC_API) {
    console.log('[getApiUrl] Using NEXT_PUBLIC_API:', process.env.NEXT_PUBLIC_API);
    return process.env.NEXT_PUBLIC_API;
  }
  
  // For client-side, dynamically detect the hostname
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const apiUrl = `http://${hostname}:5001`;
    console.log('[getApiUrl] Client-side detection - hostname:', hostname, 'apiUrl:', apiUrl);
    return apiUrl;
  }
  
  // Fallback for server-side rendering
  console.log('[getApiUrl] Using server-side fallback: http://localhost:5001');
  return 'http://localhost:5001';
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
