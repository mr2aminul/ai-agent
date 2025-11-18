import React from 'react';
import { Loader, CheckCircle, AlertCircle } from 'lucide-react';
import { ProcessingIndicator as ProcessingIndicatorType } from '@/types';

interface ProcessingIndicatorProps {
  indicator: ProcessingIndicatorType;
}

export default function ProcessingIndicator({ indicator }: ProcessingIndicatorProps) {
  const statusIcon = {
    pending: <Loader size={16} className="animate-spin text-gray-400" />,
    in_progress: <Loader size={16} className="animate-spin text-primary-500" />,
    completed: <CheckCircle size={16} className="text-success-500" />,
    error: <AlertCircle size={16} className="text-error-500" />,
  }[indicator.status];

  return (
    <div className="flex items-center gap-3 p-3 bg-gray-50 border border-gray-200 rounded-lg">
      <div className="flex-shrink-0">{statusIcon}</div>
      <div className="flex-1">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-gray-700 capitalize">{indicator.stage.replace(/_/g, ' ')}</span>
          <span className="text-xs text-gray-500">{indicator.progress}%</span>
        </div>
        <div className="w-full h-1 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${
              indicator.status === 'error' ? 'bg-error-500' : 'bg-primary-500'
            }`}
            style={{ width: `${indicator.progress}%` }}
          />
        </div>
        {indicator.message && <p className="text-xs text-gray-600 mt-1">{indicator.message}</p>}
      </div>
    </div>
  );
}
