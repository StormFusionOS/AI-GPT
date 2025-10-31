import { http, HttpResponse, delay } from 'msw';

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api';

interface MockClient {
  token: string;
  clientId: string;
  name: string;
  primaryContact: string;
}

const mockClient: MockClient = {
  token: 'mock-client-token-client-001',
  clientId: 'client-001',
  name: 'River City Clean Co.',
  primaryContact: 'Jordan Blake',
};

let interactions = [
  {
    id: 'msg-300',
    channel: 'email',
    direction: 'outbound',
    subject: 'Updated keyword focus for Q2',
    body_preview: 'We recommend targeting “eco friendly cleaning services”…',
    occurred_at: new Date().toISOString(),
    staff_member: 'Alex Morgan',
  },
  {
    id: 'msg-301',
    channel: 'sms',
    direction: 'inbound',
    subject: 'Client Reply',
    body_preview: 'Thanks for the update—excited to see results!',
    occurred_at: new Date(Date.now() - 86400000).toISOString(),
    staff_member: 'Jordan Blake',
  },
];

const appointments = [
  {
    id: 'appt-100',
    title: 'Monthly SEO Strategy Review',
    start: new Date(Date.now() + 2 * 86_400_000).toISOString(),
    end: new Date(Date.now() + 2 * 86_400_000 + 3600_000).toISOString(),
    status: 'scheduled',
    staff_member: 'Alex Morgan',
    location: 'Video Conference',
    notes: 'Review rankings and paid spend rollup.',
  },
  {
    id: 'appt-101',
    title: 'Onsite Content Shoot',
    start: new Date(Date.now() - 5 * 86_400_000).toISOString(),
    end: new Date(Date.now() - 5 * 86_400_000 + 3600_000).toISOString(),
    status: 'completed',
    staff_member: 'Nina Patel',
    location: 'Client HQ',
    notes: 'Captured testimonials and facility photos.',
  },
];

const invoices = [
  {
    id: 'inv-500',
    amount: 2850,
    currency: 'USD',
    status: 'due',
    issued_at: new Date(Date.now() - 3 * 86_400_000).toISOString(),
    due_date: new Date(Date.now() + 27 * 86_400_000).toISOString(),
    description: 'April 2025 full-service SEO retainer',
    pdf_url: 'https://example.com/invoices/inv-500.pdf',
  },
  {
    id: 'inv-501',
    amount: 2750,
    currency: 'USD',
    status: 'paid',
    issued_at: new Date(Date.now() - 34 * 86_400_000).toISOString(),
    due_date: new Date(Date.now() - 4 * 86_400_000).toISOString(),
    description: 'March 2025 full-service SEO retainer',
    pdf_url: 'https://example.com/invoices/inv-501.pdf',
  },
];

const profile = {
  id: 'client-001',
  name: 'River City Clean Co.',
  primary_contact: 'Jordan Blake',
  email: 'jordan@rivercityclean.com',
  phone: '+1-555-0100',
  address_line1: '401 Market Street',
  address_line2: 'Suite 800',
  city: 'Sacramento',
  state_region: 'CA',
  postal_code: '94203',
  country: 'USA',
  preferred_channel: 'email',
};

export const handlers = [
  http.post(`${API_BASE}/client/auth/login`, async ({ request }) => {
    const body = (await request.json()) as { email: string; password: string };
    await delay(400);
    if (body.email === 'jordan@rivercityclean.com' && body.password === 'client-portal-demo') {
      return HttpResponse.json({
        token: mockClient.token,
        client_id: mockClient.clientId,
        name: mockClient.name,
        primary_contact: mockClient.primaryContact,
      });
    }
    return new HttpResponse('Unauthorized', { status: 401 });
  }),

  http.get(`${API_BASE}/client/identity`, async () => {
    await delay(200);
    return HttpResponse.json({
      clientId: mockClient.clientId,
      role: 'client',
      name: mockClient.name,
      primaryContact: mockClient.primaryContact,
    });
  }),

  http.get(`${API_BASE}/client/dashboard`, async () => {
    await delay(250);
    return HttpResponse.json({
      client_name: mockClient.name,
      primary_contact: mockClient.primaryContact,
      service_status: 'Monthly optimization in progress; next report delivers Friday.',
      upcoming_appointments: appointments.filter((appt) => new Date(appt.start) >= new Date()),
      recent_communications: interactions.slice(0, 5),
      open_invoices: invoices.filter((invoice) => invoice.status !== 'paid'),
    });
  }),

  http.get(`${API_BASE}/client/appointments`, async () => {
    await delay(200);
    return HttpResponse.json(appointments);
  }),

  http.post(`${API_BASE}/client/appointments/:appointmentId/reschedule`, async ({ params, request }) => {
    const body = (await request.json()) as { requested_start: string; message: string };
    await delay(400);
    const appointment = appointments.find((appt) => appt.id === params.appointmentId);
    if (appointment) {
      appointment.start = body.requested_start;
      appointment.end = new Date(new Date(body.requested_start).getTime() + 3600_000).toISOString();
    }
    return HttpResponse.json({ status: 'received', requested_start: body.requested_start });
  }),

  http.get(`${API_BASE}/client/interactions`, async () => {
    await delay(200);
    return HttpResponse.json(interactions.sort((a, b) => (a.occurred_at < b.occurred_at ? 1 : -1)));
  }),

  http.post(`${API_BASE}/client/messages`, async ({ request }) => {
    const body = (await request.json()) as MessagePayload;
    await delay(300);
    const id = `msg-${Date.now()}`;
    interactions = [
      {
        id,
        channel: body.channel,
        direction: 'inbound',
        subject: 'Client Portal Message',
        body_preview: body.content.slice(0, 120),
        occurred_at: new Date().toISOString(),
        staff_member: mockClient.primaryContact,
      },
      ...interactions,
    ];
    return HttpResponse.json({ id, status: 'queued' });
  }),

  http.get(`${API_BASE}/client/invoices`, async () => {
    await delay(250);
    return HttpResponse.json(invoices);
  }),

  http.get(`${API_BASE}/client/profile`, async () => {
    await delay(200);
    return HttpResponse.json(profile);
  }),

  http.patch(`${API_BASE}/client/profile`, async ({ request }) => {
    const body = (await request.json()) as Partial<typeof profile>;
    await delay(400);
    Object.assign(profile, body);
    return HttpResponse.json(profile);
  }),

  http.post(`${API_BASE}/client/profile/password`, async () => {
    await delay(300);
    return HttpResponse.json({ status: 'accepted' });
  }),
];

type MessagePayload = {
  channel: 'email' | 'sms' | 'portal';
  content: string;
};
