import tkinter as tk # for gui
from tkinter import messagebox
import random
from collections import deque
from ai_logger import log_game
from ai_performance_analyzer import AIPerformanceAnalyzer

# ------------------------------
# center Window fnction:
# -------------------------------
def center_window(window, width, height):
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")
# ------------------------------
# Custom Colored Message Box
# ------------------------------
def colored_msg(title, msg, color="#2b2b55", fg="white"):
    box = tk.Toplevel()
    box.title(title)
    box.resizable(False, False)
    center_window(box, 380, 170)
    box.configure(bg=color)

    tk.Label(box,text=msg,fg=fg,bg=color,font=("Arial", 11),wraplength=340).pack(pady=30)

    tk.Button(box,text="OK",width=12,bg="#444488",fg="white",command=box.destroy).pack(pady=10)

    box.grab_set()
    box.focus_set()
    box.wait_window()   # Wait until user closes the popup

# -------------------------------
# Maze Game menu
# -------------------------------
class MazeGameMenu:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Maze Game Settings")
        self.window.resizable(False, False)
        self.center_window(600, 700)
        self.main = tk.Frame(self.window, bg="#202030")
        self.main.pack(fill="both", expand=True)
        self.create_widgets() # for labels & buttons
        self.window.geometry("600x700")

    def center_window(self, w, h):
        self.window.update_idletasks()
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        x = (sw // 2) - (w // 2)
        y = (sh // 2) - (h // 2)
        self.window.geometry(f"{w}x{h}+{x}+{y}")

    def create_widgets(self):
        tk.Label(self.main, text="🧩 MAZE GAME SETTINGS", font=("Arial", 20, "bold"), fg="white", bg="#202030").pack(pady=20)


        self.username = tk.StringVar()

        tk.Label(self.main, text="Player Name", fg="lightblue", bg="#202030").pack(pady=5)
        tk.Entry(self.main, textvariable=self.username, width=25).pack()

        # Maze Shapes
        self.shape = tk.StringVar(value="Square Grid")
        tk.Label(self.main, text="Maze Shape", font=("Arial", 14, "bold"), fg="lightblue", bg="#202030").pack(pady=10)
        shapes = ["Square Grid", "Rectangle Grid", "Spiral Maze", "Zig-Zag Maze", "Random Blocks"]
        for s in shapes:
            tk.Radiobutton(self.main, text=s, variable=self.shape, value=s, bg="#202030", fg="white", selectcolor="#202030").pack(anchor="w", padx=140)

        # AI Algorithm
        self.algorithm = tk.StringVar(value="BFS")
        tk.Label(self.main, text="AI Algorithm", font=("Arial", 14, "bold"), fg="lightblue", bg="#202030").pack(pady=10)
        for algo in ["BFS", "DFS"]:
            tk.Radiobutton(self.main, text=algo, variable=self.algorithm, value=algo, bg="#202030", fg="white", selectcolor="#202030").pack(anchor="w", padx=140)

        # Difficulty
        self.difficulty = tk.StringVar(value="Easy")
        tk.Label(self.main, text="Difficulty Level", font=("Arial", 14, "bold"), fg="lightblue", bg="#202030").pack(pady=10)
        for diff in ["Easy", "Medium", "Hard"]:
            tk.Radiobutton(self.main, text=diff, variable=self.difficulty, value=diff, bg="#202030", fg="white", selectcolor="#202030").pack(anchor="w", padx=140)

        # Buttons
        tk.Button(self.main, text="▶ START GAME", width=22, height=2, bg="#3cb371", fg="white", font=("Arial", 12, "bold"), command=self.start_game).pack(pady=20)
        tk.Button(self.main, text="⬅ Back to Arena", width=22, height=2, bg="#555", fg="white", command=self.window.destroy).pack()

    def start_game(self):
        self.window.destroy()
        MazeGame(tk.Toplevel(self.parent), self.shape.get(), self.algorithm.get(), self.difficulty.get(), self.username.get())

# -------------------------------
# Maze Game Class
# -------------------------------
class MazeGame:
    def __init__(self, root, shape="Square Grid", algorithm="BFS", difficulty="Easy",player_name="player"):
        self.root = root
        self.parent = root.master
        self.shape = shape
        self.algorithm = algorithm
        self.difficulty = difficulty
        self.player_name = player_name

        # Main highlights
        self.show_ai_path = False
        self.ai_path = []
        self.visited_path = set()
        self.wrong_attempts = 0
        self.wrong_cell = None
        self.moves = 0

        # Maze size
        if difficulty == "Easy":
            self.rows = self.cols = 8
        elif difficulty == "Medium":
            self.rows = self.cols = 12
        else:
            self.rows = self.cols = 16

        self.cell_size = 40
        self.grid = [[0]*self.cols for _ in range(self.rows)]
        self.cells = [[None]*self.cols for _ in range(self.rows)]

        self.player = (0, 0)
        self.end = (self.rows-1, self.cols-1)

        self.create_ui()
        self.generate_maze()
        self.calculate_ai_path()
        self.draw_maze()

        self.root.bind("<Up>", lambda e: self.move(-1, 0))
        self.root.bind("<Down>", lambda e: self.move(1, 0))
        self.root.bind("<Left>", lambda e: self.move(0, -1))
        self.root.bind("<Right>", lambda e: self.move(0, 1))

    # ---------------- UI ----------------
    def create_ui(self):
        self.root.title("Maze Solver - AI Game")
        self.root.resizable(False, False)
        center_window(self.root,
                      self.cols*self.cell_size + 200,
                      self.rows*self.cell_size + 100)

        self.grid_frame = tk.Frame(self.root, bg="#1e1e2f")
        self.grid_frame.pack(side="left", padx=20, pady=20)

        self.control_frame = tk.Frame(self.root, bg="#1e1e2f")
        self.control_frame.pack(side="right", padx=20, pady=20)

        tk.Label(self.control_frame, text=f"Algorithm: {self.algorithm}",
                 font=("Arial", 14, "bold"),
                 fg="white", bg="#1e1e2f").pack(pady=10)

        self.moves_label = tk.Label(self.control_frame, text="Moves: 0",
                                    font=("Arial", 12, "bold"),
                                    fg="yellow", bg="#1e1e2f")
        self.moves_label.pack(pady=5)

        self.wrong_label = tk.Label(self.control_frame, text="Wrong Attempts: 0",
                                    font=("Arial", 12, "bold"),
                                    fg="red", bg="#1e1e2f")
        self.wrong_label.pack(pady=5)

        tk.Button(self.control_frame, text="Hint", width=15,
                  command=self.show_hint).pack(pady=5)

        tk.Button(self.control_frame, text="Toggle AI Path", width=15,
                  command=self.toggle_ai_path).pack(pady=5)

        tk.Button(self.control_frame, text="AI Auto Solve", width=15,
                  command=self.auto_solve).pack(pady=5)

        tk.Button(self.control_frame, text="Reset Maze", width=15,
                  command=self.reset_game).pack(pady=20)

        for r in range(self.rows):
            for c in range(self.cols):
                lbl = tk.Label(self.grid_frame, width=3, height=1,
                               relief="solid", bg="white", borderwidth=1)
                lbl.grid(row=r, column=c)
                self.cells[r][c] = lbl

    # ---------------- Maze Generation ----------------
    def generate_maze(self):
        for r in range(self.rows):
            for c in range(self.cols):
                self.grid[r][c] = random.choice([0, 0, 0, 1])

        self.grid[0][0] = 0
        self.grid[self.end[0]][self.end[1]] = 0

        #ensurance karna ke starting point/target node ka aik cell open ho
        if self.cols > 1:
            self.grid[0][1] = 0
        if self.rows > 1:
            self.grid[1][0] = 0

        #ensurance karna ke ending point/target node ka aik cell empty ho
        er, ec = self.end
        if ec - 1 >= 0:
            self.grid[er][ec - 1] = 0
        if er - 1 >= 0:
            self.grid[er - 1][ec] = 0

        if self.shape == "Zig-Zag Maze":
            for r in range(self.rows):
                for c in range(self.cols):
                    self.grid[r][c] = 0 if (r + c) % 2 == 0 else 1

        if self.shape == "Spiral Maze":
            for r in range(self.rows):
                for c in range(self.cols):
                    self.grid[r][c] = 1

            top, left = 0, 0
            bottom, right = self.rows - 1, self.cols - 1

            while top <= bottom and left <= right:
                for c in range(left, right + 1):
                    self.grid[top][c] = 0
                top += 1

                for r in range(top, bottom + 1):
                    self.grid[r][right] = 0
                right -= 1

    # ---------------- AI PATH ----------------
    def calculate_ai_path(self):
        self.ai_path = self.bfs() if self.algorithm == "BFS" else self.dfs()

    def bfs(self):
        queue = deque([(self.player, [self.player])])
        visited = {self.player}

        while queue:
            (r, c), path = queue.popleft()
            if (r, c) == self.end:
                return path

            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    if self.grid[nr][nc] == 0 and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append(((nr, nc), path+[(nr, nc)]))
        return []

    def dfs(self):
        stack = [(self.player, [self.player])]
        visited = {self.player}

        while stack:
            (r, c), path = stack.pop()
            if (r, c) == self.end:
                return path

            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    if self.grid[nr][nc] == 0 and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        stack.append(((nr, nc), path+[(nr, nc)]))
        return []

    # ---------------- Movement ----------------
    def move(self, dr, dc):
        r, c = self.player
        nr, nc = r+dr, c+dc

        if not (0 <= nr < self.rows and 0 <= nc < self.cols):
            return

        self.moves += 1

        if self.grid[nr][nc] == 1 or (nr, nc) not in self.ai_path:
            self.wrong_attempts += 1
            self.wrong_cell = (nr, nc)
        else:
            self.player = (nr, nc)
            self.visited_path.add(self.player)
            self.wrong_cell = None

        self.draw_maze()

        if self.player == self.end:

            #GAME DATA LOGGING
            log_game(
                game="Maze",
                player=self.player_name,
                metric="Moves",
                value=self.moves,
                result="Win"
            )
            colored_msg("Victory 🎉",
                        f"Solved using {self.algorithm}\nMoves: {self.moves}",
                        "#004d00")
            self.root.destroy()

    # ---------------- Extra Features ----------------
    def toggle_ai_path(self):
        self.show_ai_path = not self.show_ai_path
        self.draw_maze()

    def auto_solve(self):
        def step(i):
            if i < len(self.ai_path):
                self.player = self.ai_path[i]
                self.visited_path.add(self.player)
                self.draw_maze()
                if self.player == self.end:
                    colored_msg("Victory 🎉",
                                f"Solved using {self.algorithm}\nMoves: {self.moves}",
                                "#004d00")
                    self.root.destroy()
                    return
                self.root.after(300, lambda: step(i + 1))

        step(0)

    def show_hint(self):
        if self.player in self.ai_path:
            i = self.ai_path.index(self.player)
            if i+1 < len(self.ai_path):
                r, c = self.ai_path[i+1]
                self.cells[r][c].config(bg="blue")
                self.root.after(400, self.draw_maze)

    def draw_maze(self):
        for r in range(self.rows):
            for c in range(self.cols):
                color = "white"
                if self.grid[r][c] == 1:
                    color = "black"
                if (r, c) in self.visited_path:
                    color = "yellow"
                if (r, c) == self.wrong_cell:
                    color = "red"
                if self.show_ai_path and (r, c) in self.ai_path:
                    color = "#add8e6"
                if (r, c) == self.player:
                    color = "green"
                if (r, c) == self.end:
                    color = "red"
                self.cells[r][c].config(bg=color)

        self.moves_label.config(text=f"Moves: {self.moves}")
        self.wrong_label.config(text=f"Wrong Attempts: {self.wrong_attempts}")

    def reset_game(self):
        parent = self.root.master
        self.root.destroy()
        if parent:
            MazeGameMenu(parent)    #Kabhi kabhi root.master None hota toh  → crash ho sakta


# -------------------------------
# Tic Tac Toe Menu
# -------------------------------
class TicTacToeMenu:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Tic Tac Toe - Menu")
        self.window.resizable(False, False)
        center_window(self.window, 420, 500)

        self.main = tk.Frame(self.window, bg="#1e1e2f")
        self.main.pack(fill="both", expand=True)

        tk.Label(self.main,text="TIC TAC TOE",font=("Arial", 22, "bold"),fg="white",bg="#1e1e2f").pack(pady=20)
        self.player1 = tk.StringVar()
        self.player2 = tk.StringVar(value="AI")

        tk.Label(self.main, text="Player 1 Name", fg="lightblue", bg="#1e1e2f").pack()
        tk.Entry(self.main, textvariable=self.player1, width=25).pack(pady=5)

        self.mode = tk.StringVar(value="AI")
        self.difficulty = tk.StringVar(value="Hard")

        tk.Label(self.main, text="AI Difficulty", fg="lightblue", bg="#1e1e2f").pack(pady=5)

        tk.Radiobutton(self.main, text="Easy", variable=self.difficulty,
                       value="Easy", bg="#1e1e2f", fg="white",
                       selectcolor="#1e1e2f").pack()

        tk.Radiobutton(self.main, text="Hard", variable=self.difficulty,
                       value="Hard", bg="#1e1e2f", fg="white",
                       selectcolor="#1e1e2f").pack()

        tk.Radiobutton(
            self.main, text="Play with AI",
            variable=self.mode, value="AI",
            bg="#1e1e2f", fg="white", selectcolor="#1e1e2f"
        ).pack(pady=5)

        tk.Radiobutton(
            self.main, text="2 Players",
            variable=self.mode, value="2P",
            bg="#1e1e2f", fg="white", selectcolor="#1e1e2f"
        ).pack(pady=5)

        tk.Label(self.main, text="Player 2 Name", fg="lightblue", bg="#1e1e2f").pack()
        tk.Entry(self.main, textvariable=self.player2, width=25).pack(pady=5)

        tk.Button(
            self.main, text="▶ START GAME",
            width=20, height=2,
            bg="#444488", fg="white",
            command=self.start_game
        ).pack(pady=25)

        tk.Button(
            self.main, text="⬅ Back",
            width=20, bg="#555",
            fg="white", command=self.window.destroy
        ).pack()

    def start_game(self):
        if not self.player1.get():
            colored_msg("Missing Info", "Please enter Player 1 name")
            return

        self.window.destroy()
        TicTacToeGame(
            self.parent,
            self.player1.get(),
            self.player2.get(),
            self.mode.get(),
            self.difficulty.get()
        )

# -------------------------------
# Tic Tac Toe Game
# -------------------------------
class TicTacToeGame:
    def __init__(self, parent, p1, p2, mode, difficulty="Hard"):
        self.window = tk.Toplevel(parent)
        self.window.title("Tic Tac Toe")
        center_window(self.window, 420, 540)
        self.window.resizable(False, False)

        self.p1 = p1
        self.p2 = p2 if mode == "2P" else "AI"
        self.mode = mode
        self.difficulty = difficulty

        self.scores = {self.p1: 0, self.p2: 0}
        self.current = "X"
        self.board = [""] * 9
        self.buttons = []

        self.main = tk.Frame(self.window, bg="#1e1e2f")
        self.main.pack(fill="both", expand=True)

        self.info = tk.Label(
            self.main,
            text=f"{self.p1} (X) vs {self.p2} (O)",
            fg="white", bg="#1e1e2f",
            font=("Arial", 14, "bold")
        )
        self.info.pack(pady=10)

        self.score_label = tk.Label(
            self.main,
            text=self.score_text(),
            fg="lightblue", bg="#1e1e2f"
        )
        self.score_label.pack()

        self.board_frame = tk.Frame(self.main, bg="#1e1e2f")
        self.board_frame.pack(pady=20)

        for i in range(9):
            b = tk.Button(
                self.board_frame,
                text="", font=("Arial", 22, "bold"),
                width=4, height=2,
                command=lambda i=i: self.move(i)
            )
            b.grid(row=i//3, column=i%3, padx=5, pady=5)
            self.buttons.append(b)

        tk.Button(
            self.main, text="New Game",
            width=20, bg="#555", fg="white",
            command=self.reset_prompt
        ).pack(pady=20)

    def score_text(self):
        return f"{self.p1}: {self.scores[self.p1]}   |   {self.p2}: {self.scores[self.p2]}"

    def move(self, i):
        if self.board[i]:
            return

        self.board[i] = self.current
        if self.current == "X":
            self.buttons[i].config(text="X", fg="Grey")
        else:
            self.buttons[i].config(text="O", fg="red")

        winner = self.check_winner()
        if winner:
            #GAME DATA LOGGING
            log_game(
                game="TicTacToe",
                player=winner,
                metric="Win",
                value=1,
                result="Win"
            )

            self.scores[winner] += 1
            colored_msg("Game Over", f"{winner} Wins!")
            self.update_scores()
            self.clear_board()
            return

        if "" not in self.board:
            colored_msg("Draw", "Match Draw!")
            self.clear_board()
            return

        self.current = "O" if self.current == "X" else "X"

        if self.mode == "AI" and self.current == "O":
            self.window.after(300, self.ai_move)

    def minimax(self, board, is_maximizing):
        winner = self.check_winner_board(board)
        if winner == self.p2:
            return 1
        elif winner == self.p1:
            return -1
        elif "" not in board:
            return 0

        if is_maximizing:
            best_score = -100
            for i in range(9):
                if board[i] == "":
                    board[i] = "O"
                    score = self.minimax(board, False)
                    board[i] = ""
                    best_score = max(score, best_score)
            return best_score
        else:
            best_score = 100
            for i in range(9):
                if board[i] == "":
                    board[i] = "X"
                    score = self.minimax(board, True)
                    board[i] = ""
                    best_score = min(score, best_score)
            return best_score

    def check_winner_board(self, board):
        wins = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]
        for a, b, c in wins:
            if board[a] == board[b] == board[c] != "":
                return self.p1 if board[a] == "X" else self.p2
        return None

    def easy_ai_move(self):
        empty = [i for i in range(9) if self.board[i] == ""]
        if empty:
            i = random.choice(empty)
            self.board[i] = "O"
            self.buttons[i].config(text="O", fg="red")
            self.current = "X"

    def ai_move(self):
        if self.difficulty == "Easy":
            self.easy_ai_move()
            return

        # Hard Mode (Minimax)
        best_score = -100
        best_move = None

        for i in range(9):
            if self.board[i] == "":
                self.board[i] = "O"
                score = self.minimax(self.board, False)
                self.board[i] = ""
                if score > best_score:
                    best_score = score
                    best_move = i

        if best_move is not None:
            self.board[best_move] = "O"
            self.buttons[best_move].config(text="O", fg="red")

        winner = self.check_winner()
        if winner:
            self.scores[winner] += 1
            colored_msg("Game Over", f"{winner} Wins!")
            self.update_scores()
            self.clear_board()
            return

        if "" not in self.board:
            colored_msg("Draw", "Match Draw!")
            self.clear_board()
            return

        self.current = "X"

    def check_winner(self):
        win = [
            (0,1,2),(3,4,5),(6,7,8),
            (0,3,6),(1,4,7),(2,5,8),
            (0,4,8),(2,4,6)
        ]
        for a,b,c in win:
            if self.board[a] == self.board[b] == self.board[c] != "":
                return self.p1 if self.board[a] == "X" else self.p2
        return None

    def update_scores(self):
        self.score_label.config(text=self.score_text())

    def clear_board(self):
        self.board = [""] * 9
        for b in self.buttons:
            b.config(text="")
        self.current = "X"

    def reset_prompt(self):
        if messagebox.askyesno("Reset", "Start new game with new players?"):
            self.window.destroy()
            TicTacToeMenu(self.window.master)
        else:
            self.clear_board()
# -------------------------------
# AI Quiz Menu
# -------------------------------
class QuizMenu:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("AI Quiz Game Settings")
        self.window.resizable(False, False)
        center_window(self.window, 450, 450)
        self.window.configure(bg="#202030")
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.window, text="🤖 AI Quiz Game", font=("Arial", 20, "bold"),
                 fg="white", bg="#202030").pack(pady=20)

        # User Name
        tk.Label(self.window, text="Enter Your Name:", font=("Arial", 12, "bold"),
                 fg="lightblue", bg="#202030").pack(pady=5)
        self.username_entry = tk.Entry(self.window, font=("Arial", 12))
        self.username_entry.pack(pady=5)

        # Number of Questions
        tk.Label(self.window, text="How many questions to attempt? (1-30):", font=("Arial", 12, "bold"),
                 fg="lightblue", bg="#202030").pack(pady=10)
        self.q_count_entry = tk.Entry(self.window, font=("Arial", 12))
        self.q_count_entry.insert(0, "10")
        self.q_count_entry.pack(pady=5)

        # Difficulty
        tk.Label(self.window, text="Select Difficulty:", font=("Arial", 12, "bold"),
                 fg="lightblue", bg="#202030").pack(pady=10)
        self.difficulty = tk.StringVar(value="Easy")
        for diff in ["Easy", "Medium", "Hard"]:
            tk.Radiobutton(self.window, text=diff, variable=self.difficulty, value=diff,
                           bg="#202030", fg="white", selectcolor="#202030").pack(anchor="w", padx=120)

        # Start Button
        tk.Button(self.window, text="▶ START QUIZ", width=20, height=2,
                  bg="#3cb371", fg="white", font=("Arial", 12, "bold"),
                  command=self.start_quiz).pack(pady=30)
        tk.Button(self.window, text="⬅ Back to Arena", width=20, height=2,
                  bg="#555", fg="white", command=self.window.destroy).pack()

    def start_quiz(self):
        username = self.username_entry.get().strip()
        q_count = self.q_count_entry.get().strip()
        if not username:
            colored_msg("Error", "Please enter your name!", "#7a0000")
            return
        if not q_count.isdigit() or not (1 <= int(q_count) <= 30):
            colored_msg("Error", "Please enter a valid number of questions (1-30)!", "#7a0000")
            return
        self.window.destroy()
        QuizGame(tk.Toplevel(self.parent), username, self.difficulty.get(), int(q_count))

# -------------------------------
# AI Quiz Game
# -------------------------------
class QuizGame:
    def __init__(self, root, username, difficulty, q_count):
        self.root = root
        self.username = username
        self.difficulty = difficulty
        self.q_count = q_count
        self.score = 0
        self.current_q = 0
        self.user_answers = []

        self.questions = self.load_questions()
        random.shuffle(self.questions)
        self.questions = self.questions[:self.q_count]

        self.root.title(f"AI Quiz Game - {username}")
        self.root.resizable(False, False)
        center_window(self.root, 700, 500)
        self.root.configure(bg="#1e1e2f")

        self.selected_answer = tk.StringVar()
        self.create_widgets()
        self.show_question()

    # -------- Load Questions --------
    def load_questions(self):
        base_questions = [
            {
                "q": "What is AI?",
                "correct": "Artificial Intelligence",
                "wrong": ["Automobile Industry", "Air Injection", "None"]
            },
            {
                "q": "Which data structure is used in BFS (Breadth-First Search)?",
                "correct": "Queue",
                "wrong": ["Stack", "Tree", "Graph"]
            },
            {
                "q": "Which programming language is mainly used for AI development?",
                "correct": "Python",
                "wrong": ["C++", "Java", "Ruby"]
            },
            {
                "q": "What does AI stand for?",
                "correct": "Artificial Intelligence",
                "wrong": ["Automatic Input", "Automated Interface", "None"]
            },
            {
                "q": "Which one is a Machine Learning library?",
                "correct": "TensorFlow",
                "wrong": ["Pandas", "NumPy", "Matplotlib"]
            },
            {
                "q": "Which type of AI learns from data?",
                "correct": "ML (Machine Learning)",
                "wrong": ["Expert System", "Robotics", "None"]
            },
            {
                "q": "Which technique is used in DFS (Depth-First Search)?",
                "correct": "Recursion",
                "wrong": ["Queue", "Stack", "Tree"]
            },
            {
                "q": "Which AI technique uses neural networks?",
                "correct": "Deep Learning",
                "wrong": ["Reinforcement Learning", "Decision Tree", "Clustering"]
            },
            {
                "q": "Which Python library is commonly used for Machine Learning?",
                "correct": "Scikit-learn",
                "wrong": ["Pygame", "Tkinter", "Flask"]
            },
            {
                "q": "Which AI approach is used to solve games like Chess?",
                "correct": "Reinforcement Learning",
                "wrong": ["Expert System", "Genetic Algorithm", "Regression"]
            },
            {
                "q": "In which fields can AI be applied?",
                "correct": "All of the above",
                "wrong": ["Healthcare", "Finance", "Games"]
            },
            {
                "q": "Which one is a supervised learning algorithm?",
                "correct": "Linear Regression",
                "wrong": ["K-Means", "PCA", "Apriori"]
            },
            {
                "q": "Which AI field can generate text?",
                "correct": "NLP (Natural Language Processing)",
                "wrong": ["Robotics", "Vision AI", "RL (Reinforcement Learning)"]
            },
            {
                "q": "Which algorithm is used in pathfinding?",
                "correct": "All of the above",
                "wrong": ["A*", "DFS", "BFS"]
            },
            {
                "q": "Which type of AI learns without labeled data?",
                "correct": "Unsupervised Learning",
                "wrong": ["Supervised Learning", "Reinforcement Learning", "Deep Learning"]
            },
            {
                "q": "Which model is used for image recognition in AI?",
                "correct": "CNN (Convolutional Neural Network)",
                "wrong": ["RNN (Recurrent Neural Network)", "LSTM", "SVM"]
            },
            {
                "q": "Which is an example of an AI assistant?",
                "correct": "Siri",
                "wrong": ["Excel", "Photoshop", "Chrome"]
            },
            {
                "q": "Which AI approach uses a reward system?",
                "correct": "Reinforcement Learning",
                "wrong": ["Supervised Learning", "Unsupervised Learning", "DL (Deep Learning)"]
            },
            {
                "q": "Which library is used for NLP (Natural Language Processing)?",
                "correct": "NLTK",
                "wrong": ["OpenCV", "Pandas", "Matplotlib"]
            },
            {
                "q": "What is used in AI for self-driving cars?",
                "correct": "All of the above",
                "wrong": ["Computer Vision", "ML (Machine Learning)", "Sensors"]
            },
            {
                "q": "Which Python library is used for data manipulation in ML?",
                "correct": "Pandas",
                "wrong": ["NumPy", "Scikit-learn", "TensorFlow"]
            },
            {
                "q": "Which type of AI is rule-based?",
                "correct": "Expert System",
                "wrong": ["ML (Machine Learning)", "DL (Deep Learning)", "RL (Reinforcement Learning)"]
            },
            {
                "q": "Which AI field uses graphs?",
                "correct": "Graph AI",
                "wrong": ["Vision AI", "NLP", "Reinforcement Learning"]
            },
            {
                "q": "Which algorithm is considered greedy?",
                "correct": "A*",
                "wrong": ["DFS", "BFS", "Minimax"]
            },
            {
                "q": "Which AI technique predicts stock prices?",
                "correct": "ML Regression",
                "wrong": ["Reinforcement Learning", "Deep Learning", "CNN"]
            },
            {
                "q": "Which AI model handles sequences?",
                "correct": "RNN (Recurrent Neural Network)",
                "wrong": ["CNN", "Decision Tree", "KNN"]
            },
            {
                "q": "Which is a clustering algorithm in ML?",
                "correct": "K-Means",
                "wrong": ["Linear Regression", "CNN", "Reinforcement Learning"]
            },
            {
                "q": "Which AI field analyzes images?",
                "correct": "Computer Vision",
                "wrong": ["NLP", "Reinforcement Learning", "Machine Learning"]
            },
            {
                "q": "Which AI can play games like Go?",
                "correct": "Reinforcement Learning",
                "wrong": ["Machine Learning", "Deep Learning", "Expert System"]
            }
        ]
        return base_questions


    def prepare_question(self, q):
        options = q["wrong"] + [q["correct"]]
        random.shuffle(options)
        return options, q["correct"]

    # -------- Create UI --------
    def create_widgets(self):
        self.q_frame = tk.Frame(self.root, bg="#1e1e2f")
        self.q_frame.pack(pady=20)

        self.question_label = tk.Label(self.q_frame, text="", font=("Arial", 16, "bold"),
                                       fg="white", bg="#1e1e2f", wraplength=650, justify="left")
        self.question_label.pack(pady=10)

        self.option_buttons = []
        for i in range(4):
            btn = tk.Radiobutton(self.q_frame, text="", variable=self.selected_answer, value="",
                                 font=("Arial", 12), bg="#1e1e2f", fg="white",
                                 selectcolor="#202030", anchor="w", width=50, padx=20)
            btn.pack(pady=5, anchor="w")
            self.option_buttons.append(btn)

        self.btn_frame = tk.Frame(self.root, bg="#1e1e2f")
        self.btn_frame.pack(pady=20)

        tk.Button(self.btn_frame, text="Next", width=15, command=self.next_question,
                  bg="#3cb371", fg="white", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        tk.Button(self.btn_frame, text="Hint", width=15, command=self.show_hint,
                  bg="#ffa500", fg="white", font=("Arial", 12, "bold")).pack(side="left", padx=10)

        self.score_label = tk.Label(self.root, text=f"Score: {self.score}", font=("Arial", 14, "bold"),
                                    fg="yellow", bg="#1e1e2f")
        self.score_label.pack(pady=10)

    # -------- Show Question --------
    def show_question(self):
        if self.current_q >= len(self.questions):
            return
        q = self.questions[self.current_q]
        self.question_label.config(text=f"Q{self.current_q+1}: {q['q']}")
        self.selected_answer.set(None)
        self.current_options, self.correct_answer = self.prepare_question(q)

        for i, opt in enumerate(self.current_options):
            self.option_buttons[i].config(text=opt, value=opt)

    # -------- Next Question --------
    def next_question(self):
        q = self.questions[self.current_q]
        selected = self.selected_answer.get()
        if not selected:
            colored_msg("Warning", "Please select an option!", "#7a0000")
            return

        # Store answer
        self.user_answers.append({
            "q": q["q"],
            "your": selected,
            "correct": self.correct_answer
        })

        # Determine if correct
        correct = selected == self.correct_answer
        if correct:
            self.score += 1

        # Show popup for current question result
        colored_msg("Correct...! ✅" if correct else "Wrong...:( ❌",
                    "Your answer is correct!" if correct else f"Correct Answer: {q['correct']}",
                    "#004d00" if correct else "#7a0000")

        self.score_label.config(text=f"Score: {self.score}")
        self.current_q += 1

        if self.current_q >= len(self.questions):
            self.show_overview()
        else:
            self.show_question()

    # -------- AI Hint --------
    def show_hint(self):
        q = self.questions[self.current_q]
        chance = {"Easy": 0.8, "Medium": 0.5, "Hard": 0.3}
        if random.random() <= chance[self.difficulty]:
            hint = self.correct_answer

        else:
            hint = random.choice(
                [opt for opt in self.current_options if opt != self.correct_answer]
            )

        colored_msg("AI Hint 💡", f"AI suggests: {hint}", "#1e90ff")

    # -------- Scrollable Overview --------
    def show_overview(self):
        overview = tk.Toplevel(self.root)
        overview.title("Quiz Overview")
        center_window(overview, 700, 500)
        overview.configure(bg="#1e1e2f")

        canvas = tk.Canvas(overview, bg="#1e1e2f", highlightthickness=0)
        scrollbar = tk.Scrollbar(overview, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#1e1e2f")

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # -------- Show Answers --------
        for idx, ans in enumerate(self.user_answers, 1):
            is_wrong = ans["your"] != ans["correct"]

            tk.Label(
                scroll_frame,
                text=f"Q{idx}: {ans['q']}",
                fg="white",
                bg="#1e1e2f",
                font=("Arial", 12, "bold"),
                wraplength=650,
                justify="left"
            ).pack(anchor="w", pady=(10, 2))

            tk.Label(
                scroll_frame,
                text=f"Your Answer: {ans['your']}",
                fg="red" if is_wrong else "green",
                bg="#1e1e2f",
                font=("Arial", 11)
            ).pack(anchor="w", padx=20)

            if is_wrong:
                tk.Label(
                    scroll_frame,
                    text=f"Correct Answer: {ans['correct']}",
                    fg="yellow",
                    bg="#1e1e2f",
                    font=("Arial", 11)
                ).pack(anchor="w", padx=20, pady=(0, 5))

        # -------- Final Score --------
        tk.Label(
            scroll_frame,
            text=f"Final Score: {self.score}/{len(self.questions)}",
            fg="yellow",
            bg="#1e1e2f",
            font=("Arial", 14, "bold")
        ).pack(pady=15)

        #GAME DATA LOGGING
        log_game(
            game="Quiz",
            player=self.username,
            metric="Score",
            value=self.score,
            result="Pass" if self.score >= (len(self.questions) // 2) else "Fail"
        )

        # -------- Buttons (SIDE BY SIDE) --------
        btn_frame = tk.Frame(scroll_frame, bg="#1e1e2f")
        btn_frame.pack(pady=15)

        tk.Button(
            btn_frame,
            text="New Quiz",
            width=18,
            bg="#3cb371",
            fg="white",
            font=("Arial", 11, "bold"),
            command=lambda: [overview.destroy(), QuizMenu(self.root)]
        ).pack(side="left", padx=10)

        tk.Button(
            btn_frame,
            text="Restart Quiz",
            width=18,
            bg="#ffa500",
            fg="white",
            font=("Arial", 11, "bold"),
            command=lambda: [
                overview.destroy(),
                QuizGame(tk.Toplevel(self.root), self.username, self.difficulty, self.q_count)
            ]
        ).pack(side="left", padx=10)


# -------------------------------
# Main Application
# -------------------------------
class AIGameArena:

    def __init__(self, root):

        self.root = root
        self.root.withdraw()
        self.root.title("AI Game Arena")
        self.root.resizable(False, False)
        center_window(self.root, 800, 600)
        self.root.deiconify()
        self.main_frame = tk.Frame(self.root, bg="#1e1e2f")
        self.main_frame.pack(fill="both", expand=True)
        self.create_widgets()

    def open_analyzer(self):
        AIPerformanceAnalyzer(tk.Toplevel(self.root))

    def create_widgets(self):
        tk.Label(self.main_frame, text="🎮 AI GAME ARENA", font=("Arial",22,"bold"), fg="white", bg="#1e1e2f").pack(pady=30)
        tk.Label(self.main_frame, text="Select an AI Game", font=("Arial",14), fg="lightgray", bg="#1e1e2f").pack(pady=10)
        tk.Button(self.main_frame, text="Maze Solver", width=30, height=2, command=self.open_maze_game).pack(pady=10)
        tk.Button(self.main_frame, text="Tic Tac Toe", width=30, height=2, command=lambda:TicTacToeMenu(self.root)).pack(pady=10)
        tk.Button(self.main_frame, text="AI Quiz Game", width=30, height=2, command=lambda:QuizMenu(self.root)).pack(pady=10)
        tk.Button(self.main_frame,text="AI Performance Analyzer",width=30, height=2,command=self.open_analyzer).pack(pady=10)

        tk.Button(self.main_frame, text="Exit", width=30, height=2, bg="red", fg="white", command=self.root.quit).pack(pady=20)

    def open_maze_game(self): MazeGameMenu(self.root)
    def new_window(self,title):
        w=tk.Toplevel(self.root)
        w.title(title)
        center_window(w,400,300)
        tk.Label(w,text=title,font=("Arial",16,"bold")).pack(pady=40)
        tk.Label(w,text="This module will be implemented next.", font=("Arial",12)).pack(pady=10)
        tk.Button(w,text="Close", command=w.destroy).pack(pady=20)


# -------------------------------
# Run Application
# -------------------------------
if __name__=="__main__":
    root=tk.Tk()
    app=AIGameArena(root)
    root.mainloop()
