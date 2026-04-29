"""drag_drop_list.py
─────────────────
Widget Drag & Drop générique pour tkinter.
Fonctionne avec n'importe quel type d'item (dataclass, dict, objet…).

USAGE MINIMAL
─────────────
    list_widget = DragDropList(
        parent,
        items       = my_items,
        render_item = my_render_fn,
    )

SIGNATURE render_item
─────────────────────
    def render_item(canvas, item, x, y, w, h, state):
        # state : "normal" | "ghost" | "floating"
        # Dessinez ce que vous voulez dans la zone (x, y, x+w, y+h)

CALLBACKS OPTIONNELS  (None = bouton masqué)
────────────────────
    on_reorder(items)           → appelé après tout changement d'ordre
    on_move_up(item, idx)       → ↑   (None cache le bouton)
    on_move_down(item, idx)     → ↓   (None cache le bouton)
    on_duplicate(item, idx)     → ⧉   doit retourner le clone à insérer
                                       (None cache le bouton)
    on_edit(item, idx)          → ✎   (None cache le bouton)
    on_delete(item, idx)        → ✕   retourne True pour confirmer la suppression
                                       (None cache le bouton)
"""

import tkinter as tk
from dataclasses import dataclass
from typing import Any, Callable, List, Optional

# ── Palette par défaut (remplaçable) ─────────────────────────────────────────

DEFAULT_THEME = {
    "bg": "#f0f4f8",
    "ghost": "#e2e8f0",
    "drag_bg": "#3b82f6",
    "insert": "#3b82f6",
    "btn_move": "#64748b",
    "btn_dup": "#0ea5e9",
    "btn_edit": "#f59e0b",
    "btn_del": "#ef4444",
    "btn_hover": "#1e293b",
    "btn_fg": "#ffffff",
}


# ── Config d'un bouton ────────────────────────────────────────────────────────


@dataclass
class _BtnDef:
    key: str
    symbol: str
    color_key: str  # clé dans le thème


_BUTTONS: List[_BtnDef] = [  # ordre d'affichage (droite → gauche)
    _BtnDef("delete", "✕", "btn_del"),
    _BtnDef("edit", "✎", "btn_edit"),
    _BtnDef("duplicate", "⧉", "btn_dup"),
    _BtnDef("move_down", "↓", "btn_move"),
    _BtnDef("move_up", "↑", "btn_move"),
]


# ── Widget ────────────────────────────────────────────────────────────────────


