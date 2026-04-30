import { useState } from 'react'
import { Key, Database, Server } from 'lucide-react'

function SettingsPage() {
  const [openaiKey, setOpenaiKey] = useState('')
  const [llmKey, setLlmKey] = useState('')
  const [model, setModel] = useState('gpt-4o-mini')

  return (
    <div className="max-w-3xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Configure API keys and preferences
        </p>
      </div>

      <div className="space-y-6">
        {/* OpenAI Configuration */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Key className="w-5 h-5" />
            OpenAI (for RAG Embeddings)
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                OpenAI API Key
              </label>
              <input
                type="password"
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
                placeholder="sk-..."
                className="w-full px-4 py-2 border border-border rounded-lg bg-background"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Required for RAG context retrieval. Stored securely.
              </p>
            </div>
          </div>
        </div>

        {/* LLM Configuration */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Server className="w-5 h-5" />
            LLM Provider (for Code Review)
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                LLM API Key
              </label>
              <input
                type="password"
                value={llmKey}
                onChange={(e) => setLlmKey(e.target.value)}
                placeholder="Your LLM API key"
                className="w-full px-4 py-2 border border-border rounded-lg bg-background"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
                Model
              </label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full px-4 py-2 border border-border rounded-lg bg-background"
              >
                <option value="gpt-4o-mini">GPT-4o Mini</option>
                <option value="gpt-4o">GPT-4o</option>
                <option value="gpt-4">GPT-4</option>
                <option value="claude-3-opus">Claude 3 Opus</option>
                <option value="claude-3-sonnet">Claude 3 Sonnet</option>
              </select>
            </div>
          </div>
        </div>

        {/* Vector Database */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Database className="w-5 h-5" />
            Vector Database
          </h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-accent/50 rounded-lg">
              <div>
                <p className="font-medium">ChromaDB</p>
                <p className="text-sm text-muted-foreground">Local vector storage</p>
              </div>
              <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">
                Active
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              Vector database is automatically configured. You can reset it from the repositories page.
            </p>
          </div>
        </div>

        {/* Save Button */}
        <button
          className="px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors"
          onClick={() => alert('Settings saved (demo only - configure via .env file)')}
        >
          Save Settings
        </button>
      </div>
    </div>
  )
}

export default SettingsPage
