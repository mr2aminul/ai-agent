
export interface Project {
  id: string;
  name: string;
  path: string;
  description?: string;
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
  role: 'user' | 'assistant' | 'system' | 'code-reviewer';
  content: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface Workplan {
  id: string;
  conversation_id: string;
  title: string;
  description?: string;
  status: 'draft' | 'active' | 'completed';
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  workplan_id: string;
  title: string;
  description?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'verified';
  priority: number;
  task_order: number;
  assigned_agent: 'coder' | 'reviewer' | 'tester' | 'analyst';
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Patch {
  id: string;
  task_id?: string;
  conversation_id: string;
  content: string;
  branch_name?: string;
  status: 'draft' | 'ready' | 'applied' | 'rejected';
  created_at: string;
  applied_at?: string;
}

export interface CodeReview {
  id: string;
  patch_id: string;
  reviewer_agent: string;
  feedback: string;
  issues: Array<{
    severity: 'low' | 'medium' | 'high' | 'critical';
    message: string;
    location?: string;
  }>;
  score: number;
  created_at: string;
}

export interface ProcessingLog {
  id: string;
  conversation_id: string;
  stage: 'context_fetch' | 'search' | 'generate' | 'review' | 'patch_apply';
  message: string;
  duration_ms: number;
  created_at: string;
}

export interface WebSearchResult {
  id: string;
  title: string;
  url: string;
  snippet: string;
  source: string;
}

export interface ProjectMetrics {
  id: string;
  project_id: string;
  files_count: number;
  total_lines: number;
  test_coverage: number;
  complexity_avg: number;
  dependencies_count: number;
  vulnerabilities: Array<{
    id: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    description: string;
  }>;
  updated_at: string;
}

export interface ProcessingIndicator {
  stage: string;
  status: 'pending' | 'in_progress' | 'completed' | 'error';
  message: string;
  progress: number;
}
