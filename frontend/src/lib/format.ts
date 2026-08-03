export function initials(firstName: string, lastName: string) {
  return `${firstName?.[0] ?? ''}${lastName?.[0] ?? ''}`.toUpperCase()
}

export function isNewStudent(lastActive: string | null): boolean {
  if (!lastActive) return false
  return Date.now() - new Date(lastActive).getTime() < 14 * 24 * 60 * 60 * 1000
}

export function formatRelativeTime(iso: string) {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60_000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return formatDate(iso)
}

// Single source of truth for calendar dates across the app.
// Renders "30 Jul 2026" (en-KE) so every surface is consistent and locale-correct
// for Kenya — never the browser-default M/D/YYYY.
export function formatDate(value: string | null | undefined): string {
  if (!value) return ''
  // Date-only strings (YYYY-MM-DD) parse as UTC midnight, which can shift a day
  // in local time; anchor them to local midnight so the calendar date is stable.
  const isDateOnly = /^\d{4}-\d{2}-\d{2}$/.test(value)
  const date = new Date(isDateOnly ? `${value}T00:00:00` : value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleDateString('en-KE', { day: 'numeric', month: 'short', year: 'numeric' })
}

// Kenyan county names are stored lowercase (e.g. "kiambu"); present them
// capitalized everywhere, with the one irregular spelling handled explicitly.
export function formatCounty(county: string | null | undefined): string {
  if (!county) return ''
  if (county === 'muranga') return "Murang'a"
  return county.charAt(0).toUpperCase() + county.slice(1)
}

// Turn a raw enum/token ("junior_school", "verified") into a readable label
// ("Junior school", "Verified"). Underscores become spaces and the first letter
// is capitalized; the rest is left untouched so acronyms (STEM) survive.
export function humanize(token: string | null | undefined): string {
  if (!token) return ''
  const spaced = token.replace(/_/g, ' ')
  return spaced.charAt(0).toUpperCase() + spaced.slice(1)
}
