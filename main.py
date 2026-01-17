import json
import os
import random
import re
import tkinter as tk
from tkinter import ttk

LENGTHS = ("Short", "Medium", "Long")


def generate_options(num_genres):
    """Return a mapping of length -> genre for the next area."""
    if num_genres < len(LENGTHS):
        # Fallback to allowing repeats if pool is smaller than required slots.
        return {length: random.randrange(num_genres) for length in LENGTHS}
    picks = random.sample(range(num_genres), len(LENGTHS))
    return {length: picks[idx] for idx, length in enumerate(LENGTHS)}


def simulate_mallet_usage(check_func, num_genres):
    """Run rerolls until the provided check_func returns True."""
    mallets_spent = 0
    while True:
        options = generate_options(num_genres)
        if check_func(options):
            return mallets_spent
        mallets_spent += 3


def run_simulation(num_genres, iterations=40000):
    """Simulate mallet usage to reach five areas when matching genre-only or exact length/genre combos."""
    total_genre_mallets = 0
    total_combo_mallets = 0
    for _ in range(iterations):
        target_genre = random.randrange(num_genres)
        target_length = random.choice(LENGTHS)
        for _ in range(5):
            total_genre_mallets += simulate_mallet_usage(
                lambda opts, genre=target_genre: any(g == genre for g in opts.values()),
                num_genres,
            )
            total_combo_mallets += simulate_mallet_usage(
                lambda opts, genre=target_genre, length=target_length: opts[length] == genre,
                num_genres,
            )
    divisor = max(1, iterations)
    avg_genre = total_genre_mallets / divisor
    avg_combo = total_combo_mallets / divisor
    return {"avg_mallets_to_five_genre": avg_genre, "avg_mallets_to_five_combo": avg_combo}


class PageWeightMixin:
    def _copy_page_weights(self):
        values = [str(self._sanitize_string_var(var)) for var in self.genre_page_vars]
        try:
            self.clipboard_clear()
            self.clipboard_append(",".join(values))
            self._set_page_status("Page weights copied.", success=True)
        except tk.TclError:
            self._set_page_status("Clipboard unavailable.", success=False)

    def _paste_page_weights(self):
        try:
            clipboard_content = self.clipboard_get()
        except tk.TclError:
            self._set_page_status("Clipboard unavailable.", success=False)
            return

        numbers = [part for part in re.split(r"[^\d]+", clipboard_content) if part]
        if len(numbers) != len(self.GENRES):
            self._set_page_status("Clipboard format invalid.", success=False)
            return
        for idx, value in enumerate(numbers):
            self.genre_page_vars[idx].set(value)
        self._set_page_status("Page weights pasted.", success=True)
        if hasattr(self, "_update_page_percentages"):
            self._update_page_percentages()


