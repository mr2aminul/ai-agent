import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

export interface FileOperationResult {
  success: boolean;
  error?: string;
  content?: string;
  path?: string;
  size?: number;
  items?: Array<{
    name: string;
    type: 'file' | 'directory';
    size?: number;
    path: string;
  }>;
  count?: number;
  message?: string;
  results?: string[];
  exists?: boolean;
  is_file?: boolean;
  is_dir?: boolean;
}

class FileOperationsClient {
  constructor(private projectPath: string) {}

  async readFile(filePath: string): Promise<FileOperationResult> {
    try {
      const response = await axios.post(`${API_BASE}/files/read`, {
        project_path: this.projectPath,
        file_path: filePath,
      });
      return response.data;
    } catch (error) {
      return { success: false, error: `Failed to read file: ${error}` };
    }
  }

  async writeFile(filePath: string, content: string, overwrite = true): Promise<FileOperationResult> {
    try {
      const response = await axios.post(`${API_BASE}/files/write`, {
        project_path: this.projectPath,
        file_path: filePath,
        content,
        overwrite,
      });
      return response.data;
    } catch (error) {
      return { success: false, error: `Failed to write file: ${error}` };
    }
  }

  async appendFile(filePath: string, content: string): Promise<FileOperationResult> {
    try {
      const response = await axios.post(`${API_BASE}/files/append`, {
        project_path: this.projectPath,
        file_path: filePath,
        content,
      });
      return response.data;
    } catch (error) {
      return { success: false, error: `Failed to append to file: ${error}` };
    }
  }

  async deleteFile(filePath: string): Promise<FileOperationResult> {
    try {
      const response = await axios.post(`${API_BASE}/files/delete`, {
        project_path: this.projectPath,
        file_path: filePath,
      });
      return response.data;
    } catch (error) {
      return { success: false, error: `Failed to delete file: ${error}` };
    }
  }

  async listDirectory(dirPath = '.'): Promise<FileOperationResult> {
    try {
      const response = await axios.post(`${API_BASE}/files/list`, {
        project_path: this.projectPath,
        dir_path: dirPath,
      });
      return response.data;
    } catch (error) {
      return { success: false, error: `Failed to list directory: ${error}` };
    }
  }

  async createDirectory(dirPath: string): Promise<FileOperationResult> {
    try {
      const response = await axios.post(`${API_BASE}/files/mkdir`, {
        project_path: this.projectPath,
        dir_path: dirPath,
      });
      return response.data;
    } catch (error) {
      return { success: false, error: `Failed to create directory: ${error}` };
    }
  }

  async deleteDirectory(dirPath: string): Promise<FileOperationResult> {
    try {
      const response = await axios.post(`${API_BASE}/files/rmdir`, {
        project_path: this.projectPath,
        dir_path: dirPath,
      });
      return response.data;
    } catch (error) {
      return { success: false, error: `Failed to delete directory: ${error}` };
    }
  }

  async renameFile(oldPath: string, newPath: string): Promise<FileOperationResult> {
    try {
      const response = await axios.post(`${API_BASE}/files/rename`, {
        project_path: this.projectPath,
        old_path: oldPath,
        new_path: newPath,
      });
      return response.data;
    } catch (error) {
      return { success: false, error: `Failed to rename file: ${error}` };
    }
  }

  async copyFile(sourcePath: string, destPath: string): Promise<FileOperationResult> {
    try {
      const response = await axios.post(`${API_BASE}/files/copy`, {
        project_path: this.projectPath,
        source_path: sourcePath,
        dest_path: destPath,
      });
      return response.data;
    } catch (error) {
      return { success: false, error: `Failed to copy file: ${error}` };
    }
  }

  async getFileInfo(filePath: string): Promise<FileOperationResult> {
    try {
      const response = await axios.post(`${API_BASE}/files/info`, {
        project_path: this.projectPath,
        file_path: filePath,
      });
      return response.data;
    } catch (error) {
      return { success: false, error: `Failed to get file info: ${error}` };
    }
  }

  async searchFiles(pattern: string, dirPath = '.'): Promise<FileOperationResult> {
    try {
      const response = await axios.post(`${API_BASE}/files/search`, {
        project_path: this.projectPath,
        pattern,
        dir_path: dirPath,
      });
      return response.data;
    } catch (error) {
      return { success: false, error: `Failed to search files: ${error}` };
    }
  }
}

export function createFileClient(projectPath: string): FileOperationsClient {
  return new FileOperationsClient(projectPath);
}

export async function getProjects() {
  try {
    const response = await axios.get(`${API_BASE}/projects`);
    return response.data.projects || [];
  } catch (error) {
    return [];
  }
}

export async function createProject(name: string, path: string) {
  try {
    const response = await axios.post(`${API_BASE}/projects`, { name, path });
    return response.data;
  } catch (error) {
    return { error: `Failed to create project: ${error}` };
  }
}

export async function getConversations(projectId: string) {
  try {
    const response = await axios.get(`${API_BASE}/conversations/${projectId}`);
    return response.data.conversations || [];
  } catch (error) {
    return [];
  }
}

export async function createConversation(projectId: string, title: string, model: string) {
  try {
    const response = await axios.post(`${API_BASE}/conversations`, { project_id: projectId, title, model });
    return response.data;
  } catch (error) {
    return { error: `Failed to create conversation: ${error}` };
  }
}

export async function getMessages(conversationId: string) {
  try {
    const response = await axios.get(`${API_BASE}/messages/${conversationId}`);
    return response.data.messages || [];
  } catch (error) {
    return [];
  }
}

export async function createMessage(conversationId: string, role: string, content: string) {
  try {
    const response = await axios.post(`${API_BASE}/messages`, { conversation_id: conversationId, role, content });
    return response.data;
  } catch (error) {
    return { error: `Failed to create message: ${error}` };
  }
}
