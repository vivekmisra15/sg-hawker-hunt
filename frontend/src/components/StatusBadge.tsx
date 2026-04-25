interface StatusBadgeProps {
  type: 'grade' | 'michelin' | 'halal' | 'open' | 'closed' | 'crowd';
  value?: string;
}

export function StatusBadge({ type, value }: StatusBadgeProps) {
  const base = 'px-2 py-0.5 rounded-full text-xs font-medium inline-flex items-center gap-1';

  if (type === 'grade') {
    const grade = value?.toUpperCase() ?? '';
    let cls = '';
    if (grade === 'A') cls = 'bg-success-bg text-success border border-success/30';
    else if (grade === 'B') cls = 'bg-warning-bg text-warning border border-warning/30';
    else if (grade === 'C' || grade === 'D') cls = 'bg-danger-bg text-danger border border-danger/30';
    else cls = 'bg-neutral-bg text-neutral border border-neutral/30';
    const label = grade === 'UNKNOWN' ? 'Grade —' : `Grade ${grade || '?'}`;
    return <span className={`${base} ${cls}`}>{label}</span>;
  }

  if (type === 'michelin') {
    return (
      <span
        className={`${base} bg-warning-bg text-warning border border-warning/30`}
        style={{ textShadow: '0 0 8px rgba(245,158,11,0.5)' }}
      >
        ⭐ Bib Gourmand
      </span>
    );
  }

  if (type === 'halal') {
    return (
      <span className={`${base} bg-success-bg text-success border border-success/30`}>
        ☾ Halal
      </span>
    );
  }

  if (type === 'open') {
    return (
      <span className={`${base} bg-success-bg text-success border border-success/30`}>
        <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
        Open now
      </span>
    );
  }

  if (type === 'closed') {
    return (
      <span className={`${base} bg-neutral-bg text-neutral border border-neutral/30`}>
        <span className="w-1.5 h-1.5 rounded-full bg-neutral" />
        Closed
      </span>
    );
  }

  if (type === 'crowd') {
    const busy = value === 'busy';
    return (
      <span className={`${base} ${busy ? 'bg-warning-bg text-warning border border-warning/30' : 'bg-success-bg text-success border border-success/30'}`}>
        <span className={`w-1.5 h-1.5 rounded-full ${busy ? 'bg-warning' : 'bg-success'}`} />
        {busy ? 'Busy now' : 'Quiet'}
      </span>
    );
  }

  return null;
}
