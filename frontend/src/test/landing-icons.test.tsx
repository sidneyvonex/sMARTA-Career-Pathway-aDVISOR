import { render } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { CompassIcon, LightbulbIcon, NetworkIcon, RoadmapIcon, CheckIcon, ArrowRightIcon } from '../components/landing/icons'

describe('landing icons', () => {
  it('renders all six icons as svg elements', () => {
    const { container } = render(
      <>
        <CompassIcon />
        <LightbulbIcon />
        <NetworkIcon />
        <RoadmapIcon />
        <CheckIcon />
        <ArrowRightIcon />
      </>
    )
    expect(container.querySelectorAll('svg')).toHaveLength(6)
  })

  it('applies a passed className to the svg', () => {
    const { container } = render(<CompassIcon className="landing-hero__icon" />)
    expect(container.querySelector('svg')).toHaveClass('landing-hero__icon')
  })
})
