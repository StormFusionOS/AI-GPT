import axios from 'axios';
import { addDays, addHours, addMinutes, formatISO } from 'date-fns';

import type { UserRole } from '@/contexts/AuthContext';

const baseURL = import.meta.env.VITE_API_BASE_URL ?? '/api';

const apiClient = axios.create({
  baseURL,
  withCredentials: true
});

let authToken: string | null = null;

apiClient.interceptors.request.use((config) => {
  if (authToken) {
    config.headers.Authorization = `Bearer ${authToken}`;
  }
  return config;
});

export function setAuthToken(token: string | null) {
  authToken = token;
  if (token) {
    apiClient.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete apiClient.defaults.headers.common.Authorization;
  }
}

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatarUrl?: string;
}

export interface AuthRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  accessToken: string;
  refreshToken?: string;
  user: UserProfile;
}

export interface MetricCard {
  label: string;
  value: number;
  change: number;
  trend: 'up' | 'down' | 'flat';
}

export interface HealthIndicator {
  id: string;
  label: string;
  status: 'ok' | 'warning' | 'error';
  detail: string;
  updatedAt: string;
}

export interface ActivityItem {
  id: string;
  description: string;
  timestamp: string;
  actor: string;
  type: 'lead' | 'task' | 'system';
}

export interface DashboardSnapshot {
  metrics: MetricCard[];
  health: HealthIndicator[];
  activity: ActivityItem[];
}

export interface InboxMessage {
  id: string;
  threadId: string;
  body: string;
  direction: 'inbound' | 'outbound';
  sentAt: string;
  sender: {
    type: 'user' | 'contact';
    name: string;
  };
}

export interface InboxThread {
  id: string;
  contactName: string;
  contactId: string;
  channel: string;
  lastMessageAt: string;
  unreadCount: number;
  preview: string;
  messages: InboxMessage[];
}

export type LeadStatus = 'new' | 'contacted' | 'qualified' | 'quoted' | 'won' | 'lost';

export interface LeadSummary {
  id: string;
  name: string;
  company?: string;
  value: number;
  status: LeadStatus;
  source: string;
  owner: string;
  createdAt: string;
  campaign?: string;
}

export interface LeadDetail extends LeadSummary {
  email?: string;
  phone?: string;
  notes?: string;
  interactions: Interaction[];
  appointments: Appointment[];
}

export interface Interaction {
  id: string;
  leadId: string;
  contactId: string;
  type: 'call' | 'sms' | 'email' | 'note';
  channel: string;
  content: string;
  occurredAt: string;
  createdBy: string;
}

export interface Appointment {
  id: string;
  contactId: string;
  title: string;
  start: string;
  end: string;
  location?: string;
  status: 'scheduled' | 'completed' | 'canceled';
  owner: string;
}

export interface Quote {
  id: string;
  contactName: string;
  status: 'draft' | 'sent' | 'accepted' | 'paid';
  total: number;
  issuedAt: string;
  updatedAt: string;
}

export interface Campaign {
  id: string;
  name: string;
  type: string;
  status: string;
  startDate: string;
  endDate?: string;
  budget?: number;
}

export interface CampaignDraftInput {
  name: string;
  type: string;
  description?: string;
  templateId?: number;
  scheduleAt?: string;
}

export interface ReviewQueueItem {
  id: string;
  title: string;
  summary: string;
  generatedBy: string;
  status: 'pending' | 'approved' | 'rejected';
  createdAt: string;
  proposedChanges: string;
  currentContent?: string;
}

export interface IntegrationSetting {
  id: string;
  name: string;
  description: string;
  status: 'connected' | 'disconnected';
  lastCheckedAt: string;
}

export interface SystemSetting {
  id: string;
  label: string;
  value: string | boolean | number;
  category: 'users' | 'integrations' | 'scraper' | 'system';
  description?: string;
}

export interface TeamUser extends UserProfile {
  lastActiveAt?: string;
}

