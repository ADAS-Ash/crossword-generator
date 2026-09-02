import { useState, useEffect } from 'react'
import './SettingsModal.css'

const STORAGE_KEY = 'cw_user_settings'

function loadSettings() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch { /* ignore */ }
  return { provider: '', geminiKey: '', anthropicKey: '' }
}

function saveSettings(s) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(s))
  } catch { /* ignore */ }
}

export function getByokHeaders() {
  const s = loadSettings()
  const headers = {}
  if (s.provider === 'gemini' && s.geminiKey) {
    headers['X-User-API-Key'] = s.geminiKey
    headers['X-User-Provider'] = 'gemini'
  } else if (s.provider === 'claude' && s.anthropicKey) {
    headers['X-User-API-Key'] = s.anthropicKey
    headers['X-User-Provider'] = 'claude'
  }
  return headers
}

export function hasByokKey() {
  const s = loadSettings()
  if (s.provider === 'gemini' && s.geminiKey) return true
  if (s.provider === 'claude' && s.anthropicKey) return true
  return false
}

export function SettingsModal({ open, onClose }) {
  const [settings, setSettings] = useState(loadSettings)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (open) setSettings(loadSettings())
  }, [open])

  if (!open) return null

  const handleSave = () => {
    saveSettings(settings)
    setSaved(true)
    setTimeout(() => {
      setSaved(false)
      onClose()
    }, 1000)
  }

  const handleClear = () => {
    const cleared = { provider: '', geminiKey: '', anthropicKey: '' }
    setSettings(cleared)
    saveSettings(cleared)
  }

  const update = (field, value) => {
    setSettings(prev => ({ ...prev, [field]: value }))
    setSaved(false)
  }

  return (
    <div className="settings-overlay" onClick={onClose}>
      <div className="settings-modal" onClick={e => e.stopPropagation()}>
        <div className="settings-modal__header">
          <h2 className="settings-modal__title">Settings</h2>
          <button className="settings-modal__close" onClick={onClose}>&times;</button>
        </div>

        <div className="settings-modal__section">
          <h3 className="settings-modal__subtitle">Bring Your Own Key</h3>
          <p className="settings-modal__desc">
            Provide your own API key for unlimited puzzle generation.
            Keys are stored in your browser only and sent directly to the provider.
          </p>

          <label className="settings-modal__label">
            Provider
            <select
              className="settings-modal__select"
              value={settings.provider}
              onChange={e => update('provider', e.target.value)}
            >
              <option value="">Use server default (free tier)</option>
              <option value="gemini">Google Gemini</option>
              <option value="claude">Anthropic Claude</option>
            </select>
          </label>

          {settings.provider === 'gemini' && (
            <label className="settings-modal__label">
              Gemini API Key
              <input
                type="password"
                className="settings-modal__input"
                value={settings.geminiKey}
                onChange={e => update('geminiKey', e.target.value)}
                placeholder="AIza..."
              />
              <span className="settings-modal__hint">
                Get one at <a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener noreferrer">aistudio.google.com</a>
              </span>
            </label>
          )}

          {settings.provider === 'claude' && (
            <label className="settings-modal__label">
              Anthropic API Key
              <input
                type="password"
                className="settings-modal__input"
                value={settings.anthropicKey}
                onChange={e => update('anthropicKey', e.target.value)}
                placeholder="sk-ant-..."
              />
              <span className="settings-modal__hint">
                Get one at <a href="https://console.anthropic.com/settings/keys" target="_blank" rel="noopener noreferrer">console.anthropic.com</a>
              </span>
            </label>
          )}
        </div>

        <div className="settings-modal__actions">
          <button className="settings-modal__btn settings-modal__btn--secondary" onClick={handleClear}>
            Clear keys
          </button>
          <button className="settings-modal__btn settings-modal__btn--primary" onClick={handleSave}>
            {saved ? 'Saved!' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}
