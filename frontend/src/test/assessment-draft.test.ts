import {
  assessmentDraftKey,
  clearAllAssessmentDrafts,
  loadAssessmentDraft,
  saveAssessmentDraft,
} from '../lib/assessmentDraft'

describe('assessment drafts', () => {
  beforeEach(() => localStorage.clear())

  it('scopes saved answers to the signed-in learner', () => {
    saveAssessmentDraft(7, { 1: 4 }, 1_000)
    saveAssessmentDraft(8, { 1: 2 }, 1_000)

    expect(loadAssessmentDraft(7, 2_000)).toEqual({ 1: 4 })
    expect(loadAssessmentDraft(8, 2_000)).toEqual({ 1: 2 })
  })

  it('removes an expired draft instead of restoring stale answers', () => {
    saveAssessmentDraft(7, { 1: 4 }, 1_000)

    expect(loadAssessmentDraft(7, 8 * 24 * 60 * 60 * 1000)).toEqual({})
    expect(localStorage.getItem(assessmentDraftKey(7))).toBeNull()
  })

  it('clears every learner draft without removing unrelated preferences', () => {
    saveAssessmentDraft(7, { 1: 4 })
    saveAssessmentDraft(8, { 1: 2 })
    localStorage.setItem('theme-preference', 'dark')

    clearAllAssessmentDrafts()

    expect(localStorage.getItem(assessmentDraftKey(7))).toBeNull()
    expect(localStorage.getItem(assessmentDraftKey(8))).toBeNull()
    expect(localStorage.getItem('theme-preference')).toBe('dark')
  })
})
