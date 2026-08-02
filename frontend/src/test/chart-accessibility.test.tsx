import { render, screen } from '@testing-library/react'
import GradeTrend from '../components/dashboard/student/lively/GradeTrend'
import PersonalityRadar from '../components/dashboard/student/lively/PersonalityRadar'

describe('dashboard chart text alternatives', () => {
  it('renders raw per-subject chronology without averaging ordinal levels', () => {
    render(
      <GradeTrend
        data={[
          {
            subject: 'Mathematics',
            records: [
              { period: '2026 Term 1', level: 'ME2' },
              { period: '2026 Term 2', level: 'EE2' },
            ],
          },
          {
            subject: 'English',
            records: [{ period: '2026 Term 2', level: 'AE1' }],
          },
        ]}
      />,
    )

    expect(screen.getByRole('region', { name: /academic evidence chronology/i })).toBeInTheDocument()
    expect(screen.getByText('Mathematics')).toBeInTheDocument()
    expect(screen.getByText('English')).toBeInTheDocument()
    expect(screen.getByText('2026 Term 1 · ME2')).toBeInTheDocument()
    expect(screen.getByText('2026 Term 2 · EE2')).toBeInTheDocument()
    expect(screen.getByText('2026 Term 2 · AE1')).toBeInTheDocument()
    expect(screen.queryByText(/average level|\/ 8|points/i)).not.toBeInTheDocument()
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
