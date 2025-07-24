'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { 
  Users, 
  Search, 
  Filter, 
  ChevronLeft, 
  ChevronRight, 
  Settings, 
  Shield, 
  Activity,
  TrendingUp,
  UserCheck,
  Crown,
  Database,
  Cpu,
  RefreshCw,
  RotateCcw,
  Download,
  FileText,
  User,
  DollarSign, 
  BarChart3,
  UserPlus,
  AlertCircle,
  CheckCircle,
  XCircle,
  MoreHorizontal,
  Plus,
  Minus,
  ArrowLeft,
  ArrowRight
} from 'lucide-react';
import { toast } from 'sonner';
import { useRouter } from 'next/navigation';
import { UserDetailModal } from '@/components/admin/user-detail-modal';
import { getApiUrl } from '@/utils/api-utils';

interface User {
  id: string;
  email: string;
  display_name: string;
  subscription_status: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  pose_generations_used: number;
  pose_generation_limit: number;
  extra_pose_generations: number;
  character_count?: number;
  stripe_customer_id?: string;
}

interface Analytics {
  users: {
    total: number;
    active: number;
    recent_signups: number;
  };
  subscriptions: {
    free: number;
    basic: number;
    pro: number;
    premium: number;
  };
  content: {
    total_characters: number;
  };
  usage: {
    total_pose_generations: number;
    total_extra_generations: number;
  };
}

