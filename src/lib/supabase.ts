import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export async function getProject(projectId: string) {
  const { data, error } = await supabase
    .from('projects')
    .select('*')
    .eq('id', projectId)
    .maybeSingle();

  if (error) throw error;
  return data;
}

export async function getUserProjects() {
  const { data, error } = await supabase
    .from('projects')
    .select('*')
    .order('created_at', { ascending: false });

  if (error) throw error;
  return data;
}

export async function createProject(name: string, path: string, description?: string) {
  const { data, error } = await supabase
    .from('projects')
    .insert([{ name, path, description }])
    .select()
    .maybeSingle();

  if (error) throw error;
  return data;
}

export async function getConversations(projectId: string) {
  const { data, error } = await supabase
    .from('conversations')
    .select('*')
    .eq('project_id', projectId)
    .order('created_at', { ascending: false });

  if (error) throw error;
  return data;
}

export async function createConversation(projectId: string, title?: string, model?: string) {
  const { data, error } = await supabase
    .from('conversations')
    .insert([{ project_id: projectId, title, model: model || 'gpt-oss-20b' }])
    .select()
    .maybeSingle();

  if (error) throw error;
  return data;
}

export async function getMessages(conversationId: string) {
  const { data, error } = await supabase
    .from('messages')
    .select('*')
    .eq('conversation_id', conversationId)
    .order('created_at', { ascending: true });

  if (error) throw error;
  return data;
}

export async function addMessage(conversationId: string, role: string, content: string, metadata?: Record<string, unknown>) {
  const { data, error } = await supabase
    .from('messages')
    .insert([{ conversation_id: conversationId, role, content, metadata }])
    .select()
    .maybeSingle();

  if (error) throw error;
  return data;
}

export async function getWorkplan(workplanId: string) {
  const { data, error } = await supabase
    .from('workplans')
    .select('*')
    .eq('id', workplanId)
    .maybeSingle();

  if (error) throw error;
  return data;
}

export async function getConversationWorkplans(conversationId: string) {
  const { data, error } = await supabase
    .from('workplans')
    .select('*')
    .eq('conversation_id', conversationId)
    .order('created_at', { ascending: false });

  if (error) throw error;
  return data;
}

export async function createWorkplan(conversationId: string, title: string, description?: string) {
  const { data, error } = await supabase
    .from('workplans')
    .insert([{ conversation_id: conversationId, title, description, status: 'draft' }])
    .select()
    .maybeSingle();

  if (error) throw error;
  return data;
}

export async function getTasks(workplanId: string) {
  const { data, error } = await supabase
    .from('tasks')
    .select('*')
    .eq('workplan_id', workplanId)
    .order('task_order', { ascending: true });

  if (error) throw error;
  return data;
}

export async function createTask(workplanId: string, title: string, description?: string, priority = 3, assignedAgent = 'coder') {
  const { data, error } = await supabase
    .from('tasks')
    .insert([{
      workplan_id: workplanId,
      title,
      description,
      priority,
      assigned_agent: assignedAgent,
      status: 'pending'
    }])
    .select()
    .maybeSingle();

  if (error) throw error;
  return data;
}

export async function updateTask(taskId: string, updates: Partial<any>) {
  const { data, error } = await supabase
    .from('tasks')
    .update(updates)
    .eq('id', taskId)
    .select()
    .maybeSingle();

  if (error) throw error;
  return data;
}

export async function getProjectMetrics(projectId: string) {
  const { data, error } = await supabase
    .from('project_metrics')
    .select('*')
    .eq('project_id', projectId)
    .maybeSingle();

  if (error) throw error;
  return data;
}

export async function getProcessingLogs(conversationId: string) {
  const { data, error } = await supabase
    .from('processing_logs')
    .select('*')
    .eq('conversation_id', conversationId)
    .order('created_at', { ascending: true });

  if (error) throw error;
  return data;
}

export async function addProcessingLog(conversationId: string, stage: string, message: string, duration_ms?: number) {
  const { data, error } = await supabase
    .from('processing_logs')
    .insert([{ conversation_id: conversationId, stage, message, duration_ms }])
    .select()
    .maybeSingle();

  if (error) throw error;
  return data;
}
