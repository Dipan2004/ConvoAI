import { useState } from 'react';

function InputBox({ onSend, disabled }) {
  const [message, setMessage] = useState('');
  const trimmedMessage = message.trim();

  function handleSubmit(event) {
    event.preventDefault();

    if (!trimmedMessage || disabled) {
      return;
    }

    onSend(trimmedMessage);
    setMessage('');
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      handleSubmit(event);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="border-t border-gray-200 bg-white p-4 sm:p-5">
      <div className="flex items-end gap-3 rounded-xl border border-gray-200 bg-white p-2 shadow-sm focus-within:border-gray-400 focus-within:ring-4 focus-within:ring-gray-100">
        <textarea
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          rows={1}
          placeholder="Ask the assistant"
          className="max-h-36 min-h-11 flex-1 resize-none border-0 bg-transparent px-2 py-2.5 text-sm leading-6 text-gray-950 outline-none placeholder:text-gray-400 disabled:cursor-not-allowed disabled:text-gray-400"
        />
        <button
          type="submit"
          disabled={disabled || !trimmedMessage}
          className="h-10 rounded-lg bg-gray-950 px-4 text-sm font-medium text-white transition hover:bg-gray-800 disabled:cursor-not-allowed disabled:bg-gray-300"
        >
          Send
        </button>
      </div>
    </form>
  );
}

export default InputBox;
