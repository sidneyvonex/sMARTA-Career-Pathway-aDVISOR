const DRAFT_PREFIX = 'riasec_draft:'
const DRAFT_TTL_MS = 7 * 24 * 60 * 60 * 1000
const DRAFT_SCHEMA_VERSION = 1

interface AssessmentDraft {
  version: number
  expires_at: number
  answers: Record<number, number>
}

export function assessmentDraftKey(userId: number) {
  return `${DRAFT_PREFIX}${userId}`
}

export function loadAssessmentDraft(userId: number, now = Date.now()): Record<number, number> {
  const key = assessmentDraftKey(userId)
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return {}
    const draft = JSON.parse(raw) as AssessmentDraft
    if (
      draft.version !== DRAFT_SCHEMA_VERSION ||
      draft.expires_at <= now ||
      !draft.answers ||
      typeof draft.answers !== 'object'
    ) {
      localStorage.removeItem(key)
      return {}
    }
    return draft.answers
  } catch {
    localStorage.removeItem(key)
    return {}
  }
}

export function saveAssessmentDraft(
  userId: number,
  answers: Record<number, number>,
  now = Date.now(),
) {
  const draft: AssessmentDraft = {
    version: DRAFT_SCHEMA_VERSION,
    expires_at: now + DRAFT_TTL_MS,
    answers,
  }
  localStorage.setItem(assessmentDraftKey(userId), JSON.stringify(draft))
}

export function clearAssessmentDraft(userId: number) {
  localStorage.removeItem(assessmentDraftKey(userId))
}

export function clearAllAssessmentDrafts() {
  for (let index = localStorage.length - 1; index >= 0; index -= 1) {
    const key = localStorage.key(index)
    if (key?.startsWith(DRAFT_PREFIX)) localStorage.removeItem(key)
  }
}
