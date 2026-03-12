import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import os
DEFAULT_CSV = "game_logs.csv"
# ----------------------------
# Utility
# ----------------------------
def center(win, w, h):
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

# ----------------------------
# Analyzer Class
# ----------------------------
class AIPerformanceAnalyzer:

    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg="#202030")

        self.frame.pack(fill="both", expand=True)
        self.parent = parent

        self.win = tk.Toplevel(parent)
        self.win.withdraw()
        self.win.title("AI Performance Analyzer")
        self.win.configure(bg="#1e1e2f")
        center(self.win, 1000, 650)

        self.win.deiconify()
        self.df = None
        self.selected_game = None

        self.build_ui()

        # Data default load...
        if os.path.exists(DEFAULT_CSV):
            self.load_csv(DEFAULT_CSV)
        else:
            self.status.config(text="Default game data not found", fg="orange")

        self.win.grab_set()
        self.win.focus_force()

    # ----------------------------
    def build_ui(self):
        # Top bar
        top = tk.Frame(self.win, bg="#1e1e2f")
        top.pack(fill="x")

        tk.Button(top, text="Load CSV", width=15, command=self.load_csv).pack(side="left", padx=10, pady=10)
        tk.Button(top, text="Back to Menu", width=15, command=self.win.destroy).pack(side="right", padx=10)

        # Main layout
        main = tk.Frame(self.win, bg="#1e1e2f")
        main.pack(fill="both", expand=True)

        # Left panel (Games)
        self.left = tk.Frame(main, bg="#26263a", width=220)
        self.left.pack(side="left", fill="y")

        tk.Label(self.left, text="Games", bg="#26263a", fg="white", font=("Arial", 12, "bold")).pack(pady=10)

        self.game_canvas = tk.Canvas(self.left, bg="#26263a", highlightthickness=0)
        self.scroll = ttk.Scrollbar(self.left, orient="vertical", command=self.game_canvas.yview)
        self.game_frame = tk.Frame(self.game_canvas, bg="#26263a")

        self.game_frame.bind("<Configure>",lambda e: self.game_canvas.configure(scrollregion=self.game_canvas.bbox("all")))

        self.game_canvas.create_window((0,0), window=self.game_frame, anchor="nw")
        self.game_canvas.configure(yscrollcommand=self.scroll.set)

        self.game_canvas.pack(side="left", fill="y", expand=True)
        self.scroll.pack(side="right", fill="y")

        self.status = tk.Label(
            self.win,
            text="Load a CSV file to begin analysis",
            bg="#1e1e2f",
            fg="lightgreen",
            anchor="w"
        )
        self.status.pack(fill="x", padx=10, pady=5)

        # Right panel
        self.right = tk.Frame(main, bg="#1e1e2f")
        self.right.pack(side="right", fill="both", expand=True)

        tk.Button(
            self.right,
            text="View Records",
            width=18,
            command=self.show_records,
            bg="#3c3c6e",
            fg="white"
        ).pack(pady=5)

        # Summary box
        self.summary = tk.Text(self.right, height=6, bg="#26263a", fg="white", font=("Arial", 11))
        self.summary.pack(fill="x", padx=10, pady=10)

        # Controls
        ctrl = tk.Frame(self.right, bg="#1e1e2f")
        ctrl.pack(fill="x", padx=10)

        tk.Label(ctrl, text="Metric:", fg="white", bg="#1e1e2f").pack(side="left")
        self.metric_box = ttk.Combobox(ctrl, state="readonly", width=20)
        self.metric_box.pack(side="left", padx=5)

        tk.Label(ctrl, text="Chart:", fg="white", bg="#1e1e2f").pack(side="left", padx=10)
        self.chart_box = ttk.Combobox(ctrl, state="readonly",
            values=["Line", "Bar", "Pie", "Scatter", "Stacked Bar"])
        self.chart_box.current(0)
        self.chart_box.pack(side="left")

        tk.Button(ctrl, text="Show", command=self.draw_chart).pack(side="left", padx=10)

        # Chart area
        self.chart_area = tk.Frame(self.right, bg="#1e1e2f")
        self.chart_area.pack(fill="both", expand=True, padx=10, pady=10)

    # ----------------------------
    def load_csv(self, path=None):

        if path is None:
            path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])

        if not path:
            return

        try:
            self.df = pd.read_csv(path)

            if self.df.empty:
                self.status.config(text="CSV is empty!", fg="red")
                return

            self.populate_games()
            self.status.config(
                text=f"Loaded {len(self.df)} records successfully",
                fg="lightgreen"
            )

        except Exception as e:
            self.status.config(text=f"Error loading CSV: {e}", fg="red")

    # ----------------------------
    def populate_games(self):

        # clear old buttons
        for w in self.game_frame.winfo_children():
            w.destroy()

        # unique games only
        games = sorted(self.df["Game"].dropna().unique())

        for game in games:
            tk.Button(
                self.game_frame,
                text=game,
                width=22,
                bg="#444488",
                fg="white",
                command=lambda g=game: self.select_game(g)
            ).pack(pady=6)

        # auto select first game
        if games:
            self.select_game(games[0])

    # ----------------------------
    def select_game(self, game):
        self.selected_game = game
        sub = self.df[self.df["Game"] == game]

        self.metric_box["values"] = list(sub["Metric"].unique())
        self.metric_box.current(0)

        self.update_summary(sub)

    # ----------------------------
    def update_summary(self, df):
        self.summary.delete("1.0", tk.END)

        players = df["Player"].unique()
        avg_scores = df.groupby("Player")["Value"].mean()

        text = f"""
    Game: {self.selected_game}
    ---------------------------------
    Total Records: {len(df)}

    Players:
    {chr(10).join([f"- {p} (Avg: {avg_scores[p]:.2f})" for p in players])}
    """
        self.summary.insert(tk.END, text)

    # ----------------------------
    def draw_chart(self):
        colors = plt.cm.tab10.colors

        if self.df is None or self.selected_game is None:
            return

        for w in self.chart_area.winfo_children():
            w.destroy()

        metric = self.metric_box.get()
        chart = self.chart_box.get()

        data = self.df[
            (self.df["Game"] == self.selected_game) &
            (self.df["Metric"] == metric)
        ]

        fig, ax = plt.subplots(figsize=(6,4))

        if chart == "Line":
            for i, p in enumerate(data["Player"].unique()):
                d = data[data["Player"] == p]
                ax.plot(
                    d["Date"],
                    d["Value"],
                    marker="o",
                    linewidth=2,
                    color=colors[i % len(colors)],
                    label=p
                )
            ax.legend(title="Players")
            ax.set_ylabel(metric)


        elif chart == "Bar":

            data.groupby("Player")["Value"].mean().plot(

                kind="bar",

                ax=ax

            )

        elif chart == "Pie":

            data.groupby("Result").size().plot(

                kind="pie",

                autopct="%1.1f%%",

                ax=ax

            )

            ax.set_ylabel("")

        elif chart == "Scatter":
            for i, p in enumerate(data["Player"].unique()):
                d = data[data["Player"] == p]
                ax.scatter(
                    d["Date"],
                    d["Value"],
                    color=colors[i % len(colors)],
                    label=p
                )
            ax.legend()



        elif chart == "Stacked Bar":

            pivot = data.pivot_table(

                index="Player",

                columns="Result",

                values="Value",

                aggfunc="count"

            )

            pivot.plot(kind="bar", stacked=True, ax=ax)

        ax.set_title(f"{self.selected_game} - {metric}")
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def show_records(self):

        if self.df is None or self.selected_game is None:
            return

        win = tk.Toplevel(self.win)
        win.title(f"{self.selected_game} - Records")
        center(win, 850, 400)
        win.configure(bg="#1e1e2f")

        style = ttk.Style(win)
        style.theme_use("default")

        style.configure(
            "Treeview",
            background="#26263a",
            foreground="white",
            rowheight=28,
            fieldbackground="#26263a"
        )

        style.configure(
            "Treeview.Heading",
            background="#444488",
            foreground="white",
            font=("Arial", 11, "bold")
        )

        style.map(
            "Treeview",
            background=[("selected", "#3cb371")]
        )

        cols = list(self.df.columns)

        tree = ttk.Treeview(win, columns=cols, show="headings")
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, anchor="center")

        data = self.df[self.df["Game"] == self.selected_game]

        for _, row in data.iterrows():
            tree.insert("", "end", values=list(row))
