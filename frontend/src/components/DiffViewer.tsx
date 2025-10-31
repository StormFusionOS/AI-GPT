import ReactDiffViewer, { DiffMethod } from 'react-diff-viewer-continued';
import { useMemo } from 'react';

interface DiffViewerProps {
  oldValue: string;
  newValue: string;
  splitView?: boolean;
  language?: 'html' | 'json' | 'text';
}

/**
 * Lightweight wrapper around react-diff-viewer with sane defaults for schema/content reviews.
 */
export function DiffViewer({ oldValue, newValue, splitView = true, language = 'text' }: DiffViewerProps) {
  const formattedOld = useMemo(() => formatValue(oldValue, language), [oldValue, language]);
  const formattedNew = useMemo(() => formatValue(newValue, language), [newValue, language]);

  return (
    <ReactDiffViewer
      oldValue={formattedOld}
      newValue={formattedNew}
      splitView={splitView}
      compareMethod={DiffMethod.WORDS}
      hideLineNumbers
      showDiffOnly={false}
      styles={{
        diffContainer: {
          borderRadius: '0.5rem',
          overflow: 'hidden',
          fontSize: '0.85rem',
        },
        line: {
          padding: '0.1rem 0.6rem',
        },
      }}
    />
  );
}

function formatValue(value: string, language: DiffViewerProps['language']): string {
  if (language === 'json') {
    try {
      const parsed = JSON.parse(value);
      return JSON.stringify(parsed, null, 2);
    } catch (error) {
      return value;
    }
  }
  if (language === 'html') {
    return value.replace(/></g, '>\n<');
  }
  return value;
}