const fallbackUser: UserProfile = {
  id: 'user-1',
  name: 'Avery Johnson',
  email: 'avery@example.com',
  role: 'admin'
};

let inboxThreads: InboxThread[] = createSampleThreads();
let leads: LeadDetail[] = createSampleLeads();
let appointments: Appointment[] = createSampleAppointments();
let quotes: Quote[] = createSampleQuotes();
let campaigns: Campaign[] = createSampleCampaigns();
let reviewQueue: ReviewQueueItem[] = createSampleReviewQueue();
let integrationSettings: IntegrationSetting[] = createSampleIntegrations();
let systemSettings: SystemSetting[] = createSampleSystemSettings();
let teamUsers: TeamUser[] = createSampleUsers();

export async function loginRequest(credentials: AuthRequest): Promise<AuthResponse> {
  try {
    const { data } = await apiClient.post<AuthResponse>('/auth/login', credentials);
    return data;
  } catch (error) {
    if (import.meta.env.DEV) {
      const accessToken = generateStubToken({
        sub: fallbackUser.id,
        email: credentials.email,
        name: fallbackUser.name,
        role: fallbackUser.role
      });
      return {
        accessToken,
        user: { ...fallbackUser, email: credentials.email }
      };
    }
    throw error;
  }
}

export async function fetchDashboardSnapshot(): Promise<DashboardSnapshot> {
  try {
    const { data } = await apiClient.get<DashboardSnapshot>('/dashboard');
    return data;
  } catch (error) {
    return {
      metrics: [
        { label: 'New leads (7d)', value: leads.filter((lead) => isWithinDays(lead.createdAt, 7)).length, change: 12, trend: 'up' },
        { label: 'Appointments upcoming', value: appointments.filter((appt) => isUpcoming(appt.start)).length, change: 3, trend: 'up' },
        { label: 'SEO health score', value: 86, change: -2, trend: 'down' },
        { label: 'Active campaigns', value: campaigns.filter((c) => c.status === 'running').length, change: 1, trend: 'flat' }
      ],
      health: [
        { id: 'backup', label: 'Last backup', status: 'ok', detail: 'Completed 6 hours ago', updatedAt: formatISO(new Date()) },
        { id: 'scraper', label: 'Scraper engine', status: 'warning', detail: 'Crawling slower than usual', updatedAt: formatISO(new Date()) },
        { id: 'twilio', label: 'Twilio SMS', status: 'ok', detail: 'Connected', updatedAt: formatISO(new Date()) },
        { id: 'lighthouse', label: 'SEO audits', status: 'ok', detail: 'Running hourly checks', updatedAt: formatISO(new Date()) }
      ],
      activity: leads.slice(0, 4).map((lead, index) => ({
        id: `activity-${lead.id}`,
        description: `${lead.name} moved to ${lead.status}`,
        timestamp: addMinutes(new Date(), -index * 25).toISOString(),
        actor: lead.owner,
        type: 'lead' as const
      }))
    };
  }
}

export async function fetchInboxThreads(): Promise<InboxThread[]> {
  try {
    const { data } = await apiClient.get<InboxThread[]>('/inbox');
    inboxThreads = data;
    return data;
  } catch (error) {
    return inboxThreads;
  }
}

export async function sendThreadMessage(threadId: string, body: string): Promise<InboxMessage> {
  const payload = { body };
  try {
    const { data } = await apiClient.post<InboxMessage>(`/inbox/${threadId}/messages`, payload);
    return data;
  } catch (error) {
    const message: InboxMessage = {
      id: `msg-${Date.now()}`,
      threadId,
      body,
      direction: 'outbound',
      sentAt: new Date().toISOString(),
      sender: { type: 'user', name: fallbackUser.name }
    };
    inboxThreads = inboxThreads.map((thread) =>
      thread.id === threadId
        ? {
            ...thread,
            preview: body,
            unreadCount: thread.unreadCount,
            lastMessageAt: message.sentAt,
            messages: [...thread.messages, message]
          }
        : thread
    );
    return message;
  }
}

