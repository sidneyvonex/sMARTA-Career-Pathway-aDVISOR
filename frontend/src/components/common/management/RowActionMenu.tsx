import { useEffect, useMemo, useRef, useState } from 'react'
import type { ManagementAction } from './types'

interface RowActionMenuProps {
  recordLabel: string
  actions: ManagementAction[]
  disabled?: boolean
}

export default function RowActionMenu({
  recordLabel,
  actions,
  disabled = false,
}: RowActionMenuProps) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const orderedActions = useMemo(
    () => [...actions].sort((left, right) => Number(left.tone === 'danger') - Number(right.tone === 'danger')),
    [actions],
  )

  useEffect(() => {
    if (!open) return undefined

    const closeFromOutside = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false)
    }
    const closeFromKeyboard = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return
      event.preventDefault()
      setOpen(false)
      window.requestAnimationFrame(() => triggerRef.current?.focus())
    }

    document.addEventListener('pointerdown', closeFromOutside)
    document.addEventListener('keydown', closeFromKeyboard)
    return () => {
      document.removeEventListener('pointerdown', closeFromOutside)
      document.removeEventListener('keydown', closeFromKeyboard)
    }
  }, [open])

  return (
    <div className="management-row-menu" ref={rootRef}>
      <button
        ref={triggerRef}
        type="button"
        className="management-row-menu__trigger"
        aria-label={`More actions for ${recordLabel}`}
        aria-haspopup="menu"
        aria-expanded={open}
        disabled={disabled || actions.length === 0}
        onClick={() => setOpen(current => !current)}
      >
        <span aria-hidden="true">•••</span>
      </button>

      {open && (
        <div className="management-row-menu__menu" role="menu">
          {orderedActions.map(action => (
            <button
              key={action.id}
              type="button"
              role="menuitem"
              className={action.tone === 'danger' ? 'management-row-menu__item management-row-menu__item--danger' : 'management-row-menu__item'}
              disabled={action.disabled}
              onClick={() => {
                action.onSelect()
                setOpen(false)
              }}
            >
              {action.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
