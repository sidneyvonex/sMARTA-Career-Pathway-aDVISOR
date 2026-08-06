import { describe, expect, it } from 'vitest'

import { devMailApi } from '../api/devMail'

describe('devMailApi', () => {
  it('lists captured letters newest-first', async () => {
    const res = await devMailApi.list()
    expect(res.data.error).toBeNull()
    expect(res.data.data[0].subject).toBe('Verify your CBC Guidance account')
  })

  it('fetches a single letter with its body', async () => {
    const res = await devMailApi.get(2)
    expect(res.data.data.body).toContain('/verify-email?token=')
  })

  it('clears the inbox', async () => {
    const res = await devMailApi.clear()
    expect(res.data.data.deleted).toBeGreaterThanOrEqual(0)
  })
})
