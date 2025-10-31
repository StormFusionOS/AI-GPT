import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { DiffViewer } from '@/components/DiffViewer';

/**
 * Developer-focused schema/content diff tool for quick comparisons outside the review queue.
 */
export function DiffToolPage() {
  const [left, setLeft] = useState('<h1>Existing markup</h1>');
  const [right, setRight] = useState('<h1>Updated markup</h1>');
  const [splitView, setSplitView] = useState(true);
  const [language, setLanguage] = useState<'html' | 'json' | 'text'>('html');

  const resetExamples = () => {
    setLeft('<h1>Existing markup</h1>');
    setRight('<h1>Updated markup</h1>');
    setLanguage('html');
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Schema Diff Tool</h1>
        <p className="text-sm text-muted-foreground">
          Paste any two versions of content or structured data to review differences with the same renderer used in
          the review queue.
        </p>
      </div>

      <Card>
        <CardHeader className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <CardTitle>Input</CardTitle>
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <Switch id="split-view" checked={splitView} onCheckedChange={setSplitView} />
              <Label htmlFor="split-view" className="text-sm">
                Split view
              </Label>
            </div>
            <select
              value={language}
              onChange={(event) => setLanguage(event.target.value as typeof language)}
              className="rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="html">HTML</option>
              <option value="json">JSON</option>
              <option value="text">Plain text</option>
            </select>
            <Button variant="outline" onClick={resetExamples}>
              Reset example
            </Button>
          </div>
        </CardHeader>
        <CardContent className="grid gap-4 lg:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="left-value">Original</Label>
            <Textarea
              id="left-value"
              value={left}
              onChange={(event) => setLeft(event.target.value)}
              className="min-h-[180px]"
              placeholder="Paste original content or schema"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="right-value">Proposed</Label>
            <Textarea
              id="right-value"
              value={right}
              onChange={(event) => setRight(event.target.value)}
              className="min-h-[180px]"
              placeholder="Paste updated content or schema"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Preview</CardTitle>
        </CardHeader>
        <CardContent>
          <DiffViewer oldValue={left} newValue={right} splitView={splitView} language={language} />
        </CardContent>
      </Card>
    </div>
  );
}
