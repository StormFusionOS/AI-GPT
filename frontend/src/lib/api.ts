import axios from 'axios';

const baseURL = import.meta.env.VITE_API_BASE_URL ?? '/api';

const client = axios.create({
  baseURL
});

export interface HealthResponse {
  status: string;
}

export const fetchHealth = async (): Promise<HealthResponse> => {
  const response = await client.get<HealthResponse>('/health');
  return response.data;
};
