import React, { useEffect, useState } from 'react';
import { useAppStore } from '@/store/useAppStore';
import { getUserProjects, getConversations, getMessages, getConversationWorkplans } from '@/lib/supabase';
import { Project, Conversation, Workplan } from '@/types';
import StreamingChat from './components/StreamingChat';
import TaskPanel from './components/TaskPanel';
import ProjectExplorer from './components/ProjectExplorer';
import MetricsPanel from './components/MetricsPanel';
import { Plus, Settings, Menu, X } from 'lucide-react';

export default function App() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [workplans, setWorkplans] = useState<Workplan[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showProjectPanel, setShowProjectPanel] = useState(true);
  const [selectedTabRight, setSelectedTabRight] = useState<'tasks' | 'metrics' | 'files'>('tasks');

  const {
    currentProject,
    setCurrentProject,
    currentConversation,
    setCurrentConversation,
    setMessages,
    setWorkplans: setWorkplansStore,
  } = useAppStore();

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const projectList = await getUserProjects();
      setProjects(projectList || []);
      if (projectList && projectList.length > 0) {
        setCurrentProject(projectList[0]);
      }
    } catch (error) {
      console.error('Failed to load projects:', error);
    }
  };

  const handleSelectProject = async (project: Project) => {
    setCurrentProject(project);
    try {
      const convs = await getConversations(project.id);
      setConversations(convs || []);
      if (convs && convs.length > 0) {
        handleSelectConversation(convs[0]);
      }
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const handleSelectConversation = async (conversation: Conversation) => {
    setCurrentConversation(conversation);
    try {
      const msgs = await getMessages(conversation.id);
      setMessages(msgs || []);
      const plans = await getConversationWorkplans(conversation.id);
      setWorkplans(plans || []);
      setWorkplansStore(plans || []);
    } catch (error) {
      console.error('Failed to load conversation data:', error);
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Left Sidebar - Projects */}
      <div className={`${sidebarOpen ? 'w-64' : 'w-0'} transition-all duration-300 bg-white border-r border-gray-200 shadow-sm flex flex-col overflow-hidden`}>
        <div className="p-4 border-b border-gray-200">
          <h1 className="text-lg font-bold text-gray-900">AI Agent</h1>
          <p className="text-xs text-gray-500">Development Platform</p>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          <h3 className="text-xs font-semibold text-gray-500 uppercase">Projects</h3>
          {projects.map((project) => (
            <button
              key={project.id}
              onClick={() => handleSelectProject(project)}
              className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                currentProject?.id === project.id
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <div className="text-sm font-medium truncate">{project.name}</div>
              <div className="text-xs text-gray-500 truncate">{project.path}</div>
            </button>
          ))}
        </div>

        <div className="p-4 border-t border-gray-200 space-y-2">
          <button className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors">
            <Plus size={18} />
            <span className="text-sm font-medium">New Project</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
            {currentProject && (
              <div>
                <h2 className="font-semibold text-gray-900">{currentProject.name}</h2>
                <p className="text-xs text-gray-500">{currentProject.path}</p>
              </div>
            )}
          </div>
          <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <Settings size={20} />
          </button>
        </div>

        {/* Main Grid */}
        <div className="flex-1 overflow-hidden flex gap-4 p-4">
          {/* Left Panel - Conversations */}
          <div className="w-48 bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col overflow-hidden">
            <div className="p-4 border-b border-gray-200">
              <h3 className="font-semibold text-gray-900 text-sm">Conversations</h3>
            </div>
            <div className="flex-1 overflow-y-auto p-2 space-y-1">
              {conversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => handleSelectConversation(conv)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                    currentConversation?.id === conv.id
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <div className="font-medium truncate">{conv.title || 'Untitled'}</div>
                  <div className="text-xs text-gray-500">{conv.model}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Center - Chat */}
          {currentConversation ? (
            <StreamingChat conversationId={currentConversation.id} projectPath={currentProject?.path || ''} />
          ) : (
            <div className="flex-1 flex items-center justify-center bg-white rounded-lg shadow-sm border border-gray-200 text-gray-400">
              <p>Select a conversation to start</p>
            </div>
          )}

          {/* Right Panel - Tabs */}
          <div className="w-72 bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col overflow-hidden">
            <div className="flex border-b border-gray-200">
              {['tasks', 'metrics', 'files'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setSelectedTabRight(tab as any)}
                  className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                    selectedTabRight === tab
                      ? 'text-primary-600 border-b-2 border-primary-600'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>

            <div className="flex-1 overflow-hidden">
              {selectedTabRight === 'tasks' && <TaskPanel workplan={workplans[0] || null} />}
              {selectedTabRight === 'metrics' && currentProject && <MetricsPanel projectId={currentProject.id} />}
              {selectedTabRight === 'files' && <ProjectExplorer project={currentProject} files={[]} onFileSelect={() => {}} />}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
