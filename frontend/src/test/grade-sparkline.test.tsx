import { render } from '@testing-library/react'
import GradeSparkline from '../components/common/GradeSparkline'

describe('GradeSparkline', () => {
  it('renders a step-line svg for two or more records', () => {
    const { container } = render(
      <GradeSparkline records={[{ level: 'ME2' }, { level: 'EE2' }]} />,
    )
    const svg = container.querySelector('svg.grade-sparkline')
    expect(svg).toBeInTheDocument()
    expect(svg?.querySelector('path')).toBeInTheDocument()
    expect(svg?.querySelector('circle')).toBeInTheDocument()
  })

  it('renders nothing for fewer than two records', () => {
    const { container } = render(<GradeSparkline records={[{ level: 'ME2' }]} />)
    expect(container.querySelector('svg')).not.toBeInTheDocument()
  })
})
