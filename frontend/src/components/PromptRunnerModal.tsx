import { ChangeEvent, useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { useToast } from '@/components/ui/use-toast';
import type { PromptDefinition } from '@/types';

interface PromptRunnerModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * Allows admins to invoke AI prompt templates on-demand for rapid iteration.
 */
export function PromptRunnerModal({ open, onOpenChange }: PromptRunnerModalProps) {
  const { toast } = useToast();
  const [selectedPrompt, setSelectedPrompt] = useState<string>('');
  const [formValues, setFormValues] = useState<Record<string, string>>({});

  const { data: prompts, isLoading } = useQuery({
    queryKey: ['ai-prompts'],
    queryFn: api.getPrompts,
    enabled: open,
  });

  useEffect(() => {
    if (prompts && prompts.length > 0 && !selectedPrompt) {
      setSelectedPrompt(prompts[0].name);
    }
  }, [prompts, selectedPrompt]);

  const definition = useMemo<PromptDefinition | undefined>(() => {
    return prompts?.find((prompt) => prompt.name === selectedPrompt);
  }, [prompts, selectedPrompt]);

  useEffect(() => {
    if (!definition) {
      setFormValues({});
      return;
    }
    const schema = definition.inputSchema as { properties?: Record<string, unknown> } | undefined;
    const nextState: Record<string, string> = {};
    if (schema?.properties) {
      Object.entries(schema.properties).forEach(([key]) => {
        nextState[key] = '';
      });
    }
    setFormValues(nextState);
  }, [definition]);

  const [promptResult, setPromptResult] = useState('');

  const mutation = useMutation({
    mutationFn: api.runPrompt,
    onSuccess: (result) => {
      toast({
        title: 'Prompt executed',
        description: 'Review the output below to decide next steps.',
      });
      setPromptResult(JSON.stringify(result.output, null, 2));
    },
    onError: (error) => {
      toast({ title: 'Prompt failed', description: String(error), variant: 'destructive' });
    },
  });

  const handleSubmit = () => {
    if (!definition) return;
    mutation.mutate({ prompt: definition.name, parameters: formValues });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>AI Prompt Runner</DialogTitle>
          <DialogDescription>
            Execute prebuilt LangChain templates to experiment with messaging before publishing changes.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 overflow-y-auto pr-1">
          {isLoading && <div className="text-sm text-muted-foreground">Loading prompt catalog…</div>}

          {!isLoading && prompts && prompts.length > 0 && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="prompt-select">Prompt template</Label>
                <select
                  id="prompt-select"
                  value={selectedPrompt}
                  onChange={(event) => setSelectedPrompt(event.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  {prompts.map((prompt) => (
                    <option key={prompt.name} value={prompt.name}>
                      {prompt.label}
                    </option>
                  ))}
                </select>
                {definition && <p className="text-xs text-muted-foreground">{definition.description}</p>}
              </div>

              {definition && renderSchemaFields(definition.inputSchema as Record<string, unknown>, formValues, setFormValues)}

              <div className="space-y-2">
                <Label htmlFor="prompt-output">Output</Label>
                <Textarea
                  id="prompt-output"
                  value={promptResult}
                  readOnly
                  className="min-h-[160px] font-mono text-xs"
                />
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          <Button onClick={handleSubmit} disabled={mutation.isLoading || !definition}>
            {mutation.isLoading ? 'Running…' : 'Run prompt'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function renderSchemaFields(
  schema: Record<string, unknown>,
  formValues: Record<string, string>,
  setFormValues: (values: Record<string, string>) => void,
) {
  const properties = (schema.properties as Record<string, { type?: string }> | undefined) ?? {};
  return (
    <div className="space-y-3">
      {Object.entries(properties).map(([key, definition]) => {
        const type = definition?.type ?? 'string';
        const value = formValues[key] ?? '';
        const likelyLongField = /content|context|description|notes/i.test(key);
        const isMultiline = type !== 'array' && (likelyLongField || value.length > 120);
        const FieldComponent = isMultiline ? Textarea : Input;

        return (
          <div key={key} className="space-y-2">
            <Label htmlFor={`field-${key}`}>{key}</Label>
            <FieldComponent
              id={`field-${key}`}
              value={value}
              onChange={(event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
                setFormValues({ ...formValues, [key]: event.target.value });
              }}
              className={isMultiline ? 'min-h-[120px]' : ''}
            />
          </div>
        );
      })}
    </div>
  );
}
