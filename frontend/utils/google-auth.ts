/**
 * Google OAuth utilities for PoseWeaver
 */

declare global {
  interface Window {
    google: any;
    googleSignInCallback: (response: any) => void;
  }
}

export interface GoogleUser {
  email: string;
  name: string;
  picture: string;
  sub: string; // Google user ID
}

export class GoogleAuthService {
  private static clientId: string = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '';
  
  /**
   * Initialize Google Sign-In
   */
  static async initialize(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (typeof window === 'undefined') {
        reject(new Error('Google Auth can only be initialized in browser'));
        return;
      }

      // Check if already loaded
      if (window.google?.accounts) {
        resolve();
        return;
      }

      // Load Google Identity Services script
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      
      script.onload = () => {
        if (window.google?.accounts) {
          resolve();
        } else {
          reject(new Error('Failed to load Google Identity Services'));
        }
      };
      
      script.onerror = () => {
        reject(new Error('Failed to load Google Identity Services script'));
      };
      
      document.head.appendChild(script);
    });
  }

  /**
   * Sign in with Google using popup
   */
  static async signInWithPopup(): Promise<GoogleUser> {
    if (!this.clientId) {
      throw new Error('Google Client ID not configured');
    }

    await this.initialize();

    return new Promise((resolve, reject) => {
      window.google.accounts.oauth2.initTokenClient({
        client_id: this.clientId,
        scope: 'email profile',
        callback: async (response: any) => {
          if (response.error) {
            reject(new Error(response.error));
            return;
          }

          try {
            // Get user info using the access token
            const userInfo = await this.getUserInfo(response.access_token);
            resolve(userInfo);
          } catch (error) {
            reject(error);
          }
        },
      }).requestAccessToken();
    });
  }

  /**
   * Sign in with Google using One Tap
   */
  static async initializeOneTap(callback: (user: GoogleUser) => void): Promise<void> {
    if (!this.clientId) {
      throw new Error('Google Client ID not configured');
    }

    await this.initialize();

    // Set up global callback
    window.googleSignInCallback = async (response: any) => {
      try {
        const userInfo = await this.parseCredentialResponse(response);
        callback(userInfo);
      } catch (error) {
        console.error('Google One Tap sign-in failed:', error);
      }
    };

    window.google.accounts.id.initialize({
      client_id: this.clientId,
      callback: window.googleSignInCallback,
      auto_select: false,
      cancel_on_tap_outside: true,
    });

    // Display the One Tap prompt
    window.google.accounts.id.prompt();
  }

  /**
   * Render Google Sign-In button
   */
  static renderButton(elementId: string, callback: (user: GoogleUser) => void): void {
    if (!this.clientId) {
      throw new Error('Google Client ID not configured');
    }

    this.initialize().then(() => {
      window.google.accounts.id.initialize({
        client_id: this.clientId,
        callback: async (response: any) => {
          try {
            const userInfo = await this.parseCredentialResponse(response);
            callback(userInfo);
          } catch (error) {
            console.error('Google Sign-In failed:', error);
          }
        },
      });

      window.google.accounts.id.renderButton(
        document.getElementById(elementId),
        {
          theme: 'outline',
          size: 'large',
          width: '100%',
        }
      );
    });
  }

  /**
   * Get user info from Google API using access token
   */
  private static async getUserInfo(accessToken: string): Promise<GoogleUser> {
    const response = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to get user info from Google');
    }

    const userInfo = await response.json();
    
    return {
      email: userInfo.email,
      name: userInfo.name,
      picture: userInfo.picture,
      sub: userInfo.id,
    };
  }

  /**
   * Parse credential response from Google One Tap or Sign-In button
   */
  private static async parseCredentialResponse(response: any): Promise<GoogleUser> {
    if (!response.credential) {
      throw new Error('No credential in response');
    }

    // Decode JWT token (credential is a JWT)
    const payload = JSON.parse(atob(response.credential.split('.')[1]));
    
    return {
      email: payload.email,
      name: payload.name,
      picture: payload.picture,
      sub: payload.sub,
    };
  }

  /**
   * Sign out from Google
   */
  static async signOut(): Promise<void> {
    if (typeof window !== 'undefined' && window.google?.accounts) {
      window.google.accounts.id.disableAutoSelect();
    }
  }
}
