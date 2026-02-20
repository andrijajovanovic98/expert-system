#!/usr/bin/env python3
"""
Main application window for the Expert System UI.
"""

import os
import sys
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
from pathlib import Path

# Ensure parent directory is in path for imports
_app_dir = Path(__file__).resolve().parent.parent
if str(_app_dir) not in sys.path:
    sys.path.insert(0, str(_app_dir))

from ui.theme import Colors, Fonts, Spacing, apply_theme
from ui.widgets import (
    LineNumberedText, ResultCard, ScrollableFrame,
    ReasoningText, StatusBar,
)

from parser import parse_input_file
from inference_engine import InferenceEngine, TruthValue
from reasoning_visualizer import ReasoningVisualizer
from statistics_analyzer import StatisticsAnalyzer


class ExpertSystemApp:
    """Main application class."""

    # ------------------------------------------------------------------ #
    #  Construction
    # ------------------------------------------------------------------ #
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Expert System — Propositional Calculus")
        self.root.geometry("1280x820")
        self.root.minsize(900, 600)

        apply_theme(self.root)

        # State
        self.current_file = None
        self.rules = []
        self.initial_facts = set()
        self.queries = []
        self.engine = None
        self.results = {}
        self.active_facts = set()     # for interactive toggles
        self._active_nav = None
        self.predictions = {}         # user predictions per query
        self.prediction_vars = {}     # tk StringVars for dropdowns

        self._build_ui()
        self._bind_shortcuts()

        # Load a default sample if test files exist
        self._try_load_default()

    # ------------------------------------------------------------------ #
    #  UI Construction
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        # Title bar
        self._build_titlebar()

        # Toolbar
        self._build_toolbar()

        # Separator
        tk.Frame(self.root, bg=Colors.BORDER, height=1).pack(fill="x")

        # Main content area
        self.main_frame = tk.Frame(self.root, bg=Colors.BG_DARK)
        self.main_frame.pack(fill="both", expand=True)

        self._build_sidebar()
        self._build_content_area()

        # Status bar
        self.statusbar = StatusBar(self.root)
        self.statusbar.pack(side="bottom", fill="x")

    # -- Title bar --
    def _build_titlebar(self):
        bar = tk.Frame(self.root, bg=Colors.BG_DARK, pady=Spacing.MD)
        bar.pack(fill="x")

        # Icon / logo area
        logo_frame = tk.Frame(bar, bg=Colors.BG_DARK)
        logo_frame.pack(side="left", padx=Spacing.XL)

        tk.Label(
            logo_frame, text="⚛",
            font=(Fonts.FAMILY_SANS, 22), fg=Colors.BLUE, bg=Colors.BG_DARK,
        ).pack(side="left", padx=(0, Spacing.MD))

        title_texts = tk.Frame(logo_frame, bg=Colors.BG_DARK)
        title_texts.pack(side="left")

        tk.Label(
            title_texts, text="Expert System",
            font=Fonts.get_sans_bold(Fonts.SIZE_TITLE),
            fg=Colors.LAVENDER, bg=Colors.BG_DARK,
        ).pack(anchor="w")

        tk.Label(
            title_texts, text="Propositional Calculus Inference Engine",
            font=Fonts.get_sans(Fonts.SIZE_SMALL),
            fg=Colors.TEXT_MUTED, bg=Colors.BG_DARK,
        ).pack(anchor="w")

        # Right side: file indicator
        self.file_label = tk.Label(
            bar, text="No file loaded",
            font=Fonts.get_sans(Fonts.SIZE_SMALL),
            fg=Colors.TEXT_MUTED, bg=Colors.BG_DARK,
        )
        self.file_label.pack(side="right", padx=Spacing.XL)

    # -- Toolbar --
    def _build_toolbar(self):
        toolbar = tk.Frame(self.root, bg=Colors.BG_DARK, pady=Spacing.XS)
        toolbar.pack(fill="x", padx=Spacing.XL)

        buttons = [
            ("📂  Open File", self._on_open_file),
            ("💾  Save", self._on_save_file),
            (None, None),  # separator
            ("▶  Run", self._on_run),
        ]
        for label, cmd in buttons:
            if label is None:
                tk.Frame(toolbar, width=1, height=20, bg=Colors.BORDER).pack(
                    side="left", padx=Spacing.MD, fill="y"
                )
            else:
                style = "Primary.TButton" if label.startswith("▶") else "Toolbar.TButton"
                ttk.Button(toolbar, text=label, command=cmd, style=style).pack(
                    side="left", padx=Spacing.XS
                )

    # -- Sidebar --
    def _build_sidebar(self):
        self.sidebar = tk.Frame(self.main_frame, bg=Colors.BG_DARK, width=170)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(
            self.sidebar, text="PANELS",
            font=Fonts.get_sans_bold(Fonts.SIZE_SMALL),
            fg=Colors.TEXT_MUTED, bg=Colors.BG_DARK,
        ).pack(anchor="w", padx=Spacing.XL, pady=(Spacing.LG, Spacing.SM))

        self.nav_buttons = {}
        panels = [
            ("editor", "✏️  Editor"),
            ("results", "📊  Results"),
            ("reasoning", "🔍  Reasoning"),
            ("statistics", "📈  Statistics"),
            ("facts", "🔘  Facts"),
        ]
        for key, label in panels:
            btn = ttk.Button(
                self.sidebar, text=label,
                style="Nav.TButton",
                command=lambda k=key: self._switch_panel(k),
            )
            btn.pack(fill="x", padx=Spacing.SM, pady=1)
            self.nav_buttons[key] = btn

        # Separator
        tk.Frame(self.sidebar, bg=Colors.BORDER, height=1).pack(
            fill="x", padx=Spacing.XL, pady=Spacing.LG
        )

        # Quick info panel
        self.quick_info = tk.Frame(self.sidebar, bg=Colors.BG_DARK)
        self.quick_info.pack(fill="x", padx=Spacing.XL)

        tk.Label(
            self.quick_info, text="INFO",
            font=Fonts.get_sans_bold(Fonts.SIZE_SMALL),
            fg=Colors.TEXT_MUTED, bg=Colors.BG_DARK,
        ).pack(anchor="w", pady=(0, Spacing.SM))

        self.info_rules = tk.Label(
            self.quick_info, text="Rules: -",
            font=Fonts.get_sans(Fonts.SIZE_SMALL),
            fg=Colors.TEXT_SECONDARY, bg=Colors.BG_DARK, anchor="w",
        )
        self.info_rules.pack(anchor="w")

        self.info_facts = tk.Label(
            self.quick_info, text="Facts: -",
            font=Fonts.get_sans(Fonts.SIZE_SMALL),
            fg=Colors.TEXT_SECONDARY, bg=Colors.BG_DARK, anchor="w",
        )
        self.info_facts.pack(anchor="w")

        self.info_queries = tk.Label(
            self.quick_info, text="Queries: -",
            font=Fonts.get_sans(Fonts.SIZE_SMALL),
            fg=Colors.TEXT_SECONDARY, bg=Colors.BG_DARK, anchor="w",
        )
        self.info_queries.pack(anchor="w")

    # -- Content area --
    def _build_content_area(self):
        # Vertical separator
        tk.Frame(self.main_frame, bg=Colors.BORDER, width=1).pack(
            side="left", fill="y"
        )

        self.content_frame = tk.Frame(self.main_frame, bg=Colors.BG_DARK)
        self.content_frame.pack(side="left", fill="both", expand=True)

        self.panels = {}
        self._build_editor_panel()
        self._build_results_panel()
        self._build_reasoning_panel()
        self._build_statistics_panel()
        self._build_facts_panel()

        # Show editor by default
        self._switch_panel("editor")

    # -- Editor Panel --
    def _build_editor_panel(self):
        panel = tk.Frame(self.content_frame, bg=Colors.BG_DARK)
        self.panels["editor"] = panel

        # Header
        header = tk.Frame(panel, bg=Colors.BG_DARK)
        header.pack(fill="x", padx=Spacing.XL, pady=Spacing.LG)

        tk.Label(
            header, text="Rule Editor",
            font=Fonts.get_sans_bold(Fonts.SIZE_LARGE),
            fg=Colors.BLUE, bg=Colors.BG_DARK,
        ).pack(side="left")

        tk.Label(
            header, text="Write or load rules, initial facts, and queries",
            font=Fonts.get_sans(Fonts.SIZE_SMALL),
            fg=Colors.TEXT_MUTED, bg=Colors.BG_DARK,
        ).pack(side="right")

        # Editor widget
        self.editor = LineNumberedText(panel)
        self.editor.pack(fill="both", expand=True, padx=Spacing.XL, pady=(0, Spacing.XL))

    # -- Results Panel --
    def _build_results_panel(self):
        panel = tk.Frame(self.content_frame, bg=Colors.BG_DARK)
        self.panels["results"] = panel

        header = tk.Frame(panel, bg=Colors.BG_DARK)
        header.pack(fill="x", padx=Spacing.XL, pady=Spacing.LG)

        tk.Label(
            header, text="Query Results",
            font=Fonts.get_sans_bold(Fonts.SIZE_LARGE),
            fg=Colors.BLUE, bg=Colors.BG_DARK,
        ).pack(side="left")

        ttk.Button(
            header, text="▶  Run Inference", command=self._on_run,
            style="Primary.TButton",
        ).pack(side="right")

        # Results container (scrollable)
        self.results_scroll = ScrollableFrame(panel, bg=Colors.BG_DARK)
        self.results_scroll.pack(fill="both", expand=True, padx=Spacing.XL, pady=(0, Spacing.XL))

        # Placeholder
        self.results_placeholder = tk.Label(
            self.results_scroll.scrollable_frame,
            text="Load a file, select your predictions, then press ▶ Run.",
            font=Fonts.get_sans(Fonts.SIZE_MEDIUM),
            fg=Colors.TEXT_MUTED, bg=Colors.BG_DARK,
            justify="center",
        )
        self.results_placeholder.pack(pady=Spacing.XXL * 3)

    # -- Reasoning Panel --
    def _build_reasoning_panel(self):
        panel = tk.Frame(self.content_frame, bg=Colors.BG_DARK)
        self.panels["reasoning"] = panel

        header = tk.Frame(panel, bg=Colors.BG_DARK)
        header.pack(fill="x", padx=Spacing.XL, pady=Spacing.LG)

        tk.Label(
            header, text="Reasoning Visualization",
            font=Fonts.get_sans_bold(Fonts.SIZE_LARGE),
            fg=Colors.BLUE, bg=Colors.BG_DARK,
        ).pack(side="left")

        ttk.Button(
            header, text="▶  Run Inference", command=self._on_run,
            style="Primary.TButton",
        ).pack(side="right")

        self.reasoning_text = ReasoningText(panel)
        self.reasoning_text.pack(fill="both", expand=True, padx=Spacing.XL, pady=(0, Spacing.XL))

    # -- Statistics Panel --
    def _build_statistics_panel(self):
        panel = tk.Frame(self.content_frame, bg=Colors.BG_DARK)
        self.panels["statistics"] = panel

        header = tk.Frame(panel, bg=Colors.BG_DARK)
        header.pack(fill="x", padx=Spacing.XL, pady=Spacing.LG)

        tk.Label(
            header, text="Rule Set Statistics",
            font=Fonts.get_sans_bold(Fonts.SIZE_LARGE),
            fg=Colors.BLUE, bg=Colors.BG_DARK,
        ).pack(side="left")

        ttk.Button(
            header, text="⟳  Refresh", command=self._on_run,
            style="Toolbar.TButton",
        ).pack(side="right")

        self.statistics_text = ReasoningText(panel)
        self.statistics_text.pack(fill="both", expand=True, padx=Spacing.XL, pady=(0, Spacing.XL))

    # -- Facts Panel (interactive toggles) --
    def _build_facts_panel(self):
        panel = tk.Frame(self.content_frame, bg=Colors.BG_DARK)
        self.panels["facts"] = panel

        header = tk.Frame(panel, bg=Colors.BG_DARK)
        header.pack(fill="x", padx=Spacing.XL, pady=Spacing.LG)

        tk.Label(
            header, text="Interactive Facts",
            font=Fonts.get_sans_bold(Fonts.SIZE_LARGE),
            fg=Colors.BLUE, bg=Colors.BG_DARK,
        ).pack(side="left")

        tk.Label(
            header, text="Toggle facts on/off, then run inference",
            font=Fonts.get_sans(Fonts.SIZE_SMALL),
            fg=Colors.TEXT_MUTED, bg=Colors.BG_DARK,
        ).pack(side="right")

        # Fact toggle area
        toggle_frame = tk.Frame(panel, bg=Colors.BG_DARK)
        toggle_frame.pack(fill="x", padx=Spacing.XL, pady=Spacing.LG)

        tk.Label(
            toggle_frame, text="Initial Facts",
            font=Fonts.get_sans_bold(Fonts.SIZE_MEDIUM),
            fg=Colors.TEXT_SECONDARY, bg=Colors.BG_DARK,
        ).pack(anchor="w", pady=(0, Spacing.MD))

        self.fact_buttons_frame = tk.Frame(toggle_frame, bg=Colors.BG_DARK)
        self.fact_buttons_frame.pack(fill="x")

        self.fact_buttons = {}
        for i, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            col = i % 13
            row = i // 13
            btn = ttk.Button(
                self.fact_buttons_frame,
                text=f" {letter} ",
                style="Fact.TButton",
                width=3,
                command=lambda l=letter: self._toggle_fact(l),
            )
            btn.grid(row=row, column=col, padx=2, pady=2)
            self.fact_buttons[letter] = btn

        # Query input
        query_frame = tk.Frame(panel, bg=Colors.BG_DARK)
        query_frame.pack(fill="x", padx=Spacing.XL, pady=Spacing.LG)

        tk.Label(
            query_frame, text="Queries",
            font=Fonts.get_sans_bold(Fonts.SIZE_MEDIUM),
            fg=Colors.TEXT_SECONDARY, bg=Colors.BG_DARK,
        ).pack(anchor="w", pady=(0, Spacing.MD))

        input_row = tk.Frame(query_frame, bg=Colors.BG_DARK)
        input_row.pack(fill="x")

        self.query_entry = tk.Entry(
            input_row,
            font=Fonts.get_mono(Fonts.SIZE_MEDIUM),
            bg=Colors.BG_SURFACE,
            fg=Colors.TEXT_PRIMARY,
            insertbackground=Colors.BLUE,
            selectbackground=Colors.BG_HIGHLIGHT,
            bd=0, relief="flat",
        )
        self.query_entry.pack(side="left", fill="x", expand=True, ipady=Spacing.MD, padx=(0, Spacing.MD))

        ttk.Button(
            input_row, text="▶  Query", command=self._on_interactive_query,
            style="Primary.TButton",
        ).pack(side="right")

        # Results from interactive query
        self.interactive_results_frame = tk.Frame(panel, bg=Colors.BG_DARK)
        self.interactive_results_frame.pack(fill="both", expand=True, padx=Spacing.XL, pady=(0, Spacing.XL))

    # ------------------------------------------------------------------ #
    #  Navigation
    # ------------------------------------------------------------------ #
    def _switch_panel(self, key):
        # Hide all panels
        for panel in self.panels.values():
            panel.pack_forget()

        # Update nav button styles
        for k, btn in self.nav_buttons.items():
            btn.configure(style="NavActive.TButton" if k == key else "Nav.TButton")

        # Show selected panel
        self.panels[key].pack(fill="both", expand=True)
        self._active_nav = key

    # ------------------------------------------------------------------ #
    #  Keyboard shortcuts
    # ------------------------------------------------------------------ #
    def _bind_shortcuts(self):
        self.root.bind("<Control-o>", lambda e: self._on_open_file())
        self.root.bind("<Control-s>", lambda e: self._on_save_file())
        self.root.bind("<Control-r>", lambda e: self._on_run())
        self.root.bind("<Control-1>", lambda e: self._switch_panel("editor"))
        self.root.bind("<Control-2>", lambda e: self._switch_panel("results"))
        self.root.bind("<Control-3>", lambda e: self._switch_panel("reasoning"))
        self.root.bind("<Control-4>", lambda e: self._switch_panel("statistics"))
        self.root.bind("<Control-5>", lambda e: self._switch_panel("facts"))
        self.root.bind("<F5>", lambda e: self._on_run())

    # ------------------------------------------------------------------ #
    #  File Operations
    # ------------------------------------------------------------------ #
    def _on_open_file(self):
        filetypes = [
            ("Text files", "*.txt"),
            ("All files", "*.*"),
        ]
        filepath = filedialog.askopenfilename(
            title="Open Expert System Input",
            filetypes=filetypes,
            initialdir=str(_app_dir / "test"),
        )
        if filepath:
            self._load_file(filepath)

    def _load_file(self, filepath):
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            self.current_file = filepath
            self.editor.set_content(content)
            self.file_label.configure(text=os.path.basename(filepath))
            self.statusbar.set_status(f"Loaded: {filepath}", Colors.SUCCESS)
            self._parse_current()
            self._build_prediction_selectors()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{e}")
            self.statusbar.set_status(f"Error loading file: {e}", Colors.ERROR)

    def _on_save_file(self):
        if self.current_file:
            filepath = self.current_file
        else:
            filepath = filedialog.asksaveasfilename(
                title="Save Expert System Input",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            )
        if filepath:
            try:
                with open(filepath, 'w') as f:
                    f.write(self.editor.get_content())
                self.current_file = filepath
                self.file_label.configure(text=os.path.basename(filepath))
                self.statusbar.set_status(f"Saved: {filepath}", Colors.SUCCESS)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file:\n{e}")

    def _try_load_default(self):
        """Try to load a default test file."""
        test_dir = _app_dir / "test"
        if test_dir.exists():
            candidates = sorted(test_dir.glob("test1.txt"))
            if candidates:
                self._load_file(str(candidates[0]))
                return
            candidates = sorted(test_dir.glob("*.txt"))
            if candidates:
                self._load_file(str(candidates[0]))

    # ------------------------------------------------------------------ #
    #  Parsing
    # ------------------------------------------------------------------ #
    def _parse_current(self):
        """Parse editor content and update state."""
        content = self.editor.get_content()
        if not content.strip():
            self.rules = []
            self.initial_facts = set()
            self.queries = []
            self._update_info()
            return False

        try:
            self.rules, self.initial_facts, self.queries = parse_input_file(content)
            self.active_facts = set(self.initial_facts)
            self._update_info()
            self._update_fact_buttons()
            return True
        except Exception as e:
            self.statusbar.set_status(f"Parse error: {e}", Colors.ERROR)
            return False

    def _update_info(self):
        facts_str = ", ".join(sorted(self.initial_facts)) if self.initial_facts else "-"
        queries_str = ", ".join(self.queries) if self.queries else "-"
        self.info_rules.configure(text=f"Rules: {len(self.rules)}")
        self.info_facts.configure(text=f"Facts: {facts_str}")
        self.info_queries.configure(text=f"Queries: {queries_str}")
        self.statusbar.set_info(
            f"{len(self.rules)} rules · {len(self.initial_facts)} facts · {len(self.queries)} queries"
        )

    def _update_fact_buttons(self):
        for letter, btn in self.fact_buttons.items():
            if letter in self.active_facts:
                btn.configure(style="FactActive.TButton")
            else:
                btn.configure(style="Fact.TButton")

    # ------------------------------------------------------------------ #
    #  Predictions
    # ------------------------------------------------------------------ #
    def _build_prediction_selectors(self):
        """Build prediction dropdown for each query after loading a file."""
        self.results_scroll.clear()
        self.prediction_vars.clear()
        self.predictions.clear()

        if not self.queries:
            tk.Label(
                self.results_scroll.scrollable_frame,
                text="No queries found in the file.\nAdd a line like ?GVX",
                font=Fonts.get_sans(Fonts.SIZE_MEDIUM),
                fg=Colors.TEXT_MUTED, bg=Colors.BG_DARK,
                justify="center",
            ).pack(pady=Spacing.XXL * 3)
            return

        # Instruction
        tk.Label(
            self.results_scroll.scrollable_frame,
            text="Select your prediction for each query, then press ▶ Run",
            font=Fonts.get_sans(Fonts.SIZE_MEDIUM),
            fg=Colors.TEXT_SECONDARY, bg=Colors.BG_DARK,
        ).pack(anchor="w", pady=(0, Spacing.LG))

        for query in self.queries:
            row = tk.Frame(
                self.results_scroll.scrollable_frame,
                bg=Colors.BG_OVERLAY, padx=Spacing.LG, pady=Spacing.MD,
            )
            row.pack(fill="x", pady=Spacing.XS)

            # Fact label
            tk.Label(
                row, text=query,
                font=Fonts.get_mono(Fonts.SIZE_TITLE),
                fg=Colors.BLUE, bg=Colors.BG_OVERLAY,
                width=3, anchor="w",
            ).pack(side="left", padx=(0, Spacing.XL))

            tk.Label(
                row, text="Your prediction:",
                font=Fonts.get_sans(Fonts.SIZE_NORMAL),
                fg=Colors.TEXT_MUTED, bg=Colors.BG_OVERLAY,
            ).pack(side="left", padx=(0, Spacing.MD))

            # Radio buttons for TRUE / FALSE / UNDETERMINED
            var = tk.StringVar(value="")
            self.prediction_vars[query] = var

            btn_frame = tk.Frame(row, bg=Colors.BG_OVERLAY)
            btn_frame.pack(side="left", padx=Spacing.SM)

            for value, symbol, color in [
                ("TRUE", "✓ TRUE", Colors.SUCCESS),
                ("FALSE", "✗ FALSE", Colors.ERROR),
                ("UNDETERMINED", "? UNDETERMINED", Colors.WARNING),
            ]:
                rb = tk.Radiobutton(
                    btn_frame,
                    text=symbol,
                    variable=var,
                    value=value,
                    font=Fonts.get_sans_bold(Fonts.SIZE_NORMAL),
                    fg=color,
                    bg=Colors.BG_OVERLAY,
                    selectcolor=Colors.BG_HIGHLIGHT,
                    activebackground=Colors.BG_OVERLAY,
                    activeforeground=color,
                    indicatoron=0,
                    padx=Spacing.LG,
                    pady=Spacing.SM,
                    bd=0,
                    relief="flat",
                    highlightthickness=0,
                    cursor="hand2",
                )
                rb.pack(side="left", padx=2)

        # Switch to results panel so user sees the selectors
        self._switch_panel("results")

    # ------------------------------------------------------------------ #
    #  Inference
    # ------------------------------------------------------------------ #
    def _on_run(self):
        """Run inference on current editor content."""
        if not self._parse_current():
            return

        if not self.queries:
            self.statusbar.set_status("No queries defined. Add ?XYZ line.", Colors.WARNING)
            return

        # Collect predictions before clearing the panel
        self.predictions = {}
        for query, var in self.prediction_vars.items():
            val = var.get()
            if val:
                self.predictions[query] = val

        try:
            self.engine = InferenceEngine(self.rules, self.initial_facts)
            self.results = self.engine.query_all(self.queries)

            self._display_results()
            self._display_reasoning()
            self._display_statistics()

            self.statusbar.set_status("Inference complete ✓", Colors.SUCCESS)

            # Switch to results
            self._switch_panel("results")

        except Exception as e:
            messagebox.showerror("Inference Error", f"Error during inference:\n{e}")
            self.statusbar.set_status(f"Error: {e}", Colors.ERROR)

    def _display_results(self):
        """Display query results as cards with prediction comparison."""
        self.results_scroll.clear()

        # --- Score calculation ---
        total_queries = len(self.results)
        correct = 0
        predicted_count = 0
        for fact, value in self.results.items():
            user_pred = self.predictions.get(fact, "")
            if user_pred:
                predicted_count += 1
                if user_pred == value.name:
                    correct += 1

        # --- Big score banner ---
        if predicted_count > 0:
            score_pct = int(correct / predicted_count * 100)
            if score_pct == 100:
                score_color = Colors.SUCCESS
                score_bg = "#2d4a2d"
                score_emoji = "🎉"
            elif score_pct >= 50:
                score_color = Colors.YELLOW
                score_bg = "#4a442d"
                score_emoji = "🤔"
            else:
                score_color = Colors.ERROR
                score_bg = "#4a2d2d"
                score_emoji = "💥"

            score_frame = tk.Frame(
                self.results_scroll.scrollable_frame,
                bg=score_bg, padx=Spacing.XXL, pady=Spacing.LG,
            )
            score_frame.pack(fill="x", pady=(0, Spacing.LG))

            tk.Label(
                score_frame,
                text=f"{score_emoji}  {correct} / {predicted_count} correct  ({score_pct}%)",
                font=Fonts.get_sans_bold(Fonts.SIZE_HEADER),
                fg=score_color, bg=score_bg,
            ).pack()

            if predicted_count < total_queries:
                tk.Label(
                    score_frame,
                    text=f"{total_queries - predicted_count} query(ies) had no prediction",
                    font=Fonts.get_sans(Fonts.SIZE_SMALL),
                    fg=Colors.TEXT_MUTED, bg=score_bg,
                ).pack()
        else:
            # No predictions were made
            hint = tk.Frame(
                self.results_scroll.scrollable_frame,
                bg=Colors.BG_OVERLAY, padx=Spacing.LG, pady=Spacing.MD,
            )
            hint.pack(fill="x", pady=(0, Spacing.LG))
            tk.Label(
                hint,
                text="💡 Tip: Load a file and select predictions before running to see your score!",
                font=Fonts.get_sans(Fonts.SIZE_NORMAL),
                fg=Colors.SAPPHIRE, bg=Colors.BG_OVERLAY,
            ).pack()

        # --- Summary badges ---
        true_count = sum(1 for v in self.results.values() if v == TruthValue.TRUE)
        false_count = sum(1 for v in self.results.values() if v == TruthValue.FALSE)
        undet_count = sum(1 for v in self.results.values() if v == TruthValue.UNDETERMINED)

        badge_frame = tk.Frame(self.results_scroll.scrollable_frame, bg=Colors.BG_DARK)
        badge_frame.pack(fill="x", pady=(0, Spacing.LG))

        for count, label, color, bg_color in [
            (true_count, "TRUE", Colors.SUCCESS, "#2d4a2d"),
            (false_count, "FALSE", Colors.ERROR, "#4a2d2d"),
            (undet_count, "UNDETERMINED", Colors.WARNING, "#4a442d"),
        ]:
            badge = tk.Frame(badge_frame, bg=bg_color, padx=Spacing.LG, pady=Spacing.SM)
            badge.pack(side="left", padx=(0, Spacing.MD))
            tk.Label(badge, text=f"{count}", font=Fonts.get_sans_bold(Fonts.SIZE_LARGE),
                     fg=color, bg=bg_color).pack(side="left", padx=(0, Spacing.SM))
            tk.Label(badge, text=label, font=Fonts.get_sans(Fonts.SIZE_SMALL),
                     fg=color, bg=bg_color).pack(side="left")

        # Separator
        tk.Frame(self.results_scroll.scrollable_frame, bg=Colors.BORDER, height=1).pack(
            fill="x", pady=Spacing.LG
        )

        # --- Result cards with prediction comparison ---
        for fact, value in self.results.items():
            user_pred = self.predictions.get(fact, "")
            is_correct = (user_pred == value.name) if user_pred else None

            # Card wrapper
            card_wrapper = tk.Frame(
                self.results_scroll.scrollable_frame, bg=Colors.BG_DARK,
            )
            card_wrapper.pack(fill="x", pady=Spacing.XS)

            card = ResultCard(card_wrapper, fact, value.name)
            card.pack(fill="x")

            # Prediction feedback row
            if user_pred:
                if is_correct:
                    fb_bg = "#2d4a2d"
                    fb_text = f"✓  Your prediction: {user_pred}  —  Correct!"
                    fb_color = Colors.SUCCESS
                else:
                    fb_bg = "#4a2d2d"
                    fb_text = f"✗  Your prediction: {user_pred}  —  Wrong (actual: {value.name})"
                    fb_color = Colors.ERROR

                fb = tk.Frame(card_wrapper, bg=fb_bg, padx=Spacing.LG, pady=Spacing.SM)
                fb.pack(fill="x")
                tk.Label(
                    fb, text=fb_text,
                    font=Fonts.get_sans(Fonts.SIZE_NORMAL),
                    fg=fb_color, bg=fb_bg,
                ).pack(side="left")

    def _display_reasoning(self):
        """Display reasoning visualization."""
        self.reasoning_text.clear()

        if not self.rules:
            return

        visualizer = ReasoningVisualizer(self.rules, self.initial_facts)

        # Header
        self.reasoning_text.append("REASONING VISUALIZATION\n", "header")
        facts_str = ", ".join(sorted(self.initial_facts)) if self.initial_facts else "None"
        self.reasoning_text.append(f"Initial facts: {facts_str}\n", "info")
        self.reasoning_text.append(f"Queries: {', '.join(self.queries)}\n\n", "info")

        for query in self.queries:
            self.reasoning_text.append("─" * 60 + "\n", "separator")
            self.reasoning_text.append(f"QUERY: {query}\n", "subheader")
            self.reasoning_text.append("─" * 60 + "\n\n", "separator")

            summary, result, steps = visualizer.explain_query(query)

            for step in steps:
                # Detect formal notation lines
                stripped = step.lstrip()
                if stripped.startswith("Formal:"):
                    self.reasoning_text.append(step + "\n", "formal")
                elif "TRUE" in step and "=" in step:
                    self.reasoning_text.append(step + "\n", "true_text")
                elif "FALSE" in step and "=" in step:
                    self.reasoning_text.append(step + "\n", "false_text")
                elif "UNDETERMINED" in step:
                    self.reasoning_text.append(step + "\n", "undetermined_text")
                else:
                    self.reasoning_text.append(step + "\n", "step")

            self.reasoning_text.append("\n", None)

            # Conclusion
            if result == TruthValue.TRUE:
                tag = "true_text"
            elif result == TruthValue.FALSE:
                tag = "false_text"
            else:
                tag = "undetermined_text"
            self.reasoning_text.append(f"CONCLUSION: {summary}\n\n", tag)

    def _display_statistics(self):
        """Display statistics."""
        self.statistics_text.clear()

        if not self.rules:
            self.statistics_text.append("No rules loaded.\n", "info")
            return

        analyzer = StatisticsAnalyzer(self.rules, self.initial_facts)
        stats = analyzer.analyze_rules()
        deps = analyzer.analyze_dependencies()

        # Header
        self.statistics_text.append("RULE SET STATISTICS\n\n", "header")

        # Basic metrics
        self.statistics_text.append("BASIC METRICS\n", "subheader")
        self.statistics_text.append("─" * 50 + "\n", "separator")
        self.statistics_text.append(f"  Total rules:         {stats['total_rules']}\n", "step")
        self.statistics_text.append(f"  Biconditional:       {stats['biconditional_rules']}\n", "step")
        regular = stats['total_rules'] - stats['biconditional_rules']
        self.statistics_text.append(f"  Regular:             {regular}\n\n", "step")

        # Facts
        self.statistics_text.append("FACTS\n", "subheader")
        self.statistics_text.append("─" * 50 + "\n", "separator")
        init_str = ", ".join(sorted(self.initial_facts)) if self.initial_facts else "None"
        self.statistics_text.append(f"  Initial facts:       {init_str}\n", "step")
        used_str = ", ".join(stats['facts_used'])
        self.statistics_text.append(f"  Facts used:          {len(stats['facts_used'])} ({used_str})\n", "step")
        concl_str = ", ".join(stats['facts_concluded'])
        self.statistics_text.append(f"  Facts concluded:     {len(stats['facts_concluded'])} ({concl_str})\n\n", "step")

        # Operators
        from parser import NodeType
        op_names = {
            NodeType.NOT: "NOT (!)",
            NodeType.AND: "AND (+)",
            NodeType.OR: "OR (|)",
            NodeType.XOR: "XOR (^)",
            NodeType.IMPLIES: "IMPLIES (=>)",
            NodeType.IFF: "IFF (<=>)",
        }

        self.statistics_text.append("OPERATORS\n", "subheader")
        self.statistics_text.append("─" * 50 + "\n", "separator")
        sorted_ops = sorted(stats['total_operators'].items(), key=lambda x: -x[1])
        for op_type, count in sorted_ops:
            name = op_names.get(op_type, str(op_type))
            self.statistics_text.append(f"  {name:20s} {count:3d}×\n", "step")
        self.statistics_text.append("\n", None)

        # Complexity
        if stats['complexity_scores']:
            self.statistics_text.append("COMPLEXITY\n", "subheader")
            self.statistics_text.append("─" * 50 + "\n", "separator")
            self.statistics_text.append(f"  Average complexity:  {stats['avg_complexity']:.2f}\n", "step")
            self.statistics_text.append(f"  Max complexity:      {stats['max_complexity']}\n", "step")
            self.statistics_text.append(f"  Min complexity:      {stats['min_complexity']}\n", "step")
            self.statistics_text.append(f"  Max nesting depth:   {stats['max_depth']}\n\n", "step")

        # Dependencies
        if deps:
            self.statistics_text.append("DEPENDENCIES\n", "subheader")
            self.statistics_text.append("─" * 50 + "\n", "separator")
            for fact, dependencies in sorted(deps.items()):
                if dependencies:
                    dep_str = ", ".join(sorted(dependencies))
                    self.statistics_text.append(f"  {fact} → {dep_str}\n", "step")
            self.statistics_text.append("\n", None)

        # Most complex rules
        if stats['complexity_scores']:
            self.statistics_text.append("MOST COMPLEX RULES\n", "subheader")
            self.statistics_text.append("─" * 50 + "\n", "separator")
            rules_with_complexity = list(zip(self.rules, stats['complexity_scores']))
            rules_with_complexity.sort(key=lambda x: -x[1])
            for i, (rule, complexity) in enumerate(rules_with_complexity[:5], 1):
                rule_str = analyzer.format_rule(rule)
                self.statistics_text.append(f"  {i}. [{complexity}] {rule_str}\n", "step")

    # ------------------------------------------------------------------ #
    #  Interactive Facts
    # ------------------------------------------------------------------ #
    def _toggle_fact(self, letter):
        if letter in self.active_facts:
            self.active_facts.discard(letter)
        else:
            self.active_facts.add(letter)
        self._update_fact_buttons()

    def _on_interactive_query(self):
        """Run inference with interactively selected facts."""
        query_text = self.query_entry.get().strip().upper()
        if not query_text:
            # Use queries from file
            query_text = "".join(self.queries) if self.queries else ""

        if not query_text:
            self.statusbar.set_status("Enter query letters (e.g. GVX)", Colors.WARNING)
            return

        queries = [ch for ch in query_text if ch.isupper()]
        if not queries:
            self.statusbar.set_status("Enter uppercase letters for queries", Colors.WARNING)
            return

        if not self._parse_current():
            self.statusbar.set_status("Parse the rules first (load a file or type rules)", Colors.WARNING)
            return

        try:
            engine = InferenceEngine(self.rules, self.active_facts)
            results = engine.query_all(queries)

            # Clear old results
            for w in self.interactive_results_frame.winfo_children():
                w.destroy()

            tk.Label(
                self.interactive_results_frame, text="Results",
                font=Fonts.get_sans_bold(Fonts.SIZE_MEDIUM),
                fg=Colors.TEXT_SECONDARY, bg=Colors.BG_DARK,
            ).pack(anchor="w", pady=(0, Spacing.MD))

            facts_str = ", ".join(sorted(self.active_facts)) if self.active_facts else "None"
            tk.Label(
                self.interactive_results_frame,
                text=f"Active facts: {facts_str}",
                font=Fonts.get_sans(Fonts.SIZE_SMALL),
                fg=Colors.TEXT_MUTED, bg=Colors.BG_DARK,
            ).pack(anchor="w", pady=(0, Spacing.MD))

            for fact, value in results.items():
                card = ResultCard(self.interactive_results_frame, fact, value.name)
                card.pack(fill="x", pady=Spacing.XS)

            self.statusbar.set_status("Interactive query complete ✓", Colors.SUCCESS)

        except Exception as e:
            self.statusbar.set_status(f"Query error: {e}", Colors.ERROR)

    # ------------------------------------------------------------------ #
    #  Run
    # ------------------------------------------------------------------ #
    def run(self):
        """Start the application."""
        self.root.mainloop()
