import React from 'react'

function TypingIndicator() {
  return (
    <div className="flex space-x-2 p-3">
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" 
           style={{ animationDelay: '0ms' }}></div>
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" 
           style={{ animationDelay: '150ms' }}></div>
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" 
           style={{ animationDelay: '300ms' }}></div>
    </div>
  )
}

export default TypingIndicator