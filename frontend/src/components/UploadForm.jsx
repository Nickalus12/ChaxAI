import React from 'react'

function UploadForm({ uploading, onUpload }) {
  const handleChange = (e) => {
    onUpload(e.target.files)
    e.target.value = ''
  }

  return (
    <div>
      <input type="file" multiple onChange={handleChange} className="mb-2" />
      {uploading && <p className="text-sm">Uploading...</p>}
    </div>
  )
}

export default UploadForm
