import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { AxiosError } from 'axios'
import toast from 'react-hot-toast'

import {
  studentsApi,
  type AcademicGoalCreate,
  type AcademicGoalUpdate,
} from '../api/students'


export const academicGoalKeys = {
  all: ['students', 'academic-goals'] as const,
}


function goalErrorMessage(error: unknown): string {
  const axiosError = error as AxiosError<{ message?: unknown }>
  if (!axiosError.response) {
    return 'Connection error. Please check your internet.'
  }
  const status = axiosError.response.status
  if (status === 403) return "You don't have permission to do that."
  if (status === 404) return 'That item no longer exists.'
  if (status >= 500) return 'Server error. Please try again in a moment.'
  const message = axiosError.response.data?.message
  const flatten = (value: unknown): string[] => {
    if (typeof value === 'string' && value.trim()) return [value.trim()]
    if (Array.isArray(value)) return value.flatMap(flatten)
    if (value && typeof value === 'object') {
      return Object.values(value).flatMap(flatten)
    }
    return []
  }
  const details = flatten(message)
  return details.length > 0
    ? details.join(' ')
    : 'Something went wrong. Please try again.'
}


async function withGoalToast<T>(
  loadingMessage: string,
  successMessage: string,
  operation: () => Promise<T>,
): Promise<T> {
  const toastId = toast.loading(loadingMessage)
  try {
    const result = await operation()
    toast.success(successMessage, { id: toastId })
    return result
  } catch (error) {
    toast.error(goalErrorMessage(error), { id: toastId })
    throw error
  }
}


export function useAcademicGoalMutations() {
  const queryClient = useQueryClient()
  const refresh = () => queryClient.invalidateQueries({ queryKey: academicGoalKeys.all })

  const create = useMutation({
    mutationFn: (payload: AcademicGoalCreate) => withGoalToast(
      'Creating academic goal…',
      'Academic goal created.',
      () => studentsApi.createAcademicGoal(payload),
    ),
    onSuccess: refresh,
  })
  const update = useMutation({
    mutationFn: ({ goalId, data }: { goalId: number; data: AcademicGoalUpdate }) =>
      withGoalToast(
        'Updating academic goal…',
        'Academic goal updated.',
        () => studentsApi.updateAcademicGoal(goalId, data),
      ),
    onSuccess: refresh,
  })
  const close = useMutation({
    mutationFn: (goalId: number) => withGoalToast(
      'Closing academic goal…',
      'Academic goal closed.',
      () => studentsApi.closeAcademicGoal(goalId),
    ),
    onSuccess: refresh,
  })
  const confirmAchievement = useMutation({
    mutationFn: (goalId: number) => withGoalToast(
      'Confirming achievement…',
      'Academic goal achieved.',
      () => studentsApi.confirmAcademicGoalAchievement(goalId),
    ),
    onSuccess: refresh,
  })

  return { create, update, close, confirmAchievement }
}
