import { describe, expect, it } from 'vitest'
import { studentsApi } from '../api/students'

describe('students progress API', () => {
  it('uses the explainable progress endpoint with its advisory contract', async () => {
    const response = await studentsApi.getProgress()

    expect(response.data.data).toEqual({
      subjects: [],
      overall: {
        status: 'insufficient_evidence',
        label: 'Insufficient evidence',
        subject_continuity_codes: [],
      },
      advisory_disclaimer: 'Academic progress is advisory only. It does not determine official CBE placement or admission.',
    })
  })
})
