import { Component, type ErrorInfo, type ReactNode } from 'react'
import ErrorState from './dashboard/ErrorState'

interface Props {
  children: ReactNode
  scope?: 'application' | 'route'
  resetKey?: string
}

interface State {
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    if (import.meta.env.DEV) {
      console.error('[Smarta Shauri] Unexpected frontend error', {
        error,
        componentStack: info.componentStack ?? '',
      })
    }
  }

  componentDidUpdate(previousProps: Props) {
    if (this.state.error && previousProps.resetKey !== this.props.resetKey) {
      this.setState({ error: null })
    }
  }

  private reset = () => {
    this.setState({ error: null })
  }

  render() {
    if (!this.state.error) return this.props.children

    const applicationFailure = this.props.scope === 'application'
    return (
      <div className={`error-boundary error-boundary--${applicationFailure ? 'application' : 'route'}`}>
        <ErrorState
          title={applicationFailure ? 'Smarta Shauri could not continue' : 'This page could not continue'}
          description={applicationFailure
            ? 'Reload the application. Your saved account information has not been changed.'
            : 'Try this page again. If the problem continues, return to your dashboard.'}
          onRetry={applicationFailure ? () => window.location.reload() : this.reset}
          actionLabel={applicationFailure ? 'Reload application' : 'Try this page again'}
          secondaryAction={{ label: 'Return to dashboard', to: '/' }}
        />
      </div>
    )
  }
}
