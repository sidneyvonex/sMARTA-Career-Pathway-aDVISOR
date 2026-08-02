export interface EvidenceProvenance {
  source: 'learner' | 'school'
  verified_school?: unknown | null
  verified_at: string | null
}


export function evidenceOrigin(evidence: EvidenceProvenance): string {
  return evidence.source === 'school' ? 'School entered' : 'Learner entered'
}


export function evidenceVerification(evidence: EvidenceProvenance): string {
  if (evidence.verified_at) {
    const date = new Intl.DateTimeFormat('en-GB', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      timeZone: 'UTC',
    }).format(new Date(evidence.verified_at))
    return `School verified on ${date}`
  }
  if (evidence.verified_school) {
    return 'Verification removed; school provenance retained'
  }
  return 'Not school verified'
}
