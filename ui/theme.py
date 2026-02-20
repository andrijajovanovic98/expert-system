#!/usr/bin/env python3
"""
Theme configuration for the Expert System UI.
Modern dark theme inspired by popular code editors.
"""


class Colors:
    """Color palette - Catppuccin Mocha inspired dark theme."""

    # Base colors
    BG_DARK = "#1e1e2e"
    BG_SURFACE = "#282a3a"  
    BG_OVERLAY = "#313244"
    BG_HIGHLIGHT = "#3b3d52"
    BG_LIGHTER = "#45475a"

    # Text colors
    TEXT_PRIMARY = "#cdd6f4"
    TEXT_SECONDARY = "#a6adc8"
    TEXT_MUTED = "#6c7086"
    TEXT_DARK = "#1e1e2e"

    # Accent colors
    BLUE = "#89b4fa"
    BLUE_DIM = "#4a6fa5"
    LAVENDER = "#b4befe"
    SAPPHIRE = "#74c7ec"
    TEAL = "#94e2d5"
    GREEN = "#a6e3a1"
    YELLOW = "#f9e2af"
    PEACH = "#fab387"
    RED = "#f38ba8"
    PINK = "#f5c2e7"
    MAUVE = "#cba6f7"

    # Semantic colors
    SUCCESS = GREEN
    ERROR = RED
    WARNING = YELLOW
    INFO = BLUE
    UNDETERMINED = YELLOW

    # Editor syntax highlighting
    SYN_COMMENT = "#6c7086"
    SYN_OPERATOR = "#fab387"
    SYN_FACT = "#89b4fa"
    SYN_INITIAL = "#a6e3a1"
    SYN_QUERY = "#cba6f7"
    SYN_PAREN = "#f9e2af"

    # Borders
    BORDER = "#45475a"
    BORDER_FOCUS = "#89b4fa"

    # Scrollbar
    SCROLLBAR_BG = "#313244"
    SCROLLBAR_FG = "#585b70"

    # Button states
    BTN_BG = "#313244"
    BTN_HOVER = "#45475a"
    BTN_ACTIVE = "#585b70"
    BTN_PRIMARY_BG = "#89b4fa"
    BTN_PRIMARY_FG = "#1e1e2e"


class Fonts:
    """Font configuration."""

    FAMILY_MONO = "JetBrains Mono"
    FAMILY_MONO_FALLBACK = "Consolas"
    FAMILY_MONO_FALLBACK2 = "monospace"
    FAMILY_SANS = "Segoe UI"
    FAMILY_SANS_FALLBACK = "Helvetica"

    SIZE_SMALL = 9
    SIZE_NORMAL = 10
    SIZE_MEDIUM = 11
    SIZE_LARGE = 13
    SIZE_TITLE = 16
    SIZE_HEADER = 20

    @staticmethod
    def get_mono(size=None):
        if size is None:
            size = Fonts.SIZE_NORMAL
        return (Fonts.FAMILY_MONO, size)

    @staticmethod
    def get_sans(size=None):
        if size is None:
            size = Fonts.SIZE_NORMAL
        return (Fonts.FAMILY_SANS, size)

    @staticmethod
    def get_sans_bold(size=None):
        if size is None:
            size = Fonts.SIZE_NORMAL
        return (Fonts.FAMILY_SANS, size, "bold")


class Spacing:
    """Consistent spacing values."""
    XS = 2
    SM = 4
    MD = 8
    LG = 12
    XL = 16
    XXL = 24


