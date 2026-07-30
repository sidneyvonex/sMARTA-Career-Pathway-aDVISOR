import { guidanceApi, guidanceKeys } from '../api/guidance'


describe('guidance API client', () => {
  it('uses one guidance query-key namespace', () => {
    const filters = { pathway: 'STEM', county: 'kiambu' }

    expect(guidanceKeys.framework()).toEqual(['guidance', 'framework', 'current'])
    expect(guidanceKeys.pathways()).toEqual(['guidance', 'pathways'])
    expect(guidanceKeys.combinations(filters)).toEqual([
      'guidance',
      'combinations',
      filters,
    ])
    expect(guidanceKeys.combination(42)).toEqual([
      'guidance',
      'combinations',
      'detail',
      42,
    ])
    expect(guidanceKeys.schoolOfferings()).toEqual([
      'guidance',
      'school-offerings',
    ])
  })

  it('loads the current source-dated framework', async () => {
    const response = await guidanceApi.getFramework()

    expect(response.data.data.code).toBe('CBC-SS-PILOT-2026')
    expect(response.data.data.effective_date).toBe('2026-01-01')
    expect(response.data.data.source_url).toMatch(/^https:\/\//)
  })

  it('loads pathways with tracks', async () => {
    const response = await guidanceApi.getPathways()

    expect(response.data.data).toHaveLength(3)
    expect(response.data.data[0].tracks[0].pathway.name).toBeTruthy()
  })

  it('passes combination filters and loads a detail', async () => {
    const list = await guidanceApi.getCombinations({
      pathway: 'STEM',
      county: 'kiambu',
      search: 'science',
    })
    const detail = await guidanceApi.getCombination(list.data.data[0].id)

    expect(list.data.data).toHaveLength(1)
    expect(list.data.data[0].code).toBe('ST1042')
    expect(detail.data.data.subjects).toHaveLength(3)
  })

  it('loads and replaces school offerings with explicit array semantics', async () => {
    const initial = await guidanceApi.getSchoolOfferings()
    const replacement = await guidanceApi.replaceSchoolOfferings([2, 3])

    expect(initial.data.data.combination_ids).toEqual([1])
    expect(replacement.data.data.combination_ids).toEqual([2, 3])
    expect(replacement.data.message).toBe('School offerings updated.')
  })
})
