'use client';

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { 
  User, 
  Mail, 
  Calendar, 
  Crown, 
  Shield, 
  Activity, 
  Users, 
  RefreshCw,
  Save,
  Trash2,
  AlertTriangle
} from 'lucide-react';
import { toast } from 'sonner';
import { getApiUrl } from '@/utils/api-utils';

interface UserDetails {
  id: string;
  email: string;
  display_name: string;
  bio?: string;
  avatar_url?: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  updated_at: string;
  subscription_status: string;
  subscription_tier: string;
  subscription_expires_at?: string;
  poses_generated: number;
  pose_generation_limit: number;
  extra_poses: number;
  pose_generations_reset_date?: string;
  stripe_customer_id?: string;
  characters: Array<{
    id: string;
    name: string;
    created_at: string;
  }>;
  character_count: number;
  character_limit: number;
}

interface UserDetailModalProps {
  userId: string | null;
  isOpen: boolean;
  onClose: () => void;
  onUserUpdated: () => void;
}

export function UserDetailModal({ userId, isOpen, onClose, onUserUpdated }: UserDetailModalProps) {
  const [user, setUser] = useState<UserDetails | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    display_name: '',
    bio: '',
    is_active: true,
    is_admin: false,
    subscription_status: 'free',
    extra_pose_generations: 0,
  });

  // Fetch user details when modal opens
  useEffect(() => {
    if (isOpen && userId) {
      fetchUserDetails();
    }
  }, [isOpen, userId]);

  const fetchUserDetails = async () => {
    if (!userId) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${getApiUrl()}/api/admin/users/${userId}`,
        {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
        setFormData({
          display_name: data.user.display_name || '',
          bio: data.user.bio || '',
          is_active: data.user.is_active,
          is_admin: data.user.is_admin,
          subscription_status: data.user.subscription_status,
          extra_pose_generations: data.user.extra_pose_generations,
        });
      } else {
        toast.error('Failed to fetch user details');
      }
    } catch (error) {
      console.error('Error fetching user details:', error);
      toast.error('Failed to fetch user details');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!userId || !user) return;
    
    setSaving(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${getApiUrl()}/api/admin/users/${userId}/update`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
          },
          body: JSON.stringify({
            display_name: formData.display_name,
            bio: formData.bio,
            is_admin: formData.is_admin,
            subscription_status: formData.subscription_status,
            extra_pose_generations: formData.extra_pose_generations,
            is_active: formData.is_active,
          }),
        }
      );

      if (response.ok) {
        toast.success('User updated successfully');
        onUserUpdated();
        fetchUserDetails(); // Refresh user data
      } else {
        const error = await response.json();
        toast.error(error.error || 'Failed to update user');
      }
    } catch (error) {
      console.error('Error updating user:', error);
      toast.error('Failed to update user');
    } finally {
      setSaving(false);
    }
  };

  const handleResetUsage = async () => {
    if (!userId) return;
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${getApiUrl()}/api/admin/users/${userId}/update`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
          },
          body: JSON.stringify({ reset_usage: true }),
        }
      );

      if (response.ok) {
        toast.success('Usage reset successfully');
        fetchUserDetails(); // Refresh user data
      } else {
        toast.error('Failed to reset usage');
      }
    } catch (error) {
      console.error('Error resetting usage:', error);
      toast.error('Failed to reset usage');
    }
  };

  const handleDeleteUser = async () => {
    if (!userId || !user) return;
    
    const confirmed = window.confirm(
      `Are you sure you want to delete user "${user.display_name}" (${user.email})? This action cannot be undone and will delete all associated data.`
    );
    
    if (!confirmed) return;
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${getApiUrl()}/api/admin/users/${userId}/delete`,
        {
          method: 'DELETE',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
          },
        }
      );

      if (response.ok) {
        toast.success('User deleted successfully');
        onUserUpdated();
        onClose();
      } else {
        const error = await response.json();
        toast.error(error.error || 'Failed to delete user');
      }
    } catch (error) {
      console.error('Error deleting user:', error);
      toast.error('Failed to delete user');
    }
  };

  const getSubscriptionBadge = (status: string) => {
    // Handle undefined or null status
    if (!status) {
      status = 'free';
    }
    
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      free: 'outline',
      basic: 'secondary',
      pro: 'default',
      premium: 'default',
      expired: 'destructive',
    };

    return (
      <Badge variant={variants[status] || 'outline'}>
        {status === 'pro' && <Crown className="h-3 w-3 mr-1" />}
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            User Details
          </DialogTitle>
          <DialogDescription>
            View and manage user account information and settings
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : user ? (
          <div className="space-y-6">
            {/* User Overview */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Mail className="h-4 w-4" />
                    Account Information
                  </span>
                  <div className="flex items-center gap-2">
                    {user.is_admin && (
                      <Badge variant="secondary">
                        <Shield className="h-3 w-3 mr-1" />
                        Admin
                      </Badge>
                    )}
                    {getSubscriptionBadge(user.subscription_tier || user.subscription_status)}
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="email">Email</Label>
                    <Input id="email" value={user.email} disabled />
                  </div>
                  <div>
                    <Label htmlFor="display_name">Display Name</Label>
                    <Input
                      id="display_name"
                      value={formData.display_name}
                      onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                    />
                  </div>
                </div>
                
                <div>
                  <Label htmlFor="bio">Bio</Label>
                  <Input
                    id="bio"
                    value={formData.bio}
                    onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                    placeholder="User bio..."
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Created</Label>
                    <p className="text-sm text-muted-foreground">
                      {formatDate(user.created_at)}
                    </p>
                  </div>
                  <div>
                    <Label>Last Updated</Label>
                    <p className="text-sm text-muted-foreground">
                      {formatDate(user.updated_at)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Account Settings */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-4 w-4" />
                  Account Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Account Status</Label>
                    <p className="text-sm text-muted-foreground">
                      {formData.is_active ? 'Active' : 'Inactive'}
                    </p>
                  </div>
                  <Switch
                    checked={formData.is_active}
                    onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Administrator</Label>
                    <p className="text-sm text-muted-foreground">
                      Grant admin privileges
                    </p>
                  </div>
                  <Switch
                    checked={formData.is_admin}
                    onCheckedChange={(checked) => setFormData({ ...formData, is_admin: checked })}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="subscription">Subscription Status</Label>
                    <Select
                      value={formData.subscription_status}
                      onValueChange={(value) => setFormData({ ...formData, subscription_status: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="free">Free</SelectItem>
                        <SelectItem value="basic">Basic</SelectItem>
                        <SelectItem value="pro">Pro</SelectItem>
                        <SelectItem value="premium">Premium (Legacy)</SelectItem>
                        <SelectItem value="expired">Expired</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="extra_generations">Extra Generations</Label>
                    <Input
                      id="extra_generations"
                      type="number"
                      min="0"
                      value={formData.extra_pose_generations}
                      onChange={(e) => setFormData({ ...formData, extra_pose_generations: parseInt(e.target.value) || 0 })}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Usage Statistics */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Activity className="h-4 w-4" />
                    Usage Statistics
                  </span>
                  <Button variant="outline" size="sm" onClick={handleResetUsage}>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Reset Usage
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Pose Generations</Label>
                    <p className="text-2xl font-bold">
                      {user.poses_generated} / {user.pose_generation_limit}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      +{user.extra_poses} extra available
                    </p>
                  </div>
                  <div>
                    <Label>Characters</Label>
                    <p className="text-2xl font-bold">
                      {user.character_count} / {user.character_limit === -1 ? '∞' : user.character_limit}
                    </p>
                  </div>
                </div>

                {user.pose_generations_reset_date && (
                  <div className="mt-4">
                    <Label>Usage Reset Date</Label>
                    <p className="text-sm text-muted-foreground">
                      {formatDate(user.pose_generations_reset_date)}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Characters */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  Characters ({user.characters.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                {user.characters.length > 0 ? (
                  <div className="space-y-2">
                    {user.characters.map((character) => (
                      <div key={character.id} className="flex items-center justify-between p-2 border rounded">
                        <div>
                          <p className="font-medium">{character.name}</p>
                          <p className="text-sm text-muted-foreground">
                            Created {formatDate(character.created_at)}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground">No characters created</p>
                )}
              </CardContent>
            </Card>

            <Separator />

            {/* Action Buttons */}
            <div className="flex items-center justify-between">
              <Button
                variant="destructive"
                onClick={handleDeleteUser}
                className="flex items-center gap-2"
              >
                <Trash2 className="h-4 w-4" />
                Delete User
              </Button>

              <div className="flex items-center gap-2">
                <Button variant="outline" onClick={onClose}>
                  Cancel
                </Button>
                <Button onClick={handleSave} disabled={saving}>
                  {saving ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4 mr-2" />
                      Save Changes
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center py-8">
            <p className="text-muted-foreground">User not found</p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
