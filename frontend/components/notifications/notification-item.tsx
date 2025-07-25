import React from 'react'
import { formatDistanceToNow } from 'date-fns'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Bell, 
  CreditCard, 
  Star, 
  Settings, 
  X, 
  Check,
  AlertTriangle,
  Info
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Notification } from '@/hooks/useNotifications'

interface NotificationItemProps {
  notification: Notification
  onMarkAsRead: (id: string) => void
  onDelete: (id: string) => void
}

const getNotificationIcon = (type: string) => {
  switch (type) {
    case 'pose_generation_alert':
      return <AlertTriangle className="h-4 w-4 text-amber-500" />
    case 'subscription_reminder':
      return <CreditCard className="h-4 w-4 text-blue-500" />
    case 'feature_announcement':
      return <Star className="h-4 w-4 text-purple-500" />
    case 'system_notification':
      return <Info className="h-4 w-4 text-gray-500" />
    default:
      return <Bell className="h-4 w-4 text-gray-500" />
  }
}

const getNotificationTypeLabel = (type: string) => {
  switch (type) {
    case 'pose_generation_alert':
      return 'Usage Alert'
    case 'subscription_reminder':
      return 'Subscription'
    case 'feature_announcement':
      return 'New Feature'
    case 'system_notification':
      return 'System'
    default:
      return 'Notification'
  }
}

const getNotificationVariant = (type: string) => {
  switch (type) {
    case 'pose_generation_alert':
      return 'secondary' as const
    case 'subscription_reminder':
      return 'default' as const
    case 'feature_announcement':
      return 'secondary' as const
    case 'system_notification':
      return 'outline' as const
    default:
      return 'outline' as const
  }
}

export const NotificationItem: React.FC<NotificationItemProps> = ({
  notification,
  onMarkAsRead,
  onDelete
}) => {
  const handleMarkAsRead = (e: React.MouseEvent) => {
    e.stopPropagation()
    onMarkAsRead(notification.id)
  }

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation()
    onDelete(notification.id)
  }

  const createdAt = new Date(notification.created_at)
  const timeAgo = formatDistanceToNow(createdAt, { addSuffix: true })

  return (
    <div
      className={cn(
        "group relative p-4 border-b border-border/50 hover:bg-muted/30 transition-colors",
        !notification.is_read && "bg-muted/20 border-l-4 border-l-primary"
      )}
    >
      {/* Unread indicator */}
      {!notification.is_read && (
        <div className="absolute top-4 right-4">
          <div className="w-2 h-2 bg-primary rounded-full" />
        </div>
      )}

      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="flex-shrink-0 mt-0.5">
          {getNotificationIcon(notification.type)}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0 space-y-2">
          {/* Header */}
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant={getNotificationVariant(notification.type)} className="text-xs">
              {getNotificationTypeLabel(notification.type)}
            </Badge>
            <span className="text-xs text-muted-foreground">{timeAgo}</span>
          </div>

          {/* Title */}
          <h4 className={cn(
            "text-sm font-medium leading-tight",
            !notification.is_read && "font-semibold"
          )}>
            {notification.title}
          </h4>

          {/* Message */}
          <p className="text-sm text-muted-foreground leading-relaxed">
            {notification.message}
          </p>

          {/* Additional data display */}
          {notification.type === 'pose_generation_alert' && notification.data && (
            <div className="text-xs text-muted-foreground bg-muted/50 rounded p-2 mt-2">
              Usage: {notification.data.current_usage}/{notification.data.limit} generations 
              ({notification.data.percentage}%)
            </div>
          )}

          {notification.type === 'subscription_reminder' && notification.data && notification.data.expires_at && (
            <div className="text-xs text-muted-foreground bg-muted/50 rounded p-2 mt-2">
              Status: {notification.data.subscription_status}
              {notification.data.expires_at && (
                <> • Expires: {new Date(notification.data.expires_at).toLocaleDateString()}</>
              )}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex-shrink-0 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          {!notification.is_read && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleMarkAsRead}
              className="h-8 w-8 p-0"
              title="Mark as read"
            >
              <Check className="h-3 w-3" />
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDelete}
            className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive"
            title="Delete notification"
          >
            <X className="h-3 w-3" />
          </Button>
        </div>
      </div>
    </div>
  )
}
