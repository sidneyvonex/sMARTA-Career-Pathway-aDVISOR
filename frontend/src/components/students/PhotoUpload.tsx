import { useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { studentsApi } from '../../api/students'

interface Props {
  photoUrl: string | null
  onUploaded: (url: string) => void
}

export default function PhotoUpload({ photoUrl, onUploaded }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [preview, setPreview] = useState<string | null>(photoUrl)

  const uploadMutation = useMutation({
    mutationFn: (file: File) => studentsApi.uploadPhoto(file),
    onSuccess: (res) => {
      const url = res.data.data.photo_url
      setPreview(url)
      onUploaded(url)
      toast.success('Photo updated.')
    },
    onError: () => toast.error('Photo upload failed. Use a JPEG or PNG under 5MB.'),
  })

  const removeMutation = useMutation({
    mutationFn: () => studentsApi.removePhoto(),
    onSuccess: () => {
      setPreview(null)
      onUploaded('')
      toast.success('Photo removed.')
    },
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    uploadMutation.mutate(file)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem' }}>
      {preview ? (
        <img
          src={preview}
          alt="Profile"
          style={{ width: '96px', height: '96px', borderRadius: '50%', objectFit: 'cover', border: '2px solid var(--color-border)' }}
        />
      ) : (
        <div style={{ width: '96px', height: '96px', borderRadius: '50%', background: 'var(--color-background)', border: '2px dashed var(--color-border)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-secondary)' }}>
          No photo
        </div>
      )}

      <label htmlFor="photo-input" style={{ cursor: 'pointer', color: 'var(--color-primary)', fontWeight: 600, fontSize: '0.875rem' }}>
        Choose Photo
      </label>
      <input
        id="photo-input"
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png"
        onChange={handleFileChange}
        style={{ display: 'none' }}
        aria-label="Choose photo"
      />

      {preview && (
        <button
          type="button"
          onClick={() => removeMutation.mutate()}
          disabled={removeMutation.isPending}
          style={{ fontSize: '0.8rem', color: 'var(--color-error)', background: 'none', border: 'none', cursor: 'pointer' }}
        >
          Remove photo
        </button>
      )}
    </div>
  )
}
