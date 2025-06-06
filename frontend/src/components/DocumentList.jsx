import React from 'react'

function DocumentList({ docs, onDelete }) {
  if (!docs.length) {
    return <p className="text-sm">No documents</p>
  }

  return (
    <ul className="space-y-1">
      {docs.map((d) => (
        <li key={d.name} className="flex justify-between items-center text-sm">
          <span>
            {d.name} ({d.size} bytes)
          </span>
          <button className="text-red-600" onClick={() => onDelete(d.name)}>
            delete
          </button>
        </li>
      ))}
    </ul>
  )
}

export default DocumentList
