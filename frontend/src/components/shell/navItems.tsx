import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../../store/authStore'
import { dashboardApi } from '../../api/dashboard'
import type { User } from '../../api/auth'
import { isFeatureEnabled } from '../../lib/featureFlags'

export interface NavItem {
  to: string
  label: string
  /** Shorter label for the compact phone bottom navigation. */
  short?: string
  icon: React.ReactNode
  badge?: string
}

export const NAV_ICONS = {
  grid: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true"><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></svg>,
  bar: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" d="M3 12h3m0 0V6m0 6v6m4-6h3m0 0V9m0 3v3m4-3h3m0 0V3m0 9v9" /></svg>,
  clock: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true"><circle cx="12" cy="12" r="9" /><path strokeLinecap="round" d="M12 7v5l3 3" /></svg>,
  clipboard: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>,
  person: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true"><circle cx="12" cy="8" r="4" /><path strokeLinecap="round" d="M4 20c0-4 3.6-7 8-7s8 3 8 7" /></svg>,
  users: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true"><path strokeLinecap="round" d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><path strokeLinecap="round" d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" /></svg>,
  note: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>,
  school: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" d="M3 21V9l9-6 9 6v12H3z" /></svg>,
  log: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" /></svg>,
}

export function getBaseNavItems(role: User['role']): NavItem[] {
  if (role === 'student') {
    const gradesItem = isFeatureEnabled('academic_progress_v1')
      ? { to: '/grades', label: 'My Progress', short: 'Progress', icon: NAV_ICONS.bar }
      : { to: '/grades', label: 'My Grades', short: 'Grades', icon: NAV_ICONS.bar }
    return [
      { to: '/', label: 'Dashboard', short: 'Home', icon: NAV_ICONS.grid },
      gradesItem,
      ...(isFeatureEnabled('academic_progress_v1')
        ? [{ to: '/education-goals', label: 'Education Goals', short: 'Goals', icon: NAV_ICONS.school }]
        : []),
      { to: '/explore', label: 'Explore Choices', short: 'Explore', icon: NAV_ICONS.grid },
      { to: '/compare', label: 'Compare Choices', short: 'Compare', icon: NAV_ICONS.clipboard },
      { to: '/plan', label: 'My Plan', short: 'Plan', icon: NAV_ICONS.note },
      { to: '/access', label: 'Parent Access', short: 'Access', icon: NAV_ICONS.users },
      { to: '/assessment/results', label: 'Career Profile', short: 'Career', icon: NAV_ICONS.clock },
      { to: '/assessment', label: 'Career Quiz', short: 'Quiz', icon: NAV_ICONS.clipboard },
      { to: '/profile', label: 'My Profile', short: 'Profile', icon: NAV_ICONS.person },
    ]
  }
  if (role === 'counselor') {
    return [
      { to: '/', label: 'Home', icon: NAV_ICONS.grid },
      { to: '/counselor/students', label: 'My Students', short: 'Students', icon: NAV_ICONS.users },
      { to: '/counselor/notes', label: 'Notes', icon: NAV_ICONS.note },
    ]
  }
  if (role === 'school_admin') {
    return [
      { to: '/', label: 'Dashboard', icon: NAV_ICONS.grid },
      { to: '/admin/students', label: 'Learners', icon: NAV_ICONS.users },
      { to: '/admin/counselors', label: 'Counsellors', short: 'Team', icon: NAV_ICONS.users },
      { to: '/admin/offerings', label: 'Offerings', icon: NAV_ICONS.clipboard },
      { to: '/admin/school', label: 'School profile', short: 'School', icon: NAV_ICONS.school },
    ]
  }
  if (role === 'system_admin') {
    return [
      { to: '/', label: 'Dashboard', short: 'Home', icon: NAV_ICONS.grid },
      { to: '/system-admin/schools', label: 'Schools', icon: NAV_ICONS.school },
      { to: '/system-admin/users', label: 'Users', icon: NAV_ICONS.users },
      { to: '/system-admin/catalogue', label: 'Catalogue', icon: NAV_ICONS.clipboard },
      { to: '/system-admin/audit-log', label: 'Audit Log', short: 'Audit', icon: NAV_ICONS.log },
    ]
  }
  if (role === 'parent') {
    return [
      { to: '/', label: 'Dashboard', short: 'Home', icon: NAV_ICONS.grid },
    ]
  }
  return [{ to: '/', label: 'Home', icon: NAV_ICONS.grid }]
}

const MOBILE_PRIMARY_PATHS: Partial<Record<User['role'], string[]>> = {
  student: ['/', '/grades', '/explore', '/plan'],
  counselor: ['/', '/counselor/students', '/counselor/notes'],
  school_admin: ['/', '/admin/students', '/admin/offerings', '/admin/counselors'],
  system_admin: ['/', '/system-admin/schools', '/system-admin/catalogue', '/system-admin/users'],
}

export function getMobilePrimaryItems(
  role: User['role'],
  baseNavItems: NavItem[],
  learnerNavItems: NavItem[],
): NavItem[] {
  if (role === 'parent') {
    return [...baseNavItems.slice(0, 1), ...learnerNavItems.slice(0, 1)]
  }

  const paths = MOBILE_PRIMARY_PATHS[role]
  if (!paths) return baseNavItems.slice(0, 4)

  return paths
    .map((path) => baseNavItems.find((item) => item.to === path))
    .filter((item): item is NavItem => Boolean(item))
}

/**
 * Nav items for the current user. Parents also get one item per approved
 * learner, sourced from the shared (cached) parent-children query.
 */
export function useNavItems(): { baseNavItems: NavItem[]; learnerNavItems: NavItem[] } {
  const { user } = useAuthStore()

  const parentChildrenQ = useQuery({
    queryKey: ['parent-children'],
    queryFn: () => dashboardApi.getParentChildren().then((response) => response.data.data),
    enabled: user?.role === 'parent',
  })

  const baseNavItems = user ? getBaseNavItems(user.role) : []
  const learnerNavItems: NavItem[] = user?.role === 'parent'
    ? (parentChildrenQ.data ?? []).map((child) => ({
        to: `/parent/child/${child.id}`,
        label: `${child.first_name} ${child.last_name}`,
        short: child.first_name,
        icon: NAV_ICONS.person,
        badge: `Grade ${child.grade}`,
      }))
    : []

  return { baseNavItems, learnerNavItems }
}
