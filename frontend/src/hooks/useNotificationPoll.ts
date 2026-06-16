import { useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { notificationsApi } from '../api/notifications'
import { useNotificationStore } from '../store/notificationStore'

export function useNotificationPoll() {
  const { setUnreadCount } = useNotificationStore()
  const prevCountRef = useRef<number | undefined>(undefined)

  const { data } = useQuery({
    queryKey: ['notification-unread-count'],
    queryFn: () =>
      notificationsApi.getUnreadCount().then((r) => r.data.data.count),
    refetchInterval: 60_000,
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
