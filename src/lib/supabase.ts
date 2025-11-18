import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

export interface Project {
  id: string;
  name: string;
  path: string;
  created_at: string;
  updated_at: string;
}

export interface Conversation {
  id: string;
  project_id: string;
  title?: string;
  model: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: string;
  content: string;
  created_at: string;
}

export interface Workplan {
  id: string;
  conversation_id: string;
  title: string;
  description?: string;
  tasks: any[];
  created_at: string;
  updated_at: string;
}

export async function getProject(projectId: string): Promise<Project | null> {
  try {
    const response = await axios.get(`${API_BASE}/projects`);
    const projects = response.data.projects || [];
    return projects.find((p: Project) => p.id === projectId) || null;
  } catch (error) {
    console.error('Failed to get project:', error);
    return null;
  }
}

export async function getUserProjects(): Promise<Project[]> {
  try {
    const response = await axios.get(`${API_BASE}/projects`);
    return response.data.projects || [];
  } catch (error) {
    console.error('Failed to get projects:', error);
    return [];
  }
}

export async function createProject(name: string, path: string, description?: string): Promise<any> {
  try {
    const response = await axios.post(`${API_BASE}/projects`, { name, path });
    return response.data;
  } catch (error) {
    console.error('Failed to create project:', error);
    throw error;
  }
}

export async function getConversations(projectId: string): Promise<Conversation[]> {
  try {
    const response = await axios.get(`${API_BASE}/conversations/${projectId}`);
    return response.data.conversations || [];
  } catch (error) {
    console.error('Failed to get conversations:', error);
    return [];
  }
}

export async function createConversation(projectId: string, title?: string, model?: string): Promise<any> {
  try {
    const response = await axios.post(`${API_BASE}/conversations`, {
      project_id: projectId,
      title: title || 'New Conversation',
      model: model || 'qwen/qwen3-4b-2507'
    });
    return response.data;
  } catch (error) {
    console.error('Failed to create conversation:', error);
    throw error;
  }
}

export async function getMessages(conversationId: string): Promise<Message[]> {
  try {
    const response = await axios.get(`${API_BASE}/messages/${conversationId}`);
    return response.data.messages || [];
  } catch (error) {
    console.error('Failed to get messages:', error);
    return [];
  }
}

export async function addMessage(conversationId: string, role: string, content: string, metadata?: Record<string, unknown>): Promise<any> {
  try {
    const response = await axios.post(`${API_BASE}/messages`, {
      conversation_id: conversationId,
      role,
      content
    });
    return response.data;
  } catch (error) {
    console.error('Failed to add message:', error);
    throw error;
  }
}

export async function getWorkplan(workplanId: string): Promise<Workplan | null> {
  try {
    const response = await axios.get(`${API_BASE}/workplans`);
    const workplans = response.data.workplans || [];
    return workplans.find((w: Workplan) => w.id === workplanId) || null;
  } catch (error) {
    console.error('Failed to get workplan:', error);
    return null;
  }
}

export async function getConversationWorkplans(conversationId: string): Promise<Workplan[]> {
  try {
    const response = await axios.get(`${API_BASE}/workplans/${conversationId}`);
    return response.data.workplans || [];
  } catch (error) {
    console.error('Failed to get workplans:', error);
    return [];
  }
}

export async function createWorkplan(conversationId: string, title: string, description?: string): Promise<any> {
  try {
    const response = await axios.post(`${API_BASE}/workplans`, {
      conversation_id: conversationId,
      title,
      description
    });
    return response.data;
  } catch (error) {
    console.error('Failed to create workplan:', error);
    throw error;
  }
}

export async function getTasks(workplanId: string): Promise<any[]> {
  try {
    const response = await axios.get(`${API_BASE}/tasks/${workplanId}`);
    return response.data.tasks || [];
  } catch (error) {
    console.error('Failed to get tasks:', error);
    return [];
  }
}

export async function createTask(workplanId: string, title: string, description?: string, priority = 3, assignedAgent = 'coder'): Promise<any> {
  try {
    const response = await axios.post(`${API_BASE}/tasks`, {
      workplan_id: workplanId,
      title,
      description,
      priority,
      assigned_agent: assignedAgent
    });
    return response.data;
  } catch (error) {
    console.error('Failed to create task:', error);
    throw error;
  }
}

export async function updateTask(taskId: string, updates: Partial<any>): Promise<any> {
  try {
    const response = await axios.put(`${API_BASE}/tasks/${taskId}`, updates);
    return response.data;
  } catch (error) {
    console.error('Failed to update task:', error);
    throw error;
  }
}

export async function getProjectMetrics(projectId: string): Promise<any> {
  try {
    const response = await axios.get(`${API_BASE}/metrics/${projectId}`);
    return response.data || {};
  } catch (error) {
    console.error('Failed to get metrics:', error);
    return {};
  }
}

export async function getProcessingLogs(conversationId: string): Promise<any[]> {
  try {
    const response = await axios.get(`${API_BASE}/logs/${conversationId}`);
    return response.data.logs || [];
  } catch (error) {
    console.error('Failed to get logs:', error);
    return [];
  }
}

export async function addProcessingLog(conversationId: string, stage: string, message: string, duration_ms?: number): Promise<any> {
  try {
    const response = await axios.post(`${API_BASE}/logs`, {
      conversation_id: conversationId,
      stage,
      message,
      duration_ms
    });
    return response.data;
  } catch (error) {
    console.error('Failed to add log:', error);
    throw error;
  }
}
