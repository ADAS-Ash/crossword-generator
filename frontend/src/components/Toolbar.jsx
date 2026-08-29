import { useState, useCallback } from 'react'
import { Timer } from './Timer'
import { ScoreDisplay } from './ScoreDisplay'
import './Toolbar.css'

function downloadGridAsImage(gridRef, puzzle) {
  const gridEl = gridRef?.current
  if (!gridEl || !puzzle) return

  const cells = gridEl.querySelectorAll('.cell')
  const cols = parseInt(gridEl.style.gridTemplateColumns.match(/repeat\((\d+)/)?.[1] || '0')
  if (!cols) return
  const rows = Math.ceil(cells.length / cols)

  const cellSize = 48
  const padding = 24
  const gridWidth = cols * cellSize
  const gridHeight = rows * cellSize

  const acrossWords = puzzle.words.filter(w => w.direction === 'across').sort((a, b) => a.number - b.number)
  const downWords = puzzle.words.filter(w => w.direction === 'down').sort((a, b) => a.number - b.number)

  const clueWidth = 340
  const clueFont = '13px sans-serif'
  const clueBoldFont = 'bold 15px sans-serif'
  const lineHeight = 18

  const tempCanvas = document.createElement('canvas')
  const tempCtx = tempCanvas.getContext('2d')
  tempCtx.font = clueFont

  function wrapText(text, maxWidth) {
    const words = text.split(' ')
    const lines = []
    let current = ''
    for (const word of words) {
      const test = current ? current + ' ' + word : word
      if (tempCtx.measureText(test).width > maxWidth) {
        if (current) lines.push(current)
        current = word
      } else {
        current = test
      }
    }
    if (current) lines.push(current)
    return lines
  }

  let clueHeight = 0
  const clueLineWidth = clueWidth - 40
  clueHeight += 30
  for (const w of acrossWords) {
    clueHeight += wrapText(`${w.number}. ${w.clue}`, clueLineWidth).length * lineHeight + 4
  }
  clueHeight += 36
  for (const w of downWords) {
    clueHeight += wrapText(`${w.number}. ${w.clue}`, clueLineWidth).length * lineHeight + 4
  }
  clueHeight += 20

  const titleHeight = 50
  const totalWidth = padding + gridWidth + 30 + clueWidth + padding
  const totalHeight = titleHeight + Math.max(gridHeight, clueHeight) + padding * 2

  const canvas = document.createElement('canvas')
  canvas.width = totalWidth * 2
  canvas.height = totalHeight * 2
  const ctx = canvas.getContext('2d')
  ctx.scale(2, 2)

  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, totalWidth, totalHeight)

  const topic = puzzle.metadata?.topic || 'Crossword'
  ctx.fillStyle = '#1a1a2e'
  ctx.font = 'bold 20px sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText(topic.charAt(0).toUpperCase() + topic.slice(1), totalWidth / 2, padding + 24)

  const gridX = padding
  const gridY = titleHeight + padding

  cells.forEach((cell, i) => {
    const r = Math.floor(i / cols)
    const c = i % cols
    const x = gridX + c * cellSize
    const y = gridY + r * cellSize

    const isBlack = cell.classList.contains('cell--black')
    ctx.fillStyle = isBlack ? '#1a1a2e' : '#ffffff'
    ctx.fillRect(x, y, cellSize, cellSize)

    ctx.strokeStyle = '#666666'
    ctx.lineWidth = 1
    ctx.strokeRect(x, y, cellSize, cellSize)

    if (!isBlack) {
      const numEl = cell.querySelector('.cell__number')
      if (numEl) {
        ctx.fillStyle = '#666666'
        ctx.font = 'bold 10px sans-serif'
        ctx.textAlign = 'left'
        ctx.fillText(numEl.textContent, x + 3, y + 11)
      }

      const letterEl = cell.querySelector('.cell__letter')
      if (letterEl?.textContent) {
        ctx.fillStyle = '#1a1a2e'
        ctx.font = 'bold 20px monospace'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillText(letterEl.textContent, x + cellSize / 2, y + cellSize / 2 + 1)
        ctx.textBaseline = 'alphabetic'
      }
    }
  })

  const clueX = gridX + gridWidth + 30
  let clueY = gridY

  ctx.fillStyle = '#2563eb'
  ctx.font = clueBoldFont
  ctx.textAlign = 'left'
  ctx.fillText('ACROSS', clueX, clueY + 14)
  clueY += 30

  ctx.fillStyle = '#333333'
  ctx.font = clueFont
  for (const w of acrossWords) {
    const lines = wrapText(`${w.number}. ${w.clue}`, clueLineWidth)
    for (const line of lines) {
      ctx.fillText(line, clueX, clueY + 13)
      clueY += lineHeight
    }
    clueY += 4
  }

  clueY += 16
  ctx.fillStyle = '#2563eb'
  ctx.font = clueBoldFont
  ctx.fillText('DOWN', clueX, clueY + 14)
  clueY += 30

  ctx.fillStyle = '#333333'
  ctx.font = clueFont
  for (const w of downWords) {
    const lines = wrapText(`${w.number}. ${w.clue}`, clueLineWidth)
    for (const line of lines) {
      ctx.fillText(line, clueX, clueY + 13)
      clueY += lineHeight
    }
    clueY += 4
  }

  const link = document.createElement('a')
  link.download = `crossword-${(topic || 'puzzle').replace(/\s+/g, '-').toLowerCase()}.png`
  link.href = canvas.toDataURL('image/png')
  link.click()
}

