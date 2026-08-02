import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ProfileForm from '../components/students/ProfileForm'
import PhotoUpload from '../components/students/PhotoUpload'
import SubjectList from '../components/students/SubjectList'
import GradeHistory from '../components/students/GradeHistory'
import StudentProfilePage from '../pages/StudentProfilePage'
import {
  GRADE_LEVEL_LABELS,
  GRADE_LEVEL_ORDER,
  GRADE_LEVEL_POINTS,
} from '../api/students'

const makeClient = () => new QueryClient({ defaultOptions: { queries: { retry: false } } })

const Wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={makeClient()}>
    <BrowserRouter>{children}</BrowserRouter>
  </QueryClientProvider>
)

const mockProfile = {
  id: 1, email: 'jane@test.com', first_name: 'Jane', last_name: 'Doe',
  county: 'kiambu', grade: 9 as const, mode: 'self_guided' as const,
  school_membership_status: 'not_applicable' as const,
  bio: 'Hello', date_of_birth: null, career_interests: '', photo_url: null,
  journey_status: '' as const, current_pathway: null, current_pathway_name: null,
  current_subject_combination: '', selection_source: '' as const,
  selection_date: null, selection_verified: false,
}

describe('StudentProfilePage school membership', () => {
  it('shows that a school-code request is awaiting approval', async () => {
    render(<StudentProfilePage />, { wrapper: Wrapper })
    expect(await screen.findAllByText(/school approval pending/i)).toHaveLength(2)
  })
})

describe('CBE grade scale', () => {
  it('orders Level 1 above Level 2 within every performance band', () => {
    expect(GRADE_LEVEL_ORDER).toEqual([
      'EE1', 'EE2', 'ME1', 'ME2', 'AE1', 'AE2', 'BE1', 'BE2',
    ])
    expect(GRADE_LEVEL_POINTS).toEqual({
      EE1: 8,
      EE2: 7,
      ME1: 6,
      ME2: 5,
      AE1: 4,
      AE2: 3,
      BE1: 2,
      BE2: 1,
    })
  })

  it('uses unambiguous level labels', () => {
    expect(GRADE_LEVEL_LABELS.EE1).toBe('Exceeding Expectation - Level 1')
    expect(GRADE_LEVEL_LABELS.EE2).toBe('Exceeding Expectation - Level 2')
    expect(GRADE_LEVEL_LABELS.BE1).toBe('Below Expectation - Level 1')
    expect(GRADE_LEVEL_LABELS.BE2).toBe('Below Expectation - Level 2')
  })
})

describe('ProfileForm', () => {
  it('renders bio, date_of_birth, and career_interests fields', () => {
    render(<ProfileForm profile={mockProfile} onSaved={() => {}} />, { wrapper: Wrapper })
    expect(screen.getByLabelText(/bio/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/date of birth/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/career interests/i)).toBeInTheDocument()
  })

  it('pre-fills fields with existing profile data', () => {
    render(<ProfileForm profile={mockProfile} onSaved={() => {}} />, { wrapper: Wrapper })
    expect(screen.getByLabelText(/bio/i)).toHaveValue('Hello')
  })

  it('shows a save button', () => {
    render(<ProfileForm profile={mockProfile} onSaved={() => {}} />, { wrapper: Wrapper })
    expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument()
  })
})

describe('PhotoUpload', () => {
  it('renders a file input and an upload button', () => {
    render(<PhotoUpload photoUrl={null} onUploaded={() => {}} />, { wrapper: Wrapper })
    expect(screen.getByLabelText(/choose photo/i)).toBeInTheDocument()
  })

  it('shows the existing photo when photo_url is set', () => {
    render(<PhotoUpload photoUrl="https://cdn.example.com/photo.jpg" onUploaded={() => {}} />, { wrapper: Wrapper })
    const img = screen.getByRole('img')
    expect(img).toHaveAttribute('src', 'https://cdn.example.com/photo.jpg')
  })
})

describe('SubjectList', () => {
  it('renders a list of enrolled subjects', () => {
    const subjects = [
      { id: 10, subject: { id: 1, name: 'Mathematics', code: 'MTH9', continuity_code: 'MTH', grade: 9 as const, category: 'Core' as const, is_active: true }, continuity_code: 'MTH', academic_grade: 9 as const, academic_year: 2026, is_active: true, ended_at: null, created_at: '' },
    ]
    render(<SubjectList enrolledSubjects={subjects} onRemove={() => {}} />, { wrapper: Wrapper })
    expect(screen.getByText('Mathematics')).toBeInTheDocument()
  })

  it('renders an archive button per subject', () => {
    const subjects = [
      { id: 10, subject: { id: 1, name: 'Mathematics', code: 'MTH9', continuity_code: 'MTH', grade: 9 as const, category: 'Core' as const, is_active: true }, continuity_code: 'MTH', academic_grade: 9 as const, academic_year: 2026, is_active: true, ended_at: null, created_at: '' },
    ]
    render(<SubjectList enrolledSubjects={subjects} onRemove={() => {}} />, { wrapper: Wrapper })
    expect(screen.getByRole('button', { name: /archive/i })).toBeInTheDocument()
  })

  it('identifies an enrolled subject retired from the current catalogue', () => {
    const subjects = [
      {
        id: 11,
        subject: {
          id: 4,
          name: 'Integrated Science',
          code: 'INT10',
          continuity_code: 'INT',
          grade: 10 as const,
          category: 'Core' as const,
          is_active: false,
        },
        continuity_code: 'INT',
        academic_grade: 10 as const,
        academic_year: 2026,
        is_active: true,
        ended_at: null,
        created_at: '',
      },
    ]
    render(<SubjectList enrolledSubjects={subjects} onRemove={() => {}} />, { wrapper: Wrapper })
    expect(screen.getByText(/retired from the current catalogue/i)).toBeInTheDocument()
  })
})

describe('GradeHistory', () => {
  it('renders grade rows', () => {
    const grades = [
      {
        id: 20,
        term: 1 as const,
        year: 2026,
        level: 'ME1' as const,
        source: 'school' as const,
        verified_by: 4,
        verified_at: '2026-07-30T10:00:00Z',
        created_at: '',
        updated_at: '',
      },
    ]
    render(<GradeHistory grades={grades} />, { wrapper: Wrapper })
    expect(screen.getByText('Term 1')).toBeInTheDocument()
    expect(screen.getByText('2026')).toBeInTheDocument()
    expect(screen.getByText(/meeting expectation/i)).toBeInTheDocument()
    expect(screen.getByText('School entered')).toBeInTheDocument()
    expect(screen.getByText('School verified')).toBeInTheDocument()
  })

  it('distinguishes learner-entered evidence that has not been verified', () => {
    const grades = [
      {
        id: 21,
        term: 2 as const,
        year: 2026,
        level: 'AE1' as const,
        source: 'learner' as const,
        verified_by: null,
        verified_at: null,
        created_at: '',
        updated_at: '',
      },
    ]
    render(<GradeHistory grades={grades} />, { wrapper: Wrapper })
    expect(screen.getByText('Learner entered')).toBeInTheDocument()
    expect(screen.getByText('Not school verified')).toBeInTheDocument()
  })

  it('shows empty state when no grades', () => {
    render(<GradeHistory grades={[]} />, { wrapper: Wrapper })
    expect(screen.getByText(/no grades/i)).toBeInTheDocument()
  })
})
