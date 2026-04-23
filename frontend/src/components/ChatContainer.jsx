import { useState } from 'react';
import { sendChatMessage } from '../services/api.js';
import { useSessionId } from '../hooks/useSessionId.js';
import InputBox from './InputBox.jsx';
import MessageList from './MessageList.jsx';

const initialMessage = {
  id: 'welcome',
  role: 'assistant',
  content: 'How can I help you today?',
  meta: {
    intent: 'welcome',
    confidence: 1,
  },
};

function ChatContainer() {
  const sessionId = useSessionId();
  const [messages, setMessages] = useState([initialMessage]);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSend(message) {
    const userMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: message,
    };

    setMessages((currentMessages) => [...currentMessages, userMessage]);
    setIsLoading(true);

    try {
      const data = await sendChatMessage({ sessionId, message });
      const assistantMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.response || 'Something went wrong',
        meta: data.meta,
      };

      setMessages((currentMessages) => [...currentMessages, assistantMessage]);
    } catch (error) {
      const errorMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'Something went wrong',
        meta: {
          intent: 'error',
          confidence: 0,
        },
      };

      setMessages((currentMessages) => [...currentMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="flex min-h-screen items-center justify-center px-4 py-6 sm:px-6">
      <div className="flex h-[calc(100vh-3rem)] w-full max-w-3xl flex-col overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-soft">
        <header className="border-b border-gray-200 px-5 py-4 sm:px-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h1 className="text-base font-semibold tracking-normal text-gray-950">
                AI Assistant Console
              </h1>
              <p className="mt-1 text-sm text-gray-500">
                Connected to your backend workspace
              </p>
            </div>
            <div className="hidden rounded-full border border-gray-200 px-3 py-1 text-xs font-medium text-gray-500 sm:block">
              Active session
            </div>
          </div>
        </header>

        <MessageList messages={messages} isLoading={isLoading} />
        <InputBox onSend={handleSend} disabled={isLoading} />
      </div>
    </section>
  );
}

export default ChatContainer;
