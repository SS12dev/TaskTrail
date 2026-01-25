import { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Loader2, Bot, User } from 'lucide-react';
import { Layout } from '../components/layout/Layout';
import { PageHeader } from '../components/layout/PageHeader';
import api from '../services/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

/**
 * AgentPage - AI-powered task management assistant.
 * Chat with AI to create, update, and manage tasks naturally.
 */
export const AgentPage = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Hi! I'm your TaskTrail AI assistant. I can help you create tasks, update them, organize your workflow, and answer questions about your tasks. What would you like to do today?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const userInput = input;
    setInput('');
    setIsLoading(true);

    try {
      // Call backend AI agent API using api service (handles token automatically)
      const response = await api.post('/api/v1/agent/chat', {
        message: userInput,
      });

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.message,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);

      // Show error message to user
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '❌ Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const suggestions = [
    'Create a task for tomorrow',
    'Show me my high priority tasks',
    'Break down my project into smaller tasks',
    'What should I focus on today?',
  ];

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
    inputRef.current?.focus();
  };

  return (
    <Layout>
      <PageHeader
        title="AI Agent"
        subtitle="Your intelligent task management assistant"
        icon={Bot}
        stats={[
          { label: 'Conversations', value: 1, color: 'text-purple-600 dark:text-purple-400' },
          { label: 'Tasks Created', value: 0, color: 'text-cyan-600 dark:text-cyan-400' },
        ]}
      />

      <div className="flex-1 flex flex-col h-[calc(100vh-12rem)] px-6 lg:px-8 py-6">
        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto mb-6 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {message.role === 'assistant' && (
                <div className="shrink-0 w-8 h-8 rounded-full bg-linear-to-br from-purple-500 to-cyan-500 flex items-center justify-center">
                  <Bot className="w-5 h-5 text-white" />
                </div>
              )}

              <div
                className={`max-w-[70%] rounded-2xl px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-linear-to-r from-violet-600 to-purple-600 text-white'
                    : 'bg-white dark:bg-slate-800 text-slate-900 dark:text-white border border-slate-200 dark:border-slate-700'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                <span
                  className={`text-xs mt-1 block ${
                    message.role === 'user'
                      ? 'text-purple-200'
                      : 'text-slate-500 dark:text-slate-400'
                  }`}
                >
                  {message.timestamp.toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
              </div>

              {message.role === 'user' && (
                <div className="shrink-0 w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center">
                  <User className="w-5 h-5 text-slate-600 dark:text-slate-400" />
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-3 justify-start">
              <div className="shrink-0 w-8 h-8 rounded-full bg-linear-to-br from-purple-500 to-cyan-500 flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl px-4 py-3">
                <Loader2 className="w-5 h-5 text-purple-600 dark:text-purple-400 animate-spin" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Quick Suggestions */}
        {messages.length <= 1 && (
          <div className="mb-4">
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
              Try asking:
            </p>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="px-3 py-1.5 text-sm bg-purple-50 dark:bg-purple-950/30 text-purple-700 dark:text-purple-300 rounded-full hover:bg-purple-100 dark:hover:bg-purple-950/50 transition-colors border border-purple-200 dark:border-purple-800"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="relative">
          <div className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message... (Press Enter to send)"
              disabled={isLoading}
              className="flex-1 px-4 py-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all disabled:opacity-50"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="px-6 py-3 bg-linear-to-r from-violet-600 to-purple-600 text-white rounded-xl hover:shadow-lg hover:scale-105 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 disabled:hover:shadow-none flex items-center gap-2"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <Send className="w-5 h-5" />
                  <span className="hidden sm:inline">Send</span>
                </>
              )}
            </button>
          </div>

          {/* Powered by badge */}
          <div className="flex items-center justify-center gap-1 mt-3 text-xs text-slate-500 dark:text-slate-400">
            <Sparkles className="w-3 h-3" />
            <span>Powered by AI</span>
          </div>
        </div>
      </div>
    </Layout>
  );
};
