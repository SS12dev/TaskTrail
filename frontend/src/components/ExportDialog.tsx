import { useState } from 'react';
import { useMemoryAnalytics } from '../hooks/useMemoryAnalytics';

interface ExportDialogProps {
  isOpen: boolean;
  onClose: () => void;
  projectId?: string;
}

export function ExportDialog({ isOpen, onClose, projectId }: ExportDialogProps) {
  const [format, setFormat] = useState<'json' | 'csv' | 'markdown'>('json');
  const [exporting, setExporting] = useState(false);
  const { exportConversations, exportProjectConversations } = useMemoryAnalytics();

  const handleExport = async () => {
    setExporting(true);
    try {
      if (projectId) {
        await exportProjectConversations(projectId, format);
      } else {
        await exportConversations(format);
      }
      onClose();
    } finally {
      setExporting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 max-w-sm w-full mx-4">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
          Export Conversations
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Format
            </label>
            <div className="space-y-2">
              {['json', 'csv', 'markdown'].map((f) => (
                <label key={f} className="flex items-center">
                  <input
                    type="radio"
                    name="format"
                    value={f}
                    checked={format === f}
                    onChange={(e) => setFormat(e.target.value as any)}
                    className="w-4 h-4 text-indigo-600"
                  />
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300 capitalize">
                    {f === 'markdown' ? 'Markdown' : f.toUpperCase()}
                  </span>
                </label>
              ))}
            </div>
          </div>

          <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded">
            <p className="text-sm text-blue-700 dark:text-blue-300">
              {format === 'json' && 'JSON format for backup and data analysis'}
              {format === 'csv' && 'CSV format for spreadsheet applications'}
              {format === 'markdown' && 'Markdown format for documentation and sharing'}
            </p>
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={onClose}
            disabled={exporting}
            className="flex-1 px-4 py-2 text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg font-medium disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleExport}
            disabled={exporting}
            className="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium disabled:opacity-50"
          >
            {exporting ? 'Exporting...' : 'Export'}
          </button>
        </div>
      </div>
    </div>
  );
}
