import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, screen } from '@testing-library/react'
import { PropsWithChildren } from 'react'
import { Toaster } from 'react-hot-toast'
import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'

import { tertiaryApi } from '../api/tertiary'
import { useEducationGoalMutations } from '../hooks/useEducationGoalMutations'
import { server } from './msw/server'


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


describe('tertiary exploration API', () => {
  it('provides typed catalogue reads and learner education-goal CRUD', async () => {
    const institutions = await tertiaryApi.getInstitutions({ search: 'Nairobi' })
    const programmes = await tertiaryApi.getProgrammes({ institution: 1 })
    const detail = await tertiaryApi.getProgramme(10)
    const listed = await tertiaryApi.getEducationGoals()
    const created = await tertiaryApi.createEducationGoal({
      institution: 1, programme: 10, kind: 'primary', priority: 1,
    })
    const updated = await tertiaryApi.updateEducationGoal(created.data.data.id, {
      institution: 1, programme: null, kind: 'primary', priority: 1,
    })
    const removed = await tertiaryApi.deleteEducationGoal(created.data.data.id)

    expect(institutions.data.data[0].source_scope).toBe('kuccps-2025')
    expect(programmes.data.data[0].institution.id).toBe(1)
    expect(detail.data.data.historical_admission_references[0].reference_only).toBe(true)
    expect(listed.data.data[0].kind).toBe('alternative')
    expect(updated.data.data.programme).toBeNull()
    expect(removed.data.message).toBe('Education goal removed.')
  })

  it('models omitted programmes, PATCH fields, and catalogue filters faithfully', async () => {
    const omitted = await tertiaryApi.createEducationGoal({
      institution: 1, kind: 'primary', priority: 1,
    })
    const patched = await tertiaryApi.updateEducationGoal(omitted.data.data.id, {
      institution: 2, programme: null, kind: 'alternative', priority: 2,
    })
    const noInstitutions = await tertiaryApi.getInstitutions({ county: 'Mombasa' })
    const noProgrammes = await tertiaryApi.getProgrammes({ framework: 'CBE' })

    expect(omitted.data.data.programme).toBeNull()
    expect(patched.data.data.institution.id).toBe(2)
    expect(patched.data.data.kind).toBe('alternative')
    expect(patched.data.data.priority).toBe(2)
    expect(noInstitutions.data.data).toEqual([])
    expect(noProgrammes.data.data).toEqual([])
  })

  it('shows loading and success toasts for education-goal mutations', async () => {
    const { result } = renderHook(() => useEducationGoalMutations(), { wrapper })
    let mutation: Promise<unknown>
    act(() => {
      mutation = result.current.create.mutateAsync({
        institution: 1, programme: null, kind: 'primary', priority: 1,
      })
    })
    expect(await screen.findByText('Saving education goal…')).toBeInTheDocument()
    await act(async () => mutation)
    expect(await screen.findByText('Education goal saved.')).toBeInTheDocument()
  })

  it('never displays raw serializer dictionaries or ErrorDetail text in a toast', async () => {
    server.use(http.post('/api/v1/students/education-goals/', () => HttpResponse.json({
      data: null,
      error: true,
      message: "{'programme': [ErrorDetail(string='Invalid programme.', code='invalid')]}",
    }, { status: 400 })))
    const { result } = renderHook(() => useEducationGoalMutations(), { wrapper })

    await act(async () => {
      await expect(result.current.create.mutateAsync({
        institution: 1, programme: 10, kind: 'primary', priority: 1,
      })).rejects.toBeDefined()
    })

    expect(await screen.findByText('Something went wrong. Please try again.')).toBeInTheDocument()
    expect(screen.queryByText(/ErrorDetail/)).not.toBeInTheDocument()
  })
})
