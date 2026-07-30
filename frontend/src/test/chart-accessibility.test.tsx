import { render, screen } from '@testing-library/react'
import GradeTrend from '../components/dashboard/student/lively/GradeTrend'
import PersonalityRadar from '../components/dashboard/student/lively/PersonalityRadar'

describe('dashboard chart text alternatives', () => {
  it('describes every academic trend point without requiring the graphic', () => {
    render(
      <GradeTrend
        data={[
          { term: '2026 Term 1', points: 5 },
          { term: '2026 Term 2', points: 7 },
        ]}
      />,
    )

    expect(
      screen.getByRole('img', {
        name: /academic trend: 2026 term 1, ME2; 2026 term 2, EE2/i,
      }),
    ).toBeInTheDocument()
  })

  it('describes every RIASEC dimension and score without requiring the graphic', () => {
    render(
      <PersonalityRadar
        data={[
          { label: 'Realistic', value: 18 },
          { label: 'Investigative', value: 22 },
        ]}
      />,
    )

    expect(
      screen.getByRole('img', {
        name: /RIASEC interest profile: Realistic, score 18; Investigative, score 22/i,
      }),
    ).toBeInTheDocument()
  })
})
