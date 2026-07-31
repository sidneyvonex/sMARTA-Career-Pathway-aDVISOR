import { useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { studentsApi } from '../../api/students'
import Avatar from '../common/Avatar'

interface Props {
  photoUrl: string | null
  fallbackName?: string
  onUploaded: (url: string) => void
}

export default function PhotoUpload({ photoUrl, fallbackName = 'Student', onUploaded }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [preview, setPreview] = useState<string | null>(photoUrl)

  const uploadMutation = useMutation({
    mutationFn: (file: File) => studentsApi.uploadPhoto(file),
    onSuccess: (response) => {
      const url = response.data.data.photo_url
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

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) uploadMutation.mutate(file)
  }

  return (
    <div className="photo-upload">
      <div className="photo-upload__preview">
        {preview ? (
          <img src={preview} alt={`${fallbackName} profile`} />
        ) : (
          <Avatar seed={fallbackName} size={120} shape="squircle" />
        )}
        <span className="photo-upload__status" aria-hidden="true">✓</span>
      </div>

      <div className="photo-upload__actions">
        <label htmlFor="photo-input" className="student-action student-action--secondary">
          {uploadMutation.isPending ? 'Uploading…' : 'Choose photo'}
        </label>
        <input
          id="photo-input"
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png"
          onChange={handleFileChange}
          className="sr-only"
          aria-label="Choose photo"
        />

        {preview && (
          <button
            type="button"
            onClick={() => removeMutation.mutate()}
            disabled={removeMutation.isPending}
            className="photo-upload__remove"
          >
            Remove
          </button>
        )}
      </div>
      <small>JPEG or PNG, up to 5MB</small>
    </div>
  )
}