export async function fetchLeads(): Promise<LeadSummary[]> {
  try {
    const { data } = await apiClient.get<LeadSummary[]>('/leads');
    leads = data.map((lead) => ({ ...lead, interactions: [], appointments: [] }));
    return data;
  } catch (error) {
    return leads.map((lead) => {
      const { interactions: _interactions, appointments: _appointments, ...summary } = lead;
      return summary;
    });
  }
}

export async function updateLeadStatus(leadId: string, status: LeadStatus): Promise<LeadDetail> {
  try {
    const { data } = await apiClient.patch<LeadDetail>(`/leads/${leadId}`, { status });
    leads = leads.map((lead) => (lead.id === leadId ? data : lead));
    return data;
  } catch (error) {
    leads = leads.map((lead) => (lead.id === leadId ? { ...lead, status } : lead));
    return leads.find((lead) => lead.id === leadId)!;
  }
}

export async function fetchLeadDetail(leadId: string): Promise<LeadDetail> {
  try {
    const { data } = await apiClient.get<LeadDetail>(`/leads/${leadId}`);
    leads = leads.map((lead) => (lead.id === leadId ? data : lead));
    return data;
  } catch (error) {
    const existing = leads.find((lead) => lead.id === leadId);
    if (!existing) {
      throw error;
    }
    return existing;
  }
}

export async function logInteraction(leadId: string, interaction: Pick<Interaction, 'type' | 'channel' | 'content'>): Promise<Interaction> {
  try {
    const { data } = await apiClient.post<Interaction>(`/leads/${leadId}/interactions`, interaction);
    updateLocalLeadInteraction(data);
    return data;
  } catch (error) {
    const newInteraction: Interaction = {
      id: `interaction-${Date.now()}`,
      leadId,
      contactId: leadId,
      type: interaction.type,
      channel: interaction.channel,
      content: interaction.content,
      occurredAt: new Date().toISOString(),
      createdBy: fallbackUser.name
    };
    updateLocalLeadInteraction(newInteraction);
    return newInteraction;
  }
}

function updateLocalLeadInteraction(interaction: Interaction) {
  leads = leads.map((lead) =>
    lead.id === interaction.leadId
      ? { ...lead, interactions: [interaction, ...lead.interactions] }
      : lead
  );
}

export async function fetchAppointments(): Promise<Appointment[]> {
  try {
    const { data } = await apiClient.get<Appointment[]>('/appointments');
    appointments = data;
    return data;
  } catch (error) {
    return appointments;
  }
}

export async function createAppointment(input: Omit<Appointment, 'id'>): Promise<Appointment> {
  try {
    const { data } = await apiClient.post<Appointment>('/appointments', input);
    appointments = [...appointments, data];
    return data;
  } catch (error) {
    const appointment: Appointment = { ...input, id: `appt-${Date.now()}` };
    appointments = [...appointments, appointment];
    return appointment;
  }
}

export async function fetchQuotes(): Promise<Quote[]> {
  try {
    const { data } = await apiClient.get<Quote[]>('/quotes');
    quotes = data;
    return data;
  } catch (error) {
    return quotes;
  }
}

export async function saveQuote(input: Quote): Promise<Quote> {
  try {
    const { data } = await apiClient.put<Quote>(`/quotes/${input.id}`, input);
    quotes = quotes.map((quote) => (quote.id === data.id ? data : quote));
    return data;
  } catch (error) {
    const existingIndex = quotes.findIndex((quote) => quote.id === input.id);
    if (existingIndex >= 0) {
      quotes[existingIndex] = input;
    } else {
      quotes = [...quotes, input];
    }
    return input;
  }
}

export async function fetchCampaigns(): Promise<Campaign[]> {
  try {
    const { data } = await apiClient.get<Campaign[]>('/campaigns');
    campaigns = data;
    return data;
  } catch (error) {
    return campaigns;
  }
}