class PostscriptBase(ttk.Frame):
    CHEESE_VALUES = (25, 50, 125)
    BASE_HUNTS = 10
    EXTENDED_BONUS = 3
    GENRES = ("Romance", "Adventure", "Comedy", "Tragedy", "Suspense")
    NOTORIETY_CAP = 200

    def __init__(self, parent):
        super().__init__(parent)

    def _sanitize_string_var(self, tk_var, limit=None):
        raw_value = tk_var.get().strip()
        if not raw_value:
            sanitized = 0
        elif raw_value.isdigit():
            sanitized = int(raw_value)
        else:
            filtered = "".join(ch for ch in raw_value if ch.isdigit())
            if filtered != raw_value:
                tk_var.set(filtered)
            sanitized = int(filtered) if filtered else 0
        if limit is not None and sanitized > limit:
            sanitized = limit
            tk_var.set(str(sanitized))
        return sanitized

    def _compute_target_hunts(self, extend_flag):
        return self.BASE_HUNTS + (self.EXTENDED_BONUS if extend_flag else 0)

    def _build_cheese_sequence(self, counts):
        ordered = sorted(
            ((self.CHEESE_VALUES[idx], counts[idx]) for idx in range(len(self.CHEESE_VALUES))),
            key=lambda item: item[0],
            reverse=True,
        )
        sequence = []
        for value, count in ordered:
            sequence.extend([value] * count)
        return sequence

    def _prepare_weight_cumulative(self, weights):
        cumulative = []
        running = 0.0
        for genre in self.GENRES:
            running += weights[genre]
            cumulative.append(running)
        cumulative[-1] = 1.0
        return cumulative

    def _simulate_sequence(self, base_notoriety, cheese_sequence, cumulative_weights):
        values = list(base_notoriety)
        for cheese_value in cheese_sequence:
            self._apply_hunt_step(values, cheese_value, cumulative_weights)
        ready = all(value >= 80 for value in values)
        return values, ready

    def _apply_hunt_step(self, values, cheese_value, cumulative_weights):
        idx = self._select_genre_index(cumulative_weights)
        values[idx] = min(self.NOTORIETY_CAP, values[idx] + cheese_value)
        for other in range(len(values)):
            if other != idx and values[other] > 1:
                values[other] -= 1

    def _select_genre_index(self, cumulative_weights):
        roll = random.random()
        for idx, threshold in enumerate(cumulative_weights):
            if roll <= threshold:
                return idx
        return len(cumulative_weights) - 1

    def _on_notoriety_change(self, index):
        value = self._sanitize_string_var(self.genre_notoriety_vars[index], limit=self.NOTORIETY_CAP)
        self.notoriety_progress_vars[index].set(value)

    def _copy_notoriety(self):
        values = [str(self._sanitize_string_var(var, limit=self.NOTORIETY_CAP)) for var in self.genre_notoriety_vars]
        try:
            self.clipboard_clear()
            self.clipboard_append(",".join(values))
            self._set_clipboard_status("Notoriety copied.", success=True)
        except tk.TclError:
            self._set_clipboard_status("Clipboard unavailable.", success=False)

    def _paste_notoriety(self):
        try:
            clipboard_content = self.clipboard_get()
        except tk.TclError:
            self._set_clipboard_status("Clipboard unavailable.", success=False)
            return

        numbers = [part for part in re.split(r"[^\d]+", clipboard_content) if part]
        if len(numbers) != len(self.GENRES):
            self._set_clipboard_status("Clipboard format invalid.", success=False)
            return

        for idx, value in enumerate(numbers):
            clamped = min(int(value), self.NOTORIETY_CAP)
            self.genre_notoriety_vars[idx].set(str(clamped))
        self._set_clipboard_status("Notoriety pasted.", success=True)

    def _set_clipboard_status(self, message, success=True):
        if hasattr(self, "clipboard_status_var"):
            self.clipboard_status_var.set(message)
            color = "green" if success else "red"
            if hasattr(self, "clipboard_status_label"):
                self.clipboard_status_label.configure(foreground=color)

    def _reset_notoriety(self):
        for var in self.genre_notoriety_vars:
            var.set("0")
        self._set_clipboard_status("Notoriety reset.", success=True)


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, _event=None):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self.text,
            justify="left",
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            font=("tahoma", "8", "normal"),
            wraplength=240,
        )
        label.pack(ipadx=4, ipady=2)

    def hide_tip(self, _event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


class CheeseAllocator(PageWeightMixin, PostscriptBase):
    THRESHOLD_BREAKPOINTS = (80, 90, 93)

    def __init__(self, parent):
        super().__init__(parent)
        self.extend_var = tk.BooleanVar(value=False)
        self.hunt_text_var = tk.StringVar()
        self.error_var = tk.StringVar()
        self.cheese_vars = []
        self.genre_page_vars = []
        self.genre_page_percent_vars = []
        self.genre_notoriety_vars = []
        self.notoriety_progress_vars = []
        self.clipboard_status_var = tk.StringVar()
        self.page_status_var = tk.StringVar()
        self.single_result_var = tk.StringVar(value="Single run: not started yet.")
        self.single_ready_var = tk.StringVar(value="[Not ready]")
        self.multi_result_var = tk.StringVar(value="20,000-run average: not started yet.")
        self.multi_ready_var = tk.StringVar(value="All Genre >80 Percentage: --")
        self.extension_stats_var = tk.StringVar(value="")
        self.threshold_stats_vars = {
            threshold: tk.StringVar(value=f"[%of#ofGenre>{threshold}] --")
            for threshold in self.THRESHOLD_BREAKPOINTS
        }
        self.threshold_copy_status_var = tk.StringVar(value="")
        self._build_ui()
        self._set_default_counts()
        self._update_page_percentages()

    def _build_ui(self):
        container = ttk.Frame(self)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=3)
        container.columnconfigure(1, weight=2)

        left = ttk.Frame(container)
        left.grid(row=0, column=0, sticky="nsew")
        left.columnconfigure(3, weight=1)

        right = ttk.Frame(container)
        right.grid(row=0, column=1, sticky="n", padx=(15, 0))

        row = 0
        ttk.Label(
            left,
            text="Plan hunts by balancing cheese usage, chapter weights, and genre notoriety goals.",
            justify="left",
            wraplength=400,
        ).grid(row=row, column=0, columnspan=5, sticky="w", pady=(10, 5))
        row += 1

        ttk.Checkbutton(
            left,
            text="Extend hunts (+3 attempts)",
            variable=self.extend_var,
            command=self._on_extend_toggle,
        ).grid(row=row, column=0, sticky="w", pady=(0, 5))

        row += 1

        ttk.Separator(left, orient="horizontal").grid(row=row, column=0, columnspan=5, sticky="ew", pady=10)
        row += 1

        ttk.Label(left, text="Cheese Type").grid(row=row, column=0, sticky="w")
        ttk.Label(left, text="Notoriety").grid(row=row, column=1, sticky="w")
        ttk.Label(left, text="Quantity").grid(row=row, column=2, columnspan=3)
        row += 1

        for idx, value in enumerate(self.CHEESE_VALUES):
            ttk.Label(left, text=f"{value} Notoriety Cheese").grid(row=row + idx, column=0, sticky="w", pady=4)
            ttk.Label(left, text=str(value)).grid(row=row + idx, column=1, sticky="w")

            minus_btn = ttk.Button(
                left,
                text="-",
                width=3,
                command=lambda i=idx: self._adjust_count(i, -1),
            )
            minus_btn.grid(row=row + idx, column=2, padx=(10, 2))

            var = tk.StringVar()
            var.trace_add("write", lambda *args, i=idx: self._on_entry_change(i))
            entry = ttk.Entry(left, textvariable=var, width=7, justify="center")
            entry.grid(row=row + idx, column=3, padx=2)
            self.cheese_vars.append(var)

            plus_btn = ttk.Button(
                left,
                text="+",
                width=3,
                command=lambda i=idx: self._adjust_count(i, 1),
            )
            plus_btn.grid(row=row + idx, column=4, padx=(2, 10))

        row += len(self.CHEESE_VALUES)

        ttk.Label(left, textvariable=self.error_var, foreground="red").grid(
            row=row, column=0, columnspan=5, sticky="w", pady=(10, 0)
        )
        row += 1

        ttk.Separator(left, orient="horizontal").grid(row=row, column=0, columnspan=5, sticky="ew", pady=10)
        row += 1

        page_header = ttk.Frame(left)
        page_header.grid(row=row, column=0, columnspan=5, sticky="ew")
        ttk.Label(page_header, text="Current chapter pages per Genre (used as selection weights):").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(page_header, text="Copy", command=self._copy_page_weights).grid(row=0, column=1, padx=(10, 0))
        ttk.Button(page_header, text="Paste", command=self._paste_page_weights).grid(row=0, column=2, padx=(5, 0))
        ttk.Button(page_header, text="Reset", command=self._reset_page_weights).grid(row=0, column=3, padx=(5, 0))
        self.page_status_label = tk.Label(page_header, textvariable=self.page_status_var, fg="green")
        self.page_status_label.grid(row=1, column=0, columnspan=4, sticky="w")
        row += 1

        page_frame = ttk.Frame(left)
        page_frame.grid(row=row, column=0, columnspan=5, sticky="nsew", pady=(5, 0))
        page_frame.columnconfigure(1, weight=1)
        for idx, genre in enumerate(self.GENRES):
            percent_var = tk.StringVar(value=f"{genre} (--)")
            ttk.Label(page_frame, textvariable=percent_var).grid(row=idx, column=0, sticky="w", pady=2)
            var = tk.StringVar(value="0")
            var.trace_add("write", lambda *args, i=idx: self._on_page_entry_change(i))
            entry = ttk.Entry(page_frame, textvariable=var, width=12)
            entry.grid(row=idx, column=1, sticky="w", pady=2)
            self.genre_page_vars.append(var)
            self.genre_page_percent_vars.append(percent_var)
        row += 1

        ttk.Separator(left, orient="horizontal").grid(row=row, column=0, columnspan=5, sticky="ew", pady=10)
        row += 1

        ttk.Button(left, text="Run Hunts Simulation", command=self._run_hunt_simulation).grid(
            row=row, column=0, columnspan=2, sticky="w"
        )
        row += 1

        single_frame = ttk.Frame(left)
        single_frame.grid(row=row, column=0, columnspan=5, sticky="w", pady=(10, 0))
        ttk.Label(single_frame, textvariable=self.single_result_var, wraplength=420, justify="left").grid(
            row=0, column=0, sticky="w"
        )
        self.single_ready_label = tk.Label(single_frame, textvariable=self.single_ready_var, fg="red")
        self.single_ready_label.grid(row=0, column=1, padx=(5, 0))
        row += 1

        multi_frame = ttk.Frame(left)
        multi_frame.grid(row=row, column=0, columnspan=5, sticky="w", pady=(10, 0))
        multi_frame.grid_columnconfigure(0, weight=1)
        ttk.Label(multi_frame, textvariable=self.multi_result_var, wraplength=420, justify="left").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(multi_frame, text="Copy Summary", command=self._copy_threshold_summary).grid(
            row=0, column=1, sticky="e", padx=(10, 0)
        )
        ttk.Label(multi_frame, textvariable=self.multi_ready_var).grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Label(multi_frame, textvariable=self.extension_stats_var).grid(row=2, column=0, sticky="w", pady=(4, 0))
        for offset, threshold in enumerate(self.THRESHOLD_BREAKPOINTS, start=3):
            ttk.Label(multi_frame, textvariable=self.threshold_stats_vars[threshold]).grid(
                row=offset, column=0, sticky="w", pady=(4, 0)
            )
        status_row = len(self.THRESHOLD_BREAKPOINTS) + 3
        self.threshold_copy_status_label = tk.Label(
            multi_frame, textvariable=self.threshold_copy_status_var, fg="green"
        )
        self.threshold_copy_status_label.grid(row=status_row, column=0, columnspan=2, sticky="w", pady=(4, 0))

        # Right side: Notoriety tracker
        ttk.Label(right, text="Genre Notoriety (max 200)", font=("Arial", 11, "bold")).grid(
            row=0, column=0, sticky="w", pady=(10, 5)
        )
        for idx, genre in enumerate(self.GENRES):
            ttk.Label(right, text=genre).grid(row=1 + idx * 3, column=0, sticky="w")
            progress_var = tk.IntVar(value=0)
            self.notoriety_progress_vars.append(progress_var)

            progress = ttk.Progressbar(
                right, orient="horizontal", length=200, maximum=self.NOTORIETY_CAP, variable=progress_var
            )
            progress.grid(row=2 + idx * 3, column=0, sticky="w")

            var = tk.StringVar(value="0")
            var.trace_add("write", lambda *args, i=idx: self._on_notoriety_change(i))
            entry = ttk.Entry(right, textvariable=var, width=10)
            entry.grid(row=3 + idx * 3, column=0, sticky="w", pady=(0, 5))
            self.genre_notoriety_vars.append(var)

        buttons = ttk.Frame(right)
        buttons.grid(row=1 + len(self.GENRES) * 3, column=0, pady=(10, 0), sticky="w")
        copy_paste_row = ttk.Frame(buttons)
        copy_paste_row.pack(anchor="w")
        ttk.Button(copy_paste_row, text="Copy", command=self._copy_notoriety).pack(side="left", padx=(0, 5))
        ttk.Button(copy_paste_row, text="Paste", command=self._paste_notoriety).pack(side="left")
        ttk.Button(buttons, text="Reset", command=self._reset_notoriety).pack(anchor="w", pady=(5, 0))

        self.clipboard_status_label = ttk.Label(right, textvariable=self.clipboard_status_var, foreground="green")
        self.clipboard_status_label.grid(
            row=2 + len(self.GENRES) * 3, column=0, sticky="w", pady=(5, 0)
        )
        self._update_page_percentages()
        self._update_page_percentages()

    def _on_entry_change(self, index):
        self._sanitize_value(index)
        self._update_totals()
        self._update_page_percentages()

    def _sanitize_value(self, index):
        return self._sanitize_string_var(self.cheese_vars[index])

    def _adjust_count(self, index, delta):
        current_counts = self._get_counts()
        new_value = max(0, current_counts[index] + delta)
        self.cheese_vars[index].set(str(new_value))
        self._update_totals()

    def _get_counts(self):
        return [self._sanitize_value(i) for i in range(len(self.cheese_vars))]

    def _target_hunts(self):
        return self._compute_target_hunts(self.extend_var.get())

    def _update_totals(self):
        target = self._target_hunts()
        total = sum(self._get_counts())
        self.hunt_text_var.set(f"Hunts available: {target}")
        if total == target:
            self.error_var.set("")
        else:
            self.error_var.set(f"Sum of the # of cheese is wrong! should equal to {target}. Current: {total}")

    def _set_default_counts(self):
        for idx, var in enumerate(self.cheese_vars):
            default_value = self._target_hunts() if self.CHEESE_VALUES[idx] == 50 else 0
            var.set(str(default_value))
        self._update_totals()

    def _on_extend_toggle(self):
        self._update_totals()

    def _on_page_entry_change(self, index):
        self._sanitize_string_var(self.genre_page_vars[index])
        self._update_page_percentages()

    def _reset_page_weights(self):
        for var in self.genre_page_vars:
            var.set("0")
        self._set_page_status("Cleared page weights.", success=True)
        self._update_page_percentages()

    def _update_page_percentages(self):
        counts = [self._sanitize_string_var(var) for var in self.genre_page_vars]
        total = sum(counts)
        for idx, percent_var in enumerate(self.genre_page_percent_vars):
            genre_label = self.GENRES[idx]
            if total > 0:
                pct = counts[idx] / total * 100
                percent_var.set(f"{genre_label} ({pct:.1f}%)")
            else:
                percent_var.set(f"{genre_label} (--)")

    def _set_page_status(self, message, success=True):
        color = "green" if success else "red"
        self.page_status_var.set(message)
        if hasattr(self, "page_status_label"):
            self.page_status_label.configure(fg=color)

    def _update_page_percentages(self):
        counts = [self._sanitize_string_var(var) for var in self.genre_page_vars]
        total = sum(counts)
        for idx, percent_var in enumerate(self.genre_page_percent_vars):
            genre_label = self.GENRES[idx]
            if total > 0:
                pct = counts[idx] / total * 100
                percent_var.set(f"{genre_label} ({pct:.1f}%)")
            else:
                percent_var.set(f"{genre_label} (--)")

    def _update_page_percentages(self):
        counts = [self._sanitize_string_var(var) for var in self.genre_page_vars]
        total = sum(counts)
        for idx, percent_var in enumerate(self.genre_page_percent_vars):
            genre_label = self.GENRES[idx]
            if total > 0:
                pct = counts[idx] / total * 100
                percent_var.set(f"{genre_label} ({pct:.1f}%)")
            else:
                percent_var.set(f"{genre_label} (--)")

    def _set_page_status(self, message, success=True):
        color = "green" if success else "red"
        self.page_status_var.set(message)
        if hasattr(self, "page_status_label"):
            self.page_status_label.configure(fg=color)

    def get_genre_weight_distribution(self):
        """Return normalized weights derived from user-provided page counts."""
        raw_counts = {
            genre: self._sanitize_string_var(self.genre_page_vars[idx])
            for idx, genre in enumerate(self.GENRES)
        }
        total = sum(raw_counts.values())
        if total == 0:
            fallback = 1 / len(self.GENRES)
            return {genre: fallback for genre in self.GENRES}
        return {genre: value / total for genre, value in raw_counts.items()}

    def _copy_page_weights(self):
        values = [str(self._sanitize_string_var(var)) for var in self.genre_page_vars]
        try:
            self.clipboard_clear()
            self.clipboard_append(",".join(values))
            self._set_page_status("Page weights copied.", success=True)
        except tk.TclError:
            self._set_page_status("Clipboard unavailable.", success=False)

    def _paste_page_weights(self):
        try:
            clipboard_content = self.clipboard_get()
        except tk.TclError:
            self._set_page_status("Clipboard unavailable.", success=False)
            return

        numbers = [part for part in re.split(r"[^\d]+", clipboard_content) if part]
        if len(numbers) != len(self.GENRES):
            self._set_page_status("Clipboard format invalid.", success=False)
            return
        for idx, value in enumerate(numbers):
            self.genre_page_vars[idx].set(value)
        self._set_page_status("Page weights pasted.", success=True)
        self._update_page_percentages()

    def _update_page_percentages(self):
        counts = [self._sanitize_string_var(var) for var in self.genre_page_vars]
        total = sum(counts)
        for idx, percent_var in enumerate(self.genre_page_percent_vars):
            genre_label = self.GENRES[idx]
            if total > 0:
                pct = counts[idx] / total * 100
                percent_var.set(f"{genre_label} ({pct:.1f}%)")
            else:
                percent_var.set(f"{genre_label} (--)")

    def _set_page_status(self, message, success=True):
        color = "green" if success else "red"
        self.page_status_var.set(message)
        if hasattr(self, "page_status_label"):
            self.page_status_label.configure(fg=color)

    def _copy_page_weights(self):
        values = [str(self._sanitize_string_var(var)) for var in self.genre_page_vars]
        try:
            self.clipboard_clear()
            self.clipboard_append(",".join(values))
            self._set_page_status("Page weights copied.", success=True)
        except tk.TclError:
            self._set_page_status("Clipboard unavailable.", success=False)

    def _paste_page_weights(self):
        try:
            clipboard_content = self.clipboard_get()
        except tk.TclError:
            self._set_page_status("Clipboard unavailable.", success=False)
            return

        numbers = [part for part in re.split(r"[^\d]+", clipboard_content) if part]
        if len(numbers) != len(self.GENRES):
            self._set_page_status("Clipboard format invalid.", success=False)
            return
        for idx, value in enumerate(numbers):
            self.genre_page_vars[idx].set(value)
        self._set_page_status("Page weights pasted.", success=True)
        self._update_page_percentages()

    def _update_page_percentages(self):
        counts = [self._sanitize_string_var(var) for var in self.genre_page_vars]
        total = sum(counts)
        for idx, percent_var in enumerate(self.genre_page_percent_vars):
            genre_label = self.GENRES[idx]
            if total > 0:
                pct = counts[idx] / total * 100
                percent_var.set(f"{genre_label} ({pct:.1f}%)")
            else:
                percent_var.set(f"{genre_label} (--)")

    def export_state(self):
        return {
            "extend": self.extend_var.get(),
            "cheese": self._get_counts(),
            "pages": [self._sanitize_string_var(var) for var in self.genre_page_vars],
            "notoriety": [self._sanitize_string_var(var, limit=self.NOTORIETY_CAP) for var in self.genre_notoriety_vars],
        }

    def import_state(self, data):
        pass

    def _on_notoriety_change(self, index):
        value = self._sanitize_string_var(self.genre_notoriety_vars[index], limit=self.NOTORIETY_CAP)
        self.notoriety_progress_vars[index].set(value)

    def _copy_notoriety(self):
        values = [str(self._sanitize_string_var(var, limit=self.NOTORIETY_CAP)) for var in self.genre_notoriety_vars]
        try:
            self.clipboard_clear()
            self.clipboard_append(",".join(values))
            self._set_clipboard_status("Notoriety copied.", success=True)
        except tk.TclError:
            self._set_clipboard_status("Clipboard unavailable.", success=False)

    def _paste_notoriety(self):
        try:
            clipboard_content = self.clipboard_get()
        except tk.TclError:
            self._set_clipboard_status("Clipboard unavailable.", success=False)
            return

        numbers = [part for part in re.split(r"[^\d]+", clipboard_content) if part]
        if len(numbers) != len(self.GENRES):
            self._set_clipboard_status("Clipboard format invalid.", success=False)
            return

        for idx, value in enumerate(numbers):
            clamped = min(int(value), self.NOTORIETY_CAP)
            self.genre_notoriety_vars[idx].set(str(clamped))
        self._set_clipboard_status("Notoriety pasted.", success=True)

    def _set_clipboard_status(self, message, success=True):
        self.clipboard_status_var.set(message)
        color = "green" if success else "red"
        self.clipboard_status_label.configure(foreground=color)

    def _reset_notoriety(self):
        for var in self.genre_notoriety_vars:
            var.set("0")
        self._set_clipboard_status("Notoriety reset.", success=True)

    def _run_hunt_simulation(self):
        counts = self._get_counts()
        target = self._target_hunts()
        if sum(counts) != target:
            warning = f"Single run: ensure cheese quantities sum to {target} first."
            self.single_result_var.set(warning)
            self._set_ready_indicator(ready=False, label_text="[Not ready]")
            self.multi_result_var.set("100,000-run average: waiting for a valid setup...")
            self.multi_ready_var.set("All Genre >80 Percentage: --")
            return

        cheese_sequence = self._build_cheese_sequence(counts)
        base_notoriety = [
            self._sanitize_string_var(var, limit=self.NOTORIETY_CAP) for var in self.genre_notoriety_vars
        ]
        cumulative_weights = self._prepare_weight_cumulative()

        final_values, ready = self._simulate_sequence(base_notoriety, cheese_sequence, cumulative_weights)
        pairs = "; ".join(f"{genre}:{value}" for genre, value in zip(self.GENRES, final_values))
        self.single_result_var.set(f"Single run: final genre Notoriety values: {pairs}")
        self._set_ready_indicator(ready=ready)

        runs = 100000
        totals = [0] * len(self.GENRES)
        ready_runs = 0
        threshold_counts = {
            threshold: [0] * (len(self.GENRES) + 1) for threshold in self.THRESHOLD_BREAKPOINTS
        }
        for _ in range(runs):
            values, sim_ready = self._simulate_sequence(base_notoriety, cheese_sequence, cumulative_weights)
            ready_runs += 1 if sim_ready else 0
            for idx, val in enumerate(values):
                totals[idx] += val
            for threshold in self.THRESHOLD_BREAKPOINTS:
                above_count = sum(1 for val in values if val > threshold)
                threshold_counts[threshold][above_count] += 1

        averages = [val / runs for val in totals]
        avg_pairs = "; ".join(f"{genre}:{avg:.2f}" for genre, avg in zip(self.GENRES, averages))
        ready_ratio = ready_runs / runs * 100
        self.multi_result_var.set(f"100,000-run average: {avg_pairs}")
        self.multi_ready_var.set(f"All Genre >80 Percentage: {ready_ratio:.2f}% ({ready_runs}/{runs})")
        for threshold in self.THRESHOLD_BREAKPOINTS:
            parts = []
            counts = threshold_counts[threshold]
            for genre_count in range(1, len(self.GENRES) + 1):
                percent = counts[genre_count] / runs * 100
                parts.append(f"{genre_count}: {percent:.2f}%")
            summary = "; ".join(parts)
            self.threshold_stats_vars[threshold].set(f"[%of#ofGenre>{threshold}] {summary}")
        self.threshold_copy_status_var.set("")

    def _prepare_weight_cumulative(self):
        weights = self.get_genre_weight_distribution()
        return super()._prepare_weight_cumulative(weights)

    def _set_ready_indicator(self, ready, label_text=None):
        if label_text is None:
            label_text = "[All ready!]" if ready else "[Not ready]"
        self.single_ready_var.set(label_text)
        color = "green" if ready else "red"
        self.single_ready_label.configure(fg=color)

    def _copy_threshold_summary(self):
        segments = [
            self.multi_result_var.get(),
            self.multi_ready_var.get(),
            self.extension_stats_var.get(),
        ]
        segments.extend(self.threshold_stats_vars[threshold].get() for threshold in self.THRESHOLD_BREAKPOINTS)
        payload = "\n".join(segment for segment in segments if segment.strip())
        try:
            self.clipboard_clear()
            self.clipboard_append(payload)
        except tk.TclError:
            self._set_threshold_copy_status("Clipboard unavailable.", success=False)
            return
        self._set_threshold_copy_status("Summary copied.", success=True)

    def _set_threshold_copy_status(self, message, success=True):
        self.threshold_copy_status_var.set(message)
        color = "green" if success else "red"
        self.threshold_copy_status_label.configure(foreground=color)