export default function AdminDashboard() {
  const { user } = useAuth();
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [systemData, setSystemData] = useState<any>(null);
  const [systemLogs, setSystemLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [subscriptionFilter, setSubscriptionFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [showUserModal, setShowUserModal] = useState(false);

  // Check admin access
  useEffect(() => {
    if (user && !user.is_admin) {
      toast.error('Admin access required');
      router.push('/dashboard');
      return;
    }
  }, [user, router]);

  // Fetch system data
  const fetchSystemData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${getApiUrl()}/api/admin/system/stats`,
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
        console.log('System data received:', data); // Debug log
        setSystemData(data);
      } else {
        toast.error('Failed to fetch system data');
      }
    } catch (error) {
      console.error('Error fetching system data:', error);
      toast.error('Failed to fetch system data');
    }
  };

  // Fetch system logs
  const fetchSystemLogs = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${getApiUrl()}/api/admin/system/logs`,
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
        setSystemLogs(data.logs);
      } else {
        toast.error('Failed to fetch system logs');
      }
    } catch (error) {
      console.error('Error fetching system logs:', error);
      toast.error('Failed to fetch system logs');
    }
  };

  // System maintenance actions
  const performSystemCleanup = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${getApiUrl()}/api/admin/system/maintenance/cleanup`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        toast.success(data.message);
        // Refresh system data after cleanup
        fetchSystemData();
      } else {
        const error = await response.json();
        toast.error(error.error || 'Failed to perform system cleanup');
      }
    } catch (error) {
      console.error('Error performing system cleanup:', error);
      toast.error('Failed to perform system cleanup');
    }
  };

  const resetAllUsage = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${getApiUrl()}/api/admin/system/maintenance/reset-usage`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        toast.success(data.message);
        // Refresh analytics and system data
        fetchAnalytics();
        fetchSystemData();
      } else {
        const error = await response.json();
        toast.error(error.error || 'Failed to reset usage statistics');
      }
    } catch (error) {
      console.error('Error resetting usage statistics:', error);
      toast.error('Failed to reset usage statistics');
    }
  };

  // Fetch analytics data
  const fetchAnalytics = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${getApiUrl()}/api/admin/analytics/overview`,
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
        setAnalytics(data.analytics);
      } else {
        toast.error('Failed to fetch analytics');
      }
    } catch (error) {
      console.error('Error fetching analytics:', error);
      toast.error('Failed to fetch analytics');
    }
  };

  // Fetch users data
  const fetchUsers = async () => {
    try {
      const params = new URLSearchParams({
        page: currentPage.toString(),
        limit: '20',
        ...(searchTerm && { search: searchTerm }),
        ...(subscriptionFilter && subscriptionFilter !== 'all' && { subscription: subscriptionFilter }),
        ...(statusFilter && statusFilter !== 'all' && { status: statusFilter }),
      });

      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${getApiUrl()}/api/admin/users?${params}`,
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
        setUsers(data.users);
        setTotalPages(data.pagination.pages);
      } else {
        toast.error('Failed to fetch users');
      }
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('Failed to fetch users');
    }
  };

  // Initial data load
  useEffect(() => {
    const loadData = async () => {
      await Promise.all([
        fetchUsers(),
        fetchAnalytics(),
        fetchSystemData(),
        fetchSystemLogs()
      ]);
      setLoading(false);
    };

    loadData();
  }, [user, currentPage]);

  // Refetch users when filters change
  useEffect(() => {
    if (user?.is_admin) {
      fetchUsers();
    }
  }, [searchTerm, subscriptionFilter, statusFilter]);

  const handleUserClick = (userId: string) => {
    setSelectedUserId(userId);
    setShowUserModal(true);
  };

  const handleCloseUserModal = () => {
    setShowUserModal(false);
    setSelectedUserId(null);
  };

  const handleUserUpdated = () => {
    fetchUsers(); // Refresh the user list
    fetchAnalytics(); // Refresh analytics
  };

  const getSubscriptionBadge = (status: string) => {
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

  const getStatusIcon = (isActive: boolean) => {
    return isActive ? (
      <CheckCircle className="h-4 w-4 text-green-500" />
    ) : (
      <XCircle className="h-4 w-4 text-red-500" />
    );
  };

  if (!user?.is_admin) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="w-96">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Access Denied
            </CardTitle>
            <CardDescription>
              You need administrator privileges to access this page.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Admin Dashboard</h1>
          <p className="text-muted-foreground">
            Manage users, view analytics, and monitor system health
          </p>
        </div>
        <Badge variant="secondary" className="flex items-center gap-2">
          <Shield className="h-4 w-4" />
          Administrator
        </Badge>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="users">User Management</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {analytics && (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Users</CardTitle>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{analytics.users.total}</div>
                  <p className="text-xs text-muted-foreground">
                    {analytics.users.active} active users
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Paid Subscribers</CardTitle>
                  <Crown className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {analytics.subscriptions.basic + analytics.subscriptions.pro + analytics.subscriptions.premium}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {Math.round(((analytics.subscriptions.basic + analytics.subscriptions.pro + analytics.subscriptions.premium) / analytics.users.total) * 100)}% conversion rate
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Characters</CardTitle>
                  <UserPlus className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{analytics.content.total_characters}</div>
                  <p className="text-xs text-muted-foreground">
                    {(analytics.content.total_characters / analytics.users.total).toFixed(1)} avg per user
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Pose Generations</CardTitle>
                  <Activity className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{analytics.usage.total_pose_generations}</div>
                  <p className="text-xs text-muted-foreground">
                    +{analytics.usage.total_extra_generations} extra purchased
                  </p>
                </CardContent>
              </Card>
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>New user signups in the last 30 days</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {analytics?.users.recent_signups || 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  New users this month
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>System Health</CardTitle>
                <CardDescription>Current system status</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm">Database</span>
                  <div className="flex items-center gap-1">
                    <div className={`w-2 h-2 rounded-full ${
                      systemData?.health?.database_connected ? 'bg-green-500' : 'bg-red-500'
                    }`} />
                    <span className="text-sm font-medium">
                      {systemData?.health?.database_connected ? 'Connected' : 'Disconnected'}
                    </span>
                  </div>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Memory Usage</span>
                  <span className="text-sm font-medium">
                    {systemData?.health?.memory_usage_percent || 0}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">CPU Usage</span>
                  <span className="text-sm font-medium">
                    {systemData?.health?.cpu_usage_percent || 0}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Active Users</span>
                  <span className="text-sm font-medium">
                    {systemData?.activity?.users_active_1h || 0}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Subscription Distribution</CardTitle>
                <CardDescription>Current subscription tiers</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {analytics && (
                  <>
                    <div className="flex justify-between">
                      <span className="text-sm">Free</span>
                      <span className="text-sm font-medium">{analytics.subscriptions.free}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Basic</span>
                      <span className="text-sm font-medium">{analytics.subscriptions.basic}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Pro</span>
                      <span className="text-sm font-medium">{analytics.subscriptions.pro}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Premium (Legacy)</span>
                      <span className="text-sm font-medium">{analytics.subscriptions.premium}</span>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Quick Actions Section */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
              <CardDescription>
                Common administrative tasks and system operations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Button 
                  onClick={performSystemCleanup}
                  variant="outline" 
                  className="flex items-center gap-2 h-auto p-4"
                >
                  <RefreshCw className="h-4 w-4" />
                  <div className="text-left">
                    <div className="font-medium">System Cleanup</div>
                    <div className="text-sm text-muted-foreground">Remove inactive data</div>
                  </div>
                </Button>
                <Button 
                  onClick={resetAllUsage}
                  variant="outline" 
                  className="flex items-center gap-2 h-auto p-4"
                >
                  <RotateCcw className="h-4 w-4" />
                  <div className="text-left">
                    <div className="font-medium">Reset All Usage</div>
                    <div className="text-sm text-muted-foreground">Reset pose limits</div>
                  </div>
                </Button>
                <Button 
                  onClick={fetchSystemLogs}
                  variant="outline" 
                  className="flex items-center gap-2 h-auto p-4"
                >
                  <FileText className="h-4 w-4" />
                  <div className="text-left">
                    <div className="font-medium">Refresh Logs</div>
                    <div className="text-sm text-muted-foreground">Update system logs</div>
                  </div>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Recent System Events */}
          <Card>
            <CardHeader>
              <CardTitle>Recent System Events</CardTitle>
              <CardDescription>
                Latest system activities and important events
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {systemLogs && systemLogs.length > 0 ? (
                  systemLogs.slice(0, 5).map((log, index) => (
                    <div key={index} className="flex items-center gap-2 p-2 rounded-md bg-muted/50">
                      <div className={`w-2 h-2 rounded-full ${
                        log.level === 'ERROR' ? 'bg-red-500' :
                        log.level === 'WARNING' ? 'bg-yellow-500' :
                        'bg-green-500'
                      }`} />
                      <span className="text-xs text-muted-foreground">{log.timestamp}</span>
                      <span className="text-xs font-medium">[{log.component}]</span>
                      <span className="text-sm flex-1 truncate">{log.message}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-muted-foreground py-4">
                    No recent system events
                  </div>
                )}
              </div>
              {systemLogs && systemLogs.length > 5 && (
                <div className="pt-2 border-t">
                  <p className="text-xs text-muted-foreground text-center">
                    Showing 5 of {systemLogs.length} recent events. View all in System tab.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="users" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>User Management</CardTitle>
              <CardDescription>
                Search, filter, and manage user accounts
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4 mb-6">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search users by email or name..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-8"
                    />
                  </div>
                </div>
                <Select value={subscriptionFilter} onValueChange={setSubscriptionFilter}>
                  <SelectTrigger className="w-40">
                    <SelectValue placeholder="Subscription" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Plans</SelectItem>
                    <SelectItem value="free">Free</SelectItem>
                    <SelectItem value="basic">Basic</SelectItem>
                    <SelectItem value="pro">Pro</SelectItem>
                    <SelectItem value="premium">Premium</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-32">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-4">
                {users.map((user) => (
                  <Card key={user.id} className="p-4 cursor-pointer hover:bg-muted/50 transition-colors" onClick={() => handleUserClick(user.id)}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(user.is_active)}
                          {user.is_admin && <Shield className="h-4 w-4 text-blue-500" />}
                        </div>
                        <div>
                          <p className="font-medium">{user.display_name}</p>
                          <p className="text-sm text-muted-foreground">{user.email}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-4">
                        {getSubscriptionBadge(user.subscription_status)}
                        <div className="text-right text-sm">
                          <p>{user.pose_generations_used}/{user.pose_generation_limit} poses</p>
                          <p className="text-muted-foreground">{user.character_count} characters</p>
                        </div>
                        <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); handleUserClick(user.id); }}>
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>

              {totalPages > 1 && (
                <div className="flex justify-center space-x-2 mt-6">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                  >
                    Previous
                  </Button>
                  <span className="flex items-center px-3 text-sm">
                    Page {currentPage} of {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                  >
                    Next
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Analytics Dashboard
              </CardTitle>
              <CardDescription>
                Detailed analytics and growth metrics
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Advanced analytics charts and metrics will be displayed here.
                This section can include user growth trends, revenue analytics,
                feature usage patterns, and more detailed insights.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="system" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* System Health Cards */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Database Status</CardTitle>
                <Database className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {systemData?.health?.database_connected ? 'Connected' : 'Disconnected'}
                </div>
                <p className="text-xs text-muted-foreground">
                  Response: {systemData?.health?.database_response_time || 'N/A'}ms
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
                <Cpu className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {systemData?.health?.memory_usage_percent || 0}%
                </div>
                <p className="text-xs text-muted-foreground">
                  {systemData?.health?.memory_used || 'N/A'} / {systemData?.health?.memory_total || 'N/A'}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {systemData?.health?.cpu_usage_percent || 0}%
                </div>
                <p className="text-xs text-muted-foreground">
                  {systemData?.health?.cpu_cores || 'N/A'} cores
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Users</CardTitle>
                <User className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {systemData?.activity?.users_active_1h || 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  Last hour
                </p>
              </CardContent>
            </Card>
          </div>

          {/* System Actions */}
          <Card>
            <CardHeader>
              <CardTitle>System Maintenance</CardTitle>
              <CardDescription>
                Perform system maintenance tasks and operations
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Button 
                  onClick={performSystemCleanup}
                  variant="outline" 
                  className="flex items-center gap-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  System Cleanup
                </Button>
                <Button 
                  onClick={resetAllUsage}
                  variant="outline" 
                  className="flex items-center gap-2"
                >
                  <RotateCcw className="h-4 w-4" />
                  Reset All Usage
                </Button>
                <Button variant="outline" className="flex items-center gap-2">
                  <Download className="h-4 w-4" />
                  Export Data
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Database Statistics */}
          <Card>
            <CardHeader>
              <CardTitle>Database Statistics</CardTitle>
              <CardDescription>
                Current database collection statistics and health metrics
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Users Collection:</span>
                    <span className="text-sm">{systemData?.database?.users || 0} documents</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Characters Collection:</span>
                    <span className="text-sm">{systemData?.database?.characters || 0} documents</span>
                  </div>
                  <Separator />
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Database Size:</span>
                    <span className="text-sm">{systemData?.health?.disk_usage || 'N/A'}</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">New Users (24h):</span>
                    <span className="text-sm">{systemData?.activity?.users_created_24h || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">New Characters (24h):</span>
                    <span className="text-sm">{systemData?.activity?.characters_created_24h || 0}</span>
                  </div>
                  <Separator />
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">System Uptime:</span>
                    <span className="text-sm">{systemData?.health?.uptime || 'N/A'}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* System Logs */}
          <Card>
            <CardHeader>
              <CardTitle>Recent System Logs</CardTitle>
              <CardDescription>
                Latest system events and monitoring information
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {systemLogs && systemLogs.length > 0 ? (
                  systemLogs.map((log, index) => (
                    <div key={index} className="flex items-center gap-2 p-2 rounded-md bg-muted/50">
                      <div className={`w-2 h-2 rounded-full ${
                        log.level === 'ERROR' ? 'bg-red-500' :
                        log.level === 'WARNING' ? 'bg-yellow-500' :
                        'bg-green-500'
                      }`} />
                      <span className="text-xs text-muted-foreground">{log.timestamp}</span>
                      <span className="text-xs font-medium">[{log.component}]</span>
                      <span className="text-sm">{log.message}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-muted-foreground py-4">
                    No recent logs available
                  </div>
                )}
              </div>
              <div className="pt-4">
                <Button 
                  variant="outline" 
                  className="w-full flex items-center gap-2"
                  onClick={fetchSystemLogs}
                >
                  <FileText className="h-4 w-4" />
                  Refresh Logs
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* User Detail Modal */}
      <UserDetailModal
        userId={selectedUserId}
        isOpen={showUserModal}
        onClose={handleCloseUserModal}
        onUserUpdated={handleUserUpdated}
      />
    </div>
  );
}
