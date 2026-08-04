import type { AxiosResponse } from 'axios'
import { useCallback, useState } from 'react'
import toast from 'react-hot-toast'
import { reportsApi } from '../api/reports'

type ReportFetcher = () => Promise<AxiosResponse<Blob>>
type DownloadKey = number | string

export function useDownloadReport() {
  const [downloadingKey, setDownloadingKey] = useState<DownloadKey | null>(null)

  const downloadReport = useCallback(async (
    fetcher: ReportFetcher,
    fallbackFilename: string,
    key: DownloadKey = 'report',
  ) => {
    setDownloadingKey(key)
    const toastId = toast.loading('Generating report…')

    try {
      const response = await fetcher()
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = fallbackFilename

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
          const body = await err.response.data.text()
          const json = JSON.parse(body)
          if (typeof json.message === 'string') message = json.message
        } catch {
          // Keep the friendly fallback when a blob is not a JSON error envelope.
        }
      } else if (typeof err.response?.data?.message === 'string') {
        message = err.response.data.message
      }
      toast.error(message, { id: toastId })
    } finally {
      setDownloadingKey(null)
    }
  }, [])

  const downloadStudentReport = useCallback((studentId: number) => (
    downloadReport(
      () => reportsApi.downloadStudentPdf(studentId),
      'smarta-shauri-report.pdf',
      studentId,
    )
  ), [downloadReport])

  return {
    downloadReport,
    downloadStudentReport,
    downloadingKey,
    downloadingId: typeof downloadingKey === 'number' ? downloadingKey : null,
  }
}