class PostscriptOptimizer(PageWeightMixin, PostscriptBase):
    CANDIDATE_COUNT = 20

    def __init__(self, parent):
        super().__init__(parent)
        self.extend_var = tk.BooleanVar(value=False)
        self.error_var = tk.StringVar()
        self.cheese_vars = []
        self.genre_page_vars = []
        self.genre_page_percent_vars = []
        self.genre_notoriety_vars = []
        self.notoriety_progress_vars = []
        self.clipboard_status_var = tk.StringVar()
        self.page_status_var = tk.StringVar()
        self.range_var = tk.StringVar(value="20")
        self.iterations_var = tk.StringVar(value="10")
        self.simulations_var = tk.StringVar(value="20000")
        self.candidates_var = tk.StringVar(value="20")
        self.optimization_result_var = tk.StringVar(
            value="Run optimization to find the highest All Genre ≥80 probability."
        )
        self.direction_bias = [0.0 for _ in self.GENRES]
        self._build_ui()
        self._set_default_counts()

    def _build_ui(self):
        container = ttk.Frame(self)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=3)
        container.columnconfigure(1, weight=2)

        left = ttk.Frame(container)
        left.grid(row=0, column=0, sticky="nsew")
        left.columnconfigure(3, weight=1)

        right = ttk.Frame(container)
        right.grid(row=0, column=1, sticky="n", padx=(15, 0))

        row = 0
        ttk.Label(
            left,
            text="Iteratively dial chapter weights to maximize the All Genre ≥80 readiness probability.",
            justify="left",
            wraplength=400,
        ).grid(row=row, column=0, columnspan=5, sticky="w", pady=(10, 5))
        row += 1

        ttk.Checkbutton(
            left,
            text="Extend hunts (+3 attempts)",
            variable=self.extend_var,
            command=self._on_extend_toggle,
        ).grid(row=row, column=0, sticky="w", pady=(0, 5))

        row += 1

        ttk.Separator(left, orient="horizontal").grid(row=row, column=0, columnspan=5, sticky="ew", pady=10)
        row += 1

        ttk.Label(left, text="Cheese Type").grid(row=row, column=0, sticky="w")
        ttk.Label(left, text="Notoriety").grid(row=row, column=1, sticky="w")
        ttk.Label(left, text="Quantity").grid(row=row, column=2, columnspan=3)
        row += 1

        for idx, value in enumerate(self.CHEESE_VALUES):
            ttk.Label(left, text=f"{value} Notoriety Cheese").grid(row=row + idx, column=0, sticky="w", pady=4)
            ttk.Label(left, text=str(value)).grid(row=row + idx, column=1, sticky="w")

            ttk.Button(
                left,
                text="-",
                width=3,
                command=lambda i=idx: self._adjust_count(i, -1),
            ).grid(row=row + idx, column=2, padx=(10, 2))

            var = tk.StringVar()
            var.trace_add("write", lambda *args, i=idx: self._on_entry_change(i))
            ttk.Entry(left, textvariable=var, width=7, justify="center").grid(row=row + idx, column=3, padx=2)
            self.cheese_vars.append(var)

            ttk.Button(
                left,
                text="+",
                width=3,
                command=lambda i=idx: self._adjust_count(i, 1),
            ).grid(row=row + idx, column=4, padx=(2, 10))

        row += len(self.CHEESE_VALUES)

        ttk.Label(left, textvariable=self.error_var, foreground="red").grid(
            row=row, column=0, columnspan=5, sticky="w", pady=(10, 0)
        )
        row += 1

        ttk.Separator(left, orient="horizontal").grid(row=row, column=0, columnspan=5, sticky="ew", pady=10)
        row += 1

        page_header = ttk.Frame(left)
        page_header.grid(row=row, column=0, columnspan=5, sticky="ew")
        ttk.Label(page_header, text="Current chapter pages per Genre (used as optimization seed):").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(page_header, text="Copy", command=self._copy_page_weights).grid(row=0, column=1, padx=(10, 0))
        ttk.Button(page_header, text="Paste", command=self._paste_page_weights).grid(row=0, column=2, padx=(5, 0))
        ttk.Button(page_header, text="Reset", command=self._reset_page_weights).grid(row=0, column=3, padx=(5, 0))
        self.page_status_label = tk.Label(page_header, textvariable=self.page_status_var, fg="green")
        self.page_status_label.grid(row=1, column=0, columnspan=4, sticky="w")
        row += 1

        page_frame = ttk.Frame(left)
        page_frame.grid(row=row, column=0, columnspan=5, sticky="nsew", pady=(5, 0))
        page_frame.columnconfigure(1, weight=1)
        for idx, genre in enumerate(self.GENRES):
            percent_var = tk.StringVar(value=f"{genre} (--)")
            ttk.Label(page_frame, textvariable=percent_var).grid(row=idx, column=0, sticky="w", pady=2)
            var = tk.StringVar(value="500")
            var.trace_add("write", lambda *args, i=idx: self._on_page_entry_change(i))
            ttk.Entry(page_frame, textvariable=var, width=12).grid(row=idx, column=1, sticky="w", pady=2)
            self.genre_page_vars.append(var)
            self.genre_page_percent_vars.append(percent_var)
        row += 1

        ttk.Separator(left, orient="horizontal").grid(row=row, column=0, columnspan=5, sticky="ew", pady=10)
        row += 1

        param_frame = ttk.LabelFrame(left, text="Optimization Parameters")
        param_frame.grid(row=row, column=0, columnspan=5, sticky="ew")
        ttk.Label(param_frame, text="Dial range (±%):").grid(row=0, column=0, sticky="w", padx=(5, 0), pady=4)
        ttk.Entry(param_frame, textvariable=self.range_var, width=8).grid(row=0, column=1, sticky="w", pady=4)

        ttk.Label(param_frame, text="Dial iterations:").grid(row=1, column=0, sticky="w", padx=(5, 0), pady=4)
        ttk.Entry(param_frame, textvariable=self.iterations_var, width=8).grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(param_frame, text="Candidates per iteration:").grid(row=2, column=0, sticky="w", padx=(5, 0), pady=4)
        ttk.Entry(param_frame, textvariable=self.candidates_var, width=8).grid(row=2, column=1, sticky="w", pady=4)

        ttk.Label(param_frame, text="Simulations per distribution:").grid(row=3, column=0, sticky="w", padx=(5, 0), pady=4)
        ttk.Entry(param_frame, textvariable=self.simulations_var, width=8).grid(row=3, column=1, sticky="w", pady=4)
        row += 1

        ttk.Button(left, text="Run Optimization", command=self._run_optimization).grid(row=row, column=0, sticky="w", pady=(10, 0))
        row += 1

        ttk.Label(left, textvariable=self.optimization_result_var, wraplength=420, justify="left").grid(
            row=row, column=0, columnspan=5, sticky="w", pady=(10, 0)
        )

        ttk.Label(right, text="Starting Genre Notoriety (max 200)", font=("Arial", 11, "bold")).grid(
            row=0, column=0, sticky="w", pady=(10, 5)
        )
        for idx, genre in enumerate(self.GENRES):
            ttk.Label(right, text=genre).grid(row=1 + idx * 3, column=0, sticky="w")
            progress_var = tk.IntVar(value=0)
            self.notoriety_progress_vars.append(progress_var)

            progress = ttk.Progressbar(
                right, orient="horizontal", length=200, maximum=self.NOTORIETY_CAP, variable=progress_var
            )
            progress.grid(row=2 + idx * 3, column=0, sticky="w")

            var = tk.StringVar(value="0")
            var.trace_add("write", lambda *args, i=idx: self._on_notoriety_change(i))
            ttk.Entry(right, textvariable=var, width=10).grid(row=3 + idx * 3, column=0, sticky="w", pady=(0, 5))
            self.genre_notoriety_vars.append(var)

        buttons = ttk.Frame(right)
        buttons.grid(row=1 + len(self.GENRES) * 3, column=0, pady=(10, 0), sticky="w")
        copy_paste_row = ttk.Frame(buttons)
        copy_paste_row.pack(anchor="w")
        ttk.Button(copy_paste_row, text="Copy", command=self._copy_notoriety).pack(side="left", padx=(0, 5))
        ttk.Button(copy_paste_row, text="Paste", command=self._paste_notoriety).pack(side="left")
        ttk.Button(buttons, text="Reset", command=self._reset_notoriety).pack(anchor="w", pady=(5, 0))

        self.clipboard_status_label = ttk.Label(right, textvariable=self.clipboard_status_var, foreground="green")
        self.clipboard_status_label.grid(
            row=2 + len(self.GENRES) * 3, column=0, sticky="w", pady=(5, 0)
        )
        self._update_page_percentages()

    def _on_entry_change(self, index):
        self._sanitize_value(index)
        self._update_totals()
        self._update_page_percentages()

    def _sanitize_value(self, index):
        return self._sanitize_string_var(self.cheese_vars[index])

    def _adjust_count(self, index, delta):
        current_counts = self._get_counts()
        new_value = max(0, current_counts[index] + delta)
        self.cheese_vars[index].set(str(new_value))
        self._update_totals()

    def _get_counts(self):
        return [self._sanitize_value(i) for i in range(len(self.cheese_vars))]

    def _target_hunts(self):
        return self._compute_target_hunts(self.extend_var.get())

    def _update_totals(self):
        target = self._target_hunts()
        total = sum(self._get_counts())
        if total == target:
            self.error_var.set("")
        else:
            self.error_var.set(f"Sum of the # of cheese is wrong! should equal to {target}. Current: {total}")

    def _set_default_counts(self):
        for idx, var in enumerate(self.cheese_vars):
            default_value = self._target_hunts() if self.CHEESE_VALUES[idx] == 50 else 0
            var.set(str(default_value))
        self._update_totals()

    def _on_extend_toggle(self):
        self._update_totals()

    def _on_page_entry_change(self, index):
        self._sanitize_string_var(self.genre_page_vars[index])
        self._update_page_percentages()

    def _reset_page_weights(self):
        for var in self.genre_page_vars:
            var.set("0")
        self._set_page_status("Cleared page weights.", success=True)
        self._update_page_percentages()

    def _weights_from_counts(self, counts):
        total = sum(counts)
        if total <= 0:
            equal = 1 / len(self.GENRES)
            return {genre: equal for genre in self.GENRES}
        return {genre: counts[idx] / total for idx, genre in enumerate(self.GENRES)}

    def _update_page_percentages(self):
        counts = [self._sanitize_string_var(var) for var in self.genre_page_vars]
        total = sum(counts)
        for idx, percent_var in enumerate(self.genre_page_percent_vars):
            genre_label = self.GENRES[idx]
            if total > 0:
                pct = counts[idx] / total * 100
                percent_var.set(f"{genre_label} ({pct:.1f}%)")
            else:
                percent_var.set(f"{genre_label} (--)")

    def _set_page_status(self, message, success=True):
        color = "green" if success else "red"
        self.page_status_var.set(message)
        if hasattr(self, "page_status_label"):
            self.page_status_label.configure(fg=color)

    def _run_optimization(self):
        counts = self._get_counts()
        target = self._target_hunts()
        if sum(counts) != target:
            self.optimization_result_var.set(f"Ensure cheese quantities sum to {target} before optimizing.")
            return

        base_notoriety = [
            self._sanitize_string_var(var, limit=self.NOTORIETY_CAP) for var in self.genre_notoriety_vars
        ]
        cheese_sequence = self._build_cheese_sequence(counts)

        base_counts = [self._sanitize_string_var(var) for var in self.genre_page_vars]
        if sum(base_counts) == 0:
            base_counts = [1 for _ in self.GENRES]

        dial_range = max(0, self._sanitize_string_var(self.range_var))
        iterations = max(1, self._sanitize_string_var(self.iterations_var))
        sims_per_distribution = max(1, self._sanitize_string_var(self.simulations_var))
        candidate_count = max(1, self._sanitize_string_var(self.candidates_var))

        best_counts = list(base_counts)
        best_prob = self._simulate_probability(best_counts, base_notoriety, cheese_sequence, sims_per_distribution)
        direction_bias = [0.0 for _ in self.GENRES]

        for iteration in range(iterations):
            adaptive_factor = 0.6 + 0.4 * (1 - iteration / max(1, iterations - 1))
            current_range = max(1, dial_range * adaptive_factor)
            current_candidates = max(3, int(candidate_count * adaptive_factor))
            candidates = self._systematic_candidates(best_counts, current_range)

            while len(candidates) < current_candidates:
                candidate = self._generate_candidate_counts(best_counts, current_range, direction_bias)
                if sum(candidate) == 0:
                    continue
                candidates.append(candidate)

            results = []
            for candidate in candidates:
                prob = self._simulate_probability(candidate, base_notoriety, cheese_sequence, sims_per_distribution)
                results.append((prob, candidate))

            # Always consider current best
            results.append((best_prob, list(best_counts)))
            results.sort(key=lambda item: item[0], reverse=True)
            top_results = results[:3]

            blended_counts = self._blend_top_candidates(top_results)
            blended_prob = self._simulate_probability(
                blended_counts, base_notoriety, cheese_sequence, sims_per_distribution
            )

            prev_counts = list(best_counts)
            if blended_prob >= top_results[0][0]:
                best_counts = blended_counts
                best_prob = blended_prob
            else:
                best_prob, best_counts = top_results[0]
            direction_bias = self._update_direction_bias(direction_bias, prev_counts, best_counts)

        for var, value in zip(self.genre_page_vars, best_counts):
            var.set(str(int(round(value))))

        distribution_text = "; ".join(f"{genre}:{int(round(value))}" for genre, value in zip(self.GENRES, best_counts))
        self.optimization_result_var.set(
            f"Best distribution after {iterations} iterations: {distribution_text} | "
            f"Ready probability ≈ {best_prob * 100:.2f}%"
        )
        self.direction_bias = direction_bias
        self._update_page_percentages()

    def _generate_candidate_counts(self, base_counts, dial_range, direction_bias):
        varied = list(base_counts)
        positive_indices = [idx for idx, value in enumerate(base_counts) if value > 0]
        if not positive_indices:
            positive_indices = list(range(len(base_counts)))
        subset_size = max(1, (len(positive_indices) + 1) // 2)
        if len(positive_indices) > subset_size:
            selected = random.sample(positive_indices, subset_size)
        else:
            selected = positive_indices
        for idx in selected:
            value = base_counts[idx]
            bias = direction_bias[idx] if idx < len(direction_bias) else 0.0
            delta = random.uniform(-dial_range / 100, dial_range / 100) + bias * 0.1
            varied[idx] = max(0.0, value * (1 + delta))
        return varied

    def _systematic_candidates(self, base_counts, dial_range):
        candidates = []
        if not base_counts:
            return candidates
        for idx, value in enumerate(base_counts):
            if value <= 0:
                continue
            increase = list(base_counts)
            increase[idx] = max(0.0, value * (1 + dial_range / 100))
            candidates.append(increase)
            decrease = list(base_counts)
            decrease[idx] = max(0.0, value * (1 - dial_range / 100))
            candidates.append(decrease)
        if not candidates:
            candidates = [list(base_counts)]
        return candidates

    def _blend_top_candidates(self, results):
        if not results:
            return []
        weights_sum = sum(prob for prob, _ in results)
        if weights_sum == 0:
            return list(results[0][1])
        length = len(results[0][1])
        blended = [0.0] * length
        for prob, counts in results:
            weight = prob / weights_sum
            for idx in range(length):
                blended[idx] += counts[idx] * weight
        return blended

    def _update_direction_bias(self, bias, previous_counts, new_counts):
        updated = list(bias)
        for idx in range(len(updated)):
            prev = previous_counts[idx] if idx < len(previous_counts) else 0
            new = new_counts[idx] if idx < len(new_counts) else 0
            delta = new - prev
            if delta == 0:
                updated[idx] *= 0.9
            else:
                direction = 1 if delta > 0 else -1
                updated[idx] = 0.7 * updated[idx] + 0.3 * direction
        return updated

    def _simulate_probability(self, counts, base_notoriety, cheese_sequence, simulations):
        weights = self._weights_from_counts(counts)
        cumulative = self._prepare_weight_cumulative(weights)
        ready_runs = 0
        for _ in range(simulations):
            _, ready = self._simulate_sequence(base_notoriety, cheese_sequence, cumulative)
            if ready:
                ready_runs += 1
        return ready_runs / max(1, simulations)


class RatioScalerTab(ttk.Frame):
    GENRES = ("Romance", "Adventure", "Comedy", "Tragedy", "Suspense")

    def __init__(self, parent):
        super().__init__(parent)
        self.original_counts = [0 for _ in self.GENRES]
        self.original_summary_var = tk.StringVar(value="Original distribution: not loaded.")
        self.scaled_summary_var = tk.StringVar(value="Scaled distribution will appear here.")
        self.scale_var = tk.IntVar(value=100)
        self.status_var = tk.StringVar()
        self._build_ui()
        self._refresh_scaled()

    def _build_ui(self):
        container = ttk.Frame(self)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)

        ttk.Label(
            container,
            text="Ratio Scaler: paste a five-genre distribution, then slide the total up or down while keeping the ratios intact.",
            wraplength=640,
            justify="left",
        ).grid(row=0, column=0, sticky="w", pady=(12, 6))

        buttons = ttk.Frame(container)
        buttons.grid(row=1, column=0, sticky="w")
        ttk.Button(buttons, text="Paste distribution", command=self._paste_distribution).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(buttons, text="Reset", command=self._reset_distribution).grid(row=0, column=1)
        ttk.Label(buttons, textvariable=self.status_var, foreground="red").grid(row=1, column=0, columnspan=2, sticky="w")

        ttk.Label(container, textvariable=self.original_summary_var, justify="left").grid(
            row=2, column=0, sticky="w", pady=(10, 5)
        )

        slider_frame = ttk.LabelFrame(container, text="Scale total while preserving ratios")
        slider_frame.grid(row=3, column=0, sticky="ew", pady=(8, 5))
        ttk.Label(slider_frame, text="Target total (%)").grid(row=0, column=0, sticky="w")
        ttk.Scale(
            slider_frame,
            from_=5,
            to=400,
            orient="horizontal",
            variable=self.scale_var,
            command=lambda _value: self._on_slider_change(),
            length=800,
        ).grid(row=1, column=0, sticky="ew", padx=4)
        self.scale_value_label = ttk.Label(slider_frame, text="Current scale: 100%")
        self.scale_value_label.grid(row=2, column=0, sticky="w")

        ttk.Separator(container, orient="horizontal").grid(row=4, column=0, sticky="ew", pady=10)
        preview_row = ttk.Frame(container)
        preview_row.grid(row=5, column=0, sticky="ew")
        ttk.Label(preview_row, text="Scaled distribution:", font=("Arial", 11, "bold")).pack(side="left")
        ttk.Button(preview_row, text="Copy", command=self._copy_scaled).pack(side="left", padx=(10, 0))
        ttk.Label(container, textvariable=self.scaled_summary_var, justify="left").grid(
            row=6, column=0, sticky="w", pady=(6, 0)
        )

    def _paste_distribution(self):
        try:
            clipboard_content = self.clipboard_get()
        except tk.TclError:
            self.status_var.set("Clipboard unavailable.")
            return
        numbers = [part for part in re.split(r"[^\d]+", clipboard_content) if part]
        if len(numbers) != len(self.GENRES):
            self.status_var.set("Need exactly 5 numbers.")
            return
        self.original_counts = [int(value) for value in numbers]
        self.status_var.set("Distribution pasted.")
        self._update_original_summary()
        self._refresh_scaled()

    def _reset_distribution(self):
        self.original_counts = [0 for _ in self.GENRES]
        self.status_var.set("Reset.")
        self._update_original_summary()
        self._refresh_scaled()

    def _update_original_summary(self):
        total = sum(self.original_counts)
        if total <= 0:
            self.original_summary_var.set("Original distribution: not loaded.")
            return
        lines = []
        for genre, value in zip(self.GENRES, self.original_counts):
            pct = value / total * 100 if total else 0
            lines.append(f"{genre}: {value} ({pct:.1f}%)")
        self.original_summary_var.set("Original distribution:\n" + "\n".join(lines))

    def _on_slider_change(self):
        self.scale_value_label.config(text=f"Current scale: {self.scale_var.get()}%")
        self._refresh_scaled()

    def _refresh_scaled(self):
        base_total = sum(self.original_counts)
        if base_total <= 0:
            self.scaled_summary_var.set("Please paste a distribution first.")
            return
        scale_fraction = self.scale_var.get() / 100.0
        target_total = max(1, base_total * scale_fraction)
        scaled = []
        for value in self.original_counts:
            ratio = value / base_total if base_total else 0
            scaled.append(ratio * target_total)
        lines = []
        for genre, value in zip(self.GENRES, scaled):
            pct = value / target_total * 100 if target_total else 0
            lines.append(f"{genre}: {int(round(value))} ({pct:.1f}%)")
        self.scaled_summary_var.set("Scaled distribution:\n" + "\n".join(lines))

    def _copy_scaled(self):
        base_total = sum(self.original_counts)
        if base_total <= 0:
            self.status_var.set("Nothing to copy yet.")
            return
        scale_fraction = self.scale_var.get() / 100.0
        target_total = max(1, base_total * scale_fraction)
        scaled = []
        for value in self.original_counts:
            ratio = value / base_total if base_total else 0
            scaled.append(ratio * target_total)
        text = ",".join(str(int(round(value))) for value in scaled)
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.status_var.set("Scaled distribution copied.")
        except tk.TclError:
            self.status_var.set("Clipboard unavailable.")

    def _blend_top_candidates(self, results):
        if not results:
            return []
        weights_sum = sum(prob for prob, _ in results)
        if weights_sum == 0:
            return list(results[0][1])
        length = len(results[0][1])
        blended = [0.0] * length
        for prob, counts in results:
            weight = prob / weights_sum
            for idx in range(length):
                blended[idx] += counts[idx] * weight
        return blended

    def _update_direction_bias(self, bias, previous_counts, new_counts):
        updated = list(bias)
        for idx in range(len(updated)):
            prev = previous_counts[idx] if idx < len(previous_counts) else 0
            new = new_counts[idx] if idx < len(new_counts) else 0
            delta = new - prev
            if delta == 0:
                updated[idx] *= 0.9
            else:
                direction = 1 if delta > 0 else -1
                updated[idx] = 0.7 * updated[idx] + 0.3 * direction
        return updated

    def _simulate_probability(self, counts, base_notoriety, cheese_sequence, simulations):
        weights = self._weights_from_counts(counts)
        cumulative = self._prepare_weight_cumulative(weights)
        ready_runs = 0
        for _ in range(simulations):
            _, ready = self._simulate_sequence(base_notoriety, cheese_sequence, cumulative)
            if ready:
                ready_runs += 1
        return ready_runs / max(1, simulations)


