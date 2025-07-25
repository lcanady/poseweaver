import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { 
  Bell, 
  BellRing, 
  CheckCheck, 
  Trash2, 
  Loader2,
  Settings
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useNotifications } from '@/hooks/useNotifications'
import { NotificationItem } from './notification-item'
import { useToast } from '@/hooks/use-toast'

export const NotificationCenter: React.FC = () => {
  const { 
    notifications, 
    unreadCount, 
    loading, 
    error,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    clearAllNotifications,
    refresh
  } = useNotifications()
  const { toast } = useToast()
  const [isOpen, setIsOpen] = useState(false)

  const handleMarkAsRead = async (notificationId: string) => {
    const success = await markAsRead(notificationId)
    if (success) {
      toast({
        title: "Marked as read",
        description: "Notification marked as read successfully."
      })
    } else {
      toast({
        title: "Error",
        description: "Failed to mark notification as read.",
        variant: "destructive"
      })
    }
  }

  const handleDelete = async (notificationId: string) => {
    const success = await deleteNotification(notificationId)
    if (success) {
      toast({
        title: "Deleted",
        description: "Notification deleted successfully."
      })
    } else {
      toast({
        title: "Error",
        description: "Failed to delete notification.",
        variant: "destructive"
      })
    }
  }

  const handleMarkAllAsRead = async () => {
    const success = await markAllAsRead()
    if (success) {
      toast({
        title: "All marked as read",
        description: "All notifications marked as read successfully."
      })
    } else {
      toast({
        title: "Error",
        description: "Failed to mark all notifications as read.",
        variant: "destructive"
      })
    }
  }

  const handleClearAll = async () => {
    const success = await clearAllNotifications()
    if (success) {
      toast({
        title: "All cleared",
        description: "All notifications cleared successfully."
      })
    } else {
      toast({
        title: "Error",
        description: "Failed to clear all notifications.",
        variant: "destructive"
      })
    }
  }

  const handleRefresh = () => {
    refresh()
    toast({
      title: "Refreshed",
      description: "Notifications refreshed successfully."
    })
  }

  const unreadNotifications = notifications.filter(n => !n.is_read)
  const hasNotifications = notifications.length > 0

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="relative h-9 w-9 p-0"
          title={`${unreadCount} unread notifications`}
        >
          {unreadCount > 0 ? (
            <BellRing className="h-4 w-4" />
          ) : (
            <Bell className="h-4 w-4" />
          )}
          {unreadCount > 0 && (
            <Badge 
              variant="destructive" 
              className="absolute -top-2 -right-2 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs"
            >
              {unreadCount > 99 ? '99+' : unreadCount}
            </Badge>
          )}
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent 
        align="end" 
        className="w-96 p-0"
        sideOffset={8}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border/50">
          <div className="flex items-center gap-2">
            <Bell className="h-4 w-4" />
            <span className="font-semibold">Notifications</span>
            {unreadCount > 0 && (
              <Badge variant="secondary" className="text-xs">
                {unreadCount} new
              </Badge>
            )}
          </div>
          
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              disabled={loading}
              className="h-8 w-8 p-0"
              title="Refresh notifications"
            >
              {loading ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Settings className="h-3 w-3" />
              )}
            </Button>
          </div>
        </div>

        {/* Actions */}
        {hasNotifications && (
          <div className="flex items-center justify-between p-3 bg-muted/30 border-b border-border/50">
            <div className="flex items-center gap-2">
              {unreadCount > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleMarkAllAsRead}
                  className="h-7 text-xs"
                >
                  <CheckCheck className="h-3 w-3 mr-1" />
                  Mark all read
                </Button>
              )}
            </div>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearAll}
              className="h-7 text-xs text-muted-foreground hover:text-destructive"
            >
              <Trash2 className="h-3 w-3 mr-1" />
              Clear all
            </Button>
          </div>
        )}

        {/* Content */}
        <div className="max-h-96">
          {loading && notifications.length === 0 ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
              <span className="text-sm text-muted-foreground">Loading notifications...</span>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center p-8 text-center">
              <Bell className="h-8 w-8 text-muted-foreground mb-2" />
              <p className="text-sm text-muted-foreground mb-2">Failed to load notifications</p>
              <Button variant="outline" size="sm" onClick={handleRefresh}>
                Try again
              </Button>
            </div>
          ) : !hasNotifications ? (
            <div className="flex flex-col items-center justify-center p-8 text-center">
              <Bell className="h-8 w-8 text-muted-foreground mb-2" />
              <p className="text-sm font-medium mb-1">No notifications</p>
              <p className="text-xs text-muted-foreground">You're all caught up!</p>
            </div>
          ) : (
            <ScrollArea className="max-h-96">
              {/* Show unread notifications first */}
              {unreadNotifications.length > 0 && (
                <>
                  {unreadNotifications.map((notification) => (
                    <NotificationItem
                      key={notification.id}
                      notification={notification}
                      onMarkAsRead={handleMarkAsRead}
                      onDelete={handleDelete}
                    />
                  ))}
                  {notifications.filter(n => n.is_read).length > 0 && (
                    <Separator className="my-2" />
                  )}
                </>
              )}
              
              {/* Show read notifications */}
              {notifications.filter(n => n.is_read).map((notification) => (
                <NotificationItem
                  key={notification.id}
                  notification={notification}
                  onMarkAsRead={handleMarkAsRead}
                  onDelete={handleDelete}
                />
              ))}
            </ScrollArea>
          )}
        </div>

        {/* Footer */}
        {hasNotifications && (
          <div className="p-3 border-t border-border/50 bg-muted/20">
            <p className="text-xs text-muted-foreground text-center">
              Showing {notifications.length} recent notifications
            </p>
          </div>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
