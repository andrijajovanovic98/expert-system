#!/usr/bin/env python3
"""
Custom widgets for the Expert System UI.
"""

import tkinter as tk
import tkinter.ttk as ttk
from ui.theme import Colors, Fonts, Spacing


class LineNumberedText(tk.Frame):
    """Text editor with line numbers and syntax highlighting."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=Colors.BG_SURFACE, bd=0)

        self._build_widgets()
        self._bind_events()
        self._syntax_rules = self._build_syntax_rules()

    def _build_widgets(self):
        # Line numbers
        self.line_numbers = tk.Text(
            self,
            width=4,
            padx=Spacing.SM,
            pady=Spacing.MD,
            takefocus=0,
            border=0,
            background=Colors.BG_OVERLAY,
            foreground=Colors.TEXT_MUTED,
            font=Fonts.get_mono(Fonts.SIZE_NORMAL),
            state="disabled",
            wrap="none",
            cursor="arrow",
            selectbackground=Colors.BG_OVERLAY,
            selectforeground=Colors.TEXT_MUTED,
        )
        self.line_numbers.pack(side="left", fill="y")

        # Separator line
        sep = tk.Frame(self, width=1, bg=Colors.BORDER)
        sep.pack(side="left", fill="y")

        # Main text area
        text_frame = tk.Frame(self, bg=Colors.BG_SURFACE)
        text_frame.pack(side="left", fill="both", expand=True)

        self.text = tk.Text(
            text_frame,
            wrap="none",
            padx=Spacing.MD,
            pady=Spacing.MD,
            border=0,
            background=Colors.BG_SURFACE,
            foreground=Colors.TEXT_PRIMARY,
            insertbackground=Colors.BLUE,
            selectbackground=Colors.BG_HIGHLIGHT,
            selectforeground=Colors.TEXT_PRIMARY,
            font=Fonts.get_mono(Fonts.SIZE_NORMAL),
            undo=True,
            autoseparators=True,
            maxundo=-1,
            tabs="4c",
        )

        scrollbar = ttk.Scrollbar(
            text_frame, orient="vertical", command=self._on_scroll
        )
        scrollbar.pack(side="right", fill="y")

        self.text.configure(yscrollcommand=scrollbar.set)
        self.text.pack(side="left", fill="both", expand=True)

    def _on_scroll(self, *args):
        self.text.yview(*args)
        self.line_numbers.yview(*args)

    def _bind_events(self):
        self.text.bind("<KeyRelease>", self._on_text_change)
        self.text.bind("<ButtonRelease>", self._on_text_change)
        self.text.bind("<MouseWheel>", self._on_mousewheel)
        self.text.bind("<Button-4>", self._on_mousewheel)
        self.text.bind("<Button-5>", self._on_mousewheel)
        self.text.bind("<<Modified>>", self._on_modified)

    def _on_mousewheel(self, event):
        self.line_numbers.yview_moveto(self.text.yview()[0])

    def _on_modified(self, event=None):
        if self.text.edit_modified():
            self._update_line_numbers()
            self._apply_syntax_highlighting()
            self.text.edit_modified(False)

    def _on_text_change(self, event=None):
        self._update_line_numbers()
        self._apply_syntax_highlighting()
        self.line_numbers.yview_moveto(self.text.yview()[0])

    def _update_line_numbers(self):
        self.line_numbers.configure(state="normal")
        self.line_numbers.delete("1.0", "end")

        line_count = int(self.text.index("end-1c").split(".")[0])
        line_str = "\n".join(str(i) for i in range(1, line_count + 1))
        self.line_numbers.insert("1.0", line_str)
        self.line_numbers.configure(state="disabled")

    def _build_syntax_rules(self):
        """Define syntax highlighting tag configurations."""
        tags = {
            "comment": {"foreground": Colors.SYN_COMMENT, "font": Fonts.get_mono(Fonts.SIZE_NORMAL)},
            "operator": {"foreground": Colors.SYN_OPERATOR, "font": Fonts.get_mono(Fonts.SIZE_NORMAL)},
            "fact": {"foreground": Colors.SYN_FACT, "font": Fonts.get_mono(Fonts.SIZE_NORMAL)},
            "initial_line": {"foreground": Colors.SYN_INITIAL, "font": Fonts.get_mono(Fonts.SIZE_NORMAL)},
            "query_line": {"foreground": Colors.SYN_QUERY, "font": Fonts.get_mono(Fonts.SIZE_NORMAL)},
            "paren": {"foreground": Colors.SYN_PAREN, "font": Fonts.get_mono(Fonts.SIZE_NORMAL)},
        }
        for tag_name, config in tags.items():
            self.text.tag_configure(tag_name, **config)

        # Priority: comment > initial_line > query_line > operator > paren > fact
        self.text.tag_raise("comment")
        return tags

    def _apply_syntax_highlighting(self):
        """Apply syntax highlighting to the entire text."""
        for tag in self._syntax_rules:
            self.text.tag_remove(tag, "1.0", "end")

        content = self.text.get("1.0", "end")
        lines = content.split("\n")

        for line_idx, line in enumerate(lines):
            line_num = line_idx + 1
            stripped = line.lstrip()

            # Comment highlighting
            if "#" in line:
                comment_start = line.index("#")
                start = f"{line_num}.{comment_start}"
                end = f"{line_num}.end"
                self.text.tag_add("comment", start, end)
                # Only highlight before the comment
                line_before_comment = line[:comment_start]
            else:
                line_before_comment = line

            # Initial facts line
            if stripped.startswith("="):
                start = f"{line_num}.0"
                comment_end = len(line_before_comment)
                end = f"{line_num}.{comment_end}"
                self.text.tag_add("initial_line", start, end)
                continue

            # Query line
            if stripped.startswith("?"):
                start = f"{line_num}.0"
                comment_end = len(line_before_comment)
                end = f"{line_num}.{comment_end}"
                self.text.tag_add("query_line", start, end)
                continue

            # Operators and facts in rule lines
            i = 0
            while i < len(line_before_comment):
                ch = line_before_comment[i]

                # Check for <=>
                if ch == "<" and i + 2 < len(line_before_comment) and line_before_comment[i:i+3] == "<=>":
                    self.text.tag_add("operator", f"{line_num}.{i}", f"{line_num}.{i+3}")
                    i += 3
                    continue
                # Check for =>
                if ch == "=" and i + 1 < len(line_before_comment) and line_before_comment[i:i+2] == "=>":
                    self.text.tag_add("operator", f"{line_num}.{i}", f"{line_num}.{i+2}")
                    i += 2
                    continue
                # Single-char operators
                if ch in "!+|^":
                    self.text.tag_add("operator", f"{line_num}.{i}", f"{line_num}.{i+1}")
                    i += 1
                    continue
                # Parentheses
                if ch in "()":
                    self.text.tag_add("paren", f"{line_num}.{i}", f"{line_num}.{i+1}")
                    i += 1
                    continue
                # Facts (uppercase letters)
                if ch.isupper():
                    self.text.tag_add("fact", f"{line_num}.{i}", f"{line_num}.{i+1}")
                    i += 1
                    continue

                i += 1

    def get_content(self):
        """Get the text content."""
        return self.text.get("1.0", "end-1c")

    def set_content(self, content):
        """Set the text content."""
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self._update_line_numbers()
        self._apply_syntax_highlighting()

    def clear(self):
        """Clear the text."""
        self.text.delete("1.0", "end")
        self._update_line_numbers()


class ResultCard(tk.Frame):
    """A card-style widget for displaying a single result."""

    def __init__(self, parent, fact, value_name, **kwargs):
        super().__init__(parent, bg=Colors.BG_OVERLAY, padx=Spacing.LG, pady=Spacing.MD, **kwargs)

        if value_name == "TRUE":
            symbol = "✓"
            color = Colors.SUCCESS
            badge_bg = "#2d4a2d"
        elif value_name == "FALSE":
            symbol = "✗"
            color = Colors.ERROR
            badge_bg = "#4a2d2d"
        else:
            symbol = "?"
            color = Colors.WARNING
            badge_bg = "#4a442d"

        # Left: badge with symbol
        badge = tk.Frame(self, bg=badge_bg, padx=Spacing.MD, pady=Spacing.SM)
        badge.pack(side="left", padx=(0, Spacing.LG))

        symbol_label = tk.Label(
            badge,
            text=symbol,
            font=Fonts.get_sans_bold(Fonts.SIZE_LARGE),
            fg=color,
            bg=badge_bg,
        )
        symbol_label.pack()

        # Middle: fact name
        tk.Label(
            self,
            text=fact,
            font=Fonts.get_mono(Fonts.SIZE_TITLE),
            fg=Colors.TEXT_PRIMARY,
            bg=Colors.BG_OVERLAY,
        ).pack(side="left", padx=(0, Spacing.LG))

        # Right: value
        tk.Label(
            self,
            text=value_name,
            font=Fonts.get_sans_bold(Fonts.SIZE_MEDIUM),
            fg=color,
            bg=Colors.BG_OVERLAY,
        ).pack(side="right")

    def rounded_rect(self, canvas, x1, y1, x2, y2, radius=10, **kwargs):
        """Draw a rounded rectangle on a canvas."""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1, x2, y1 + radius,
            x2, y2 - radius,
            x2, y2, x2 - radius, y2,
            x1 + radius, y2,
            x1, y2, x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        return canvas.create_polygon(points, smooth=True, **kwargs)


class ScrollableFrame(tk.Frame):
    """A scrollable frame widget."""

    def __init__(self, parent, bg=None, **kwargs):
        if bg is None:
            bg = Colors.BG_DARK
        super().__init__(parent, bg=bg, **kwargs)

        self.canvas = tk.Canvas(
            self, bg=bg, highlightthickness=0, bd=0
        )
        self.scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Resize inner frame to canvas width
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Mouse wheel scrolling
        self.scrollable_frame.bind("<Enter>", self._bind_mousewheel)
        self.scrollable_frame.bind("<Leave>", self._unbind_mousewheel)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def clear(self):
        """Remove all children of the scrollable frame."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()