class ContingencyStartFixer(ttk.Frame):
    LENGTH_VALUES = {"10": 250, "20": 500, "30": 750}

    def __init__(self, parent):
        super().__init__(parent)
        self.genres = PostscriptBase.GENRES
        self.original_counts = [0 for _ in self.genres]
        self.original_summary_var = tk.StringVar(value="Original distribution: not loaded.")
        self.adjusted_summary_var = tk.StringVar(value="Adjusted preview will appear here.")
        self.status_var = tk.StringVar()
        self.genre_choice = tk.StringVar(value=self.genres[0])
        self.length_choice = tk.StringVar(value="10")
        self.share_var = tk.IntVar(value=35)
        self._build_ui()
        self._update_original_summary()
        self._recompute_distribution()

    def _build_ui(self):
        container = ttk.Frame(self)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)

        ttk.Label(
            container,
            text="Contingency start fixer: paste an existing chapter-page distribution, "
            "boost one genre with fixed pages, then slide to control its final share while the rest keep relative ratios.",
            wraplength=640,
            justify="left",
        ).grid(row=0, column=0, sticky="w", pady=(10, 5))

        controls = ttk.Frame(container)
        controls.grid(row=1, column=0, sticky="ew")
        ttk.Button(controls, text="Paste page distribution", command=self._paste_pages).grid(row=0, column=0, sticky="w")
        ttk.Button(controls, text="Reset", command=self._reset_pages).grid(row=0, column=1, padx=(10, 0))
        ttk.Label(controls, textvariable=self.status_var, foreground="red").grid(row=1, column=0, columnspan=2, sticky="w")

        ttk.Label(container, textvariable=self.original_summary_var, justify="left").grid(
            row=2, column=0, sticky="w", pady=(10, 5)
        )

        picker = ttk.Frame(container)
        picker.grid(row=3, column=0, sticky="ew", pady=(5, 5))

        ttk.Label(picker, text="Target Genre:").grid(row=0, column=0, sticky="w")
        genre_box = ttk.Combobox(
            picker, values=self.genres, textvariable=self.genre_choice, state="readonly", width=15
        )
        genre_box.grid(row=0, column=1, padx=(5, 15))
        genre_box.bind("<<ComboboxSelected>>", lambda _event: self._recompute_distribution())

        ttk.Label(picker, text="Length boost:").grid(row=0, column=2, sticky="w")
        length_box = ttk.Combobox(
            picker, values=list(self.LENGTH_VALUES.keys()), textvariable=self.length_choice, state="readonly", width=6
        )
        length_box.grid(row=0, column=3, padx=(5, 0))
        length_box.bind("<<ComboboxSelected>>", lambda _event: self._recompute_distribution())
        ttk.Label(picker, text="(10→+250, 20→+500, 30→+750 pages)").grid(row=0, column=4, sticky="w", padx=(8, 0))

        slider_frame = ttk.Frame(container)
        slider_frame.grid(row=4, column=0, sticky="ew", pady=(10, 5))
        ttk.Label(slider_frame, text="Target genre share of total (%):").grid(row=0, column=0, sticky="w")
        ttk.Scale(
            slider_frame,
            from_=5,
            to=80,
            orient="horizontal",
            variable=self.share_var,
            command=lambda _value: self._on_slider_change(),
        ).grid(row=1, column=0, sticky="ew")
        self.share_value_label = ttk.Label(slider_frame, text=f"Current share: {self.share_var.get()}%")
        self.share_value_label.grid(row=2, column=0, sticky="w")

        ttk.Separator(container, orient="horizontal").grid(row=5, column=0, sticky="ew", pady=10)

        preview_row = ttk.Frame(container)
        preview_row.grid(row=6, column=0, sticky="ew")
        ttk.Label(preview_row, text="Adjusted distribution preview:", font=("Arial", 11, "bold")).pack(side="left")
        ttk.Button(preview_row, text="Copy", command=self._copy_adjusted).pack(side="left", padx=(10, 0))
        ttk.Label(container, textvariable=self.adjusted_summary_var, justify="left").grid(
            row=7, column=0, sticky="w", pady=(5, 10)
        )

        ttk.Label(
            container,
            text="Scenario:\n"
            "Use this when a second run begins with the same Genre you already satisfied; you can inject extra pages "
            "and rebalance the remaining Genres to maximize the chance of hitting the next target instantly.\n\n"
            "How to use:\n"
            "1. Paste the current chapter-page distribution from any module.\n"
            "2. Choose the Genre/length that start in this run (length grants fixed pages).\n"
            "3. Adjust the slider until the target Genre share looks reasonable.\n"
            "4. Copy the adjusted distribution and feed it back into the main simulator/optimizer.",
            justify="left",
            wraplength=640,
        ).grid(row=8, column=0, sticky="w", pady=(5, 0))

    def _paste_pages(self):
        try:
            clipboard_content = self.clipboard_get()
        except tk.TclError:
            self.status_var.set("Clipboard unavailable.")
            return
        numbers = [part for part in re.split(r"[^\d]+", clipboard_content) if part]
        if len(numbers) != len(self.genres):
            self.status_var.set("Expected exactly 5 numbers when pasting.")
            return
        self.original_counts = [int(value) for value in numbers]
        self.status_var.set("Page distribution pasted.")
        self._update_original_summary()
        self._recompute_distribution()

    def _reset_pages(self):
        self.original_counts = [0 for _ in self.genres]
        self.status_var.set("Reset to zero.")
        self._update_original_summary()
        self._recompute_distribution()

    def _update_original_summary(self):
        total = sum(self.original_counts)
        if total == 0:
            self.original_summary_var.set("Original distribution: no data loaded yet.")
            return
        lines = []
        for genre, value in zip(self.genres, self.original_counts):
            pct = value / total * 100 if total > 0 else 0
            lines.append(f"{genre}: {value} ({pct:.1f}%)")
        self.original_summary_var.set("Original distribution:\n" + "\n".join(lines))

    def _on_slider_change(self):
        self.share_value_label.configure(text=f"Current share: {self.share_var.get()}%")
        self._recompute_distribution()

    def _recompute_distribution(self):
        total_original = sum(self.original_counts)
        if total_original == 0:
            self.adjusted_summary_var.set("Please paste a page distribution first.")
            return
        target_genre = self.genre_choice.get()
        if target_genre not in self.genres:
            self.adjusted_summary_var.set("Please select a valid genre.")
            return
        try:
            length_key = self.length_choice.get()
            boost = self.LENGTH_VALUES[length_key]
        except KeyError:
            self.adjusted_summary_var.set("Select a valid length.")
            return
        target_index = self.genres.index(target_genre)
        base_counts = list(self.original_counts)
        base_target = base_counts[target_index] + boost
        share_fraction = max(0.05, min(self.share_var.get() / 100.0, 0.9))
        required_total = base_target / share_fraction
        fallback_total = sum(base_counts) + boost
        final_total = max(required_total, fallback_total)
        target_value = final_total * share_fraction
        remaining_total = final_total - target_value
        result = [0.0 for _ in self.genres]
        result[target_index] = target_value

        other_indices = [idx for idx in range(len(self.genres)) if idx != target_index]
        others_sum = sum(base_counts[idx] for idx in other_indices)
        if others_sum <= 0:
            equal_share = remaining_total / len(other_indices) if other_indices else 0
            for idx in other_indices:
                result[idx] = equal_share
        else:
            for idx in other_indices:
                ratio = base_counts[idx] / others_sum
                result[idx] = remaining_total * ratio

        lines = []
        for genre, value in zip(self.genres, result):
            pct = value / final_total * 100 if final_total > 0 else 0
            lines.append(f"{genre}: {int(round(value))} ({pct:.1f}%)")
        self.adjusted_summary_var.set("Adjusted distribution:\n" + "\n".join(lines))

    def export_state(self):
        return {
            "pages": self.original_counts,
            "genre": self.genre_choice.get(),
            "length": self.length_choice.get(),
            "share": self.share_var.get(),
        }

    def import_state(self, data):
        pass

    def _copy_adjusted(self):
        counts = self._compute_adjusted_values()
        if counts is None:
            self.status_var.set("Nothing to copy yet.")
            return
        text = ",".join(str(int(round(value))) for value in counts)
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.status_var.set("Adjusted distribution copied.")
        except tk.TclError:
            self.status_var.set("Clipboard unavailable.")

    def _compute_adjusted_values(self):
        total_original = sum(self.original_counts)
        if total_original == 0:
            return None
        target_genre = self.genre_choice.get()
        if target_genre not in self.genres:
            return None
        try:
            boost = self.LENGTH_VALUES[self.length_choice.get()]
        except KeyError:
            return None
        target_index = self.genres.index(target_genre)
        base_counts = list(self.original_counts)
        base_target = base_counts[target_index] + boost
        share_fraction = max(0.05, min(self.share_var.get() / 100.0, 0.9))
        required_total = base_target / share_fraction
        fallback_total = sum(base_counts) + boost
        final_total = max(required_total, fallback_total)
        target_value = final_total * share_fraction
        remaining_total = final_total - target_value
        result = [0.0 for _ in self.genres]
        result[target_index] = target_value
        other_indices = [idx for idx in range(len(self.genres)) if idx != target_index]
        others_sum = sum(base_counts[idx] for idx in other_indices)
        if others_sum <= 0:
            equal_share = remaining_total / len(other_indices) if other_indices else 0
            for idx in other_indices:
                result[idx] = equal_share
        else:
            for idx in other_indices:
                ratio = base_counts[idx] / others_sum
                result[idx] = remaining_total * ratio
        return result

    def _simulate_probability(self, counts, base_notoriety, cheese_sequence, simulations):
        weights = self._weights_from_counts(counts)
        cumulative = self._prepare_weight_cumulative(weights)
        ready_runs = 0
        for _ in range(simulations):
            _, ready = self._simulate_sequence(base_notoriety, cheese_sequence, cumulative)
            if ready:
                ready_runs += 1
        return ready_runs / max(1, simulations)

    def _generate_candidate_counts(self, base_counts, dial_range, direction_bias):
        varied = list(base_counts)
        positive_indices = [idx for idx, value in enumerate(base_counts) if value > 0]
        if not positive_indices:
            positive_indices = list(range(len(base_counts)))
        subset_size = max(1, (len(positive_indices) + 1) // 2)
        if len(positive_indices) > subset_size:
            selected = random.sample(positive_indices, subset_size)
        else:
            selected = positive_indices
        for idx in selected:
            value = base_counts[idx]
            bias = direction_bias[idx] if idx < len(direction_bias) else 0.0
            delta = random.uniform(-dial_range / 100, dial_range / 100) + bias * 0.1
            varied[idx] = max(0.0, value * (1 + delta))
        return varied

    def _systematic_candidates(self, base_counts, dial_range):
        candidates = []
        if not base_counts:
            return candidates
        for idx, value in enumerate(base_counts):
            if value <= 0:
                continue
            increase = list(base_counts)
            increase[idx] = max(0.0, value * (1 + dial_range / 100))
            candidates.append(increase)
            decrease = list(base_counts)
            decrease[idx] = max(0.0, value * (1 - dial_range / 100))
            candidates.append(decrease)
        if not candidates:
            candidates = [list(base_counts)]
        return candidates

    def _blend_top_candidates(self, results):
        if not results:
            return []
        weights_sum = sum(prob for prob, _ in results)
        if weights_sum == 0:
            return list(results[0][1])
        length = len(results[0][1])
        blended = [0.0] * length
        for prob, counts in results:
            weight = prob / weights_sum
            for idx in range(length):
                blended[idx] += counts[idx] * weight
        return blended

    def _update_direction_bias(self, bias, previous_counts, new_counts):
        updated = list(bias)
        for idx in range(len(updated)):
            prev = previous_counts[idx] if idx < len(previous_counts) else 0
            new = new_counts[idx] if idx < len(new_counts) else 0
            delta = new - prev
            if delta == 0:
                updated[idx] *= 0.9
            else:
                direction = 1 if delta > 0 else -1
                updated[idx] = 0.7 * updated[idx] + 0.3 * direction
        return updated

    def _copy_page_weights(self):
        values = [str(self._sanitize_string_var(var)) for var in self.genre_page_vars]
        try:
            self.clipboard_clear()
            self.clipboard_append(",".join(values))
            self._set_page_status("Page weights copied.", success=True)
        except tk.TclError:
            self._set_page_status("Clipboard unavailable.", success=False)

    def _paste_page_weights(self):
        try:
            clipboard_content = self.clipboard_get()
        except tk.TclError:
            self._set_page_status("Clipboard unavailable.", success=False)
            return

        numbers = [part for part in re.split(r"[^\d]+", clipboard_content) if part]
        if len(numbers) != len(self.GENRES):
            self._set_page_status("Clipboard format invalid.", success=False)
            return
        for idx, value in enumerate(numbers):
            self.genre_page_vars[idx].set(value)
        self._set_page_status("Page weights pasted.", success=True)
        self._update_page_percentages()

    def _update_page_percentages(self):
        counts = [self._sanitize_string_var(var) for var in self.genre_page_vars]
        total = sum(counts)
        for idx, percent_var in enumerate(self.genre_page_percent_vars):
            genre_label = self.GENRES[idx]
            if total > 0:
                pct = counts[idx] / total * 100
                percent_var.set(f"{genre_label} ({pct:.1f}%)")
            else:
                percent_var.set(f"{genre_label} (--)")

    def _set_page_status(self, message, success=True):
        color = "green" if success else "red"
        self.page_status_var.set(message)
        if hasattr(self, "page_status_label"):
            self.page_status_label.configure(fg=color)

class DualPostscriptSimulator(PostscriptBase):
    MULTI_RUNS = 50000

    def __init__(self, parent):
        super().__init__(parent)
        self.setup_data = []
        self.clipboard_status_var = tk.StringVar()
        self.genre_notoriety_vars = []
        self.notoriety_progress_vars = []
        self.first_result_var = tk.StringVar(value="First run result: not started yet.")
        self.second_result_var = tk.StringVar(value="Second run final result: not started yet.")
        self.final_ready_var = tk.StringVar(value="[Not ready]")
        self.multi_result_var = tk.StringVar(value="50,000-run combined average: not started yet.")
        self.multi_ready_var = tk.StringVar(value="All Genre >80 Percentage: --")
        self.extension_stats_var = tk.StringVar(value="Auto-extend usage: --")
        self._build_ui()

    def _build_ui(self):
        container = ttk.Frame(self)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=3)
        container.columnconfigure(1, weight=2)

        left = ttk.Frame(container)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.columnconfigure(0, weight=1)
        left.columnconfigure(1, weight=1)

        right = ttk.Frame(container)
        right.grid(row=0, column=1, sticky="n")

        row = 0
        ttk.Label(
            left,
            text="Stack two hunts: configure Setup 1 and Setup 2, then run them sequentially.",
            justify="left",
            wraplength=400,
        ).grid(row=row, column=0, sticky="w", pady=(10, 5))
        row += 1

        setups_frame = ttk.Frame(left)
        setups_frame.grid(row=row, column=0, columnspan=2, sticky="nsew")
        setups_frame.columnconfigure(0, weight=1)
        setups_frame.columnconfigure(1, weight=1)

        for idx in range(2):
            m_value = 10 if idx == 0 else 0
            self._create_setup_section(
                setups_frame, f"Setup {idx + 1}", row=0, column=idx, m_value=m_value
            )

        row += 1

        ttk.Separator(left, orient="horizontal").grid(row=row, column=0, sticky="ew", pady=10)
        row += 1

        ttk.Button(left, text="Run Dual Hunts Simulation", command=self._run_dual_simulation).grid(
            row=row, column=0, sticky="w"
        )
        row += 1

        first_frame = ttk.Frame(left)
        first_frame.grid(row=row, column=0, sticky="w", pady=(10, 0))
        ttk.Label(first_frame, textvariable=self.first_result_var, wraplength=420, justify="left").grid(
            row=0, column=0, sticky="w"
        )
        row += 1

        second_frame = ttk.Frame(left)
        second_frame.grid(row=row, column=0, sticky="w", pady=(10, 0))
        ttk.Label(second_frame, textvariable=self.second_result_var, wraplength=420, justify="left").grid(
            row=0, column=0, sticky="w"
        )
        self.final_ready_label = tk.Label(second_frame, textvariable=self.final_ready_var, fg="red")
        self.final_ready_label.grid(row=0, column=1, padx=(5, 0))
        row += 1

        multi_frame = ttk.Frame(left)
        multi_frame.grid(row=row, column=0, sticky="w", pady=(10, 0))
        ttk.Label(multi_frame, textvariable=self.multi_result_var, wraplength=420, justify="left").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(multi_frame, textvariable=self.multi_ready_var).grid(row=1, column=0, sticky="w", pady=(4, 0))

        ttk.Label(right, text="Starting Genre Notoriety (max 200)", font=("Arial", 11, "bold")).grid(
            row=0, column=0, sticky="w", pady=(10, 5)
        )
        for idx, genre in enumerate(self.GENRES):
            ttk.Label(right, text=genre).grid(row=1 + idx * 3, column=0, sticky="w")
            progress_var = tk.IntVar(value=0)
            self.notoriety_progress_vars.append(progress_var)
            progress = ttk.Progressbar(
                right, orient="horizontal", length=200, maximum=self.NOTORIETY_CAP, variable=progress_var
            )
            progress.grid(row=2 + idx * 3, column=0, sticky="w")
            var = tk.StringVar(value="0")
            var.trace_add("write", lambda *args, i=idx: self._on_notoriety_change(i))
            entry = ttk.Entry(right, textvariable=var, width=10)
            entry.grid(row=3 + idx * 3, column=0, sticky="w", pady=(0, 5))
            self.genre_notoriety_vars.append(var)

        buttons = ttk.Frame(right)
        buttons.grid(row=1 + len(self.GENRES) * 3, column=0, pady=(10, 0), sticky="w")
        copy_paste_row = ttk.Frame(buttons)
        copy_paste_row.pack(anchor="w")
        ttk.Button(copy_paste_row, text="Copy", command=self._copy_notoriety).pack(side="left", padx=(0, 5))
        ttk.Button(copy_paste_row, text="Paste", command=self._paste_notoriety).pack(side="left")
        ttk.Button(buttons, text="Reset", command=self._reset_notoriety).pack(anchor="w", pady=(5, 0))

        self.clipboard_status_label = ttk.Label(right, textvariable=self.clipboard_status_var, foreground="green")
        self.clipboard_status_label.grid(
            row=2 + len(self.GENRES) * 3, column=0, sticky="w", pady=(5, 0)
        )

        for setup in self.setup_data:
            self._set_default_setup_counts(setup)

    def _create_setup_section(self, parent, title, row, column, m_value):
        frame = ttk.LabelFrame(parent, text=title)
        frame.grid(row=row, column=column, sticky="nsew", padx=(0, 10) if column == 0 else (10, 0), pady=(0, 10))

        setup = {
            "frame": frame,
            "extend_var": tk.BooleanVar(value=False),
            "auto_extend_var": tk.BooleanVar(value=False),
            "cheese_vars": [],
            "page_vars": [],
            "error_var": tk.StringVar(),
            "m_value": m_value,
        }
        self.setup_data.append(setup)

        local_row = 0
        ttk.Checkbutton(
            frame,
            text="Extend hunts (+3 attempts)",
            variable=setup["extend_var"],
            command=lambda s=setup: self._on_extend_toggle(s),
        ).grid(row=local_row, column=0, columnspan=3, sticky="w")
        local_row += 1

        ttk.Checkbutton(
            frame,
            text=f"Auto-extend if top genre < {80 + m_value}",
            variable=setup["auto_extend_var"],
        ).grid(row=local_row, column=0, columnspan=4, sticky="w", pady=(0, 5))
        help_label = ttk.Label(frame, text="?", foreground="blue", cursor="question_arrow")
        help_label.grid(row=local_row, column=4, sticky="w")
        tooltip_text = (
            f"Adds 3 extra hunts if any highest-page genre stays below {80 + m_value} notoriety.\n"
            f"During extension: uses 125-point cheese until all top genres reach {33 + m_value},"
            " then switches to 50-point cheese."
        )
        ToolTip(help_label, tooltip_text)
        local_row += 1

        ttk.Label(frame, text="Cheese Type").grid(row=local_row, column=0, sticky="w")
        ttk.Label(frame, text="Notoriety").grid(row=local_row, column=1, sticky="w")
        ttk.Label(frame, text="Quantity").grid(row=local_row, column=2, columnspan=3)
        local_row += 1

        for idx, value in enumerate(self.CHEESE_VALUES):
            ttk.Label(frame, text=f"{value} Notoriety").grid(row=local_row + idx, column=0, sticky="w", pady=2)
            ttk.Label(frame, text=str(value)).grid(row=local_row + idx, column=1, sticky="w")
            ttk.Button(
                frame, text="-", width=3, command=lambda s=setup, i=idx: self._adjust_count(s, i, -1)
            ).grid(row=local_row + idx, column=2, padx=(10, 2))

            var = tk.StringVar()
            var.trace_add("write", lambda *args, s=setup, i=idx: self._on_cheese_entry_change(s, i))
            ttk.Entry(frame, textvariable=var, width=7, justify="center").grid(row=local_row + idx, column=3, padx=2)
            setup["cheese_vars"].append(var)

            ttk.Button(
                frame, text="+", width=3, command=lambda s=setup, i=idx: self._adjust_count(s, i, 1)
            ).grid(row=local_row + idx, column=4, padx=(2, 0))

        local_row += len(self.CHEESE_VALUES)
        ttk.Label(frame, textvariable=setup["error_var"], foreground="red").grid(
            row=local_row, column=0, columnspan=5, sticky="w", pady=(5, 0)
        )
        local_row += 1

        ttk.Separator(frame, orient="horizontal").grid(row=local_row, column=0, columnspan=5, sticky="ew", pady=5)
        local_row += 1

        header = ttk.Frame(frame)
        header.grid(row=local_row, column=0, columnspan=5, sticky="ew")
        ttk.Label(header, text="Chapter pages per Genre (weights):").grid(row=0, column=0, sticky="w")
        ttk.Button(header, text="Reset", command=lambda s=setup: self._reset_page_weights(s)).grid(
            row=0, column=1, padx=(10, 0)
        )
        local_row += 1

        page_frame = ttk.Frame(frame)
        page_frame.grid(row=local_row, column=0, columnspan=5, sticky="ew", pady=(3, 0))
        for idx, genre in enumerate(self.GENRES):
            ttk.Label(page_frame, text=f"{genre}:").grid(row=idx, column=0, sticky="w")
            var = tk.StringVar(value="0")
            var.trace_add("write", lambda *args, s=setup, i=idx: self._on_page_entry_change(s, i))
            ttk.Entry(page_frame, textvariable=var, width=10).grid(row=idx, column=1, pady=1, sticky="w")
            setup["page_vars"].append(var)

        return row + 1

    def _on_cheese_entry_change(self, setup, index):
        self._sanitize_setup_value(setup, index)
        self._update_setup_totals(setup)

    def _sanitize_setup_value(self, setup, index):
        return self._sanitize_string_var(setup["cheese_vars"][index])

    def _adjust_count(self, setup, index, delta):
        counts = self._get_counts(setup)
        new_value = max(0, counts[index] + delta)
        setup["cheese_vars"][index].set(str(new_value))
        self._update_setup_totals(setup)

    def _get_counts(self, setup):
        return [self._sanitize_setup_value(setup, idx) for idx in range(len(setup["cheese_vars"]))]

    def _setup_target_hunts(self, setup):
        return self._compute_target_hunts(setup["extend_var"].get())

    def _update_setup_totals(self, setup):
        target = self._setup_target_hunts(setup)
        total = sum(self._get_counts(setup))
        if total == target:
            setup["error_var"].set("")
        else:
            setup["error_var"].set(f"Cheese count mismatch. Need {target}, current {total}.")

    def _set_default_setup_counts(self, setup):
        target = self._setup_target_hunts(setup)
        for idx, var in enumerate(setup["cheese_vars"]):
            default_value = target if self.CHEESE_VALUES[idx] == 50 else 0
            var.set(str(default_value))
        self._update_setup_totals(setup)

    def _on_extend_toggle(self, setup):
        self._update_setup_totals(setup)

    def _on_page_entry_change(self, setup, index):
        self._sanitize_string_var(setup["page_vars"][index])

    def _reset_page_weights(self, setup):
        for var in setup["page_vars"]:
            var.set("0")

    def _get_weight_distribution(self, setup):
        raw = {
            genre: self._sanitize_string_var(setup["page_vars"][idx]) for idx, genre in enumerate(self.GENRES)
        }
        total = sum(raw.values())
        if total == 0:
            fallback = 1 / len(self.GENRES)
            return {genre: fallback for genre in self.GENRES}
        return {genre: value / total for genre, value in raw.items()}

    def _run_dual_simulation(self):
        if not all(sum(self._get_counts(setup)) == self._setup_target_hunts(setup) for setup in self.setup_data):
            self.first_result_var.set("First run result: fix cheese totals for both setups first.")
            self.second_result_var.set("Second run final result: awaiting valid setup.")
            self._set_final_ready(False, label_text="[Not ready]")
            self.multi_result_var.set("50,000-run combined average: waiting for valid setup...")
            self.multi_ready_var.set("All Genre >80 Percentage: --")
            self.extension_stats_var.set("Auto-extend usage: Setup1 -- / Setup2 --")
            return

        sequences = [self._build_cheese_sequence(self._get_counts(setup)) for setup in self.setup_data]
        base_notoriety = [
            self._sanitize_string_var(var, limit=self.NOTORIETY_CAP) for var in self.genre_notoriety_vars
        ]
        cumulative_weights = [
            self._prepare_weight_cumulative(self._get_weight_distribution(setup)) for setup in self.setup_data
        ]

        first_values, _, first_extended = self._execute_setup(base_notoriety, 0, sequences, cumulative_weights)
        first_pairs = "; ".join(f"{genre}:{value}" for genre, value in zip(self.GENRES, first_values))
        suffix_one = " (auto-extended)" if first_extended else ""
        self.first_result_var.set(f"First run result: {first_pairs}{suffix_one}")

        final_values, ready, second_extended = self._execute_setup(first_values, 1, sequences, cumulative_weights)
        final_pairs = "; ".join(f"{genre}:{value}" for genre, value in zip(self.GENRES, final_values))
        suffix_two = " (auto-extended)" if second_extended else ""
        self.second_result_var.set(f"Second run final result: {final_pairs}{suffix_two}")
        self._set_final_ready(ready)

        totals = [0] * len(self.GENRES)
        ready_runs = 0
        extend_counts = [0, 0]
        total_extensions = 0
        for _ in range(self.MULTI_RUNS):
            start_values = list(base_notoriety)
            mid_values, _, ext1 = self._execute_setup(start_values, 0, sequences, cumulative_weights)
            if ext1:
                extend_counts[0] += 1
                total_extensions += 1
            end_values, run_ready, ext2 = self._execute_setup(mid_values, 1, sequences, cumulative_weights)
            if ext2:
                extend_counts[1] += 1
                total_extensions += 1
            if run_ready:
                ready_runs += 1
            for idx, val in enumerate(end_values):
                totals[idx] += val

        averages = [val / self.MULTI_RUNS for val in totals]
        avg_pairs = "; ".join(f"{genre}:{avg:.2f}" for genre, avg in zip(self.GENRES, averages))
        ready_ratio = ready_runs / self.MULTI_RUNS * 100
        avg_extensions = total_extensions / self.MULTI_RUNS
        self.multi_result_var.set(f"50,000-run combined average: {avg_pairs} | Avg auto-extends/run: {avg_extensions:.2f}")
        self.multi_ready_var.set(
            f"All Genre >80 Percentage: {ready_ratio:.2f}% ({ready_runs}/{self.MULTI_RUNS})"
        )
        extend_rate1 = extend_counts[0] / self.MULTI_RUNS * 100
        extend_rate2 = extend_counts[1] / self.MULTI_RUNS * 100
        self.extension_stats_var.set(
            f"Auto-extend usage: Setup1 {extend_rate1:.2f}% ({extend_counts[0]}/{self.MULTI_RUNS}) / "
            f"Setup2 {extend_rate2:.2f}% ({extend_counts[1]}/{self.MULTI_RUNS})"
        )

    def _execute_setup(self, start_values, setup_index, sequences, cumulative_weights):
        values, ready = self._simulate_sequence(start_values, sequences[setup_index], cumulative_weights[setup_index])
        extended = False
        config = self._extension_config(self.setup_data[setup_index])
        if config and self._should_trigger_extension(values, config):
            extended = True
            self._apply_extension(values, cumulative_weights[setup_index], config)
        ready = all(val >= 80 for val in values)
        return values, ready, extended

    def _extension_config(self, setup):
        if not setup["auto_extend_var"].get():
            return None
        page_counts = [self._sanitize_string_var(var) for var in setup["page_vars"]]
        if not page_counts:
            return None
        max_pages = max(page_counts)
        if max_pages <= 0:
            return None
        top_indices = [idx for idx, value in enumerate(page_counts) if value == max_pages]
        m_value = setup["m_value"]
        return {
            "top_indices": top_indices,
            "threshold_ready": 80 + m_value,
            "threshold_high": 33 + m_value,
            "extra_hunts": 3,
            "setup_index": self.setup_data.index(setup),
        }

    def _should_trigger_extension(self, values, config):
        if config["setup_index"] == 1:
            setup = self.setup_data[1]
            for idx in config["top_indices"]:
                page_count = self._sanitize_string_var(setup["page_vars"][idx])
                if page_count == 0 and values[idx] < 83:
                    return False
        return any(values[idx] < config["threshold_ready"] for idx in config["top_indices"])

    def _apply_extension(self, values, cumulative_weights, config):
        switch_to_medium = False
        for _ in range(config["extra_hunts"]):
            if not switch_to_medium:
                if any(values[idx] < config["threshold_high"] for idx in config["top_indices"]):
                    cheese_value = 125
                else:
                    switch_to_medium = True
                    cheese_value = 50
            else:
                cheese_value = 50
            self._apply_hunt_step(values, cheese_value, cumulative_weights)

    def _set_final_ready(self, ready, label_text=None):
        if label_text is None:
            label_text = "[All ready!]" if ready else "[Not ready]"
        self.final_ready_var.set(label_text)
        color = "green" if ready else "red"
        self.final_ready_label.configure(fg=color)


