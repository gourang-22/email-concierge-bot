import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const aiAPI = {
  analyze: () => api.post('/ai/analyze'),
};

export const taskAPI = {
  getAll: () => api.get('/tasks/'),
  updateStatus: (id, status) => api.patch(`/tasks/${id}`, { status }),
};

export const gmailAPI = {
  sync: () => api.post('/gmail/sync'),
};

export default api;
