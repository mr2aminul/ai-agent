
import React from 'react';
import { Message } from '@/types';
import { CheckCircle, Code } from 'lucide-react';
import Markdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { dracula } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isSystemMessage = message.role === 'system';
  const isCodeReview = message.role === 'code-reviewer';

  if (isSystemMessage) {
    return (
      <div className="flex justify-center my-2">
        <div className="bg-gray-100 text-gray-600 text-xs px-3 py-1 rounded-full">{message.content}</div>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
          isUser
            ? 'bg-primary-500 text-white rounded-br-none'
            : isCodeReview
              ? 'bg-warning-50 border border-warning-200 text-gray-900 rounded-bl-none'
              : 'bg-gray-100 text-gray-900 rounded-bl-none'
        }`}
      >
        {isCodeReview && (
          <div className="flex items-center gap-2 mb-2 pb-2 border-b border-warning-200">
            <CheckCircle size={16} className="text-warning-600" />
            <span className="text-xs font-semibold text-warning-700">Code Review</span>
          </div>
        )}

        <div className={`text-sm prose prose-sm max-w-none ${isUser ? 'prose-invert' : ''}`}>
          {isUser ? (
            <p className="m-0">{message.content}</p>
          ) : (
            <Markdown
              components={{
                code: ({ node, inline, className, children, ...props }: any) => {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <SyntaxHighlighter
                      style={dracula}
                      language={match[1]}
                      PreTag="div"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                },
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                ul: ({ children }) => <ul className="mb-2 ml-4 list-disc">{children}</ul>,
                ol: ({ children }) => <ol className="mb-2 ml-4 list-decimal">{children}</ol>,
                li: ({ children }) => <li className="mb-1">{children}</li>,
                h1: ({ children }) => <h1 className="text-lg font-bold mb-2">{children}</h1>,
                h2: ({ children }) => <h2 className="text-base font-bold mb-2">{children}</h2>,
                h3: ({ children }) => <h3 className="text-sm font-bold mb-1">{children}</h3>,
              }}
            >
              {message.content}
            </Markdown>
          )}
        </div>
      </div>
    </div>
  );
}
