import { useCallback } from 'react'

export function useKeyboardNav({
  selectedCell, direction, puzzle, userGrid,
  setCellValue, moveToNextCell, moveToNextEmptyInWord, moveToPrevCell,
  moveDirection, selectNextClue, selectPrevClue,
  setDirection, selectCell,
}) {
  const handleKeyDown = useCallback((e) => {
    if (!selectedCell || !puzzle) return

    const { row, col } = selectedCell

    switch (e.key) {
      case 'ArrowUp':
        e.preventDefault()
        moveDirection(-1, 0)
        break
      case 'ArrowDown':
        e.preventDefault()
        moveDirection(1, 0)
        break
      case 'ArrowLeft':
        e.preventDefault()
        moveDirection(0, -1)
        break
      case 'ArrowRight':
        e.preventDefault()
        moveDirection(0, 1)
        break
      case 'Tab':
        e.preventDefault()
        if (e.shiftKey) {
          selectPrevClue()
        } else {
          selectNextClue()
        }
        break
      case 'Backspace':
        e.preventDefault()
        if (userGrid[row]?.[col]) {
          setCellValue(row, col, '')
        } else {
          moveToPrevCell()
        }
        break
      case 'Delete':
        e.preventDefault()
        setCellValue(row, col, '')
        break
      case ' ':
        e.preventDefault()
        setDirection(d => d === 'across' ? 'down' : 'across')
        break
      default:
        if (/^[a-zA-Z]$/.test(e.key)) {
          e.preventDefault()
          setCellValue(row, col, e.key.toUpperCase())
          if (!moveToNextEmptyInWord()) {
            moveToNextCell()
          }
        }
    }
  }, [
    selectedCell, direction, puzzle, userGrid,
    setCellValue, moveToNextCell, moveToNextEmptyInWord, moveToPrevCell,
    moveDirection, selectNextClue, selectPrevClue,
    setDirection, selectCell,
  ])

  return { handleKeyDown }
}
