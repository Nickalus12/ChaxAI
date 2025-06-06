import React, { useRef } from 'react'

function FileUpload({ onUpload, disabled, className }) {
  const fileInputRef = useRef(null)

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files)
    if (files.length > 0) {
      onUpload(files)
      e.target.value = ''
    }
  }

  return (
    <div className={className}>
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf,.txt,.md"
        onChange={handleFileChange}
        disabled={disabled}
        className="hidden"
      />
      <button
        onClick={() => fileInputRef.current?.click()}
        disabled={disabled}
        className="px-4 py-2 border border-gray-300 dark:border-gray-600 
                   rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700
                   disabled:opacity-50 disabled:cursor-not-allowed
                   transition-colors"
      >
        📎 Upload Files
      </button>
    </div>
  )
}

export default FileUpload