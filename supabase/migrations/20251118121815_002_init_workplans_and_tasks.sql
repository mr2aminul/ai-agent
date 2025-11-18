/*
  # Initialize workplans and tasks tables

  1. New Tables
    - `workplans`
      - `id` (uuid, primary key)
      - `conversation_id` (uuid, foreign key)
      - `title` (text)
      - `description` (text)
      - `status` (text: draft, active, completed)
      - `created_at` (timestamp)
      - `updated_at` (timestamp)
    
    - `tasks`
      - `id` (uuid, primary key)
      - `workplan_id` (uuid, foreign key)
      - `title` (text)
      - `description` (text)
      - `status` (text: pending, in_progress, completed, verified)
      - `priority` (integer: 1-5)
      - `order` (integer)
      - `assigned_agent` (text: coder, reviewer, tester, analyst)
      - `metadata` (jsonb)
      - `created_at` (timestamp)
      - `updated_at` (timestamp)

  2. Security
    - Enable RLS on all tables
    - Add policies for authenticated users
*/

CREATE TABLE IF NOT EXISTS workplans (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  title text NOT NULL,
  description text,
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'completed')),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tasks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workplan_id uuid NOT NULL REFERENCES workplans(id) ON DELETE CASCADE,
  title text NOT NULL,
  description text,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'verified')),
  priority integer DEFAULT 3 CHECK (priority >= 1 AND priority <= 5),
  task_order integer,
  assigned_agent text DEFAULT 'coder' CHECK (assigned_agent IN ('coder', 'reviewer', 'tester', 'analyst')),
  metadata jsonb DEFAULT '{}',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE workplans ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view workplans in their conversations"
  ON workplans FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM conversations
      WHERE conversations.id = workplans.conversation_id
      AND conversations.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can create workplans in their conversations"
  ON workplans FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM conversations
      WHERE conversations.id = workplans.conversation_id
      AND conversations.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update workplans in their conversations"
  ON workplans FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM conversations
      WHERE conversations.id = workplans.conversation_id
      AND conversations.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM conversations
      WHERE conversations.id = workplans.conversation_id
      AND conversations.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can view tasks in their workplans"
  ON tasks FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM workplans
      INNER JOIN conversations ON conversations.id = workplans.conversation_id
      WHERE workplans.id = tasks.workplan_id
      AND conversations.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can create tasks in their workplans"
  ON tasks FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM workplans
      INNER JOIN conversations ON conversations.id = workplans.conversation_id
      WHERE workplans.id = tasks.workplan_id
      AND conversations.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update tasks in their workplans"
  ON tasks FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM workplans
      INNER JOIN conversations ON conversations.id = workplans.conversation_id
      WHERE workplans.id = tasks.workplan_id
      AND conversations.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM workplans
      INNER JOIN conversations ON conversations.id = workplans.conversation_id
      WHERE workplans.id = tasks.workplan_id
      AND conversations.user_id = auth.uid()
    )
  );
