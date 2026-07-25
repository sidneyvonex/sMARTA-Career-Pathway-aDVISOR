import { render } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { CompassIcon, LightbulbIcon, NetworkIcon, RoadmapIcon } from '../components/landing/icons'

describe('landing icons', () => {
  it('renders all four icons as svg elements', () => {
    const { container } = render(
      <>
        <CompassIcon />
        <LightbulbIcon />
        <NetworkIcon />
        <RoadmapIcon />
      </>
    )
    expect(container.querySelectorAll('svg')).toHaveLength(4)
  })

  it('applies a passed className to the svg', () => {
    const { container } = render(<CompassIcon className="landing-hero__icon" />)
    expect(container.querySelector('svg')).toHaveClass('landing-hero__icon')
  })
})
