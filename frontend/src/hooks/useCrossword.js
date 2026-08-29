import { useState, useCallback, useMemo } from 'react'

export function useCrossword() {
  const [puzzle, setPuzzle] = useState(null)
  const [userGrid, setUserGrid] = useState([])
  const [selectedCell, setSelectedCell] = useState(null)
  const [direction, setDirection] = useState('across')
  const [revealedCells, setRevealedCells] = useState(new Set())
  const [checkedCells, setCheckedCells] = useState({})
  const [isComplete, setIsComplete] = useState(false)

  const loadPuzzle = useCallback((data) => {
    setPuzzle(data)
    const rows = data.grid.length
    const cols = data.grid[0].length
    setUserGrid(
      Array.from({ length: rows }, () => Array.from({ length: cols }, () => ''))
    )
    setSelectedCell(null)
    setDirection('across')
    setRevealedCells(new Set())
    setCheckedCells({})
    setIsComplete(false)
  }, [])

  const wordsAcross = useMemo(
    () => (puzzle?.words || []).filter(w => w.direction === 'across').sort((a, b) => a.number - b.number),
    [puzzle]
  )

  const wordsDown = useMemo(
    () => (puzzle?.words || []).filter(w => w.direction === 'down').sort((a, b) => a.number - b.number),
    [puzzle]
  )

  const allWords = useMemo(() => [...wordsAcross, ...wordsDown], [wordsAcross, wordsDown])

  const activeWord = useMemo(() => {
    if (!selectedCell || !puzzle) return null
    const { row, col } = selectedCell

    const matching = allWords.filter(w => {
      if (w.direction === direction) {
        if (direction === 'across') {
          return row === w.row && col >= w.col && col < w.col + w.length
        } else {
          return col === w.col && row >= w.row && row < w.row + w.length
        }
      }
      return false
    })

    if (matching.length > 0) return matching[0]

    const other = direction === 'across' ? 'down' : 'across'
    const fallback = allWords.filter(w => {
      if (w.direction === other) {
        if (other === 'across') {
          return row === w.row && col >= w.col && col < w.col + w.length
        } else {
          return col === w.col && row >= w.row && row < w.row + w.length
        }
      }
      return false
    })

    return fallback[0] || null
  }, [selectedCell, direction, allWords, puzzle])

  const highlightedCells = useMemo(() => {
    if (!activeWord) return new Set()
    const cells = new Set()
    for (let i = 0; i < activeWord.length; i++) {
      const r = activeWord.direction === 'across' ? activeWord.row : activeWord.row + i
      const c = activeWord.direction === 'across' ? activeWord.col + i : activeWord.col
      cells.add(`${r},${c}`)
    }
    return cells
  }, [activeWord])

  const selectCell = useCallback((row, col) => {
    if (!puzzle || puzzle.grid[row]?.[col] === '#') return

    if (selectedCell?.row === row && selectedCell?.col === col) {
      setDirection(d => d === 'across' ? 'down' : 'across')
    } else {
      setSelectedCell({ row, col })
    }
  }, [puzzle, selectedCell])

  const setCellValue = useCallback((row, col, value) => {
    setUserGrid(prev => {
      const next = prev.map(r => [...r])
      next[row][col] = value.toUpperCase()
      return next
    })
    setCheckedCells(prev => {
      const next = { ...prev }
      delete next[`${row},${col}`]
      return next
    })
  }, [])

  const moveToNextCell = useCallback(() => {
    if (!selectedCell || !puzzle) return
    const { row, col } = selectedCell
    if (direction === 'across') {
      for (let c = col + 1; c < puzzle.grid[0].length; c++) {
        if (puzzle.grid[row][c] !== '#') {
          setSelectedCell({ row, col: c })
          return
        }
      }
    } else {
      for (let r = row + 1; r < puzzle.grid.length; r++) {
        if (puzzle.grid[r][col] !== '#') {
          setSelectedCell({ row: r, col })
          return
        }
      }
    }
  }, [selectedCell, direction, puzzle])

  const moveToNextEmptyInWord = useCallback(() => {
    if (!selectedCell || !puzzle || !activeWord) return false
    const { row, col } = selectedCell
    for (let i = 0; i < activeWord.length; i++) {
      const r = activeWord.direction === 'across' ? activeWord.row : activeWord.row + i
      const c = activeWord.direction === 'across' ? activeWord.col + i : activeWord.col
      if ((r !== row || c !== col) && !userGrid[r]?.[c]) {
        setSelectedCell({ row: r, col: c })
        return true
      }
    }
    return false
  }, [selectedCell, puzzle, activeWord, userGrid])

  const moveToPrevCell = useCallback(() => {
    if (!selectedCell || !puzzle) return
    const { row, col } = selectedCell
    if (direction === 'across') {
      for (let c = col - 1; c >= 0; c--) {
        if (puzzle.grid[row][c] !== '#') {
          setSelectedCell({ row, col: c })
          return
        }
      }
    } else {
      for (let r = row - 1; r >= 0; r--) {
        if (puzzle.grid[r][col] !== '#') {
          setSelectedCell({ row: r, col })
          return
        }
      }
    }
  }, [selectedCell, direction, puzzle])

  const moveDirection = useCallback((dr, dc) => {
    if (!selectedCell || !puzzle) return
    let r = selectedCell.row + dr
    let c = selectedCell.col + dc
    while (r >= 0 && r < puzzle.grid.length && c >= 0 && c < puzzle.grid[0].length) {
      if (puzzle.grid[r][c] !== '#') {
        setSelectedCell({ row: r, col: c })
        return
      }
      r += dr
      c += dc
    }
  }, [selectedCell, puzzle])

  const selectClue = useCallback((word) => {
    setDirection(word.direction)
    setSelectedCell({ row: word.row, col: word.col })
  }, [])

  const selectNextClue = useCallback(() => {
    if (!activeWord) {
      if (allWords.length > 0) selectClue(allWords[0])
      return
    }
    const list = activeWord.direction === 'across' ? wordsAcross : wordsDown
    const idx = list.findIndex(w => w.number === activeWord.number)
    if (idx < list.length - 1) {
      selectClue(list[idx + 1])
    } else {
      const other = activeWord.direction === 'across' ? wordsDown : wordsAcross
      if (other.length > 0) selectClue(other[0])
    }
  }, [activeWord, wordsAcross, wordsDown, allWords, selectClue])

  const selectPrevClue = useCallback(() => {
    if (!activeWord) return
    const list = activeWord.direction === 'across' ? wordsAcross : wordsDown
    const idx = list.findIndex(w => w.number === activeWord.number)
    if (idx > 0) {
      selectClue(list[idx - 1])
    } else {
      const other = activeWord.direction === 'across' ? wordsDown : wordsAcross
      if (other.length > 0) selectClue(other[other.length - 1])
    }
  }, [activeWord, wordsAcross, wordsDown, selectClue])

  const revealLetter = useCallback(() => {
    if (!selectedCell || !puzzle) return
    const { row, col } = selectedCell
    const answer = puzzle.grid[row][col]
    if (answer === '#') return
    setCellValue(row, col, answer)
    setRevealedCells(prev => new Set(prev).add(`${row},${col}`))
  }, [selectedCell, puzzle, setCellValue])

  const revealWord = useCallback(() => {
    if (!activeWord || !puzzle) return
    setUserGrid(prev => {
      const next = prev.map(r => [...r])
      const newRevealed = new Set(revealedCells)
      for (let i = 0; i < activeWord.length; i++) {
        const r = activeWord.direction === 'across' ? activeWord.row : activeWord.row + i
        const c = activeWord.direction === 'across' ? activeWord.col + i : activeWord.col
        next[r][c] = puzzle.grid[r][c]
        newRevealed.add(`${r},${c}`)
      }
      setRevealedCells(newRevealed)
      return next
    })
  }, [activeWord, puzzle, revealedCells])

  const revealAll = useCallback(() => {
    if (!puzzle) return
    const newGrid = puzzle.grid.map(row =>
      row.map(cell => cell === '#' ? '' : cell)
    )
    setUserGrid(newGrid)
    const newRevealed = new Set()
    for (let r = 0; r < puzzle.grid.length; r++) {
      for (let c = 0; c < puzzle.grid[r].length; c++) {
        if (puzzle.grid[r][c] !== '#') {
          newRevealed.add(`${r},${c}`)
        }
      }
    }
    setRevealedCells(newRevealed)
    setCheckedCells({})
  }, [puzzle])

  const clearWord = useCallback(() => {
    if (!activeWord || !puzzle) return
    setUserGrid(prev => {
      const next = prev.map(r => [...r])
      for (let i = 0; i < activeWord.length; i++) {
        const r = activeWord.direction === 'across' ? activeWord.row : activeWord.row + i
        const c = activeWord.direction === 'across' ? activeWord.col + i : activeWord.col
        if (!revealedCells.has(`${r},${c}`)) {
          next[r][c] = ''
        }
      }
      return next
    })
    setCheckedCells(prev => {
      const next = { ...prev }
      for (let i = 0; i < activeWord.length; i++) {
        const r = activeWord.direction === 'across' ? activeWord.row : activeWord.row + i
        const c = activeWord.direction === 'across' ? activeWord.col + i : activeWord.col
        delete next[`${r},${c}`]
      }
      return next
    })
    setSelectedCell({ row: activeWord.row, col: activeWord.col })
  }, [activeWord, puzzle, revealedCells])

  const checkWord = useCallback(() => {
    if (!activeWord || !puzzle) return
    const results = { ...checkedCells }
    for (let i = 0; i < activeWord.length; i++) {
      const r = activeWord.direction === 'across' ? activeWord.row : activeWord.row + i
      const c = activeWord.direction === 'across' ? activeWord.col + i : activeWord.col
      const userVal = userGrid[r]?.[c] || ''
      if (!userVal) continue
      const key = `${r},${c}`
      results[key] = userVal === puzzle.grid[r][c] ? 'correct' : 'incorrect'
    }
    setCheckedCells(results)
  }, [activeWord, puzzle, userGrid, checkedCells])

  const checkAnswers = useCallback(() => {
    if (!puzzle) return
    const results = {}
    let allCorrect = true
    for (let r = 0; r < puzzle.grid.length; r++) {
      for (let c = 0; c < puzzle.grid[r].length; c++) {
        if (puzzle.grid[r][c] === '#') continue
        const userVal = userGrid[r]?.[c] || ''
        if (!userVal) {
          allCorrect = false
          continue
        }
        const key = `${r},${c}`
        if (userVal === puzzle.grid[r][c]) {
          results[key] = 'correct'
        } else {
          results[key] = 'incorrect'
          allCorrect = false
        }
      }
    }
    setCheckedCells(results)
    if (allCorrect) setIsComplete(true)
  }, [puzzle, userGrid])

  return {
    puzzle, userGrid, selectedCell, direction, revealedCells, checkedCells,
    isComplete, highlightedCells, activeWord, wordsAcross, wordsDown,
    loadPuzzle, selectCell, setCellValue, moveToNextCell, moveToNextEmptyInWord,
    moveToPrevCell, moveDirection, selectClue, selectNextClue, selectPrevClue,
    revealLetter, revealWord, revealAll, clearWord, checkWord, checkAnswers,
    setDirection,
  }
}