class ReasoningText(tk.Text):
    """A read-only text widget styled for reasoning output."""

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            wrap="word",
            padx=Spacing.LG,
            pady=Spacing.LG,
            border=0,
            background=Colors.BG_SURFACE,
            foreground=Colors.TEXT_PRIMARY,
            font=Fonts.get_mono(Fonts.SIZE_NORMAL),
            state="disabled",
            cursor="arrow",
            selectbackground=Colors.BG_HIGHLIGHT,
            selectforeground=Colors.TEXT_PRIMARY,
            **kwargs,
        )

        # Reasoning tags
        self.tag_configure("header", foreground=Colors.LAVENDER, font=Fonts.get_sans_bold(Fonts.SIZE_LARGE))
        self.tag_configure("subheader", foreground=Colors.BLUE, font=Fonts.get_sans_bold(Fonts.SIZE_MEDIUM))
        self.tag_configure("true_text", foreground=Colors.SUCCESS, font=Fonts.get_mono(Fonts.SIZE_NORMAL))
        self.tag_configure("false_text", foreground=Colors.ERROR, font=Fonts.get_mono(Fonts.SIZE_NORMAL))
        self.tag_configure("undetermined_text", foreground=Colors.WARNING, font=Fonts.get_mono(Fonts.SIZE_NORMAL))
        self.tag_configure("step", foreground=Colors.TEXT_SECONDARY, font=Fonts.get_mono(Fonts.SIZE_NORMAL))
        self.tag_configure("formal", foreground=Colors.MAUVE, font=Fonts.get_mono(Fonts.SIZE_SMALL))
        self.tag_configure("separator", foreground=Colors.BORDER, font=Fonts.get_mono(Fonts.SIZE_SMALL))
        self.tag_configure("conclusion", foreground=Colors.LAVENDER, font=Fonts.get_sans_bold(Fonts.SIZE_MEDIUM))
        self.tag_configure("info", foreground=Colors.SAPPHIRE, font=Fonts.get_sans(Fonts.SIZE_NORMAL))

    def append(self, text, tag=None):
        """Append text with an optional tag."""
        self.configure(state="normal")
        if tag:
            self.insert("end", text, tag)
        else:
            self.insert("end", text)
        self.configure(state="disabled")

    def clear(self):
        """Clear all text."""
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.configure(state="disabled")


class StatusBar(tk.Frame):
    """Status bar at the bottom of the window."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=Colors.BG_OVERLAY, height=28, **kwargs)
        self.pack_propagate(False)

        # Left side: status message
        self.status_label = tk.Label(
            self,
            text="Ready",
            font=Fonts.get_sans(Fonts.SIZE_SMALL),
            fg=Colors.TEXT_MUTED,
            bg=Colors.BG_OVERLAY,
            anchor="w",
            padx=Spacing.MD,
        )
        self.status_label.pack(side="left", fill="x", expand=True)

        # Right side: info
        self.info_label = tk.Label(
            self,
            text="",
            font=Fonts.get_sans(Fonts.SIZE_SMALL),
            fg=Colors.TEXT_MUTED,
            bg=Colors.BG_OVERLAY,
            anchor="e",
            padx=Spacing.MD,
        )
        self.info_label.pack(side="right")

    def set_status(self, message, color=None):
        if color is None:
            color = Colors.TEXT_MUTED
        self.status_label.configure(text=message, fg=color)

    def set_info(self, message):
        self.info_label.configure(text=message)
