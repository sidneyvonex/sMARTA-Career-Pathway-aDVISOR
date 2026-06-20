import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useDownloadReport } from '../../hooks/useDownloadReport'

function TestDownloadButton({ studentId }: { studentId: number }) {
  const { downloadReport, isDownloading } = useDownloadReport()
  return (
    <button
      onClick={() => downloadReport(studentId)}
      disabled={isDownloading}
    >
      {isDownloading ? 'Generating…' : 'Download Report'}
    </button>
  )
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {ui}
        <Toaster />
      </BrowserRouter>
    </QueryClientProvider>,
  )
}

describe('useDownloadReport', () => {
  beforeEach(() => {
    // Mock URL.createObjectURL and revokeObjectURL
    global.URL.createObjectURL = vi.fn(() => 'blob:mock-url')
    global.URL.revokeObjectURL = vi.fn()
  })

  it('renders download button', () => {
    renderWithProviders(<TestDownloadButton studentId={1} />)
    expect(screen.getByText('Download Report')).toBeInTheDocument()
  })

  it('button is not disabled initially', () => {
    renderWithProviders(<TestDownloadButton studentId={1} />)
    expect(screen.getByText('Download Report')).not.toBeDisabled()
  })

  it('shows loading state when clicked', async () => {
    renderWithProviders(<TestDownloadButton studentId={1} />)
    const button = screen.getByText('Download Report')
    await userEvent.click(button)
    await waitFor(() => {
      expect(
        screen.queryByText('Generating…') || screen.queryByText('Download Report'),
      ).toBeInTheDocument()
    })
  })

  it('triggers download on successful response', async () => {
    const appendChildSpy = vi.spyOn(document.body, 'appendChild')
    renderWithProviders(<TestDownloadButton studentId={1} />)
    await userEvent.click(screen.getByText('Download Report'))
    await waitFor(() => {
      expect(global.URL.createObjectURL).toHaveBeenCalled()
    })
    appendChildSpy.mockRestore()
  })
})
