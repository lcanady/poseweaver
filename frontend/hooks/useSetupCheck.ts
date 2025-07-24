'use client';

import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { getApiUrl } from '@/utils/api-utils';

interface SetupStatus {
  needsSetup: boolean;
  checking: boolean;
  error: string | null;
}

export function useSetupCheck(): SetupStatus {
  const [needsSetup, setNeedsSetup] = useState(false);
  const [checking, setChecking] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Skip setup check if already on setup page or API routes
    if (pathname === '/setup' || pathname.startsWith('/api/')) {
      setChecking(false);
      return;
    }

    // Only run setup check on client side after component mounts
    if (typeof window !== 'undefined') {
      checkSetupStatus();
    } else {
      setChecking(false);
    }
  }, [pathname]);

  const checkSetupStatus = async () => {
    try {
      const response = await fetch(
        `${getApiUrl()}/api/setup/check`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setNeedsSetup(data.needs_setup);
        
        // If setup is needed and we're not already on the setup page, redirect
        if (data.needs_setup && pathname !== '/setup') {
          router.push('/setup');
        }
      } else {
        console.error('Failed to check setup status');
        setError('Failed to check setup status');
      }
    } catch (error) {
      console.error('Error checking setup status:', error);
      setError('Error checking setup status');
    } finally {
      setChecking(false);
    }
  };

  return {
    needsSetup,
    checking,
    error,
  };
}
