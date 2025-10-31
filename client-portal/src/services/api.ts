import axios from 'axios';

import type {
  Appointment,
  DashboardSummary,
  Interaction,
  Invoice,
  LoginResponse,
  MessageRequest,
  PasswordChangeRequest,
  Profile,
  RescheduleRequest,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
});

type AuthState = {
  token: string | null;
  clientId: string | null;
};

const authState: AuthState = {
  token: null,
  clientId: null,
};

api.interceptors.request.use((config) => {
  if (authState.token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${authState.token}`;
  }
  if (authState.clientId) {
    config.headers = config.headers ?? {};
    config.headers['X-User-Role'] = 'client';
    config.headers['X-Client-Id'] = authState.clientId;
  }
  return config;
});

export function setAuthContext(token: string | null, clientId: string | null) {
  authState.token = token;
  authState.clientId = clientId;
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>('/client/auth/login', { email, password });
  return data;
}

export async function fetchIdentity(): Promise<{ clientId: string; role: string; name: string; primaryContact: string }> {
  const { data } = await api.get('/client/identity');
  return data;
}

export async function fetchDashboard(): Promise<DashboardSummary> {
  const { data } = await api.get<DashboardSummary>('/client/dashboard');
  return data;
}

export async function fetchAppointments(): Promise<Appointment[]> {
  const { data } = await api.get<Appointment[]>('/client/appointments');
  return data;
}

export async function submitReschedule(
  appointmentId: string,
  payload: RescheduleRequest,
): Promise<{ status: string }> {
  const { data } = await api.post(`/client/appointments/${appointmentId}/reschedule`, payload);
  return data;
}

export async function fetchInteractions(): Promise<Interaction[]> {
  const { data } = await api.get<Interaction[]>('/client/interactions');
  return data;
}

export async function sendMessage(payload: MessageRequest): Promise<{ id: string; status: string }> {
  const { data } = await api.post('/client/messages', payload);
  return data;
}

export async function fetchInvoices(): Promise<Invoice[]> {
  const { data } = await api.get<Invoice[]>('/client/invoices');
  return data;
}

export async function fetchProfile(): Promise<Profile> {
  const { data } = await api.get<Profile>('/client/profile');
  return data;
}

export async function updateProfile(partial: Partial<Profile>): Promise<Profile> {
  const { data } = await api.patch<Profile>('/client/profile', partial);
  return data;
}

export async function changePassword(payload: PasswordChangeRequest): Promise<void> {
  await api.post('/client/profile/password', payload);
}