export function Toolbar({
  puzzle, userGrid, revealedCells,
  timerFormatted, timerRunning, onTimerToggle,
  onRevealLetter, onRevealWord, onRevealAll,
  onClearWord, onCheckWord, onCheckAnswers,
  isDark, onToggleTheme, isComplete, gridRef,
}) {
  const [showRevealConfirm, setShowRevealConfirm] = useState(false)

  const handleRevealAll = useCallback(() => {
    setShowRevealConfirm(true)
  }, [])

  const confirmRevealAll = useCallback(() => {
    onRevealAll()
    setShowRevealConfirm(false)
  }, [onRevealAll])

  const handleDownload = useCallback(() => {
    downloadGridAsImage(gridRef, puzzle)
  }, [gridRef, puzzle])

  return (
    <div className="toolbar">
      <div className="toolbar__left">
        <Timer
          formatted={timerFormatted}
          isRunning={timerRunning}
          onToggle={onTimerToggle}
        />
        <ScoreDisplay
          puzzle={puzzle}
          userGrid={userGrid}
          revealedCells={revealedCells}
        />
      </div>
      <div className="toolbar__right">
        <button className="toolbar__btn" onClick={onCheckWord} title="Check Word">
          Check Word
        </button>
        <button className="toolbar__btn" onClick={onRevealLetter} title="Reveal Letter">
          Reveal Letter
        </button>
        <button className="toolbar__btn" onClick={onRevealWord} title="Reveal Word">
          Reveal Word
        </button>
        <button className="toolbar__btn" onClick={onClearWord} title="Clear Word">
          Clear Word
        </button>
        <button className="toolbar__btn toolbar__btn--primary" onClick={onCheckAnswers} title="Check All">
          Check All
        </button>
        <button className="toolbar__btn toolbar__btn--danger" onClick={handleRevealAll} title="Reveal All">
          Reveal All
        </button>
        <button className="toolbar__btn toolbar__btn--icon" onClick={handleDownload} title="Download as image">
          📥
        </button>
        <button
          className="toolbar__btn toolbar__btn--icon"
          onClick={onToggleTheme}
          title={isDark ? 'Light mode' : 'Dark mode'}
        >
          {isDark ? '☀️' : '🌙'}
        </button>
      </div>

      {showRevealConfirm && (
        <div className="toolbar__confirm-overlay">
          <div className="toolbar__confirm">
            <p className="toolbar__confirm-title">Giving up already?</p>
            <p className="toolbar__confirm-text">
              This will reveal every answer. Your score will be forever haunted by this moment of weakness.
            </p>
            <div className="toolbar__confirm-actions">
              <button
                className="toolbar__btn"
                onClick={() => setShowRevealConfirm(false)}
              >
                No, I've got this
              </button>
              <button
                className="toolbar__btn toolbar__btn--danger"
                onClick={confirmRevealAll}
              >
                Show me everything
              </button>
            </div>
          </div>
        </div>
      )}

      {isComplete && (
        <div className="toolbar__complete">
          Puzzle Complete!
        </div>
      )}
    </div>
  )
}
