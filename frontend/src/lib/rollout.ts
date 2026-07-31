export const ROLLOUT_COUNTIES = [
  { value: 'kiambu', label: 'Kiambu' },
  { value: 'muranga', label: "Murang'a" },
  { value: 'nyeri', label: 'Nyeri' },
  { value: 'kirinyaga', label: 'Kirinyaga' },
  { value: 'nyandarua', label: 'Nyandarua' },
] as const

export const ALL_ROLLOUT_COUNTIES = [
  { value: '', label: 'All rollout counties' },
  ...ROLLOUT_COUNTIES,
]

