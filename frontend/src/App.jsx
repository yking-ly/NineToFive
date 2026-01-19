import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'

function App() {
  const [backendData, setBackendData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('http://127.0.0.1:5000/api/data')
      .then(res => {
        if (!res.ok) {
          throw new Error('Network response was not ok')
        }
        return res.json()
      })
      .then(data => {
        setBackendData(data)
        setLoading(false)
      })
      .catch(err => {
        console.error("Error fetching data:", err)
        setError("Failed to connect to backend. Is it running?")
        setLoading(false)
      })
  }, [])

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      <div className="bg-white p-8 rounded-xl shadow-2xl max-w-4xl w-full">
        <h1 className="text-4xl font-extrabold text-blue-700 mb-6 text-center">
          AI Legal Helper
        </h1>
        <p className="text-gray-600 mb-8 text-center border-b pb-4">
          Frontend is connected to Flask backend.
        </p>

        {loading && <p className="text-blue-500 animate-pulse text-center">Loading data from backend...</p>}

        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {backendData && (
          <div className="space-y-4">
            <div className="flex justify-between items-center bg-gray-100 p-3 rounded">
              <span className="font-semibold text-gray-700">Status:</span>
              <span className="text-green-600 font-bold uppercase">{backendData.status}</span>
            </div>

            <div className="mt-6 border-t pt-6">
              <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-4">Project Documentation (from server)</h3>
              <article className="prose prose-blue prose-lg max-w-none text-left">
                <ReactMarkdown>{backendData.readme}</ReactMarkdown>
              </article>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
