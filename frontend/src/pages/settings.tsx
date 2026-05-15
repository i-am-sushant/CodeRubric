import { useState, useEffect } from 'react'
import { Key, Database, Server, CheckCircle, AlertCircle, Loader2, RefreshCw } from 'lucide-react'
import axios from 'axios'

interface LLMSettings {
  llm_api_type: string
  llm_api_base: string
  model: string
  has_api_key: boolean
  embedding_model: string
  vector_store_path: string
}

interface Provider {
  value: string
  label: string
  placeholder: string
}

const MODEL_SUGGESTIONS: Record<string, string[]> = {
  google: ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash-lite'],
  openai: ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo', 'o1-mini'],
  anthropic: ['claude-sonnet-4-20250514', 'claude-3-5-haiku-20241022', 'claude-3-opus-20240229'],
}

const ASHNA_API_BASE = 'https://api.ashna.ai/v1/api'

function SettingsPage() {
  const [current, setCurrent] = useState<LLMSettings | null>(null)
  const [providers, setProviders] = useState<Provider[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Form state
  const [apiKey, setApiKey] = useState('')
  const [apiType, setApiType] = useState('')
  const [apiBase, setApiBase] = useState('')
  const [model, setModel] = useState('')

  const fetchSettings = async () => {
    setLoading(true)
    try {
      const [settingsRes, providersRes] = await Promise.all([
        axios.get('/api/settings/'),
        axios.get('/api/settings/providers'),
      ])
      setCurrent(settingsRes.data)
      setProviders(providersRes.data)
      setApiType(settingsRes.data.llm_api_type)
      setApiBase(settingsRes.data.llm_api_base || '')
      setModel(settingsRes.data.model)
    } catch (e: any) {
      setError('Failed to load settings: ' + (e.response?.data?.detail || e.message))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchSettings() }, [])

  const handleSave = async () => {
    setSaving(true)
    setError('')
    setSuccess('')
    try {
      const payload: Record<string, string> = {}
      const normalizedApiBase = apiBase.trim()
      if (apiKey) payload.llm_api_key = apiKey
      if (apiType && apiType !== current?.llm_api_type) payload.llm_api_type = apiType
      if (normalizedApiBase !== (current?.llm_api_base || '')) payload.llm_api_base = normalizedApiBase
      if (model && model !== current?.model) payload.model = model

      if (Object.keys(payload).length === 0) {
        setError('No changes to save.')
        setSaving(false)
        return
      }

      const res = await axios.put('/api/settings/', payload)
      setCurrent(res.data)
      setApiKey('')
      setSuccess('Settings saved and applied immediately.')
      setTimeout(() => setSuccess(''), 4000)
    } catch (e: any) {
      setError('Failed to save: ' + (e.response?.data?.detail || e.message))
    } finally {
      setSaving(false)
    }
  }

  const selectedPlaceholder = providers.find(p => p.value === apiType)?.placeholder || 'Your API key'
  const modelOptions = MODEL_SUGGESTIONS[apiType] || []
  const isAshnaBase = apiBase.includes('api.ashna.ai')

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="max-w-3xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Configure LLM provider and API keys. Changes apply immediately.
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-destructive/10 text-destructive flex items-center gap-2 text-sm">
          <AlertCircle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}
      {success && (
        <div className="mb-4 p-3 rounded-lg bg-green-500/10 text-green-600 flex items-center gap-2 text-sm">
          <CheckCircle className="w-4 h-4 shrink-0" /> {success}
        </div>
      )}

      <div className="space-y-6">
        {/* Current Status */}
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Server className="w-5 h-5" />
              Current LLM Configuration
            </h2>
            <button onClick={fetchSettings} className="text-muted-foreground hover:text-foreground">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
          {current && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="p-3 bg-accent/50 rounded-lg">
                <p className="text-xs text-muted-foreground">Provider</p>
                <p className="font-medium">{current.llm_api_type || 'not set'}</p>
              </div>
              <div className="p-3 bg-accent/50 rounded-lg">
                <p className="text-xs text-muted-foreground">Base URL</p>
                <p className="font-medium truncate" title={current.llm_api_base || 'default'}>
                  {current.llm_api_base || 'default'}
                </p>
              </div>
              <div className="p-3 bg-accent/50 rounded-lg">
                <p className="text-xs text-muted-foreground">Model</p>
                <p className="font-medium">{current.model || 'not set'}</p>
              </div>
              <div className="p-3 bg-accent/50 rounded-lg">
                <p className="text-xs text-muted-foreground">API Key</p>
                <p className="font-medium flex items-center gap-1">
                  {current.has_api_key ? (
                    <><CheckCircle className="w-4 h-4 text-green-500" /> Set</>
                  ) : (
                    <><AlertCircle className="w-4 h-4 text-destructive" /> Missing</>
                  )}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Update LLM */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Key className="w-5 h-5" />
            Update LLM Settings
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Provider</label>
              <select
                value={apiType}
                onChange={(e) => {
                  setApiType(e.target.value)
                  const defaults = MODEL_SUGGESTIONS[e.target.value]
                  if (defaults?.length) setModel(defaults[0])
                }}
                className="w-full px-4 py-2 border border-border rounded-lg bg-background"
              >
                {providers.map(p => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
              <p className="text-xs text-muted-foreground mt-1">
                Any provider supported by microcore works. Set via <code>.env</code> or here at runtime.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">API Base URL</label>
              <div className="flex gap-2">
                <input
                  type="url"
                  value={apiBase}
                  onChange={(e) => setApiBase(e.target.value)}
                  placeholder={ASHNA_API_BASE}
                  className="flex-1 px-4 py-2 border border-border rounded-lg bg-background"
                />
                <button
                  type="button"
                  onClick={() => {
                    setApiType('openai')
                    setApiBase(ASHNA_API_BASE)
                  }}
                  className="px-3 py-2 border border-border rounded-lg hover:bg-accent transition-colors text-sm"
                >
                  Use Ashna
                </button>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                For Ashna, use provider <code>openai</code> and base URL <code>{ASHNA_API_BASE}</code>.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">API Key</label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={current?.has_api_key ? '(unchanged — enter new key to replace)' : selectedPlaceholder}
                className="w-full px-4 py-2 border border-border rounded-lg bg-background"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Leave blank to keep the current key. Only enter a new value to replace it.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Model</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  placeholder={isAshnaBase ? 'Ashna model name' : 'e.g. gemini-2.0-flash'}
                  className="flex-1 px-4 py-2 border border-border rounded-lg bg-background"
                />
              </div>
              {modelOptions.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {modelOptions.map(m => (
                    <button
                      key={m}
                      onClick={() => setModel(m)}
                      className={`px-2 py-0.5 text-xs rounded border transition-colors ${
                        model === m
                          ? 'bg-primary text-primary-foreground border-primary'
                          : 'bg-accent/50 border-border hover:bg-accent'
                      }`}
                    >
                      {m}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* RAG / Embeddings — Read-Only Info */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Database className="w-5 h-5" />
            RAG & Embeddings
          </h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-accent/50 rounded-lg">
              <div>
                <p className="font-medium">Embedding Model</p>
                <p className="text-sm text-muted-foreground">
                  {current?.embedding_model || 'all-MiniLM-L6-v2'} (local, no API key needed)
                </p>
              </div>
              <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium dark:bg-green-900/30 dark:text-green-400">
                Local
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-accent/50 rounded-lg">
              <div>
                <p className="font-medium">Vector Store</p>
                <p className="text-sm text-muted-foreground">ChromaDB (auto-configured)</p>
              </div>
              <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium dark:bg-green-900/30 dark:text-green-400">
                Active
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              RAG embeddings use a local sentence-transformers model — no external API key required.
              To change the embedding model, set <code>EMBEDDING_MODEL</code> in your <code>.env</code> file.
            </p>
          </div>
        </div>

        {/* Save Button */}
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center gap-2"
        >
          {saving && <Loader2 className="w-4 h-4 animate-spin" />}
          {saving ? 'Saving...' : 'Save & Apply'}
        </button>
      </div>
    </div>
  )
}

export default SettingsPage
