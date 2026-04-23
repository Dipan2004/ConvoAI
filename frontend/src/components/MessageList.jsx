import { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble.jsx';

function LoadingIndicator() {
  return (
    <div className="flex items-center gap-1 rounded-2xl rounded-bl-md border border-gray-200 bg-white px-4 py-3 shadow-sm">
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.2s]" />
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.1s]" />
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400" />
    </div>
  );
}

function MessageList({ messages, isLoading }) {
  const listEndRef = useRef(null);

  useEffect(() => {
    listEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="min-h-0 flex-1 overflow-y-auto bg-gray-50/70 px-4 py-5 sm:px-6">
      <div className="space-y-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {isLoading ? (
          <div className="flex justify-start">
            <LoadingIndicator />
          </div>
        ) : null}

        <div ref={listEndRef} />
      </div>
    </div>
  );
}

export default MessageList;
