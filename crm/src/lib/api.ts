import axios from 'axios';

export interface LeadBoardItem {
  id: string;
  contact_id: string;
  contact_name: string;
  status: string;
  source?: string | null;
  created_at: string;
  last_message_preview?: string | null;
}

export interface InteractionItem {
  id: string;
  lead_id?: string | null;
  contact_id: string;
  interaction_type: string;
  content: string;
  occurred_at: string;
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
});

export const fetchLeads = async (token: string): Promise<LeadBoardItem[]> => {
  const response = await api.get('/api/v1/leads', {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data as LeadBoardItem[];
};

export const fetchLeadInteractions = async (
  leadId: string,
  token: string
): Promise<InteractionItem[]> => {
  const response = await api.get(`/api/v1/leads/${leadId}/interactions`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data as InteractionItem[];
};
