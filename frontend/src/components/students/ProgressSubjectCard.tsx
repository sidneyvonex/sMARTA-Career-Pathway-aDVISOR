import { useState } from 'react'
import {
  GRADE_LEVEL_LABELS,
  type ProgressEvidence,
  type SubjectProgress,
} from '../../api/students'
import ResponsiveDataList from '../common/dashboard/ResponsiveDataList'
import { evidenceOrigin, evidenceVerification } from '../../lib/academicEvidence'
import GradeSparkline from '../common/GradeSparkline'


const CONFIDENCE_LABELS: Record<SubjectProgress['evidence_confidence'], string> = {
  learner_entered: 'Learner-entered evidence',
  school_verified: 'School-verified evidence',
  mixed: 'Mixed learner-entered and school-verified evidence',
}


function trendText(progress: SubjectProgress): string {
  const evidence = progress.records_used
  if (evidence.length < 2) return 'Not enough status evidence to describe a trend.'
  const first = evidence[0]
  const latest = evidence[evidence.length - 1]
  const direction = latest.rank > first.rank
    ? 'Improving'
    : latest.rank < first.rank
      ? 'Declining'
      : 'Steady'
  return `${direction} from ${GRADE_LEVEL_LABELS[first.level]} to ${GRADE_LEVEL_LABELS[latest.level]} across ${evidence.length} status records.`
}


interface Props {
  progress: SubjectProgress
  evidence: ProgressEvidence[]
  onRecordResult?: () => void
  recordResultDisabled?: boolean
}


export default function ProgressSubjectCard({
  progress,
  evidence,
  onRecordResult,
  recordResultDisabled = false,
}: Props) {
  const isEmpty = progress.rule_code === 'missing_evidence' && evidence.length === 0
  const [detailsOpen, setDetailsOpen] = useState(false)
  const [historyOpen, setHistoryOpen] = useState(false)
  const detailsId = `subject-details-${progress.continuity_code}`
  const historyId = `subject-history-${progress.continuity_code}`

  if (isEmpty) {
    return (
      <article className={`progress-subject progress-subject--${progress.status}`}>
        <header className="progress-subject__header">
          <div>
            <h3>{progress.subject_name}</h3>
            <p className="progress-subject__confidence">{CONFIDENCE_LABELS[progress.evidence_confidence]}</p>
          </div>
          <span className={`progress-status progress-status--${progress.status}`}>
            {progress.label}
          </span>
        </header>

        <p className="progress-subject__missing">No results recorded yet for this subject.</p>

        {onRecordResult && (
          <button
            type="button"
            className="student-action student-action--secondary"
            onClick={onRecordResult}
            disabled={recordResultDisabled}
            aria-label={`Record a result for ${progress.subject_name}`}
          >
            Record a result
          </button>
        )}
      </article>
    )
  }

  return (
    <article className={`progress-subject progress-subject--${progress.status}`}>
      <header className="progress-subject__header">
        <div>
          <h3>{progress.subject_name}</h3>
          <p className="progress-subject__confidence">{CONFIDENCE_LABELS[progress.evidence_confidence]}</p>
        </div>
        <span className={`progress-status progress-status--${progress.status}`}>
          {progress.label}
        </span>
      </header>

      {!detailsOpen && (
        <p className="progress-subject__teaser">{progress.suggested_action}</p>
      )}

      <div className="progress-subject__details">
        <button
          type="button"
          className="progress-subject__toggle"
          aria-expanded={detailsOpen}
          aria-controls={detailsId}
          aria-label={`${detailsOpen ? 'Hide' : 'View'} ${progress.subject_name} details`}
          onClick={() => setDetailsOpen((current) => !current)}
        >
          {detailsOpen ? 'Hide details' : 'View details'}
          <span aria-hidden="true">⌄</span>
        </button>
        {detailsOpen && (
          <div className="progress-subject__details-content" id={detailsId}>
          <div className="progress-subject__trend-chart">
            <GradeSparkline records={progress.records_used} />
            <p className="progress-subject__trend">{trendText(progress)}</p>
          </div>

          {evidence.length > 0 && (
            <div className="progress-trail" aria-hidden="true">
              {evidence.map((record) => (
                <span className="progress-trail__record" key={record.id}>
                  <strong>{record.level}</strong>
                  <small>G{record.academic_grade} T{record.term}</small>
                </span>
              ))}
            </div>
          )}

          <div className="progress-alert" role="note" aria-label={`${progress.subject_name} status explanation`}>
            <strong>Why this status</strong>
            <p>{progress.explanation}</p>
            <p><strong>Suggested action:</strong> {progress.suggested_action}</p>
          </div>

          <section className="progress-evidence-used" aria-labelledby={`evidence-used-${progress.continuity_code}`}>
            <h4 id={`evidence-used-${progress.continuity_code}`}>Evidence used for this status</h4>
            <ResponsiveDataList
              ariaLabel={`${progress.subject_name} evidence used for this status`}
              items={progress.records_used}
              getKey={(record) => record.id}
              columns={[
                {
                  key: 'period',
                  label: 'Period',
                  render: (record) => `Grade ${record.academic_grade}, ${record.year}, Term ${record.term}`,
                },
                {
                  key: 'level',
                  label: 'CBE level',
                  render: (record) => GRADE_LEVEL_LABELS[record.level],
                },
                {
                  key: 'framework',
                  label: 'Assessment framework',
                  render: (record) => `${record.framework.code} ${record.framework.version}`,
                },
                {
                  key: 'origin',
                  label: 'Origin',
                  render: evidenceOrigin,
                },
                {
                  key: 'verification',
                  label: 'Verification',
                  render: evidenceVerification,
                },
              ]}
              empty={<p className="progress-evidence__empty">No evidence records were used for this status.</p>}
            />
          </section>

          <div className="progress-evidence">
            <button
              type="button"
              className="progress-evidence__toggle"
              aria-expanded={historyOpen}
              aria-controls={historyId}
              aria-label={`${historyOpen ? 'Hide' : 'View'} ${progress.subject_name} evidence history`}
              onClick={() => setHistoryOpen((current) => !current)}
            >
              {historyOpen ? 'Hide full evidence history' : 'View full evidence history'}
              <span aria-hidden="true">⌄</span>
            </button>
            {historyOpen && (
              <div id={historyId}>
                <ResponsiveDataList
                  ariaLabel={`${progress.subject_name} evidence`}
                  items={evidence}
                  getKey={(record) => record.id}
                  columns={[
                    {
                      key: 'period',
                      label: 'Period',
                      render: (record) => `Grade ${record.academic_grade}, ${record.year}, Term ${record.term}`,
                    },
                    {
                      key: 'level',
                      label: 'CBE level',
                      render: (record) => GRADE_LEVEL_LABELS[record.level],
                    },
                    {
                      key: 'origin',
                      label: 'Origin',
                      render: evidenceOrigin,
                    },
                    {
                      key: 'verification',
                      label: 'Verification',
                      render: evidenceVerification,
                    },
                    {
                      key: 'framework',
                      label: 'Assessment framework',
                      render: (record) => `${record.framework.code} ${record.framework.version}`,
                    },
                  ]}
                  empty={<p className="progress-evidence__empty">No evidence records are available.</p>}
                />
              </div>
            )}
          </div>
        </div>
        )}
      </div>
    </article>
  )
}
