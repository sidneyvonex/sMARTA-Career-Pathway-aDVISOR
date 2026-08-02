export type FeatureFlag = 'academic_progress_v1'


const ENV_KEYS: Record<FeatureFlag, keyof ImportMetaEnv> = {
  academic_progress_v1: 'VITE_ACADEMIC_PROGRESS_V1',
}


export function isFeatureEnabled(flag: FeatureFlag): boolean {
  return import.meta.env[ENV_KEYS[flag]] === 'true'
}
