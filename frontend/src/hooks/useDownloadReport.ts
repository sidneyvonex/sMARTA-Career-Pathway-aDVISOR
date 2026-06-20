import { useState, useCallback } from 'react'
import toast from 'react-hot-toast'
import { reportsApi } from '../api/reports'

export function useDownloadReport() {
  const [downloadingId, setDownloadingId] = useState<number | null>(null)

  const downloadReport = useCallback(async (studentId: number) => {
    setDownloadingId(studentId)
    const toastId = toast.loading('Generating report…')

    try {
      const response = await reportsApi.downloadStudentPdf(studentId)
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = URL.createObjectURL(blob)

      const link = document.createElement('a')
      link.href = url
      link.download = `smarta-shauri-report.pdf`

      const disposition = response.headers['content-disposition']
      if (disposition) {
        const match = disposition.match(/filename="?(.+?)"?$/)
        if (match) link.download = match[1]
      }

      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      toast.success('Report downloaded.', { id: toastId })
    } catch (err: any) {
      let message = 'Failed to generate report.'
      if (err.response?.data instanceof Blob) {
        try {
          const text = await err.response.data.text()
          const json = JSON.parse(text)
          if (typeof json.message === 'string') message = json.message
        } catch {
          // blob parse failed, use default message
        }
      } else if (typeof err.response?.data?.message === 'string') {
        message = err.response.data.message
      }
      toast.error(message, { id: toastId })
    } finally {
      setDownloadingId(null)
    }
  }, [])

  return { downloadReport, downloadingId }
}
