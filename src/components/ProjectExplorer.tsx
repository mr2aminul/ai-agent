import React, { useState, useEffect } from 'react';
import { Project } from '@/types';
import { ChevronDown, ChevronRight, FileText, Folder, Code, Loader } from 'lucide-react';
import { createFileClient, FileOperationResult } from '@/lib/fileOperations';

interface FileItem {
  name: string;
  path: string;
  isDirectory: boolean;
  children?: FileItem[];
}

interface ProjectExplorerProps {
  project: Project | null;
  files: FileItem[];
  onFileSelect: (path: string) => void;
}

export default function ProjectExplorer({ project, files: initialFiles, onFileSelect }: ProjectExplorerProps) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [files, setFiles] = useState<FileItem[]>(initialFiles);
  const [loading, setLoading] = useState(false);
  const [fileClient, setFileClient] = useState<ReturnType<typeof createFileClient> | null>(null);

  useEffect(() => {
    if (project?.path) {
      setFileClient(createFileClient(project.path));
      loadProjectFiles();
    }
  }, [project?.path]);

  const loadProjectFiles = async () => {
    if (!project?.path || !fileClient) return;

    setLoading(true);
    try {
      const result = await fileClient.listDirectory('.');
      if (result.success && result.items) {
        const fileTree = buildFileTree(result.items);
        setFiles(fileTree);
      }
    } catch (error) {
      console.error('Failed to load project files:', error);
    } finally {
      setLoading(false);
    }
  };

  const buildFileTree = (items: any[]): FileItem[] => {
    return items.map(item => ({
      name: item.name,
      path: item.path,
      isDirectory: item.type === 'directory',
      children: []
    }));
  };

  const toggleExpanded = (path: string) => {
    const newExpanded = new Set(expanded);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpanded(newExpanded);
  };

  const FileTreeItem = ({ item, depth = 0 }: { item: FileItem; depth?: number }) => {
    const isExpanded = expanded.has(item.path);
    const hasChildren = item.children && item.children.length > 0;

    return (
      <div key={item.path}>
        <div
          className="flex items-center gap-2 px-2 py-1 hover:bg-gray-100 cursor-pointer rounded text-sm"
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
        >
          {item.isDirectory ? (
            <>
              <button
                onClick={() => toggleExpanded(item.path)}
                className="flex-shrink-0 hover:bg-gray-200 p-1 rounded"
              >
                {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              </button>
              <Folder size={16} className="text-warning-500 flex-shrink-0" />
              <span className="text-gray-700 flex-1 truncate">{item.name}</span>
            </>
          ) : (
            <>
              <div className="w-4 flex-shrink-0" />
              <Code size={16} className="text-primary-500 flex-shrink-0" />
              <button
                onClick={() => onFileSelect(item.path)}
                className="text-gray-700 flex-1 truncate text-left hover:text-primary-600 transition-colors"
              >
                {item.name}
              </button>
            </>
          )}
        </div>

        {item.isDirectory && isExpanded && hasChildren && (
          <div>
            {item.children?.map((child) => (
              <FileTreeItem key={child.path} item={child} depth={depth + 1} />
            ))}
          </div>
        )}
      </div>
    );
  };

  if (!project) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        <p>No project selected</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900">{project.name}</h3>
        <p className="text-xs text-gray-500">{project.path}</p>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <Loader size={20} className="animate-spin text-primary-500" />
          </div>
        ) : files.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p className="text-sm">No files found</p>
          </div>
        ) : (
          files.map((item) => <FileTreeItem key={item.path} item={item} />)
        )}
      </div>
    </div>
  );
}
