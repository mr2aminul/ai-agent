/*
  # Initialize web search and context tables

  1. New Tables
    - `web_search_results`
      - `id` (uuid, primary key)
      - `conversation_id` (uuid, foreign key)
      - `query` (text)
      - `results` (jsonb array)
      - `source` (text: google, bing, duckduckgo)
      - `created_at` (timestamp)
    
    - `processing_logs`
      - `id` (uuid, primary key)
      - `conversation_id` (uuid, foreign key)
      - `stage` (text: context_fetch, search, generate, review)
      - `message` (text)
      - `duration_ms` (integer)
      - `created_at` (timestamp)
    
    - `indexed_files`
      - `id` (uuid, primary key)
      - `project_id` (uuid, foreign key)
      - `file_path` (text)
      - `content_hash` (text)
      - `chunk_count` (integer)
      - `indexed_at` (timestamp)

  2. Security
    - Enable RLS on all tables
    - Add policies for authenticated users
*/

CREATE TABLE IF NOT EXISTS web_search_results (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  query text NOT NULL,
  results jsonb DEFAULT '[]',
  source text DEFAULT 'google',
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS processing_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  stage text NOT NULL CHECK (stage IN ('context_fetch', 'search', 'generate', 'review', 'patch_apply')),
  message text,
  duration_ms integer,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS indexed_files (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  file_path text NOT NULL,
  content_hash text,
  chunk_count integer DEFAULT 0,
  indexed_at timestamptz DEFAULT now()
);

ALTER TABLE web_search_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE indexed_files ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view search results in their conversations"
  ON web_search_results FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM conversations
      WHERE conversations.id = web_search_results.conversation_id
      AND conversations.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can create search results in their conversations"
  ON web_search_results FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM conversations
      WHERE conversations.id = web_search_results.conversation_id
      AND conversations.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can view processing logs in their conversations"
  ON processing_logs FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM conversations
      WHERE conversations.id = processing_logs.conversation_id
      AND conversations.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can create processing logs in their conversations"
  ON processing_logs FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM conversations
      WHERE conversations.id = processing_logs.conversation_id
      AND conversations.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can view indexed files in their projects"
  ON indexed_files FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM projects
      WHERE projects.id = indexed_files.project_id
      AND projects.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert indexed files in their projects"
  ON indexed_files FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM projects
      WHERE projects.id = indexed_files.project_id
      AND projects.user_id = auth.uid()
    )
  );

CREATE INDEX idx_conversations_project_id ON conversations(project_id);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_workplans_conversation_id ON workplans(conversation_id);
CREATE INDEX idx_tasks_workplan_id ON tasks(workplan_id);
CREATE INDEX idx_patches_conversation_id ON patches(conversation_id);
CREATE INDEX idx_processing_logs_conversation_id ON processing_logs(conversation_id);
