import React from 'react'

function MessageList({ messages }) {
  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`p-4 rounded-lg ${
            message.type === 'user'
              ? 'bg-blue-100 dark:bg-blue-900 ml-auto max-w-[80%]'
              : message.type === 'assistant'
              ? 'bg-gray-100 dark:bg-gray-800 mr-auto max-w-[80%]'
              : 'bg-yellow-100 dark:bg-yellow-900 text-center'
          }`}
        >
          <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
            {message.type === 'user' ? 'You' : message.type === 'assistant' ? 'Assistant' : 'System'}
          </div>
          <div className="text-gray-800 dark:text-gray-100">
            {message.content}
          </div>
          {message.sources && message.sources.length > 0 && (
            <div className="mt-2 text-xs text-gray-500">
              Sources: {message.sources.join(', ')}
            </div>
          )}
          {message.confidence && (
            <div className="mt-1 text-xs text-gray-500">
              Confidence: {message.confidence}%
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export default MessageList