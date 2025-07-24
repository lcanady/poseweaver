'use client';

import { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { getApiUrl } from '@/utils/api-utils';

interface SuccessResponse {
  success: boolean;
  message: string;
  subscription_status?: string;
  user_email?: string;
  redirect_url?: string;
  error?: string;
}

export default function SuccessPage() {
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [response, setResponse] = useState<SuccessResponse | null>(null);
  const searchParams = useSearchParams();
  const router = useRouter();

  useEffect(() => {
    const sessionId = searchParams.get('session_id');
    
    if (!sessionId) {
      setStatus('error');
      setResponse({
        success: false,
        error: 'Missing session ID',
        message: 'Payment session not found'
      });
      return;
    }

    // Call the backend success endpoint
    fetch(`${getApiUrl()}/api/purchase/success?session_id=${sessionId}`)
      .then(res => res.json())
      .then((data: SuccessResponse) => {
        setResponse(data);
        setStatus(data.success ? 'success' : 'error');
        
        // Redirect after 3 seconds if successful
        if (data.success && data.redirect_url) {
          setTimeout(() => {
            router.push(data.redirect_url!);
          }, 3000);
        }
      })
      .catch(error => {
        console.error('Error processing payment success:', error);
        setStatus('error');
        setResponse({
          success: false,
          error: 'Failed to process payment confirmation',
          message: 'Please contact support if your payment was charged'
        });
      });
  }, [searchParams, router]);

  if (status === 'loading') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="bg-white/10 backdrop-blur-sm rounded-lg p-8 text-center max-w-md">
          <Loader2 className="h-12 w-12 text-amber-400 animate-spin mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-white mb-2">Processing Payment</h1>
          <p className="text-gray-300">Please wait while we confirm your payment...</p>
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="bg-white/10 backdrop-blur-sm rounded-lg p-8 text-center max-w-md">
          <XCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-white mb-2">Payment Issue</h1>
          <p className="text-gray-300 mb-4">
            {response?.message || 'There was an issue processing your payment confirmation.'}
          </p>
          {response?.error && (
            <p className="text-red-300 text-sm mb-4">Error: {response.error}</p>
          )}
          <button
            onClick={() => router.push('/dashboard')}
            className="bg-amber-500 hover:bg-amber-600 text-white px-6 py-2 rounded-lg transition-colors"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
      <div className="bg-white/10 backdrop-blur-sm rounded-lg p-8 text-center max-w-md">
        <CheckCircle className="h-12 w-12 text-green-400 mx-auto mb-4" />
        <h1 className="text-2xl font-bold text-white mb-2">Payment Successful!</h1>
        <p className="text-gray-300 mb-4">
          {response?.message || 'Your payment has been processed successfully.'}
        </p>
        
        {response?.subscription_status && (
          <div className="bg-amber-500/20 border border-amber-500/30 rounded-lg p-4 mb-4">
            <p className="text-amber-200 font-medium">
              Subscription Status: {response.subscription_status.charAt(0).toUpperCase() + response.subscription_status.slice(1)}
            </p>
          </div>
        )}
        
        {response?.user_email && (
          <p className="text-gray-400 text-sm mb-4">
            Account: {response.user_email}
          </p>
        )}
        
        <div className="text-gray-300 text-sm mb-4">
          Redirecting to your dashboard in 3 seconds...
        </div>
        
        <button
          onClick={() => router.push(response?.redirect_url || '/dashboard')}
          className="bg-amber-500 hover:bg-amber-600 text-white px-6 py-2 rounded-lg transition-colors"
        >
          Continue to Dashboard
        </button>
      </div>
    </div>
  );
}
