import { useState, useEffect } from 'react';
import { MessageSquare, Plus, Trash2, Archive } from 'lucide-react';
import api from '../services/api';

interface Conversation {
  id: string;
  title: string;
  message_count: number;
  updated_at: string;
  archived: boolean;
}

interface ConversationListProps {
  onSelectConversation: (conversationId: string) => void;
  currentConversationId?: string;
}

/**
 * ConversationList - Sidebar component for listing and managing conversations
 */
export const ConversationList = ({ onSelectConversation, currentConversationId }: ConversationListProps) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showArchived, setShowArchived] = useState(false);

  useEffect(() => {
    fetchConversations();
  }, [showArchived]);

  const fetchConversations = async () => {
    try {
      setIsLoading(true);
      const response = await api.get(`/api/v1/agent/conversations?archived=${showArchived}`);
      setConversations(response.data);
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateNew = () => {
    // Signal parent to create new conversation (no conversation_id)
    onSelectConversation('');
  };

  const handleArchive = async (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.delete(`/api/v1/agent/conversations/${conversationId}`, {
        params: { permanent: false }
      });
      fetchConversations();
    } catch (error) {
      console.error('Failed to archive conversation:', error);
    }
  };

  const handleDelete = async (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to permanently delete this conversation?')) {
      try {
        await api.delete(`/api/v1/agent/conversations/${conversationId}`, {
          params: { permanent: true }
        });
        fetchConversations();
      } catch (error) {
        console.error('Failed to delete conversation:', error);
      }
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-700">
      {/* Header */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-700">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
          <MessageSquare className="w-5 h-5" />
          Conversations
        </h2>
        <button
          onClick={handleCreateNew}
          className="w-full px-4 py-2 bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-lg hover:opacity-90 transition-opacity flex items-center justify-center gap-2 font-medium"
        >
          <Plus className="w-4 h-4" />
          New Chat
        </button>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-slate-500">Loading...</div>
        ) : conversations.length === 0 ? (
          <div className="p-4 text-center text-slate-500 text-sm">
            {showArchived ? 'No archived conversations' : 'No conversations yet. Start a new chat!'}
          </div>
        ) : (
          <div className="space-y-2 p-3">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                onClick={() => onSelectConversation(conv.id)}
                className={`p-3 rounded-lg cursor-pointer transition-colors group ${
                  currentConversationId === conv.id
                    ? 'bg-violet-100 dark:bg-violet-900/30 border border-violet-300 dark:border-violet-700'
                    : 'hover:bg-slate-100 dark:hover:bg-slate-800 border border-transparent'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-slate-900 dark:text-white truncate">
                      {conv.title}
                    </h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      {conv.message_count} messages • {formatDate(conv.updated_at)}
                    </p>
                  </div>
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                    <button
                      onClick={(e) => handleArchive(conv.id, e)}
                      className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded"
                      title="Archive"
                    >
                      <Archive className="w-4 h-4 text-slate-500" />
                    </button>
                    <button
                      onClick={(e) => handleDelete(conv.id, e)}
                      className="p-1 hover:bg-red-100 dark:hover:bg-red-900/30 rounded"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Toggle Archived */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-700">
        <button
          onClick={() => setShowArchived(!showArchived)}
          className="w-full text-xs text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
        >
          {showArchived ? 'Show Active' : 'Show Archived'}
        </button>
      </div>
    </div>
  );
};
