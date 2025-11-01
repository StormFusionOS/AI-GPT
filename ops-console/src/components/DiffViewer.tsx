import React from 'react';

interface DiffViewerProps {
  before: unknown;
  after: unknown;
  format?: 'text' | 'json';
  beforeLabel?: string;
  afterLabel?: string;
}

const stringify = (value: unknown, format: 'text' | 'json') => {
  if (value === null || value === undefined) {
    return '—';
  }
  if (typeof value === 'string' && format === 'text') {
    return value;
  }
  if (format === 'json') {
    try {
      return JSON.stringify(value, null, 2);
    } catch (error) {
      return String(value);
    }
  }
  return typeof value === 'string' ? value : String(value);
};

const DiffViewer: React.FC<DiffViewerProps> = ({
  before,
  after,
  format = 'json',
  beforeLabel = 'Current',
  afterLabel = 'Proposed',
}) => {
  const beforeValue = stringify(before, format);
  const afterValue = stringify(after, format);

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="flex h-full flex-col rounded-md border border-slate-200 bg-slate-50 p-3 text-sm dark:border-slate-800 dark:bg-slate-900">
        <span className="mb-2 font-semibold text-slate-600 dark:text-slate-300">{beforeLabel}</span>
        <pre className="flex-1 whitespace-pre-wrap break-words font-mono text-xs text-slate-700 dark:text-slate-200">
          {beforeValue}
        </pre>
      </div>
      <div className="flex h-full flex-col rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm dark:border-emerald-900 dark:bg-emerald-950">
        <span className="mb-2 font-semibold text-emerald-700 dark:text-emerald-300">{afterLabel}</span>
        <pre className="flex-1 whitespace-pre-wrap break-words font-mono text-xs text-emerald-800 dark:text-emerald-100">
          {afterValue}
        </pre>
      </div>
    </div>
  );
};

export default DiffViewer;
