import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ProfileForm from '../components/students/ProfileForm'
import PhotoUpload from '../components/students/PhotoUpload'
import SubjectList from '../components/students/SubjectList'
import GradeHistory from '../components/students/GradeHistory'

const makeClient = () => new QueryClient({ defaultOptions: { queries: { retry: false } } })

const Wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={makeClient()}>
    <BrowserRouter>{children}</BrowserRouter>
  </QueryClientProvider>
)

const mockProfile = {
  id: 1, email: 'jane@test.com', first_name: 'Jane', last_name: 'Doe',
  county: 'kiambu', grade: 9 as const, mode: 'self_guided' as const,
  bio: 'Hello', date_of_birth: null, career_interests: '', photo_url: null,
}

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
      { id: 10, subject: { id: 1, name: 'Mathematics', code: 'MTH9', grade: 9 as const, category: 'Core' as const }, created_at: '' },
    ]
    render(<SubjectList enrolledSubjects={subjects} onRemove={() => {}} />, { wrapper: Wrapper })
    expect(screen.getByText('Mathematics')).toBeInTheDocument()
  })

  it('renders a remove button per subject', () => {
    const subjects = [
      { id: 10, subject: { id: 1, name: 'Mathematics', code: 'MTH9', grade: 9 as const, category: 'Core' as const }, created_at: '' },
    ]
    render(<SubjectList enrolledSubjects={subjects} onRemove={() => {}} />, { wrapper: Wrapper })
    expect(screen.getByRole('button', { name: /remove/i })).toBeInTheDocument()
  })
})

describe('GradeHistory', () => {
  it('renders grade rows', () => {
    const grades = [
      { id: 20, term: 1 as const, year: 2026, level: 'ME1' as const, created_at: '', updated_at: '' },
    ]
    render(<GradeHistory grades={grades} />, { wrapper: Wrapper })
    expect(screen.getByText('Term 1')).toBeInTheDocument()
    expect(screen.getByText('2026')).toBeInTheDocument()
    expect(screen.getByText(/meeting expectation/i)).toBeInTheDocument()
  })

  it('shows empty state when no grades', () => {
    render(<GradeHistory grades={[]} />, { wrapper: Wrapper })
    expect(screen.getByText(/no grades/i)).toBeInTheDocument()
  })
})
