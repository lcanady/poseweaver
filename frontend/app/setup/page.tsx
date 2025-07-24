'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { getApiUrl } from '@/utils/api-utils';
import { 
  Shield, 
  User, 
  Mail, 
  Lock, 
  CheckCircle, 
  AlertCircle,
  Feather,
  Crown
} from 'lucide-react';
import { toast } from 'sonner';

export default function SetupPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(true);
  const [needsSetup, setNeedsSetup] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    display_name: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Check if setup is needed on component mount (client-side only)
  useEffect(() => {
    // Only run setup check on client side after component mounts
    if (typeof window !== 'undefined') {
      checkSetupStatus();
    } else {
      setChecking(false);
    }
  }, []);

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
        
        if (!data.needs_setup) {
          // Setup not needed, redirect to home
          router.push('/');
        }
      } else {
        toast.error('Failed to check setup status');
        router.push('/');
      }
    } catch (error) {
      console.error('Error checking setup status:', error);
      toast.error('Failed to check setup status');
      router.push('/');
    } finally {
      setChecking(false);
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters long';
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    if (!formData.display_name.trim()) {
      newErrors.display_name = 'Display name is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(
        `${getApiUrl()}/api/setup/create-admin`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: formData.email.trim(),
            password: formData.password,
            display_name: formData.display_name.trim(),
          }),
        }
      );

      const data = await response.json();

      if (response.ok) {
        toast.success('First admin user created successfully!');
        // Redirect to login page
        router.push('/login?message=Admin account created successfully. Please log in.');
      } else {
        toast.error(data.error || 'Failed to create admin user');
      }
    } catch (error) {
      console.error('Error creating admin user:', error);
      toast.error('Failed to create admin user');
    } finally {
      setLoading(false);
    }
  };

  const handleSkipSetup = async () => {
    try {
      const response = await fetch(
        `${getApiUrl()}/api/setup/skip`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        toast.success('Setup skipped');
        router.push('/');
      } else {
        toast.error('Failed to skip setup');
      }
    } catch (error) {
      console.error('Error skipping setup:', error);
      toast.error('Failed to skip setup');
    }
  };

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="text-muted-foreground">Checking setup status...</p>
        </div>
      </div>
    );
  }

  if (!needsSetup) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Card className="w-96">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              Setup Complete
            </CardTitle>
            <CardDescription>
              PoseWeaver is already configured and ready to use.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="flex items-center justify-center">
            <div className="flex items-center justify-center w-16 h-16 bg-primary rounded-full mb-4">
              <Feather className="h-8 w-8 text-primary-foreground" />
            </div>
          </div>
          <h1 className="text-3xl font-bold">Welcome to PoseWeaver</h1>
          <p className="text-muted-foreground">
            Let's set up your first administrator account to get started.
          </p>
        </div>

        {/* Setup Alert */}
        <Alert>
          <Shield className="h-4 w-4" />
          <AlertDescription>
            No administrator accounts were found. Create the first admin account to manage your PoseWeaver installation.
          </AlertDescription>
        </Alert>

        {/* Setup Form */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Crown className="h-5 w-5" />
              Create Administrator Account
            </CardTitle>
            <CardDescription>
              This account will have full administrative privileges.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email" className="flex items-center gap-2">
                  <Mail className="h-4 w-4" />
                  Email Address
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="admin@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className={errors.email ? 'border-destructive' : ''}
                />
                {errors.email && (
                  <p className="text-sm text-destructive flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {errors.email}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="display_name" className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Display Name
                </Label>
                <Input
                  id="display_name"
                  type="text"
                  placeholder="Administrator"
                  value={formData.display_name}
                  onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                  className={errors.display_name ? 'border-destructive' : ''}
                />
                {errors.display_name && (
                  <p className="text-sm text-destructive flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {errors.display_name}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="password" className="flex items-center gap-2">
                  <Lock className="h-4 w-4" />
                  Password
                </Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter a secure password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className={errors.password ? 'border-destructive' : ''}
                />
                {errors.password && (
                  <p className="text-sm text-destructive flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {errors.password}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm Password</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  placeholder="Confirm your password"
                  value={formData.confirmPassword}
                  onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                  className={errors.confirmPassword ? 'border-destructive' : ''}
                />
                {errors.confirmPassword && (
                  <p className="text-sm text-destructive flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {errors.confirmPassword}
                  </p>
                )}
              </div>

              <div className="flex flex-col space-y-2 pt-4">
                <Button type="submit" disabled={loading} className="w-full">
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Creating Admin Account...
                    </>
                  ) : (
                    <>
                      <Shield className="h-4 w-4 mr-2" />
                      Create Administrator Account
                    </>
                  )}
                </Button>
                
                {process.env.NODE_ENV === 'development' && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleSkipSetup}
                    className="w-full"
                  >
                    Skip Setup (Development Only)
                  </Button>
                )}
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Security Notice */}
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="text-sm">
            <strong>Security Notice:</strong> This administrator account will have full access to manage users, 
            view analytics, and configure system settings. Keep these credentials secure.
          </AlertDescription>
        </Alert>
      </div>
    </div>
  );
}