export async function saveCampaignDraft(draft: CampaignDraftInput): Promise<Campaign> {
  try {
    const { data } = await apiClient.post<Campaign>('/campaigns', draft);
    campaigns = [...campaigns, data];
    return data;
  } catch (error) {
    const campaign: Campaign = {
      id: `campaign-${Date.now()}`,
      name: draft.name,
      type: draft.type,
      status: 'draft',
      startDate: draft.scheduleAt ?? new Date().toISOString(),
      endDate: undefined,
      budget: undefined
    };
    campaigns = [...campaigns, campaign];
    return campaign;
  }
}

export async function fetchReviewQueue(): Promise<ReviewQueueItem[]> {
  try {
    const { data } = await apiClient.get<ReviewQueueItem[]>('/review-queue');
    reviewQueue = data;
    return data;
  } catch (error) {
    return reviewQueue;
  }
}

export async function updateReviewQueueItem(id: string, status: ReviewQueueItem['status']): Promise<ReviewQueueItem> {
  try {
    const { data } = await apiClient.patch<ReviewQueueItem>(`/review-queue/${id}`, { status });
    reviewQueue = reviewQueue.map((item) => (item.id === id ? data : item));
    return data;
  } catch (error) {
    reviewQueue = reviewQueue.map((item) => (item.id === id ? { ...item, status } : item));
    return reviewQueue.find((item) => item.id === id)!;
  }
}

export async function fetchIntegrationSettings(): Promise<IntegrationSetting[]> {
  try {
    const { data } = await apiClient.get<IntegrationSetting[]>('/settings/integrations');
    integrationSettings = data;
    return data;
  } catch (error) {
    return integrationSettings;
  }
}

export async function fetchSystemSettings(): Promise<SystemSetting[]> {
  try {
    const { data } = await apiClient.get<SystemSetting[]>('/settings/system');
    systemSettings = data;
    return data;
  } catch (error) {
    return systemSettings;
  }
}

export async function updateSystemSetting(settingId: string, value: SystemSetting['value']): Promise<SystemSetting> {
  try {
    const { data } = await apiClient.patch<SystemSetting>(`/settings/system/${settingId}`, { value });
    systemSettings = systemSettings.map((setting) => (setting.id === settingId ? data : setting));
    return data;
  } catch (error) {
    systemSettings = systemSettings.map((setting) => (setting.id === settingId ? { ...setting, value } : setting));
    return systemSettings.find((setting) => setting.id === settingId)!;
  }
}

export async function fetchUsers(): Promise<TeamUser[]> {
  try {
    const { data } = await apiClient.get<TeamUser[]>('/users');
    teamUsers = data;
    return data;
  } catch (error) {
    return teamUsers;
  }
}

export async function inviteUser(email: string, role: UserRole): Promise<TeamUser> {
  try {
    const { data } = await apiClient.post<TeamUser>('/users/invite', { email, role });
    teamUsers = [...teamUsers, data];
    return data;
  } catch (error) {
    const user: TeamUser = {
      id: `user-${Date.now()}`,
      name: email.split('@')[0] ?? 'New teammate',
      email,
      role,
      lastActiveAt: new Date().toISOString()
    };
    teamUsers = [...teamUsers, user];
    return user;
  }
}

// ---------------------------------------------------------------------------
// Sample data helpers
// ---------------------------------------------------------------------------

