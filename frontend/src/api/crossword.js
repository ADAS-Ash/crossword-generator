export async function generateCrossword(topic, gridSize = 15, wordCount = 20) {
  const res = await fetch('/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic, grid_size: gridSize, word_count: wordCount }),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Server error' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }

  return res.json()
}

export async function loadPuzzleById(puzzleId) {
  const res = await fetch(`/api/puzzle/${encodeURIComponent(puzzleId)}`)

  if (!res.ok) {
    if (res.status === 404) return null
    const err = await res.json().catch(() => ({ detail: 'Server error' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }

  return res.json()
}

export async function checkHealth() {
  const res = await fetch('/api/health')
  return res.json()
}
