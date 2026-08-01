import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, screen } from '@testing-library/react'
import { HttpResponse, delay, http } from 'msw'
import { PropsWithChildren } from 'react'
import { Toaster } from 'react-hot-toast'
import { describe, expect, it } from 'vitest'

import { studentsApi } from '../api/students'
import { useAcademicGoalMutations } from '../hooks/useAcademicGoalMutations'
import { academicGoalFixture } from './msw/handlers'
import { server } from './msw/server'


const payload = {
  continuity_code: 'MTH',
  target_level: 'ME1' as const,
  target_term: 3 as const,
  target_year: 2026,
  target_academic_grade: 10 as const,
  action_plan: 'Practise twice each week.',
}


function wrapper({ children }: PropsWithChildren) {
  const queryClient = new QueryClient({
    defaultOptions: { mutations: { retry: false }, queries: { retry: false } },
  })
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster />
    </QueryClientProvider>
  )
}


describe('academic goal API', () => {
  it('supports typed learner CRUD and explicit achievement confirmation', async () => {
    const listed = await studentsApi.getAcademicGoals()
    const created = await studentsApi.createAcademicGoal(payload)
    const updated = await studentsApi.updateAcademicGoal(created.data.data.id, {
      action_plan: 'Attend weekly support sessions.',
    })
    const confirmed = await studentsApi.confirmAcademicGoalAchievement(
      created.data.data.id,
    )
    const closed = await studentsApi.closeAcademicGoal(8)

    expect(listed.data.data[0].current_level).toEqual({
      code: 'ME2',
      rank: 5,
      framework: { code: 'CBC-SENIOR-SCHOOL', version: 'pilot-2026' },
    })
    expect(created.data.data.target_level.code).toBe('ME1')
    expect(updated.data.data.action_plan).toBe('Attend weekly support sessions.')
    expect(confirmed.data.data.status).toBe('achieved')
    expect(confirmed.data.data.ready_for_achievement).toBe(true)
    expect(confirmed.data.data.achievement_evidence_snapshot?.evidence_id).toBe(21)
    expect(closed.data.data.status).toBe('closed')
    expect(closed.data.data.current_level.code).toBe('ME2')

    await expect(
      studentsApi.closeAcademicGoal(created.data.data.id),
    ).rejects.toMatchObject({ response: { status: 409 } })
  })

  it('shows loading and success toasts for goal mutations', async () => {
    server.use(
      http.post('/api/v1/students/academic-goals/', async () => {
        await delay(80)
        return HttpResponse.json({
          data: academicGoalFixture({ action_plan: payload.action_plan }),
          error: null,
          message: 'Academic goal created.',
        }, { status: 201 })
      }),
    )
    const { result } = renderHook(() => useAcademicGoalMutations(), { wrapper })

    let mutation: Promise<unknown>
    act(() => {
      mutation = result.current.create.mutateAsync(payload)
    })
    expect(await screen.findByText('Creating academic goal…')).toBeInTheDocument()
    await act(async () => mutation)

    expect(await screen.findByText('Academic goal created.')).toBeInTheDocument()
  })

  it('replaces the loading toast with the standard server-error message', async () => {
    server.use(
      http.post('/api/v1/students/academic-goals/', () => HttpResponse.json(
        { data: null, error: true, message: 'Internal detail.' },
        { status: 500 },
      )),
    )
    const { result } = renderHook(() => useAcademicGoalMutations(), { wrapper })

    await act(async () => {
      await expect(result.current.create.mutateAsync(payload)).rejects.toBeTruthy()
    })

    expect(await screen.findByText(
      'Server error. Please try again in a moment.',
    )).toBeInTheDocument()
  })

  it('replaces the close loading toast with an invalid-transition API error', async () => {
    server.use(
      http.delete('/api/v1/students/academic-goals/7/', async () => {
        await delay(80)
        return HttpResponse.json(
          {
            data: null,
            error: true,
            message: 'Only an active academic goal can be closed.',
          },
          { status: 409 },
        )
      }),
    )
    const { result } = renderHook(() => useAcademicGoalMutations(), { wrapper })

    let mutation: Promise<unknown>
    act(() => {
      mutation = result.current.close.mutateAsync(7)
    })
    expect(await screen.findByText('Closing academic goal…')).toBeInTheDocument()
    await act(async () => {
      await expect(mutation).rejects.toBeTruthy()
    })

    expect(screen.queryByText('Closing academic goal…')).not.toBeInTheDocument()
    expect(await screen.findByText(
      'Only an active academic goal can be closed.',
    )).toBeInTheDocument()
  })
})