function createSampleThreads(): InboxThread[] {
  const now = new Date();
  return [
    {
      id: 'thread-1',
      contactName: 'Casey Morgan',
      contactId: 'contact-1',
      channel: 'Twilio SMS',
      lastMessageAt: formatISO(now),
      unreadCount: 1,
      preview: 'Thanks for the proposal! Can we meet tomorrow?',
      messages: [
        {
          id: 'msg-1',
          threadId: 'thread-1',
          body: 'Thanks for the proposal! Can we meet tomorrow?',
          direction: 'inbound',
          sentAt: formatISO(addMinutes(now, -2)),
          sender: { type: 'contact', name: 'Casey Morgan' }
        },
        {
          id: 'msg-2',
          threadId: 'thread-1',
          body: 'Absolutely, I will send an invite.',
          direction: 'outbound',
          sentAt: formatISO(addMinutes(now, -1)),
          sender: { type: 'user', name: fallbackUser.name }
        }
      ]
    },
    {
      id: 'thread-2',
      contactName: 'Jamie Chen',
      contactId: 'contact-2',
      channel: 'Email',
      lastMessageAt: formatISO(addMinutes(now, -45)),
      unreadCount: 0,
      preview: 'Following up on the SEO audit results.',
      messages: [
        {
          id: 'msg-3',
          threadId: 'thread-2',
          body: 'Following up on the SEO audit results.',
          direction: 'outbound',
          sentAt: formatISO(addMinutes(now, -45)),
          sender: { type: 'user', name: fallbackUser.name }
        }
      ]
    }
  ];
}

function createSampleLeads(): LeadDetail[] {
  const now = new Date();
  return [
    {
      id: 'lead-1',
      name: 'Acme Plumbing',
      company: 'Acme Plumbing',
      value: 4800,
      status: 'contacted',
      source: 'Facebook',
      owner: 'Jordan Ruiz',
      createdAt: formatISO(addDays(now, -3)),
      campaign: 'Spring Promo',
      email: 'hello@acmeplumbing.com',
      phone: '(555) 123-4567',
      notes: 'Interested in new SEO retainer',
      interactions: [
        {
          id: 'interaction-1',
          leadId: 'lead-1',
          contactId: 'contact-1',
          type: 'call',
          channel: 'Twilio Voice',
          content: 'Initial discovery call completed.',
          occurredAt: formatISO(addHours(now, -6)),
          createdBy: 'Jordan Ruiz'
        }
      ],
      appointments: [
        {
          id: 'appt-1',
          contactId: 'contact-1',
          title: 'Strategy session',
          start: formatISO(addDays(now, 1)),
          end: formatISO(addDays(now, 1)),
          location: 'Zoom',
          status: 'scheduled',
          owner: 'Jordan Ruiz'
        }
      ]
    },
    {
      id: 'lead-2',
      name: 'Brightside Dental',
      company: 'Brightside Dental',
      value: 7200,
      status: 'qualified',
      source: 'Referral',
      owner: 'Avery Johnson',
      createdAt: formatISO(addDays(now, -12)),
      campaign: 'Email Nurture',
      email: 'info@brightside.dental',
      phone: '(555) 222-8800',
      notes: 'Needs updated analytics dashboard',
      interactions: [],
      appointments: []
    },
    {
      id: 'lead-3',
      name: 'Harvest Landscaping',
      company: 'Harvest Landscaping',
      value: 9500,
      status: 'new',
      source: 'Website',
      owner: 'Morgan Blake',
      createdAt: formatISO(addDays(now, -1)),
      campaign: 'SEO Campaign',
      email: 'sales@harvest-land.com',
      phone: '(555) 998-2233',
      notes: 'Requested demo of SEO audit.',
      interactions: [],
      appointments: []
    }
  ];
}

function createSampleAppointments(): Appointment[] {
  const now = new Date();
  return [
    {
      id: 'appt-1',
      contactId: 'contact-1',
      title: 'Strategy session',
      start: formatISO(addDays(now, 1)),
      end: formatISO(addDays(now, 1)),
      location: 'Zoom',
      status: 'scheduled',
      owner: 'Jordan Ruiz'
    },
    {
      id: 'appt-2',
      contactId: 'contact-2',
      title: 'SEO Audit Review',
      start: formatISO(addDays(now, 2)),
      end: formatISO(addDays(now, 2)),
      location: 'HQ',
      status: 'scheduled',
      owner: 'Avery Johnson'
    }
  ];
}

