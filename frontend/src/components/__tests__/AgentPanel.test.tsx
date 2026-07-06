import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { AgentPanel } from '../AgentPanel'
import { AgentTrace } from '../../hooks/useSSE'

describe('AgentPanel', () => {
  it('shows idle message when state is idle and no traces', () => {
    render(<AgentPanel traces={[]} state="idle" />)
    expect(screen.getByText('Agents ready. Enter a query to begin.')).toBeInTheDocument()
  })

  it('renders agent trace header', () => {
    render(<AgentPanel traces={[]} state="idle" />)
    expect(screen.getByText('agent trace')).toBeInTheDocument()
  })

  it('has aria-live polite on the trace container', () => {
    render(<AgentPanel traces={[]} state="idle" />)
    const log = screen.getByRole('log')
    expect(log).toHaveAttribute('aria-live', 'polite')
    expect(log).toHaveAttribute('aria-label', 'Agent reasoning trace')
  })

  it('renders trace messages grouped by agent', () => {
    const traces: AgentTrace[] = [
      { agent: 'orchestrator', message: 'Parsing query...', timestamp: 1000 },
      { agent: 'location', message: 'Finding centres...', timestamp: 2000 },
    ]
    render(<AgentPanel traces={traces} state="searching" />)
    // Non-newest lines render as plain text spans
    expect(screen.getByText('Parsing query...')).toBeInTheDocument()
    // The newest line uses TypewriterText (char-by-char motion spans)
    // so we verify it exists in the container's textContent
    const log = screen.getByRole('log')
    expect(log.textContent).toContain('Finding centres...')
  })

  it('shows agent block headers', () => {
    const traces: AgentTrace[] = [
      { agent: 'orchestrator', message: 'Starting...', timestamp: 1000 },
      { agent: 'hygiene', message: 'Checking grades...', timestamp: 2000 },
    ]
    render(<AgentPanel traces={traces} state="searching" />)
    expect(screen.getByText('Orchestrator')).toBeInTheDocument()
    expect(screen.getByText('Hygiene')).toBeInTheDocument()
  })

  it('shows blinking cursor while searching', () => {
    const traces: AgentTrace[] = [
      { agent: 'orchestrator', message: 'Working...', timestamp: 1000 },
    ]
    render(<AgentPanel traces={traces} state="searching" />)
    expect(screen.getByText('\u258A')).toBeInTheDocument() // block cursor
  })

  it('shows complete indicator when state is complete', () => {
    const traces: AgentTrace[] = [
      { agent: 'orchestrator', message: 'Done', timestamp: 1000 },
    ]
    render(<AgentPanel traces={traces} state="complete" />)
    expect(screen.getByText('Analysis complete')).toBeInTheDocument()
  })

  it('shows error indicator when state is error', () => {
    const traces: AgentTrace[] = [
      { agent: 'orchestrator', message: 'Starting...', timestamp: 1000 },
    ]
    render(<AgentPanel traces={traces} state="error" />)
    expect(screen.getByText(/Error/)).toBeInTheDocument()
  })

  it('does not show cursor or completion in idle state with traces', () => {
    const traces: AgentTrace[] = [
      { agent: 'orchestrator', message: 'Old trace', timestamp: 1000 },
    ]
    render(<AgentPanel traces={traces} state="idle" />)
    expect(screen.queryByText('Analysis complete')).not.toBeInTheDocument()
    expect(screen.queryByText('\u258A')).not.toBeInTheDocument()
  })
})
