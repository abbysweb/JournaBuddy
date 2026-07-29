import { useState } from 'react';

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setStatusMsg("Uploading...");
    
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      const data = await response.json();
      setTaskId(data.task_id);
      setStatusMsg("Upload successful! Task ID: " + data.task_id);
    } catch (err: any) {
      console.error(err);
      setStatusMsg("Error: " + err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-10">
      <header className="mb-10 text-center">
        <h1 className="text-4xl font-bold text-[#2b4c3f] mb-2">JournaBuddy</h1>
        <p className="text-gray-600">Research Paper Intelligence Platform</p>
      </header>

      <main className="w-full max-w-3xl bg-white p-8 rounded-xl shadow-sm border border-gray-100">
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">Upload Manuscript</h2>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-10 text-center bg-gray-50 hover:bg-gray-100 transition-colors">
            <input 
              type="file" 
              accept="application/pdf"
              className="mb-4"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
            <p className="text-sm text-gray-500">Only PDF files are supported (Max 50MB).</p>
            
            <button 
              onClick={handleUpload}
              disabled={!file || uploading}
              className="mt-6 bg-[#38bdf8] hover:bg-sky-500 text-white font-medium py-2 px-6 rounded-md disabled:opacity-50 transition-colors"
            >
              {uploading ? "Processing..." : "Analyze Paper"}
            </button>
            
            {statusMsg && (
              <p className="mt-4 text-sm font-medium text-gray-700">{statusMsg}</p>
            )}
          </div>
        </div>

        {taskId && (
          <div className="mt-8 p-6 bg-sky-50 rounded-lg border border-sky-100">
            <h3 className="text-lg font-medium text-sky-900 mb-2">Analysis in Progress</h3>
            <p className="text-sky-700 text-sm">
              Your document is being processed. (SSE Streaming will be implemented in Phase 3).
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