function createSampleQuotes(): Quote[] {
  const now = new Date();
  return [
    {
      id: 'quote-1',
      contactName: 'Acme Plumbing',
      status: 'sent',
      total: 4800,
      issuedAt: formatISO(addDays(now, -1)),
      updatedAt: formatISO(addHours(now, -3))
    },
    {
      id: 'quote-2',
      contactName: 'Harvest Landscaping',
      status: 'draft',
      total: 3200,
      issuedAt: formatISO(now),
      updatedAt: formatISO(now)
    }
  ];
}

function createSampleCampaigns(): Campaign[] {
  const now = new Date();
  return [
    {
      id: 'campaign-1',
      name: 'Spring SEO Blitz',
      type: 'SEO',
      status: 'running',
      startDate: formatISO(addDays(now, -15)),
      endDate: formatISO(addDays(now, 45)),
      budget: 15000
    },
    {
      id: 'campaign-2',
      name: 'Referral Drip Sequence',
      type: 'Email',
      status: 'draft',
      startDate: formatISO(addDays(now, 5))
    }
  ];
}

function createSampleReviewQueue(): ReviewQueueItem[] {
  const now = new Date();
  return [
    {
      id: 'review-1',
      title: 'Add FAQ schema to /services',
      summary: 'Schema markup update suggested by AI crawler',
      generatedBy: 'AI crawler',
      status: 'pending',
      createdAt: formatISO(addHours(now, -4)),
      proposedChanges: '<h2>Frequently Asked Questions</h2><p>...</p>',
      currentContent: '<!-- existing content -->'
    },
    {
      id: 'review-2',
      title: 'Update hero copy on homepage',
      summary: 'Conversion AI recommends refreshed messaging',
      generatedBy: 'Conversion AI',
      status: 'pending',
      createdAt: formatISO(addHours(now, -10)),
      proposedChanges: '<h1>Grow faster with our marketing ops platform</h1>'
    }
  ];
}

function createSampleIntegrations(): IntegrationSetting[] {
  const now = new Date();
  return [
    {
      id: 'twilio',
      name: 'Twilio',
      description: 'SMS and voice messaging provider',
      status: 'connected',
      lastCheckedAt: formatISO(addMinutes(now, -12))
    },
    {
      id: 'google',
      name: 'Google Business Profile',
      description: 'Location reviews and updates',
      status: 'disconnected',
      lastCheckedAt: formatISO(addHours(now, -7))
    }
  ];
}

function createSampleSystemSettings(): SystemSetting[] {
  return [
    {
      id: 'invite-required-role',
      label: 'Default user role',
      value: 'sales',
      category: 'users',
      description: 'Role assigned to new invitations'
    },
    {
      id: 'scraper-frequency',
      label: 'Crawler frequency (hours)',
      value: 6,
      category: 'scraper',
      description: 'How often to crawl target sites'
    },
    {
      id: 'backup-window',
      label: 'Backup window',
      value: '02:00',
      category: 'system',
      description: 'Nightly backup start time'
    }
  ];
}

function generateStubToken(payload: { sub: string; email: string; name: string; role: UserRole }) {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const body = btoa(
    JSON.stringify({
      ...payload,
      exp: Math.floor(Date.now() / 1000) + 60 * 60 * 4
    })
  );
  return `${header}.${body}.stub`;
}

function isWithinDays(date: string, days: number) {
  return new Date(date).getTime() >= Date.now() - days * 24 * 60 * 60 * 1000;
}

function isUpcoming(date: string) {
  return new Date(date).getTime() >= Date.now();
}

function createSampleUsers(): TeamUser[] {
  const now = new Date();
  return [
    {
      id: 'user-1',
      name: 'Avery Johnson',
      email: 'avery@example.com',
      role: 'admin',
      lastActiveAt: formatISO(now)
    },
    {
      id: 'user-2',
      name: 'Jordan Ruiz',
      email: 'jordan@example.com',
      role: 'sales',
      lastActiveAt: formatISO(addMinutes(now, -45))
    },
    {
      id: 'user-3',
      name: 'Morgan Blake',
      email: 'morgan@example.com',
      role: 'tech',
      lastActiveAt: formatISO(addHours(now, -5))
    }
  ];
}
