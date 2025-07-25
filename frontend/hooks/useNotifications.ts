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
  const { user } = useAuth()
  const [state, setState] = useState<NotificationState>({
    notifications: [],
    unreadCount: 0,
    loading: false,
    error: null
  })

  const getAuthHeaders = useCallback(() => {
    const token = localStorage.getItem('access_token')
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  }, [])

  const fetchNotifications = useCallback(async (limit = 50, unreadOnly = false) => {
    if (!user?._id) return

    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
        unread_only: unreadOnly.toString()
      })

      const response = await fetch(
        `${getApiUrl()}/api/notifications?${params}`,
        {
          method: 'GET',
          headers: getAuthHeaders(),
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
  }, [user?._id, getAuthHeaders])

  const fetchUnreadCount = useCallback(async () => {
    if (!user?._id) return

    try {
      const response = await fetch(
        `${getApiUrl()}/api/notifications/unread-count`,
        {
          method: 'GET',
          headers: getAuthHeaders(),
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
  }, [user?._id, getAuthHeaders])

  const markAsRead = useCallback(async (notificationId: string) => {
    if (!user?._id) return false

    try {
      const response = await fetch(
        `${getApiUrl()}/api/notifications/${notificationId}/read`,
        {
          method: 'POST',
          headers: getAuthHeaders(),
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
  }, [user?._id, getAuthHeaders])

  const markAllAsRead = useCallback(async () => {
    if (!user?._id) return false

    try {
      const response = await fetch(
        `${getApiUrl()}/api/notifications/read-all`,
        {
          method: 'POST',
          headers: getAuthHeaders(),
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
  }, [user?._id, getAuthHeaders])

  const deleteNotification = useCallback(async (notificationId: string) => {
    if (!user?._id) return false

    try {
      const response = await fetch(
        `${getApiUrl()}/api/notifications/${notificationId}`,
        {
          method: 'DELETE',
          headers: getAuthHeaders(),
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
  }, [user?._id, getAuthHeaders])

  const clearAllNotifications = useCallback(async () => {
    if (!user?._id) return false

    try {
      const response = await fetch(
        `${getApiUrl()}/api/notifications/clear-all`,
        {
          method: 'DELETE',
          headers: getAuthHeaders(),
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
  }, [user?._id, getAuthHeaders])

  // Auto-fetch notifications and unread count when user changes
  useEffect(() => {
    if (user?._id) {
      fetchNotifications()
      fetchUnreadCount()
    }
  }, [user?._id, fetchNotifications, fetchUnreadCount])

  // Refresh unread count periodically (every 30 seconds)
  useEffect(() => {
    if (!user?._id) return

    const interval = setInterval(() => {
      fetchUnreadCount()
    }, 30000) // 30 seconds

    return () => clearInterval(interval)
  }, [user?._id, fetchUnreadCount])

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