class DualPostscriptPrunedSimulator(DualPostscriptSimulator):
    """Variant of the dual simulator that zeroes high-notoriety genres before starting setup 2."""

    def _run_dual_simulation(self):
        if not all(sum(self._get_counts(setup)) == self._setup_target_hunts(setup) for setup in self.setup_data):
            self.first_result_var.set("First run result: fix cheese totals for both setups first.")
            self.second_result_var.set(
                "Second run final result: awaiting valid setup (pruned variant)."
            )
            self._set_final_ready(False, label_text="[Not ready]")
            self.multi_result_var.set("50,000-run combined average: waiting for valid setup...")
            self.multi_ready_var.set("All Genre >80 Percentage: --")
            self.extension_stats_var.set("Auto-extend usage: Setup1 -- / Setup2 --")
            return

        sequences = [self._build_cheese_sequence(self._get_counts(setup)) for setup in self.setup_data]
        base_notoriety = [
            self._sanitize_string_var(var, limit=self.NOTORIETY_CAP) for var in self.genre_notoriety_vars
        ]

        first_cumulative = self._prepare_weight_cumulative(self._get_weight_distribution(self.setup_data[0]))
        first_values, _, first_extended = self._execute_setup_with_custom_weights(
            base_notoriety, 0, sequences[0], first_cumulative
        )
        first_pairs = "; ".join(f"{genre}:{value}" for genre, value in zip(self.GENRES, first_values))
        suffix_one = " (auto-extended)" if first_extended else ""
        self.first_result_var.set(f"First run result: {first_pairs}{suffix_one}")

        second_cumulative, pruned_counts = self._prepare_pruned_cumulative(first_values)
        final_values, ready, second_extended = self._execute_setup_with_custom_weights(
            first_values, 1, sequences[1], second_cumulative, pruned_counts
        )
        final_pairs = "; ".join(f"{genre}:{value}" for genre, value in zip(self.GENRES, final_values))
        suffix_two = " (auto-extended)" if second_extended else ""
        self.second_result_var.set(
            f"Second run final result (high-genre pages pruned): {final_pairs}{suffix_two}"
        )
        self._set_final_ready(ready)

        totals = [0] * len(self.GENRES)
        ready_runs = 0
        extend_counts = [0, 0]
        total_extensions = 0
        for _ in range(self.MULTI_RUNS):
            start_values = list(base_notoriety)
            mid_values, _, ext1 = self._execute_setup_with_custom_weights(
                start_values, 0, sequences[0], first_cumulative
            )
            if ext1:
                extend_counts[0] += 1
                total_extensions += 1

            pruned_cumulative, multi_pruned_counts = self._prepare_pruned_cumulative(mid_values)
            end_values, run_ready, ext2 = self._execute_setup_with_custom_weights(
                mid_values, 1, sequences[1], pruned_cumulative, multi_pruned_counts
            )
            if ext2:
                extend_counts[1] += 1
                total_extensions += 1

            if run_ready:
                ready_runs += 1
            for idx, val in enumerate(end_values):
                totals[idx] += val

        averages = [val / self.MULTI_RUNS for val in totals]
        avg_pairs = "; ".join(f"{genre}:{avg:.2f}" for genre, avg in zip(self.GENRES, averages))
        ready_ratio = ready_runs / self.MULTI_RUNS * 100
        avg_extensions = total_extensions / self.MULTI_RUNS
        self.multi_result_var.set(
            f"50,000-run combined average (pruned): {avg_pairs} | Avg auto-extends/run: {avg_extensions:.2f}"
        )
        self.multi_ready_var.set(
            f"All Genre >80 Percentage: {ready_ratio:.2f}% ({ready_runs}/{self.MULTI_RUNS})"
        )
        extend_rate1 = extend_counts[0] / self.MULTI_RUNS * 100
        extend_rate2 = extend_counts[1] / self.MULTI_RUNS * 100
        self.extension_stats_var.set(
            f"Auto-extend usage: Setup1 {extend_rate1:.2f}% ({extend_counts[0]}/{self.MULTI_RUNS}) / "
            f"Setup2 {extend_rate2:.2f}% ({extend_counts[1]}/{self.MULTI_RUNS})"
        )

    def _execute_setup_with_custom_weights(
        self, start_values, setup_index, sequence, cumulative_weights, custom_counts=None
    ):
        values, ready = self._simulate_sequence(start_values, sequence, cumulative_weights)
        extended = False
        if custom_counts is None:
            config = self._extension_config(self.setup_data[setup_index])
            trigger = self._should_trigger_extension(values, config) if config else False
        else:
            config = self._extension_config_with_counts(self.setup_data[setup_index], custom_counts)
            trigger = (
                self._should_trigger_extension_with_counts(values, config, custom_counts) if config else False
            )
        if config and trigger:
            extended = True
            self._apply_extension(values, cumulative_weights, config)
        ready = all(val >= 80 for val in values)
        return values, ready, extended

    def _prepare_pruned_cumulative(self, notoriety_values):
        pruned_counts = self._build_pruned_page_counts(notoriety_values)
        weights = self._weights_from_counts_list(pruned_counts)
        cumulative = self._prepare_weight_cumulative(weights)
        return cumulative, pruned_counts

    def _weights_from_counts_list(self, counts):
        total = sum(counts)
        if total <= 0:
            equal = 1 / len(self.GENRES)
            return {genre: equal for genre in self.GENRES}
        return {genre: counts[idx] / total for idx, genre in enumerate(self.GENRES)}

    def _build_pruned_page_counts(self, notoriety_values):
        setup = self.setup_data[1]
        threshold = self._second_setup_prune_threshold()
        counts = [self._sanitize_string_var(var) for var in setup["page_vars"]]
        pruned = []
        for idx, count in enumerate(counts):
            if notoriety_values[idx] > threshold:
                pruned.append(0)
            else:
                pruned.append(count)
        return pruned

    def _second_setup_prune_threshold(self):
        setup = self.setup_data[1]
        return 93 if setup["extend_var"].get() else 90

    def _extension_config_with_counts(self, setup, custom_counts):
        if not setup["auto_extend_var"].get():
            return None
        page_counts = list(custom_counts)
        if not page_counts:
            return None
        max_pages = max(page_counts)
        if max_pages <= 0:
            return None
        top_indices = [idx for idx, value in enumerate(page_counts) if value == max_pages]
        m_value = setup["m_value"]
        return {
            "top_indices": top_indices,
            "threshold_ready": 80 + m_value,
            "threshold_high": 33 + m_value,
            "extra_hunts": 3,
            "setup_index": self.setup_data.index(setup),
        }

    def _should_trigger_extension_with_counts(self, values, config, custom_counts):
        if config["setup_index"] == 1:
            for idx in config["top_indices"]:
                page_count = custom_counts[idx]
                if page_count == 0 and values[idx] < 83:
                    return False
        return any(values[idx] < config["threshold_ready"] for idx in config["top_indices"])


