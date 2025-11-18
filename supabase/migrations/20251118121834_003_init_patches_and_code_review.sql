/*
  # Initialize patches and code review tables

  1. New Tables
    - `patches`
      - `id` (uuid, primary key)
      - `task_id` (uuid, foreign key)
      - `conversation_id` (uuid, foreign key)
      - `content` (text)
      - `branch_name` (text)
      - `status` (text: draft, ready, applied, rejected)
      - `created_at` (timestamp)
      - `applied_at` (timestamp)
    
    - `code_reviews`
      - `id` (uuid, primary key)
      - `patch_id` (uuid, foreign key)
      - `reviewer_agent` (text)
      - `feedback` (text)
      - `issues` (jsonb array)
      - `score` (integer: 0-100)
      - `created_at` (timestamp)
    
    - `project_metrics`
      - `id` (uuid, primary key)
      - `project_id` (uuid, foreign key)
      - `files_count` (integer)
      - `total_lines` (integer)
      - `test_coverage` (numeric)
      - `complexity_avg` (numeric)
      - `dependencies_count` (integer)
      - `vulnerabilities` (jsonb)
      - `updated_at` (timestamp)

  2. Security
    - Enable RLS on all tables
    - Add policies for authenticated users
*/

CREATE TABLE IF NOT EXISTS patches (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id uuid REFERENCES tasks(id) ON DELETE SET NULL,
  conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  content text NOT NULL,
  branch_name text,
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'ready', 'applied', 'rejected')),
  created_at timestamptz DEFAULT now(),
  applied_at timestamptz
);

CREATE TABLE IF NOT EXISTS code_reviews (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  patch_id uuid NOT NULL REFERENCES patches(id) ON DELETE CASCADE,
  reviewer_agent text DEFAULT 'reviewer',
  feedback text,
  issues jsonb DEFAULT '[]',
  score integer CHECK (score >= 0 AND score <= 100),
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS project_metrics (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  files_count integer DEFAULT 0,
  total_lines integer DEFAULT 0,
  test_coverage numeric DEFAULT 0.0,
  complexity_avg numeric DEFAULT 0.0,
  dependencies_count integer DEFAULT 0,
  vulnerabilities jsonb DEFAULT '[]',
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE patches ENABLE ROW LEVEL SECURITY;
ALTER TABLE code_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_metrics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view patches in their conversations"
  ON patches FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM conversations
      WHERE conversations.id = patches.conversation_id
      AND conversations.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can create patches in their conversations"
  ON patches FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM conversations
      WHERE conversations.id = patches.conversation_id
      AND conversations.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update patches in their conversations"
  ON patches FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM conversations
      WHERE conversations.id = patches.conversation_id
      AND conversations.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM conversations
      WHERE conversations.id = patches.conversation_id
      AND conversations.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can view code reviews for their patches"
  ON code_reviews FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM patches
      INNER JOIN conversations ON conversations.id = patches.conversation_id
      WHERE patches.id = code_reviews.patch_id
      AND conversations.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can view metrics for their projects"
  ON project_metrics FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM projects
      WHERE projects.id = project_metrics.project_id
      AND projects.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update metrics for their projects"
  ON project_metrics FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM projects
      WHERE projects.id = project_metrics.project_id
      AND projects.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM projects
      WHERE projects.id = project_metrics.project_id
      AND projects.user_id = auth.uid()
    )
  );
