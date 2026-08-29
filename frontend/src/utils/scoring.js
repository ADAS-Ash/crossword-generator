export function calculateScore(puzzle, userGrid, revealedCells) {
  if (!puzzle) return { correct: 0, total: 0, percentage: 0 }

  let correct = 0
  let total = 0

  for (let r = 0; r < puzzle.grid.length; r++) {
    for (let c = 0; c < puzzle.grid[r].length; c++) {
      if (puzzle.grid[r][c] === '#') continue
      total++
      const userVal = userGrid[r]?.[c] || ''
      const isRevealed = revealedCells.has(`${r},${c}`)
      if (userVal === puzzle.grid[r][c] && !isRevealed) {
        correct++
      }
    }
  }

  return {
    correct,
    total,
    percentage: total > 0 ? Math.round((correct / total) * 100) : 0,
  }
}
