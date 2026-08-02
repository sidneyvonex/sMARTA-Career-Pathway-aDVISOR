import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { AxiosError } from 'axios'
import toast from 'react-hot-toast'

import {
  tertiaryApi,
  type EducationGoalWrite,
} from '../api/tertiary'


export const educationGoalKeys = {
  all: ['students', 'education-goals'] as const,
}


function errorMessage(error: unknown): string {
  const axiosError = error as AxiosError<{ message?: unknown }>
  if (!axiosError.response) return 'Connection error. Please check your internet.'
  if (axiosError.response.status === 403) return "You don't have permission to do that."
  if (axiosError.response.status === 404) return 'That item no longer exists.'
  if (axiosError.response.status >= 500) return 'Server error. Please try again in a moment.'
  const message = axiosError.response.data?.message
  if (typeof message !== 'string') return 'Something went wrong. Please try again.'
  const clean = message.trim()
  if (!clean || /ErrorDetail\s*\(/.test(clean) || /^[{[]/.test(clean)) {
    return 'Something went wrong. Please try again.'
  }
  return clean
}


async function withToast<T>(loading: string, success: string, operation: () => Promise<T>) {
  const toastId = toast.loading(loading)
  try {
    const result = await operation()
    toast.success(success, { id: toastId })
    return result
  } catch (error) {
    toast.error(errorMessage(error), { id: toastId })
    throw error
  }
}


export function useEducationGoalMutations() {
  const queryClient = useQueryClient()
  const refresh = () => queryClient.invalidateQueries({ queryKey: educationGoalKeys.all })
  const create = useMutation({
    mutationFn: (payload: EducationGoalWrite) => withToast(
      'Saving education goal…', 'Education goal saved.',
      () => tertiaryApi.createEducationGoal(payload),
    ),
    onSuccess: refresh,
  })
  const update = useMutation({
    mutationFn: ({ goalId, data }: { goalId: number; data: Partial<EducationGoalWrite> }) =>
      withToast(
        'Updating education goal…', 'Education goal updated.',
        () => tertiaryApi.updateEducationGoal(goalId, data),
      ),
    onSuccess: refresh,
  })
  const remove = useMutation({
    mutationFn: (goalId: number) => withToast(
      'Removing education goal…', 'Education goal removed.',
      () => tertiaryApi.deleteEducationGoal(goalId),
    ),
    onSuccess: refresh,
  })
  return { create, update, remove }
}
