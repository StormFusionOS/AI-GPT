export interface ClientIdentity {
  clientId: string;
  name: string;
  primaryContact: string;
  role: 'client';
}

export interface DashboardSummary {
  client_name: string;
  primary_contact: string;
  service_status: string;
  upcoming_appointments: Appointment[];
  recent_communications: Interaction[];
  open_invoices: Invoice[];
}

export interface Appointment {
  id: string;
  title: string;
  start: string;
  end: string;
  status: 'scheduled' | 'completed' | 'cancelled' | string;
  staff_member?: string | null;
  location?: string | null;
  notes?: string | null;
}

export interface Interaction {
  id: string;
  channel: 'email' | 'sms' | 'call' | string;
  direction: 'inbound' | 'outbound' | string;
  subject: string;
  body_preview: string;
  occurred_at: string;
  staff_member?: string | null;
}

export interface Invoice {
  id: string;
  amount: number;
  currency: string;
  status: 'paid' | 'due' | 'overdue' | string;
  issued_at: string;
  due_date: string;
  description?: string;
  pdf_url?: string;
}

export interface Profile {
  id: string;
  name: string;
  primary_contact: string;
  email: string;
  phone?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state_region?: string;
  postal_code?: string;
  country?: string;
  preferred_channel?: string;
}

export interface LoginResponse {
  token: string;
  client_id: string;
  name: string;
  primary_contact: string;
}

export interface MessageRequest {
  channel: 'email' | 'sms' | 'portal';
  content: string;
}

export interface RescheduleRequest {
  requested_start: string;
  message: string;
}

export interface PasswordChangeRequest {
  new_password: string;
}
