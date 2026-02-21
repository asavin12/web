import { useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/api/client';

export interface Notification {
  id: number;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
  time_ago?: string;
  url?: string;
  sender?: {
    id: number;
    username: string;
    avatar?: string;
  };
  icon?: string;
  color?: string;
}

interface NotificationsResponse {
  results: Notification[];
  count: number;
  unread_count: number;
}

export function useNotifications() {
  const queryClient = useQueryClient();

  // Fetch notifications
  const { data, isLoading, refetch } = useQuery<NotificationsResponse>({
    queryKey: ['notifications'],
    queryFn: async () => {
      const response = await api.get('/accounts/notifications/');
      return response.data;
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const notifications = data?.results || [];
  const unreadCount = data?.unread_count || 0;

  // Mark single notification as read
  const markAsReadMutation = useMutation({
    mutationFn: async (notificationId: number) => {
      await api.post(`/accounts/notifications/${notificationId}/mark-read/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  // Mark all notifications as read
  const markAllReadMutation = useMutation({
    mutationFn: async () => {
      await api.post('/accounts/notifications/mark-all-read/');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  const markAsRead = useCallback((notificationId: number) => {
    markAsReadMutation.mutate(notificationId);
  }, [markAsReadMutation]);

  const markAllRead = useCallback(() => {
    markAllReadMutation.mutate();
  }, [markAllReadMutation]);

  return {
    notifications,
    unreadCount,
    isLoading,
    markAsRead,
    markAllRead,
    refetch,
  };
}

export default useNotifications;
