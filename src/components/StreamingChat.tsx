import React, { useEffect, useRef, useState } from 'react';
import { Send, Loader, AlertCircle } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import MessageBubble from './MessageBubble';
import ProcessingIndicator from './ProcessingIndicator';

interface StreamingChatProps {
  conversationId: string;
  projectPath: string;
}

export default function StreamingChat({ conversationId, projectPath }: StreamingChatProps) {
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages, addMessage, processingIndicators, addProcessingIndicator, updateProcessingIndicator, error } =
    useAppStore();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, processingIndicators]);

  const handleSendMessage = async () => {
    if (!input.trim() || isStreaming) return;

    const userMessage = input.trim();
    setInput('');
    setIsStreaming(true);

    try {
      addMessage({
        id: `temp-${Date.now()}`,
        conversation_id: conversationId,
        role: 'user',
        content: userMessage,
        created_at: new Date().toISOString(),
      });

      addProcessingIndicator({
        stage: 'context_fetch',
        status: 'in_progress',
        message: 'Fetching project context...',
        progress: 10,
      });

      const eventSource = new EventSource(
        `/api/chat/stream?conversation_id=${conversationId}&query=${encodeURIComponent(userMessage)}&project_path=${encodeURIComponent(projectPath)}`
      );

      let fullResponse = '';
      let currentStage = '';

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'processing') {
          currentStage = data.stage;
          updateProcessingIndicator(data.stage, {
            status: 'in_progress',
            message: data.message,
            progress: data.progress,
          });
        } else if (data.type === 'chunk') {
          fullResponse += data.content;

          if (!messages.some((m) => m.id === `stream-${conversationId}`)) {
            addMessage({
              id: `stream-${conversationId}`,
              conversation_id: conversationId,
              role: 'assistant',
              content: fullResponse,
              created_at: new Date().toISOString(),
            });
          }
        } else if (data.type === 'complete') {
          updateProcessingIndicator(currentStage, {
            status: 'completed',
            progress: 100,
          });
          eventSource.close();
        }
      };

      eventSource.onerror = () => {
        updateProcessingIndicator(currentStage, {
          status: 'error',
          message: 'Connection error',
        });
        eventSource.close();
        setIsStreaming(false);
      };
    } catch (err) {
      console.error('Error sending message:', err);
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && processingIndicators.length === 0 && (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p>Start a conversation to begin...</p>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {processingIndicators.length > 0 && (
          <div className="space-y-2">
            {processingIndicators.map((indicator) => (
              <ProcessingIndicator key={indicator.stage} indicator={indicator} />
            ))}
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 p-3 bg-error-50 border border-error-200 rounded-lg text-error-700">
            <AlertCircle size={18} />
            <span className="text-sm">{error}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-gray-200 p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Ask about the project or request changes..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100"
            disabled={isStreaming}
          />
          <button
            onClick={handleSendMessage}
            disabled={isStreaming || !input.trim()}
            className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
          >
            {isStreaming ? <Loader size={18} className="animate-spin" /> : <Send size={18} />}
          </button>
        </div>
      </div>
    </div>
  );
}