class MalletFarmSimulator(PostscriptBase):
    CYCLE_SIMULATIONS = 10000

    def __init__(self, parent):
        super().__init__(parent)
        self.iterations_var = tk.StringVar(value="10000")
        self.mallets_per_run_var = tk.StringVar(value="5")
        self.cheese_mid_var = tk.StringVar(value="8")
        self.cheese_high_var = tk.StringVar(value="2")
        self.error_var = tk.StringVar()
        self.run_summary_var = tk.StringVar(value="Average runs per cycle: --")
        self.hunt_summary_var = tk.StringVar(value="Average hunts per cycle: --")
        self.mallet_summary_var = tk.StringVar(value="Estimated mallets gained per cycle: --")
        self._build_ui()

    def _build_ui(self):
        container = ttk.Frame(self)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)

        description = (
            "Just Farming Mallets simulator: spam six short chapters per run, translate accumulated page weights "
            "into notoriety via fixed cheese (8×+50, 2×+125 by default), and repeat until every genre exceeds 80 notoriety. "
            "This tab estimates how many full runs and hunts are needed per cycle and how many mallets you gain if you know "
            "your expected Mallets/run value."
        )
        ttk.Label(container, text=description, wraplength=780, justify="left").grid(
            row=0, column=0, sticky="w", pady=(10, 5)
        )

        form = ttk.Frame(container)
        form.grid(row=1, column=0, sticky="w", pady=(5, 10))

        ttk.Label(form, text="Cycles to simulate:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.iterations_var, width=10).grid(row=0, column=1, padx=(4, 15))

        ttk.Label(form, text="Mallets earned per run (optional):").grid(row=0, column=2, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.mallets_per_run_var, width=10).grid(row=0, column=3, padx=(4, 15))

        ttk.Label(form, text="+50 notoriety cheese per run:").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.cheese_mid_var, width=10).grid(row=1, column=1, padx=(4, 15))

        ttk.Label(form, text="+125 notoriety cheese per run:").grid(row=1, column=2, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.cheese_high_var, width=10).grid(row=1, column=3, padx=(4, 15))

        ttk.Label(container, textvariable=self.error_var, foreground="red").grid(row=2, column=0, sticky="w")

        ttk.Button(container, text="Run Mallet Farming Simulation", command=self._run_mallet_simulation).grid(
            row=3, column=0, sticky="w", pady=(5, 10)
        )

        results = ttk.Frame(container)
        results.grid(row=4, column=0, sticky="w", pady=(5, 10))

        ttk.Label(results, textvariable=self.run_summary_var, font=("Arial", 11)).grid(
            row=0, column=0, sticky="w", pady=2
        )
        ttk.Label(results, textvariable=self.hunt_summary_var, font=("Arial", 11)).grid(
            row=1, column=0, sticky="w", pady=2
        )
        ttk.Label(results, textvariable=self.mallet_summary_var, font=("Arial", 11)).grid(
            row=2, column=0, sticky="w", pady=2
        )

    def _sanitize_int_var(self, tk_var, default):
        value = tk_var.get().strip()
        if not value:
            tk_var.set(str(default))
            return default
        try:
            parsed = int(value)
        except ValueError:
            tk_var.set(str(default))
            return default
        return parsed

    def _sanitize_float_var(self, tk_var, default):
        value = tk_var.get().strip()
        if not value:
            tk_var.set(str(default))
            return default
        try:
            parsed = float(value)
        except ValueError:
            tk_var.set(str(default))
            return default
        return parsed

    def _run_mallet_simulation(self):
        cycles = max(1, self._sanitize_int_var(self.iterations_var, 10000))
        mallets_per_run = max(0.0, self._sanitize_float_var(self.mallets_per_run_var, 0.0))
        cheese_mid = max(0, self._sanitize_int_var(self.cheese_mid_var, 8))
        cheese_high = max(0, self._sanitize_int_var(self.cheese_high_var, 2))
        if cheese_mid + cheese_high <= 0:
            self.error_var.set("Provide at least one cheese so notoriety can advance.")
            return
        self.error_var.set("")
        stats = self._simulate_cycles(cycles, mallets_per_run, cheese_mid, cheese_high)
        self.run_summary_var.set(
            f"Average runs per cycle: {stats['avg_runs_per_cycle']:.2f} (last cycle took {stats['last_cycle_runs']} runs)"
        )
        self.hunt_summary_var.set(
            f"Average hunts per cycle: {stats['avg_hunts_per_cycle']:.2f} (last cycle spent {stats['last_cycle_hunts']} hunts)"
        )
        self.mallet_summary_var.set(
            f"Estimated mallets gained per cycle: {stats['estimated_mallets_per_cycle']:.2f}"
        )

    def _simulate_cycles(self, cycles, mallets_per_run, cheese_mid, cheese_high):
        total_runs = 0
        total_hunts = 0
        last_cycle_runs = 0
        last_cycle_hunts = 0
        for _ in range(cycles):
            notoriety = [0] * len(self.GENRES)
            runs = 0
            hunts = 0
            while True:
                run_hunts = self._simulate_single_run(notoriety, cheese_mid, cheese_high)
                runs += 1
                hunts += run_hunts
                if all(value > 80 for value in notoriety):
                    total_runs += runs
                    total_hunts += hunts
                    last_cycle_runs = runs
                    last_cycle_hunts = hunts
                    notoriety = [0] * len(self.GENRES)
                    break
            # Cycle resets notoriety automatically after break.
        avg_runs = total_runs / cycles
        avg_hunts = total_hunts / cycles
        mallet_gain = avg_runs * mallets_per_run
        return {
            "avg_runs_per_cycle": avg_runs,
            "avg_hunts_per_cycle": avg_hunts,
            "estimated_mallets_per_cycle": mallet_gain,
            "last_cycle_runs": last_cycle_runs,
            "last_cycle_hunts": last_cycle_hunts,
        }

    def _simulate_single_run(self, notoriety, cheese_mid, cheese_high):
        pages = [0 for _ in self.GENRES]
        hunts = 0
        for idx in range(6):
            hunts_needed = random.choice((10, 20, 30)) if idx == 0 else 10
            hunts += hunts_needed
            genre_idx = random.randrange(len(self.GENRES))
            pages[genre_idx] += (hunts_needed // 10) * 250
        sequence = self._build_mallet_cheese_sequence(cheese_mid, cheese_high)
        hunts += len(sequence)
        weights = self._weights_from_page_counts(pages)
        cumulative = self._prepare_weight_cumulative(weights)
        for cheese_value in sequence:
            self._apply_hunt_step(notoriety, cheese_value, cumulative)
        return hunts

    def _build_mallet_cheese_sequence(self, cheese_mid, cheese_high):
        sequence = [50] * cheese_mid
        sequence.extend([125] * cheese_high)
        return sequence

    def _weights_from_page_counts(self, counts):
        total = sum(counts)
        if total <= 0:
            equal = 1 / len(self.GENRES)
            return {genre: equal for genre in self.GENRES}
        return {genre: counts[idx] / total for idx, genre in enumerate(self.GENRES)}


class SimulationTab(ttk.Frame):
    def __init__(self, parent, num_genres, iterations=40000):
        super().__init__(parent)
        self.num_genres = num_genres
        self.iterations = iterations
        self.avg_mallets_genre_var = tk.StringVar()
        self.avg_mallets_combo_var = tk.StringVar()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        info = (
            f"{self.iterations} simulations. Each run keeps rerolling until the same genre appears in five new areas,"
            " and separately until the exact length/genre combo reappears."
        )
        ttk.Label(self, text=f"Genre pool size: {self.num_genres}").grid(row=0, column=0, sticky="w", pady=(10, 2))
        ttk.Label(self, text=info, justify="left").grid(row=1, column=0, sticky="w")

        ttk.Separator(self, orient="horizontal").grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)

        ttk.Label(self, text="Avg. Mallets to match same Genre across five areas:").grid(row=3, column=0, sticky="w")
        ttk.Label(self, textvariable=self.avg_mallets_genre_var, font=("Arial", 12, "bold")).grid(row=4, column=0, sticky="w")

        ttk.Label(self, text="Avg. Mallets to match same Length + Genre across five areas:").grid(row=5, column=0, sticky="w", pady=(10, 0))
        ttk.Label(self, textvariable=self.avg_mallets_combo_var, font=("Arial", 12, "bold")).grid(row=6, column=0, sticky="w")

        ttk.Button(self, text="Run again", command=self.refresh).grid(row=7, column=0, pady=20, sticky="w")

    def refresh(self):
        stats = run_simulation(self.num_genres, self.iterations)
        self.avg_mallets_genre_var.set(f"{stats['avg_mallets_to_five_genre']:.2f} Mallets")
        self.avg_mallets_combo_var.set(f"{stats['avg_mallets_to_five_combo']:.2f} Mallets")