class DragDropList(tk.Frame):
    """Liste réordonnables par drag & drop.

    Paramètres
    ----------
    parent       : widget parent tkinter
    items        : liste d'objets quelconques (modifiée IN-PLACE)
    render_item  : fn(canvas, item, x, y, w, h, state) — obligatoire
    item_height  : hauteur en px de chaque item (défaut 56)
    item_width   : largeur totale en px (défaut 520)
    pad          : espacement vertical entre items (défaut 6)
    btn_size     : taille des boutons en px (défaut 28)
    theme        : dict de couleurs (fusionne avec DEFAULT_THEME)
    on_reorder   : fn(items)
    on_move_up   : fn(item, idx)  | None → bouton masqué
    on_move_down : fn(item, idx)  | None → bouton masqué
    on_duplicate : fn(item, idx) → clone | None → bouton masqué
    on_edit      : fn(item, idx)  | None → bouton masqué
    on_delete    : fn(item, idx) → bool  | None → bouton masqué
    """

    def __init__(
        self,
        parent,
        items: List[Any],
        render_item: Callable,
        *,
        item_height: int = 56,
        item_width: int = 520,
        pad: int = 6,
        btn_size: int = 28,
        theme: Optional[dict] = None,
        on_reorder: Optional[Callable] = None,
        on_move_up: Optional[Callable] = None,
        on_move_down: Optional[Callable] = None,
        on_duplicate: Optional[Callable] = None,
        on_edit: Optional[Callable] = None,
        on_delete: Optional[Callable] = None,
    ):
        self._theme = {**DEFAULT_THEME, **(theme or {})}
        super().__init__(parent, bg=self._theme["bg"])

        self.items = items
        self._render_item = render_item
        self.ITEM_H = item_height
        self.ITEM_W = item_width
        self.PAD = pad
        self.BTN_SIZE = btn_size

        # Callbacks → dict interne
        self._cbs = {
            "move_up": on_move_up,
            "move_down": on_move_down,
            "duplicate": on_duplicate,
            "edit": on_edit,
            "delete": on_delete,
        }
        self._on_reorder = on_reorder

        # Boutons visibles (ceux dont le callback n'est pas None)
        self._visible_btns = [b for b in _BUTTONS if self._cbs.get(b.key) is not None]

        # État interne drag
        self._drag_idx = None
        self._drag_offset = 0
        self._insert_pos = None
        self._hovered_btn = None  # (item_idx, btn_key) | None

        self._build_canvas()

    # ─── Canvas ──────────────────────────────────────────────────────────────

    def _total_h(self):
        return max(1, len(self.items)) * (self.ITEM_H + self.PAD) + self.PAD

    def _build_canvas(self):
        if hasattr(self, "canvas"):
            self.canvas.destroy()
        self.canvas = tk.Canvas(
            self,
            width=self.ITEM_W + self.PAD * 2,
            height=self._total_h(),
            bg=self._theme["bg"],
            highlightthickness=0,
            cursor="hand2",
        )
        self.canvas.pack(padx=16, pady=16)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_hover)
        self.canvas.bind("<Leave>", self._on_leave)
        self.redraw()

    def rebuild(self):
        """À appeler si vous avez ajouté / supprimé des items depuis l'extérieur."""
        self._build_canvas()

    # ─── Géométrie ───────────────────────────────────────────────────────────

    def _item_y(self, idx):
        return self.PAD + idx * (self.ITEM_H + self.PAD)

    def _btn_rects(self, idx):
        """→ {btn_key: (x1, y1, x2, y2)} pour les boutons visibles de l'item idx."""
        y = self._item_y(idx)
        cy = y + self.ITEM_H // 2
        x_r = self.PAD + self.ITEM_W - 4
        out = {}
        for i, btn in enumerate(self._visible_btns):
            x2 = x_r - i * (self.BTN_SIZE + 4)
            x1 = x2 - self.BTN_SIZE
            out[btn.key] = (x1, cy - self.BTN_SIZE // 2, x2, cy + self.BTN_SIZE // 2)
        return out

    def _btn_zone_width(self):
        n = len(self._visible_btns)
        return n * (self.BTN_SIZE + 4) + 8 if n else 0

    def _hit_btn(self, mx, my, idx):
        for key, (x1, y1, x2, y2) in self._btn_rects(idx).items():
            if x1 <= mx <= x2 and y1 <= my <= y2:
                return key
        return None

    def _idx_at(self, y):
        idx = (y - self.PAD) // (self.ITEM_H + self.PAD)
        return idx if 0 <= idx < len(self.items) else None

    # ─── Dessin ──────────────────────────────────────────────────────────────

    def _rounded_rect(self, x1, y1, x2, y2, r, fill, outline=""):
        cv = self.canvas
        cv.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, fill=fill, outline=fill)
        cv.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, fill=fill, outline=fill)
        cv.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, fill=fill, outline=fill)
        cv.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, fill=fill, outline=fill)
        cv.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline=fill)
        cv.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline=fill)
        if outline and outline != fill:
            cv.create_rectangle(x1, y1, x2, y2, outline=outline, fill="")

    def _draw_ghost(self, idx):
        y = self._item_y(idx)
        self._rounded_rect(self.PAD, y, self.PAD + self.ITEM_W, y + self.ITEM_H, 8, self._theme["ghost"])

    def _draw_floating(self, idx, y_top):
        """Item en cours de drag : fond bleu, render_item appelé en état 'floating'."""
        x, w, h = self.PAD, self.ITEM_W, self.ITEM_H
        self._rounded_rect(x, y_top, x + w, y_top + h, 8, self._theme["drag_bg"])
        render_w = w - self._btn_zone_width()
        self._render_item(self.canvas, self.items[idx], x, y_top, render_w, h, "floating")

    def _draw_normal(self, idx):
        y = self._item_y(idx)
        x = self.PAD
        w = self.ITEM_W
        h = self.ITEM_H
        bw = self._btn_zone_width()

        # Fond de l'item (géré par render_item ou laissé transparent)
        render_w = w - bw
        self._render_item(self.canvas, self.items[idx], x, y, render_w, h, "normal")

        # Boutons
        rects = self._btn_rects(idx)
        for btn in self._visible_btns:
            x1, y1, x2, y2 = rects[btn.key]
            hovered = self._hovered_btn == (idx, btn.key)
            col = self._theme["btn_hover"] if hovered else self._theme[btn.color_key]
            self._rounded_rect(x1, y1, x2, y2, 5, col)
            self.canvas.create_text(
                (x1 + x2) // 2,
                (y1 + y2) // 2,
                text=btn.symbol,
                fill=self._theme["btn_fg"],
                font=("Segoe UI", 11, "bold"),
            )

    def _draw_insert_line(self, pos):
        y = self._item_y(pos) - self.PAD // 2
        self.canvas.create_line(self.PAD, y, self.PAD + self.ITEM_W, y, fill=self._theme["insert"], width=3)

    def redraw(self, floating_idx=None, floating_y=None):
        """Redessine tout le canvas. Peut être appelé depuis l'extérieur."""
        self.canvas.delete("all")
        for i in range(len(self.items)):
            if i == floating_idx:
                self._draw_ghost(i)
            else:
                self._draw_normal(i)
        if floating_idx is not None and floating_y is not None:
            self._draw_floating(floating_idx, floating_y)
            if self._insert_pos is not None:
                self._draw_insert_line(self._insert_pos)

    # ─── Événements ──────────────────────────────────────────────────────────

    def _on_press(self, event):
        idx = self._idx_at(event.y)
        if idx is None:
            return
        btn = self._hit_btn(event.x, event.y, idx)
        if btn:
            self._dispatch_btn(idx, btn)
        else:
            self._drag_idx = idx
            self._drag_offset = event.y - self._item_y(idx)

    def _on_drag(self, event):
        if self._drag_idx is None:
            return
        fy = event.y - self._drag_offset
        raw = (fy + self.ITEM_H / 2 - self.PAD) / (self.ITEM_H + self.PAD)
        pos = max(0, min(len(self.items), round(raw)))
        self._insert_pos = None if pos in (self._drag_idx, self._drag_idx + 1) else pos
        self.redraw(floating_idx=self._drag_idx, floating_y=fy)

    def _on_release(self, event):
        if self._drag_idx is None:
            return
        fy = event.y - self._drag_offset
        raw = (fy + self.ITEM_H / 2 - self.PAD) / (self.ITEM_H + self.PAD)
        new_pos = max(0, min(len(self.items), round(raw)))
        item = self.items.pop(self._drag_idx)
        if new_pos > self._drag_idx:
            new_pos -= 1
        self.items.insert(new_pos, item)
        self._drag_idx = None
        self._insert_pos = None
        self.redraw()
        if self._on_reorder:
            self._on_reorder(self.items)

    def _on_hover(self, event):
        idx = self._idx_at(event.y)
        prev = self._hovered_btn
        self._hovered_btn = (idx, self._hit_btn(event.x, event.y, idx)) if idx is not None else None
        if self._hovered_btn != prev:
            self.redraw()

    def _on_leave(self, event):
        if self._hovered_btn:
            self._hovered_btn = None
            self.redraw()

    # ─── Dispatch boutons ─────────────────────────────────────────────────────

    def _dispatch_btn(self, idx, key):
        cb = self._cbs.get(key)
        if cb is None:
            return
        item = self.items[idx]

        if key == "move_up" and idx > 0:
            self.items.insert(idx - 1, self.items.pop(idx))
            cb(item, idx)
            self._notify_reorder()
            self.rebuild()

        elif key == "move_down" and idx < len(self.items) - 1:
            self.items.insert(idx + 1, self.items.pop(idx))
            cb(item, idx)
            self._notify_reorder()
            self.rebuild()

        elif key == "duplicate":
            clone = cb(item, idx)  # l'appelant fabrique le clone
            if clone is not None:
                self.items.insert(idx + 1, clone)
                self._notify_reorder()
                self.rebuild()

        elif key == "edit":
            cb(item, idx)  # l'appelant gère la popup/panneau

        elif key == "delete":
            confirmed = cb(item, idx)  # l'appelant gère la confirmation
            if confirmed:
                self.items.pop(idx)
                self._notify_reorder()
                self.rebuild()

    def _notify_reorder(self):
        if self._on_reorder:
            self._on_reorder(self.items)
