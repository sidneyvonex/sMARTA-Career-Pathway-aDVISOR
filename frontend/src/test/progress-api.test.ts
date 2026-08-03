import { describe, expect, it } from 'vitest'
import { studentsApi } from '../api/students'

describe('students progress API', () => {
  it('uses the explainable progress endpoint with its advisory contract', async () => {
    const response = await studentsApi.getProgress()

    expect(response.data.data).toEqual({
      subjects: [
        {
          continuity_code: 'MTH',
          subject_name: 'Mathematics',
          status: 'on_track',
          label: 'On track',
          rule_code: 'otherwise_me_on_track',
          explanation: 'The available academic evidence is meeting expectation.',
          suggested_action: 'Continue practising and record the next available evidence.',
          evidence_confidence: 'learner_entered',
          records_used: [],
          evidence: [],
          decision_inputs: {
            latest_framework: { code: 'CBC-SENIOR-SCHOOL', version: 'v1' },
            me2_rank: 5,
          },
        },
      ],
      overall: {
        status: 'on_track',
        label: 'On track',
        subject_continuity_codes: ['MTH'],
      },
      advisory_disclaimer: 'Academic progress is advisory only. It does not determine official CBE placement or admission.',
    })
  })
})
