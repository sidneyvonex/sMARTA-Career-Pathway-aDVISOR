const USER_SCOPED_STORAGE_KEYS = [
  'riasec_draft',
]

export function clearUserScopedStorage() {
  USER_SCOPED_STORAGE_KEYS.forEach((key) => localStorage.removeItem(key))
}
