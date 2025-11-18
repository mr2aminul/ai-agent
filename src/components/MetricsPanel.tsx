import React, { useEffect, useState } from 'react';
import { ProjectMetrics } from '@/types';
import { AlertCircle, Code2, Package, TestTube, TrendingUp } from 'lucide-react';
import { getProjectMetrics } from '@/lib/supabase';

interface MetricsPanelProps {
  projectId: string;
}

export default function MetricsPanel({ projectId }: MetricsPanelProps) {
  const [metrics, setMetrics] = useState<ProjectMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getProjectMetrics(projectId)
      .then(setMetrics)
      .finally(() => setLoading(false));
  }, [projectId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        <p>Loading metrics...</p>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        <p>No metrics available</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Files</span>
            <Code2 size={18} className="text-primary-500" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{metrics.files_count}</p>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Lines of Code</span>
            <TrendingUp size={18} className="text-primary-500" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{(metrics.total_lines / 1000).toFixed(1)}K</p>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Test Coverage</span>
            <TestTube size={18} className="text-success-500" />
          </div>
          <div className="flex items-center gap-2">
            <p className="text-2xl font-bold text-gray-900">{Math.round(metrics.test_coverage)}%</p>
            <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div className="h-full bg-success-500" style={{ width: `${metrics.test_coverage}%` }} />
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Dependencies</span>
            <Package size={18} className="text-secondary-500" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{metrics.dependencies_count}</p>
        </div>
      </div>

      {metrics.vulnerabilities.length > 0 && (
        <div className="bg-error-50 border border-error-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle size={18} className="text-error-600" />
            <h4 className="font-semibold text-error-700">Security Issues</h4>
          </div>
          <div className="space-y-2">
            {metrics.vulnerabilities.map((vuln, idx) => (
              <div key={idx} className="text-sm">
                <span className={`inline-block px-2 py-1 rounded text-xs font-medium mr-2 ${
                  vuln.severity === 'critical' ? 'bg-error-200 text-error-800' :
                  vuln.severity === 'high' ? 'bg-error-100 text-error-700' :
                  vuln.severity === 'medium' ? 'bg-warning-100 text-warning-700' :
                  'bg-blue-100 text-blue-700'
                }`}>
                  {vuln.severity.toUpperCase()}
                </span>
                <span className="text-gray-700">{vuln.description}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="text-xs text-gray-500">
        Last updated: {new Date(metrics.updated_at).toLocaleString()}
      </div>
    </div>
  );
}
