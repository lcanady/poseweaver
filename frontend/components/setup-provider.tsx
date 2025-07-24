'use client';

import { useSetupCheck } from '@/hooks/useSetupCheck';
import { usePathname } from 'next/navigation';

interface SetupProviderProps {
  children: React.ReactNode;
}

export function SetupProvider({ children }: SetupProviderProps) {
  const { needsSetup, checking, error } = useSetupCheck();
  const pathname = usePathname();

  // Show loading screen while checking setup status
  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="text-muted-foreground">Loading PoseWeaver...</p>
        </div>
      </div>
    );
  }

  // Show error screen if setup check failed
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <div className="text-destructive">
            <p className="text-lg font-semibold">Setup Check Failed</p>
            <p className="text-sm text-muted-foreground">{error}</p>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // If setup is needed, the useSetupCheck hook will handle redirection
  // Just render children normally - the hook handles the routing
  return <>{children}</>;
}
