import React, { useEffect } from 'react';
import { Task, Workplan } from '@/types';
import { CheckCircle2, Circle, Clock, AlertCircle, Zap } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { getTasks, updateTask } from '@/lib/supabase';

interface TaskPanelProps {
  workplan: Workplan | null;
}

export default function TaskPanel({ workplan }: TaskPanelProps) {
  const { tasks, setTasks } = useAppStore();

  useEffect(() => {
    if (workplan) {
      getTasks(workplan.id).then(setTasks);
    }
  }, [workplan, setTasks]);

  if (!workplan) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        <p>No workplan selected</p>
      </div>
    );
  }

  const statusIcons = {
    pending: <Circle size={18} className="text-gray-400" />,
    in_progress: <Loader size={18} className="text-primary-500 animate-spin" />,
    completed: <CheckCircle2 size={18} className="text-success-500" />,
    verified: <CheckCircle2 size={18} className="text-success-600" />,
  };

  const agentColors = {
    coder: 'bg-blue-100 text-blue-700',
    reviewer: 'bg-purple-100 text-purple-700',
    tester: 'bg-green-100 text-green-700',
    analyst: 'bg-orange-100 text-orange-700',
  };

  const priorityIcons = {
    1: <AlertCircle size={14} className="text-gray-400" />,
    2: <Zap size={14} className="text-warning-400" />,
    3: <Zap size={14} className="text-warning-500" />,
    4: <Zap size={14} className="text-warning-600" />,
    5: <AlertCircle size={14} className="text-error-500" />,
  };

  const handleStatusChange = async (task: Task, newStatus: Task['status']) => {
    try {
      const updated = await updateTask(task.id, { status: newStatus, updated_at: new Date().toISOString() });
      setTasks(tasks.map((t) => (t.id === task.id ? updated : t)));
    } catch (error) {
      console.error('Failed to update task:', error);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900">{workplan.title}</h3>
        <p className="text-sm text-gray-500">{tasks.length} tasks</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {tasks.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p>No tasks yet</p>
          </div>
        ) : (
          tasks.map((task) => (
            <div key={task.id} className="p-3 border border-gray-200 rounded-lg hover:border-gray-300 hover:shadow-sm transition-all">
              <div className="flex items-start gap-3">
                <button
                  onClick={() =>
                    handleStatusChange(
                      task,
                      task.status === 'completed' ? 'pending' : 'completed'
                    )
                  }
                  className="flex-shrink-0 mt-1 hover:opacity-70 transition-opacity"
                >
                  {statusIcons[task.status as keyof typeof statusIcons]}
                </button>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-medium text-sm text-gray-900 truncate">{task.title}</h4>
                    {priorityIcons[task.priority as keyof typeof priorityIcons]}
                  </div>
                  {task.description && (
                    <p className="text-xs text-gray-600 mb-2 line-clamp-2">{task.description}</p>
                  )}
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`text-xs font-medium px-2 py-1 rounded ${agentColors[task.assigned_agent as keyof typeof agentColors]}`}>
                      {task.assigned_agent}
                    </span>
                    <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded capitalize">
                      {task.status.replace(/_/g, ' ')}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

import { Loader } from 'lucide-react';
