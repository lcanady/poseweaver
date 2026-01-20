import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '@/contexts/auth-context'
import { getApiUrl } from '@/utils/api-utils'

export interface Notification {
  id: string
  user_id: string
  type: 'pose_generation_alert' | 'subscription_reminder' | 'feature_announcement' | 'system_notification'
  title: string
  message: string
  data: Record<string, any>
  is_read: boolean
  created_at: string
}

export interface NotificationState {
  notifications: Notification[]
  unreadCount: number
  loading: boolean
  error: string | null
}

export const useNotifications = () => {
  const { user, getToken } = useAuth()
  const [state, setState] = useState<NotificationState>({
    notifications: [],
    unreadCount: 0,
    loading: false,
    error: null
  })

  // We need to resolve getToken async, so getAuthHeaders becomes async 
  // or we call getToken inside the fetch functions.
  // Let's modify fetch calls to get token directly.

  const fetchNotifications = useCallback(async (limit = 50, unreadOnly = false) => {
    if (!user?.uid) return

    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const token = await getToken()
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }

      const params = new URLSearchParams({
        limit: limit.toString(),
        unread_only: unreadOnly.toString()
      })

      const response = await fetch(
        `${getApiUrl()}/api/notifications?${params}`,
        {
          method: 'GET',
          headers,
          credentials: 'include'
        }
      )

      if (!response.ok) {
        throw new Error(`Failed to fetch notifications: ${response.status}`)
      }

      const data = await response.json()

      if (data.success) {
        setState(prev => ({
          ...prev,
          notifications: data.notifications,
          unreadCount: data.unread_count,
          loading: false
        }))
      } else {
        throw new Error(data.error || 'Failed to fetch notifications')
      }
    } catch (error) {
      console.error('Error fetching notifications:', error)
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch notifications'
      }))
    }
  }, [user?.uid, getToken])

  const fetchUnreadCount = useCallback(async () => {
    if (!user?.uid) return

    try {
      const token = await getToken()
      const response = await fetch(
        `${getApiUrl()}/api/notifications/unread-count`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          credentials: 'include'
        }
      )

      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          setState(prev => ({ ...prev, unreadCount: data.unread_count }))
        }
      }
    } catch (error) {
      console.error('Error fetching unread count:', error)
    }
  }, [user?.uid, getToken])

  const markAsRead = useCallback(async (notificationId: string) => {
    if (!user?.uid) return false

    try {
      const token = await getToken()
      const response = await fetch(
        `${getApiUrl()}/api/notifications/${notificationId}/read`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          credentials: 'include'
        }
      )

      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          setState(prev => ({
            ...prev,
            notifications: prev.notifications.map(n =>
              n.id === notificationId ? { ...n, is_read: true } : n
            ),
            unreadCount: data.unread_count
          }))
          return true
        }
      }
      return false
    } catch (error) {
      console.error('Error marking notification as read:', error)
      return false
    }
  }, [user?.uid, getToken])

  const markAllAsRead = useCallback(async () => {
    if (!user?.uid) return false

    try {
      const token = await getToken()
      const response = await fetch(
        `${getApiUrl()}/api/notifications/read-all`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          credentials: 'include'
        }
      )

      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          setState(prev => ({
            ...prev,
            notifications: prev.notifications.map(n => ({ ...n, is_read: true })),
            unreadCount: 0
          }))
          return true
        }
      }
      return false
    } catch (error) {
      console.error('Error marking all notifications as read:', error)
      return false
    }
  }, [user?.uid, getToken])

  const deleteNotification = useCallback(async (notificationId: string) => {
    if (!user?.uid) return false

    try {
      const token = await getToken()
      const response = await fetch(
        `${getApiUrl()}/api/notifications/${notificationId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          credentials: 'include'
        }
      )

      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          setState(prev => ({
            ...prev,
            notifications: prev.notifications.filter(n => n.id !== notificationId),
            unreadCount: data.unread_count
          }))
          return true
        }
      }
      return false
    } catch (error) {
      console.error('Error deleting notification:', error)
      return false
    }
  }, [user?.uid, getToken])

  const clearAllNotifications = useCallback(async () => {
    if (!user?.uid) return false

    try {
      const token = await getToken()
      const response = await fetch(
        `${getApiUrl()}/api/notifications/clear-all`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          credentials: 'include'
        }
      )

      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          setState(prev => ({
            ...prev,
            notifications: [],
            unreadCount: 0
          }))
          return true
        }
      }
      return false
    } catch (error) {
      console.error('Error clearing all notifications:', error)
      return false
    }

  }, [user?.uid, getToken])

  // Auto-fetch notifications and unread count when user changes
  useEffect(() => {
    if (user?.uid) {
      fetchNotifications()
      fetchUnreadCount()
    }
  }, [user?.uid, fetchNotifications, fetchUnreadCount])

  // Refresh unread count periodically (every 30 seconds)
  useEffect(() => {
    if (!user?.uid) return

    const interval = setInterval(() => {
      fetchUnreadCount()
    }, 30000) // 30 seconds

    return () => clearInterval(interval)
  }, [user?.uid, fetchUnreadCount])

  return {
    ...state,
    fetchNotifications,
    fetchUnreadCount,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    clearAllNotifications,
    refresh: fetchNotifications
  }
}
