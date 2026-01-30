import { useState, useCallback } from 'react';
import api from '../services/api';

interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface Conversation {
  id: string;
  title: string;
  messages: ConversationMessage[];
  created_at: string;
  updated_at: string;
  archived: boolean;
  metadata: Record<string, any>;
}

/**
 * useConversations - Hook for managing agent conversations
 */
export const useConversations = () => {
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createConversation = useCallback(async (title?: string): Promise<string> => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await api.post('/api/v1/agent/conversations', null, {
        params: title ? { title } : {}
      });

      const conversationId = response.data.id;
      
      // Create empty conversation object
      const newConversation: Conversation = {
        id: conversationId,
        title: response.data.title,
        messages: [],
        created_at: response.data.created_at,
        updated_at: response.data.created_at,
        archived: false,
        metadata: {}
      };

      setCurrentConversation(newConversation);
      return conversationId;
    } catch (err: any) {
      const message = err?.response?.data?.detail || 'Failed to create conversation';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadConversation = useCallback(async (conversationId: string): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await api.get(`/api/v1/agent/conversations/${conversationId}`);
      setCurrentConversation(response.data);
    } catch (err: any) {
      const message = err?.response?.data?.detail || 'Failed to load conversation';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const sendMessage = useCallback(
    async (message: string, conversationIdOverride?: string): Promise<string> => {
      try {
        setError(null);

        // Create conversation if this is first message
        let conversationId = conversationIdOverride || currentConversation?.id;
        if (!conversationId) {
          conversationId = await createConversation();
        }

        // Send message
        const response = await api.post('/api/v1/agent/chat', {
          message,
          conversation_id: conversationId
        });

        // Add messages to local state (functional update to avoid stale state)
        setCurrentConversation((prev) => {
          const base = prev && prev.id === conversationId
            ? prev
            : {
                id: conversationId,
                title: prev?.title ?? 'New Conversation',
                messages: [],
                created_at: prev?.created_at ?? new Date().toISOString(),
                updated_at: prev?.updated_at ?? new Date().toISOString(),
                archived: false,
                metadata: {}
              };

          return {
            ...base,
            messages: [
              ...base.messages,
              {
                role: 'user',
                content: message,
                timestamp: new Date().toISOString()
              },
              {
                role: 'assistant',
                content: response.data.message,
                timestamp: new Date().toISOString()
              }
            ],
            updated_at: new Date().toISOString()
          };
        });

        return response.data.message;
      } catch (err: any) {
        const message = err?.response?.data?.detail || 'Failed to send message';
        setError(message);
        throw err;
      }
    },
    [currentConversation, createConversation]
  );

  const updateConversationTitle = useCallback(async (conversationId: string, title: string) => {
    try {
      setError(null);
      await api.put(`/api/v1/agent/conversations/${conversationId}`, null, {
        params: { title }
      });

      if (currentConversation?.id === conversationId) {
        setCurrentConversation({
          ...currentConversation,
          title
        });
      }
    } catch (err: any) {
      const message = err?.response?.data?.detail || 'Failed to update conversation title';
      setError(message);
      throw err;
    }
  }, [currentConversation]);

  const archiveConversation = useCallback(async (conversationId: string) => {
    try {
      setError(null);
      await api.delete(`/api/v1/agent/conversations/${conversationId}`, {
        params: { permanent: false }
      });
    } catch (err: any) {
      const message = err?.response?.data?.detail || 'Failed to archive conversation';
      setError(message);
      throw err;
    }
  }, []);

  const deleteConversation = useCallback(async (conversationId: string) => {
    try {
      setError(null);
      await api.delete(`/api/v1/agent/conversations/${conversationId}`, {
        params: { permanent: true }
      });
    } catch (err: any) {
      const message = err?.response?.data?.detail || 'Failed to delete conversation';
      setError(message);
      throw err;
    }
  }, []);

  return {
    currentConversation,
    isLoading,
    error,
    createConversation,
    loadConversation,
    sendMessage,
    updateConversationTitle,
    archiveConversation,
    deleteConversation
  };
};
