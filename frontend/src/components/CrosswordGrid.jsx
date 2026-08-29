import { useRef, useEffect, forwardRef, useImperativeHandle } from 'react'
import { CrosswordCell } from './CrosswordCell'
import './CrosswordGrid.css'

export const CrosswordGrid = forwardRef(function CrosswordGrid({
  puzzle, userGrid, selectedCell, highlightedCells,
  revealedCells, checkedCells, selectCell, onKeyDown,
}, ref) {
  const gridRef = useRef(null)

  useImperativeHandle(ref, () => gridRef.current)

  useEffect(() => {
    if (selectedCell && gridRef.current) {
      gridRef.current.focus()
    }
  }, [selectedCell])

  const handleCellClick = (row, col) => {
    selectCell(row, col)
    if (gridRef.current) gridRef.current.focus()
  }

  if (!puzzle) return null

  const rows = puzzle.grid.length
  const cols = puzzle.grid[0].length

  const cellNumbers = {}
  for (const w of puzzle.words) {
    cellNumbers[`${w.row},${w.col}`] = w.number
  }

  return (
    <div
      ref={gridRef}
      className="crossword-grid"
      style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}
      tabIndex={0}
      onKeyDown={onKeyDown}
    >
      {puzzle.grid.map((row, r) =>
        row.map((cell, c) => {
          const key = `${r},${c}`
          return (
            <CrosswordCell
              key={key}
              row={r}
              col={c}
              value={userGrid[r]?.[c] || ''}
              answer={cell}
              number={cellNumbers[key]}
              isBlack={cell === '#'}
              isSelected={selectedCell?.row === r && selectedCell?.col === c}
              isHighlighted={highlightedCells.has(key)}
              isRevealed={revealedCells.has(key)}
              checkStatus={checkedCells[key]}
              onClick={handleCellClick}
            />
          )
        })
      )}
    </div>
  )
})
