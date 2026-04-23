function formatConfidence(confidence) {
  if (typeof confidence !== 'number' || Number.isNaN(confidence)) {
    return 'unknown';
  }

  return `${Math.round(confidence * 100)}%`;
}

function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  return (
    <article className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[85%] sm:max-w-[72%] ${isUser ? 'text-right' : 'text-left'}`}>
        <div
          className={[
            'rounded-2xl px-4 py-3 text-sm leading-6 shadow-sm',
            isUser
              ? 'rounded-br-md bg-gray-950 text-white'
              : 'rounded-bl-md border border-gray-200 bg-white text-gray-900',
          ].join(' ')}
        >
          <p className="whitespace-pre-wrap break-words">{message.content}</p>
        </div>

        {!isUser && message.meta ? (
          <div className="mt-2 px-1 text-xs text-gray-500">
            <span>intent: {message.meta.intent || 'unknown'}</span>
            <span className="mx-2 text-gray-300">/</span>
            <span>confidence: {formatConfidence(message.meta.confidence)}</span>
          </div>
        ) : null}
      </div>
    </article>
  );
}

export default MessageBubble;
