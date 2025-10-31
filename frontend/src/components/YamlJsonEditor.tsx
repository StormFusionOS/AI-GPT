import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

interface YamlJsonEditorProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  rows?: number;
  error?: string;
}

export function YamlJsonEditor({ label, value, onChange, rows = 18, error }: YamlJsonEditorProps) {
  return (
    <div className="space-y-2">
      <Label htmlFor="config-editor">{label}</Label>
      <Textarea
        id="config-editor"
        rows={rows}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        spellCheck={false}
        className={cn('font-mono text-sm', error ? 'border-destructive' : undefined)}
      />
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  );
}
