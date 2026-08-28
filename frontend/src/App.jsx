import { useState, useCallback } from 'react'
import { generateCrossword } from './api/crossword'
import { useCrossword } from './hooks/useCrossword'
import { useKeyboardNav } from './hooks/useKeyboardNav'
import { useTimer } from './hooks/useTimer'
import { useTheme } from './hooks/useTheme'
import { TopicForm } from './components/TopicForm'
import { Toolbar } from './components/Toolbar'
import { CrosswordGrid } from './components/CrosswordGrid'
import { CluePanel } from './components/CluePanel'
import { LoadingOverlay } from './components/LoadingOverlay'
import './App.css'

function App() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const { isDark, toggleTheme } = useTheme()
  const timer = useTimer()

  const crossword = useCrossword()
  const { handleKeyDown } = useKeyboardNav({
    selectedCell: crossword.selectedCell,
    direction: crossword.direction,
    puzzle: crossword.puzzle,
    userGrid: crossword.userGrid,
    setCellValue: crossword.setCellValue,
    moveToNextCell: crossword.moveToNextCell,
    moveToPrevCell: crossword.moveToPrevCell,
    moveDirection: crossword.moveDirection,
    selectNextClue: crossword.selectNextClue,
    selectPrevClue: crossword.selectPrevClue,
    setDirection: crossword.setDirection,
    selectCell: crossword.selectCell,
  })

  const handleGenerate = useCallback(async (topic, gridSize) => {
    setIsLoading(true)
    setError(null)
    timer.reset()
    try {
      const data = await generateCrossword(topic, gridSize)
      crossword.loadPuzzle(data)
      timer.start()
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }, [crossword, timer])

  return (
    <div className="app">
      <header className="app__header">
        <h1 className="app__title">Crossword Generator<span className="app__powered">by NaikLabs</span></h1>
        <p className="app__subtitle">AI-powered puzzles on any topic</p>
      </header>

      <div className="app__form-section">
        <TopicForm onGenerate={handleGenerate} isLoading={isLoading} />
      </div>

      {error && (
        <div className="app__error">
          <p>{error}</p>
        </div>
      )}

      {crossword.puzzle && (
        <>
          <Toolbar
            puzzle={crossword.puzzle}
            userGrid={crossword.userGrid}
            revealedCells={crossword.revealedCells}
            timerFormatted={timer.formatted}
            timerRunning={timer.isRunning}
            onTimerToggle={timer.toggle}
            onRevealLetter={crossword.revealLetter}
            onRevealWord={crossword.revealWord}
            onCheckAnswers={crossword.checkAnswers}
            isDark={isDark}
            onToggleTheme={toggleTheme}
            isComplete={crossword.isComplete}
          />

          <div className="app__puzzle">
            <div className="app__grid-container">
              <LoadingOverlay isLoading={isLoading} />
              <CrosswordGrid
                puzzle={crossword.puzzle}
                userGrid={crossword.userGrid}
                selectedCell={crossword.selectedCell}
                highlightedCells={crossword.highlightedCells}
                revealedCells={crossword.revealedCells}
                checkedCells={crossword.checkedCells}
                selectCell={crossword.selectCell}
                onKeyDown={handleKeyDown}
              />
            </div>
            <CluePanel
              wordsAcross={crossword.wordsAcross}
              wordsDown={crossword.wordsDown}
              activeWord={crossword.activeWord}
              onSelectClue={crossword.selectClue}
            />
          </div>

          <div className="app__meta">
            <span>Theme: {crossword.puzzle.metadata.topic}</span>
            <span>Words: {crossword.puzzle.metadata.words_placed}</span>
            <span>Provider: {crossword.puzzle.metadata.provider}</span>
          </div>
        </>
      )}

      {!crossword.puzzle && !isLoading && (
        <div className="app__empty">
          <p>Enter a topic above and generate your first puzzle!</p>
        </div>
      )}

      {isLoading && !crossword.puzzle && (
        <div className="app__loading-standalone">
          <LoadingOverlay isLoading={true} />
        </div>
      )}

      <footer className="app__footer">
        <p>Powered by <a href="https://naiklabs.dev" target="_blank" rel="noopener">NaikLabs</a></p>
      </footer>
    </div>
  )
}

export default App