def build_app():
    root = tk.Tk()
    root.title("Conclusion Cliff Simulator")
    root.geometry("1080x780")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    overview = ttk.Frame(notebook)
    notebook.add(overview, text="Overview")

    description = (
        "Overview tab: Read this guide to understand each tool, key parameters, and how the tabs complement one another.\n\n"
        "Postscript Optimizer: Starting from your current cheese + page setup, automatically dial the chapter weights through multiple rounds. Each iteration generates systematic and randomized candidates, simulates each candidate a configurable number of times, blends the best performers, and reports the improved distribution and readiness probability. Parameters control dial range, number of iterations, candidates per iteration, and per-candidate simulation count.\n\n"
        "Postscript Simulator: Configure cheese allocations, chapter-page weights, and optional hunt extensions. Inspect a detailed single run plus a 30,000-run summary (average notoriety per genre and the All-Genre-≥80 probability). Clipboard helpers let you copy/paste page weights and notoriety values for quick scenario adjustments.\n\n"
        "Ratio Scaler: Paste any five-genre distribution and use a slider to uniformly scale the total pages while preserving the genre ratios. The scaled numbers/percentages update instantly for quick what-if checks.\n\n"
        "Contingency Start Fixer: Paste an existing chapter-page distribution, pick a genre + hunt length (adds a fixed page boost), then use the slider to target a final share for that genre while the other genres keep their relative ratios. Ideal for patching awkward starts or planning emergency boosts; results update live with counts and percentages.\n\n"
        "Dual Postscript Simulator: Define two setups that run back-to-back (Setup 2 builds on Setup 1's results). Both setups support auto-extend conditions, page-weight copy/paste, and notoriety editing. After showing the first-run and final-run outcomes (with auto-extend indicators), the tool performs 50,000 combined runs to summarize average notoriety, All-Genre-≥80 percentage, and auto-extend usage frequency for each setup.\n\n"
        "Dual Postscript (Pruned): Same dual-run workflow, but when Setup 2 begins it automatically treats any genre that ended Setup 1 above 90 notoriety (93 if extended) as having zero page weight, so Setup 2 focuses entirely on the remaining genres. Statistics and auto-extend logic respect this pruning.\n\n"
        "Just Farming Mallets: Approximate how many quick short-only runs and hunts it takes to push every genre beyond 80 notoriety when you ignore map mechanics. Enter how many mallets you typically earn per run to project mallets per cycle.\n\n"
        "5 Genres / 6 Genres: Each refresh runs 40,000 simulations to estimate how many Mallets it takes to roll the same genre (and separately the exact length/genre combo) across five new areas when drawing from 5- or 6-genre pools."
    )
    ttk.Label(overview, text=description, justify="left", padding=10, wraplength=660).pack(anchor="w")

    optimizer_tab = PostscriptOptimizer(notebook)
    notebook.add(optimizer_tab, text="Postscript Optimizer")
    cheese_tab = CheeseAllocator(notebook)
    notebook.add(cheese_tab, text="Postscript Simulator")
    scaler_tab = RatioScalerTab(notebook)
    notebook.add(scaler_tab, text="Ratio Scaler")
    fixer_tab = ContingencyStartFixer(notebook)
    notebook.add(fixer_tab, text="Contingency Start Fixer")
    dual_tab = DualPostscriptSimulator(notebook)
    notebook.add(dual_tab, text="Dual Postscript Simulator")
    dual_pruned_tab = DualPostscriptPrunedSimulator(notebook)
    notebook.add(dual_pruned_tab, text="Dual Postscript (Pruned)")
    mallet_tab = MalletFarmSimulator(notebook)
    notebook.add(mallet_tab, text="Just Farming Mallets")
    tab_5_genres = SimulationTab(notebook, num_genres=5)
    tab_6_genres = SimulationTab(notebook, num_genres=6)
    notebook.add(tab_5_genres, text="5 Genres")
    notebook.add(tab_6_genres, text="6 Genres")

    return root


if __name__ == "__main__":
    app = build_app()
    app.mainloop()
