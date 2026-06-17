export function greeting(firstName: string) {
  const h = new Date().getHours()
  if (h < 12) return `Good morning, ${firstName}`
  if (h < 17) return `Good afternoon, ${firstName}`
  return `Good evening, ${firstName}`
}

export function todayLabel() {
  return new Date().toLocaleDateString('en-KE', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  })
}
