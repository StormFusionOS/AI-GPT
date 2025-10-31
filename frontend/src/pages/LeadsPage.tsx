import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { DragDropContext, Draggable, Droppable, type DropResult } from '@hello-pangea/dnd';
import { Link } from 'react-router-dom';
import { Filter, KanbanSquare, ListFilter } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { fetchLeads, updateLeadStatus, type LeadSummary, type LeadStatus } from '@/services/api';

const PIPELINE: { status: LeadStatus; title: string; description: string }[] = [
  { status: 'new', title: 'New', description: 'Incoming leads awaiting triage' },
  { status: 'contacted', title: 'Contacted', description: 'Initial outreach performed' },
  { status: 'qualified', title: 'Qualified', description: 'Discovery complete' },
  { status: 'quoted', title: 'Quoted', description: 'Proposal delivered' },
  { status: 'won', title: 'Won', description: 'Closed and onboarded' },
  { status: 'lost', title: 'Lost', description: 'Did not convert' }
];

export function LeadsPage() {
  const queryClient = useQueryClient();
  const { data: leads } = useQuery({ queryKey: ['leads'], queryFn: fetchLeads, staleTime: 30_000 });
  const [view, setView] = useState<'kanban' | 'table'>('kanban');
  const [search, setSearch] = useState('');

  const mutation = useMutation({
    mutationFn: ({ leadId, status }: { leadId: string; status: LeadStatus }) => updateLeadStatus(leadId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] });
    }
  });

  const groupedLeads = useMemo(() => {
    const grouping = new Map<LeadStatus, LeadSummary[]>();
    PIPELINE.forEach((stage) => grouping.set(stage.status, []));
    (leads ?? []).forEach((lead) => {
      const stage = grouping.get(lead.status);
      if (stage) stage.push(lead);
    });
    return grouping;
  }, [leads]);

  const filteredLeads = useMemo(() => {
    if (!search) return leads ?? [];
    const term = search.toLowerCase();
    return (leads ?? []).filter((lead) =>
      [lead.name, lead.source, lead.status, lead.campaign].some((field) => field?.toLowerCase().includes(term))
    );
  }, [leads, search]);

  const handleDragEnd = (result: DropResult) => {
    if (!result.destination || result.destination.droppableId === result.source.droppableId) {
      return;
    }
    const newStatus = result.destination.droppableId as LeadStatus;
    mutation.mutate({ leadId: result.draggableId, status: newStatus });
    queryClient.setQueryData<LeadSummary[]>(['leads'], (prev) => {
      if (!prev) return prev;
      return prev.map((lead) => (lead.id === result.draggableId ? { ...lead, status: newStatus } : lead));
    });
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Leads</h1>
          <p className="text-sm text-muted-foreground">Manage the revenue pipeline across marketing and sales.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline">
            <Filter className="mr-2 h-4 w-4" /> Filters
          </Button>
          <Button>Create lead</Button>
        </div>
      </div>

      <Tabs value={view} onValueChange={(value) => setView(value as 'kanban' | 'table')}>
        <TabsList className="mb-4">
          <TabsTrigger value="kanban" className="flex items-center gap-2">
            <KanbanSquare className="h-4 w-4" /> Kanban
          </TabsTrigger>
          <TabsTrigger value="table" className="flex items-center gap-2">
            <ListFilter className="h-4 w-4" /> Table
          </TabsTrigger>
        </TabsList>
        <TabsContent value="kanban" className="border-none bg-transparent p-0">
          <DragDropContext onDragEnd={handleDragEnd}>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
              {PIPELINE.map((stage) => (
                <Droppable droppableId={stage.status} key={stage.status}>
                  {(provided, snapshot) => (
                    <div
                      ref={provided.innerRef}
                      {...provided.droppableProps}
                      className={`flex h-full min-h-[300px] flex-col rounded-lg border bg-card/60 p-3 ${
                        snapshot.isDraggingOver ? 'border-primary/60 bg-primary/5' : 'border-border'
                      }`}
                    >
                      <div className="mb-3">
                        <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">{stage.title}</h3>
                        <p className="text-xs text-muted-foreground">{stage.description}</p>
                      </div>
                      <div className="flex flex-1 flex-col gap-3">
                        {groupedLeads.get(stage.status)?.map((lead, index) => (
                          <Draggable key={lead.id} draggableId={lead.id} index={index}>
                            {(dragProvided, dragSnapshot) => (
                              <div
                                ref={dragProvided.innerRef}
                                {...dragProvided.draggableProps}
                                {...dragProvided.dragHandleProps}
                                className={`space-y-2 rounded-md border border-border bg-background p-3 text-sm shadow-sm transition ${
                                  dragSnapshot.isDragging ? 'ring-2 ring-primary' : ''
                                }`}
                              >
                                <div className="flex items-center justify-between">
                                  <Link to={`/leads/${lead.id}`} className="font-semibold text-foreground hover:underline">
                                    {lead.name}
                                  </Link>
                                  <Badge variant="secondary">${lead.value.toLocaleString()}</Badge>
                                </div>
                                <p className="text-xs text-muted-foreground">Source · {lead.source}</p>
                                {lead.campaign && <p className="text-xs text-muted-foreground">Campaign · {lead.campaign}</p>}
                              </div>
                            )}
                          </Draggable>
                        ))}
                        {provided.placeholder}
                      </div>
                    </div>
                  )}
                </Droppable>
              ))}
            </div>
          </DragDropContext>
        </TabsContent>

        <TabsContent value="table" className="border-none bg-transparent p-0">
          <Card>
            <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <CardTitle className="text-base">Lead table</CardTitle>
              <Input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search by name, source, or campaign"
                className="max-w-xs"
              />
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Campaign</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Value</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredLeads.map((lead) => (
                    <TableRow key={lead.id} className="cursor-pointer" onClick={() => setView('kanban')}>
                      <TableCell>
                        <Link to={`/leads/${lead.id}`} className="font-medium text-foreground hover:underline">
                          {lead.name}
                        </Link>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">{lead.source}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="capitalize">
                          {lead.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">{lead.campaign ?? '—'}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(lead.createdAt).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right text-sm font-semibold">
                        ${lead.value.toLocaleString()}
                      </TableCell>
                    </TableRow>
                  ))}
                  {!filteredLeads.length && (
                    <TableRow>
                      <TableCell colSpan={6} className="py-8 text-center text-sm text-muted-foreground">
                        No leads found.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
