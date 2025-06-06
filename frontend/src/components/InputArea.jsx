import React from 'react'

function InputArea({ value, onChange, onSend, disabled, placeholder }) {
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSend()
    }
  }

  return (
    <div className="flex gap-2">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyPress={handleKeyPress}
        disabled={disabled}
        placeholder={placeholder}
        rows="1"
        className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 
                   rounded-lg resize-none dark:bg-gray-700 dark:text-white
                   focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <button
        onClick={onSend}
        disabled={disabled || !value.trim()}
        className="px-6 py-2 bg-blue-500 text-white rounded-lg
                   hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed
                   transition-colors"
      >
        Send
      </button>
    </div>
  )
}

export default InputArea