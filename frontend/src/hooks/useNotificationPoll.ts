import { useRef, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { notificationsApi } from '../api/notifications'
import { useNotificationStore } from '../store/notificationStore'
import { useAuthStore } from '../store/authStore'

export function useNotificationPoll() {
  const { isAuthenticated } = useAuthStore()
  const { setUnreadCount } = useNotificationStore()
  const prevCountRef = useRef<number | undefined>(undefined)

  const { data } = useQuery({
    queryKey: ['notification-unread-count'],
    queryFn: () =>
      notificationsApi.getUnreadCount().then((r) => r.data.data.count),
    refetchInterval: isAuthenticated ? 60_000 : false,
    enabled: isAuthenticated,
  })

  useEffect(() => {
    if (data === undefined) return
    if (prevCountRef.current !== undefined && data > prevCountRef.current) {
      toast.success('You have new notifications.')
    }
    prevCountRef.current = data
    setUnreadCount(data)
  }, [data, setUnreadCount])
}