def apply_theme(root):
    """Apply the dark theme to the root window and ttk styles."""
    import tkinter.ttk as ttk

    root.configure(bg=Colors.BG_DARK)

    style = ttk.Style()

    try:
        style.theme_use("clam")
    except Exception:
        pass

    # -- Frame --
    style.configure("TFrame", background=Colors.BG_DARK)
    style.configure("Surface.TFrame", background=Colors.BG_SURFACE)
    style.configure("Overlay.TFrame", background=Colors.BG_OVERLAY)

    # -- Label --
    style.configure(
        "TLabel",
        background=Colors.BG_DARK,
        foreground=Colors.TEXT_PRIMARY,
        font=Fonts.get_sans(),
    )
    style.configure(
        "Title.TLabel",
        background=Colors.BG_DARK,
        foreground=Colors.LAVENDER,
        font=Fonts.get_sans_bold(Fonts.SIZE_HEADER),
    )
    style.configure(
        "Subtitle.TLabel",
        background=Colors.BG_DARK,
        foreground=Colors.TEXT_SECONDARY,
        font=Fonts.get_sans(Fonts.SIZE_MEDIUM),
    )
    style.configure(
        "Section.TLabel",
        background=Colors.BG_DARK,
        foreground=Colors.BLUE,
        font=Fonts.get_sans_bold(Fonts.SIZE_LARGE),
    )
    style.configure(
        "Success.TLabel",
        background=Colors.BG_DARK,
        foreground=Colors.SUCCESS,
        font=Fonts.get_sans_bold(Fonts.SIZE_MEDIUM),
    )
    style.configure(
        "Error.TLabel",
        background=Colors.BG_DARK,
        foreground=Colors.ERROR,
        font=Fonts.get_sans_bold(Fonts.SIZE_MEDIUM),
    )
    style.configure(
        "Warning.TLabel",
        background=Colors.BG_DARK,
        foreground=Colors.WARNING,
        font=Fonts.get_sans_bold(Fonts.SIZE_MEDIUM),
    )
    style.configure(
        "Surface.TLabel",
        background=Colors.BG_SURFACE,
        foreground=Colors.TEXT_PRIMARY,
    )
    style.configure(
        "StatusBar.TLabel",
        background=Colors.BG_OVERLAY,
        foreground=Colors.TEXT_MUTED,
        font=Fonts.get_sans(Fonts.SIZE_SMALL),
        padding=(Spacing.MD, Spacing.SM),
    )

    # -- Button --
    style.configure(
        "TButton",
        background=Colors.BTN_BG,
        foreground=Colors.TEXT_PRIMARY,
        font=Fonts.get_sans(Fonts.SIZE_NORMAL),
        borderwidth=0,
        padding=(Spacing.LG, Spacing.MD),
    )
    style.map(
        "TButton",
        background=[("active", Colors.BTN_HOVER), ("pressed", Colors.BTN_ACTIVE)],
        foreground=[("active", Colors.TEXT_PRIMARY)],
    )
    style.configure(
        "Primary.TButton",
        background=Colors.BTN_PRIMARY_BG,
        foreground=Colors.BTN_PRIMARY_FG,
        font=Fonts.get_sans_bold(Fonts.SIZE_NORMAL),
    )
    style.map(
        "Primary.TButton",
        background=[("active", Colors.LAVENDER), ("pressed", Colors.SAPPHIRE)],
        foreground=[("active", Colors.BTN_PRIMARY_FG)],
    )
    style.configure(
        "Toolbar.TButton",
        background=Colors.BG_DARK,
        foreground=Colors.TEXT_SECONDARY,
        font=Fonts.get_sans(Fonts.SIZE_NORMAL),
        padding=(Spacing.LG, Spacing.SM),
        borderwidth=0,
    )
    style.map(
        "Toolbar.TButton",
        background=[("active", Colors.BG_OVERLAY)],
        foreground=[("active", Colors.TEXT_PRIMARY)],
    )
    style.configure(
        "Fact.TButton",
        background=Colors.BG_OVERLAY,
        foreground=Colors.TEXT_SECONDARY,
        font=Fonts.get_mono(Fonts.SIZE_MEDIUM),
        padding=(Spacing.SM, Spacing.XS),
        borderwidth=1,
    )
    style.map(
        "Fact.TButton",
        background=[("active", Colors.BG_HIGHLIGHT)],
    )
    style.configure(
        "FactActive.TButton",
        background=Colors.GREEN,
        foreground=Colors.TEXT_DARK,
        font=Fonts.get_mono(Fonts.SIZE_MEDIUM),
        padding=(Spacing.SM, Spacing.XS),
        borderwidth=1,
    )
    style.map(
        "FactActive.TButton",
        background=[("active", Colors.TEAL)],
        foreground=[("active", Colors.TEXT_DARK)],
    )

    style.configure(
        "Nav.TButton",
        background=Colors.BG_DARK,
        foreground=Colors.TEXT_MUTED,
        font=Fonts.get_sans(Fonts.SIZE_NORMAL),
        padding=(Spacing.XL, Spacing.MD),
        borderwidth=0,
    )
    style.map(
        "Nav.TButton",
        background=[("active", Colors.BG_SURFACE)],
        foreground=[("active", Colors.TEXT_PRIMARY)],
    )
    style.configure(
        "NavActive.TButton",
        background=Colors.BG_SURFACE,
        foreground=Colors.BLUE,
        font=Fonts.get_sans_bold(Fonts.SIZE_NORMAL),
        padding=(Spacing.XL, Spacing.MD),
        borderwidth=0,
    )

    # -- Notebook (tabs) --
    style.configure(
        "TNotebook",
        background=Colors.BG_DARK,
        borderwidth=0,
    )
    style.configure(
        "TNotebook.Tab",
        background=Colors.BG_OVERLAY,
        foreground=Colors.TEXT_MUTED,
        font=Fonts.get_sans(Fonts.SIZE_NORMAL),
        padding=(Spacing.XL, Spacing.MD),
        borderwidth=0,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", Colors.BG_SURFACE)],
        foreground=[("selected", Colors.BLUE)],
    )

    # -- Separator --
    style.configure("TSeparator", background=Colors.BORDER)

    # -- PanedWindow --
    style.configure(
        "TPanedwindow",
        background=Colors.BORDER,
    )

    # -- Scrollbar --
    style.configure(
        "Vertical.TScrollbar",
        background=Colors.SCROLLBAR_BG,
        troughcolor=Colors.BG_SURFACE,
        borderwidth=0,
        arrowsize=0,
    )
    style.map(
        "Vertical.TScrollbar",
        background=[("active", Colors.SCROLLBAR_FG)],
    )

    return style
