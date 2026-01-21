/**
 * Utility functions for API calls with dynamic URL detection
 */

/**
 * Get the API base URL dynamically based on the current environment
 * This works for both localhost and production deployment
 */
export function getApiUrl(): string {
  // If NEXT_PUBLIC_API_URL is set, use it (for production or explicit configuration)
  if (process.env.NEXT_PUBLIC_API_URL) {
    console.log('[getApiUrl] Using NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL);
    return process.env.NEXT_PUBLIC_API_URL;
  }

  // For client-side development, use localhost:5001
  if (typeof window !== 'undefined') {
    // Check if we're on localhost for development
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      const apiUrl = 'http://localhost:5001'; // Point directly to Flask backend
      console.log('[getApiUrl] Development mode - using:', apiUrl);
      return apiUrl;
    }

    // For production, we should have NEXT_PUBLIC_API_URL set
    // If not, this is an error condition
    console.error('[getApiUrl] Production environment detected but NEXT_PUBLIC_API_URL not set!');
    console.error('[getApiUrl] Current hostname:', hostname);
    throw new Error('NEXT_PUBLIC_API_URL environment variable must be set for production deployment');
  }

  // Fallback for server-side rendering in development
  console.log('[getApiUrl] Using server-side fallback: http://localhost:5001');
  return 'http://localhost:5001';
}

/**
 * Make an authenticated API request with dynamic URL detection
 */
export async function apiRequest(endpoint: string, options: RequestInit = {}) {
  const baseUrl = getApiUrl();
  const url = `${baseUrl}${endpoint}`;

  // Merge headers
  const headers = {
    'Content-Type': 'application/json',
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

  // Merge headers
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  return fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  });
}
