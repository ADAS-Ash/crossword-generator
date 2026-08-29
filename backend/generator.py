class CrosswordGenerator:
    def __init__(self, size: int = 15):
        self.size = size
        self.grid: list[list[str]] = [[" " for _ in range(size)] for _ in range(size)]
        self.placed_words: list[dict] = []

    def generate(self, words: list[str]) -> "CrosswordGenerator":
        words = sorted([w.upper() for w in words if w.isalpha()], key=len, reverse=True)
        if not words:
            return self

        first = words.pop(0)
        row = self.size // 2
        col = (self.size - len(first)) // 2
        self._place_word(first, row, col, "H")

        for word in words:
            self._try_place(word)

        return self

    def _try_place(self, word: str):
        best = None
        best_score = 0

        for r in range(self.size):
            for c in range(self.size):
                cell = self.grid[r][c]
                if cell == " ":
                    continue
                for i, ch in enumerate(word):
                    if ch != cell:
                        continue
                    hr, hc = r, c - i
                    if self._can_place(word, hr, hc, "H"):
                        score = self._score_placement(word, hr, hc, "H")
                        if score > best_score:
                            best_score = score
                            best = (hr, hc, "H")

                    vr, vc = r - i, c
                    if self._can_place(word, vr, vc, "V"):
                        score = self._score_placement(word, vr, vc, "V")
                        if score > best_score:
                            best_score = score
                            best = (vr, vc, "V")

        if best:
            self._place_word(word, *best)

    def _score_placement(self, word: str, row: int, col: int, direction: str) -> int:
        score = 0
        for i in range(len(word)):
            r = row if direction == "H" else row + i
            c = col + i if direction == "H" else col
            if self.grid[r][c] == word[i]:
                score += 1
        return score

    def _can_place(self, word: str, row: int, col: int, direction: str) -> bool:
        length = len(word)

        if direction == "H":
            if col < 0 or col + length > self.size or row < 0 or row >= self.size:
                return False
        else:
            if row < 0 or row + length > self.size or col < 0 or col >= self.size:
                return False

        intersections = 0
        for i in range(length):
            r = row if direction == "H" else row + i
            c = col + i if direction == "H" else col
            cell = self.grid[r][c]

            if cell != " " and cell != word[i]:
                return False

            if cell == word[i]:
                intersections += 1
            else:
                if direction == "H":
                    if r > 0 and self.grid[r - 1][c] != " ":
                        return False
                    if r < self.size - 1 and self.grid[r + 1][c] != " ":
                        return False
                else:
                    if c > 0 and self.grid[r][c - 1] != " ":
                        return False
                    if c < self.size - 1 and self.grid[r][c + 1] != " ":
                        return False

        if direction == "H":
            if col > 0 and self.grid[row][col - 1] != " ":
                return False
            if col + length < self.size and self.grid[row][col + length] != " ":
                return False
        else:
            if row > 0 and self.grid[row - 1][col] != " ":
                return False
            if row + length < self.size and self.grid[row + length][col] != " ":
                return False

        return intersections > 0

    def _place_word(self, word: str, row: int, col: int, direction: str):
        for i, char in enumerate(word):
            r = row if direction == "H" else row + i
            c = col + i if direction == "H" else col
            self.grid[r][c] = char
        self.placed_words.append({
            "word": word, "row": row, "col": col, "direction": direction,
        })

    def crop(self) -> "CrosswordGenerator":
        min_r, max_r = self.size, 0
        min_c, max_c = self.size, 0

        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] != " ":
                    min_r = min(min_r, r)
                    max_r = max(max_r, r)
                    min_c = min(min_c, c)
                    max_c = max(max_c, c)

        if min_r > max_r:
            return self

        new_rows = max_r - min_r + 1
        new_cols = max_c - min_c + 1
        new_grid = [
            [self.grid[r][c] for c in range(min_c, max_c + 1)]
            for r in range(min_r, max_r + 1)
        ]

        for pw in self.placed_words:
            pw["row"] -= min_r
            pw["col"] -= min_c

        self.grid = new_grid
        self.size = max(new_rows, new_cols)
        self._rows = new_rows
        self._cols = new_cols
        return self

    @property
    def rows(self) -> int:
        return getattr(self, "_rows", len(self.grid))

    @property
    def cols(self) -> int:
        return getattr(self, "_cols", len(self.grid[0]) if self.grid else 0)

    def number_clues(self) -> dict:
        rows = self.rows
        cols = self.cols

        number = 1
        cell_numbers: dict[tuple[int, int], int] = {}

        for r in range(rows):
            for c in range(cols):
                if c >= len(self.grid[r]) or self.grid[r][c] == " ":
                    continue
                starts_across = (
                    (c == 0 or self.grid[r][c - 1] == " ")
                    and c + 1 < cols
                    and c + 1 < len(self.grid[r])
                    and self.grid[r][c + 1] != " "
                )
                starts_down = (
                    (r == 0 or self.grid[r - 1][c] == " ")
                    and r + 1 < rows
                    and self.grid[r + 1][c] != " "
                )
                if starts_across or starts_down:
                    cell_numbers[(r, c)] = number
                    number += 1

        return cell_numbers

    def build_response_grid(self) -> list[list[str]]:
        rows = self.rows
        cols = self.cols
        result = []
        for r in range(rows):
            row = []
            for c in range(cols):
                if c < len(self.grid[r]) and self.grid[r][c] != " ":
                    row.append(self.grid[r][c])
                else:
                    row.append("#")
            result.append(row)
        return result
