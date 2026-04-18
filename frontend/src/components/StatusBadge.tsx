interface StatusBadgeProps {
  type: 'grade' | 'michelin' | 'halal' | 'open' | 'closed' | 'crowd';
  value?: string;
}

export function StatusBadge({ type, value }: StatusBadgeProps) {
  const base = 'px-2 py-0.5 rounded-full text-xs font-medium inline-flex items-center gap-1';

  if (type === 'grade') {
    const grade = value?.toUpperCase() ?? '';
    let cls = '';
    if (grade === 'A') cls = 'bg-green-500/20 text-green-400 border border-green-500/30';
    else if (grade === 'B') cls = 'bg-amber-500/20 text-amber-400 border border-amber-500/30';
    else cls = 'bg-red-500/20 text-red-400 border border-red-500/30';
    return <span className={`${base} ${cls}`}>Grade {grade || '?'}</span>;
  }

  if (type === 'michelin') {
    return (
      <span className={`${base} bg-amber-500/10 text-amber-300 border border-amber-500/40`}>
        ⭐ Bib Gourmand
      </span>
    );
  }

  if (type === 'halal') {
    return (
      <span className={`${base} bg-green-500/10 text-green-400 border border-green-500/30`}>
        ☾ Halal
      </span>
    );
  }

  if (type === 'open') {
    return (
      <span className={`${base} bg-green-500/10 text-green-400 border border-green-500/30`}>
        <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
        Open now
      </span>
    );
  }

  if (type === 'closed') {
    return (
      <span className={`${base} bg-white/5 text-white/40 border border-white/10`}>
        <span className="w-1.5 h-1.5 rounded-full bg-white/30" />
        Closed
      </span>
    );
  }

  if (type === 'crowd') {
    const busy = value === 'busy';
    return (
      <span className={`${base} ${busy ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30' : 'bg-green-500/10 text-green-400 border border-green-500/30'}`}>
        <span className={`w-1.5 h-1.5 rounded-full ${busy ? 'bg-amber-400' : 'bg-green-400'}`} />
        {busy ? 'Busy now' : 'Quiet'}
      </span>
    );
  }

  return null;
}
