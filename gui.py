import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from PIL import Image, ImageTk

from main import (BARCODE_TYPES, QR_CODE, generate_barcode, generate_qr, list_printers, make_sequence,
                  print_images, read_excel)

PREVIEW_SIZE = (400, 340)

BG = "#F4F5F7"
CARD = "#FFFFFF"
BORDER = "#E3E5E8"
TEXT = "#1F2328"
MUTED = "#6B7280"
ACCENT = "#2563EB"
ACCENT_HOVER = "#1D4ED8"
SECONDARY = "#EEF0F3"
SECONDARY_HOVER = "#E2E5E9"
ERROR = "#DC2626"
SUCCESS = "#16A34A"
FONT = "Segoe UI"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Barcode Generator")
        self.configure(bg=BG)
        self.resizable(False, False)

        self.image = None
        self.preview = None
        self.showing_example = False
        self.columns = {}
        self.values = []
        self.source = "excel"

        self._setup_style()
        self._build()
        self.entry.focus_set()

    def _setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "TCombobox",
            padding=6,
            fieldbackground=CARD,
            background=CARD,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            arrowcolor=MUTED,
        )
        style.map("TCombobox", fieldbackground=[("readonly", CARD)], bordercolor=[("focus", ACCENT)])
        # clam outlines the scale trough in the slider colour; the "default" theme's elements are flat.
        style.element_create("Flat.trough", "from", "default", "Horizontal.Scale.trough")
        style.element_create("Flat.slider", "from", "default", "Horizontal.Scale.slider")
        style.layout("Horizontal.TScale",
                     [("Flat.trough", {"sticky": "nswe", "children": [("Flat.slider", {"side": "left", "sticky": ""})]})])
        style.configure(
            "Horizontal.TScale",
            background=ACCENT,
            troughcolor=SECONDARY,
            borderwidth=0,
            troughrelief="flat",
            sliderrelief="flat",
            sliderlength=14,
            sliderthickness=14,
        )
        style.map("Horizontal.TScale", background=[("disabled", BORDER)])
        style.configure("TScrollbar", background=SECONDARY, troughcolor=CARD, bordercolor=CARD, arrowcolor=MUTED,
                        lightcolor=SECONDARY, darkcolor=SECONDARY)
        self.option_add("*TCombobox*Listbox.font", (FONT, 10))
        self.option_add("*TCombobox*Listbox.selectBackground", ACCENT)

    def _build(self):
        card = tk.Frame(self, bg=CARD, highlightthickness=1, highlightbackground=BORDER, padx=24, pady=24)
        card.pack(padx=24, pady=24)

        tk.Label(card, text="Barcode Generator", bg=CARD, fg=TEXT, font=(FONT, 16, "bold")).pack(anchor="w")
        tk.Label(card, text="Enter text or numbers, or import them from Excel.", bg=CARD, fg=MUTED,
                 font=(FONT, 10)).pack(anchor="w", pady=(2, 18))

        body = tk.Frame(card, bg=CARD)
        body.pack()
        left = tk.Frame(body, bg=CARD)
        left.pack(side="left", fill="y")
        tk.Frame(left, bg=CARD, width=300, height=0).pack()
        right = tk.Frame(body, bg=CARD)
        right.pack(side="left", fill="y", padx=(24, 0))

        self._build_controls(left)
        self._build_preview(right)
        self._show_source("excel")
        self.clear()

    def _build_controls(self, parent):
        self._label(parent, "Content")
        entry_box = tk.Frame(
            parent, bg=CARD, highlightthickness=1, highlightbackground=BORDER, highlightcolor=BORDER, padx=8
        )
        entry_box.pack(fill="x")
        self.data_var = tk.StringVar()
        self.entry = tk.Entry(
            entry_box,
            textvariable=self.data_var,
            font=(FONT, 11),
            bg=CARD,
            fg=TEXT,
            relief="flat",
            insertbackground=TEXT,
        )
        self.entry.pack(fill="x", ipady=7)
        self.entry.bind("<Return>", self.generate)
        self.entry.bind("<FocusIn>", lambda e: entry_box.configure(highlightbackground=ACCENT, highlightcolor=ACCENT))
        self.entry.bind("<FocusOut>", lambda e: entry_box.configure(highlightbackground=BORDER, highlightcolor=BORDER))

        self._label(parent, "Type", pady=(14, 4))
        self.type_var = tk.StringVar(value=QR_CODE)
        type_box = ttk.Combobox(
            parent,
            textvariable=self.type_var,
            values=list(BARCODE_TYPES),
            height=len(BARCODE_TYPES),
            state="readonly",
            font=(FONT, 10),
        )
        type_box.pack(fill="x")
        type_box.bind("<<ComboboxSelected>>", self._on_type_change)
        self.hint_label = tk.Label(parent, bg=CARD, fg=MUTED, font=(FONT, 9), anchor="w", justify="left",
                                   wraplength=300)
        self.hint_label.pack(fill="x", pady=(4, 0))

        self.size_var = tk.IntVar(value=5)
        self._slider(parent, "Size", self.size_var)
        self.height_var = tk.IntVar(value=5)
        self.height_slider = self._slider(parent, "Height", self.height_var)
        self.height_slider.state(["disabled"])

        self._button(parent, "Generate", self.generate, primary=True).pack(fill="x", pady=(16, 0))

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=18)

        tabs = tk.Frame(parent, bg=SECONDARY, padx=3, pady=3)
        tabs.pack(fill="x")
        self.source_tabs = {}
        for source, text in (("excel", "From Excel"), ("sequence", "Number sequence")):
            tab = tk.Label(tabs, text=text, font=(FONT, 9), cursor="hand2", pady=4)
            tab.pack(side="left", expand=True, fill="x")
            tab.bind("<Button-1>", lambda e, source=source: self._show_source(source))
            self.source_tabs[source] = tab

        panel_holder = tk.Frame(parent, bg=CARD)
        panel_holder.pack(fill="x")
        self.source_panels = {"excel": tk.Frame(panel_holder, bg=CARD), "sequence": tk.Frame(panel_holder, bg=CARD)}
        self._build_excel_panel(self.source_panels["excel"])
        self._build_sequence_panel(self.source_panels["sequence"])

        list_box = tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT)
        list_box.pack(fill="both", expand=True, pady=(8, 0))
        scrollbar = ttk.Scrollbar(list_box, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        self.listbox = tk.Listbox(
            list_box,
            font=(FONT, 10),
            bg=CARD,
            fg=TEXT,
            relief="flat",
            bd=0,
            highlightthickness=0,
            selectbackground=ACCENT,
            selectforeground="#FFFFFF",
            activestyle="none",
            exportselection=False,
            selectmode="extended",  # click, Shift+click for a range, Ctrl+click to add or remove one
            height=6,
            yscrollcommand=scrollbar.set,
        )
        self.listbox.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=4)
        scrollbar.configure(command=self.listbox.yview)
        self.listbox.bind("<<ListboxSelect>>", self._on_value_select)
        self.listbox.bind("<Button-1>", self._on_list_click, add="+")
        # match the physical A key (keycode 65) so Ctrl+A also works with a Greek keyboard layout
        self.listbox.bind("<Control-KeyPress>", lambda e: self._select_all_values() if e.keycode == 65 else None)

        batch_actions = tk.Frame(parent, bg=CARD)
        batch_actions.pack(fill="x", pady=(8, 0))
        self.save_all_button = self._button(batch_actions, "Save all as PNG…", self.save_all)
        self.save_all_button.pack(side="left", expand=True, fill="x", padx=(0, 6))
        self.print_all_button = self._button(batch_actions, "Print all…",
                                             lambda: self.open_print_dialog(self._chosen_values()))
        self.print_all_button.pack(side="left", expand=True, fill="x", padx=(6, 0))

    def _build_excel_panel(self, parent):
        file_row = tk.Frame(parent, bg=CARD)
        file_row.pack(fill="x", pady=(8, 6))
        self.file_label = tk.Label(file_row, text="No file loaded", bg=CARD, fg=MUTED, font=(FONT, 9), anchor="w")
        self.file_label.pack(side="left", fill="x", expand=True)
        self._button(file_row, "Import Excel…", self.import_excel, pady=3).pack(side="right")

        column_row = tk.Frame(parent, bg=CARD)
        column_row.pack(fill="x")
        self.column_var = tk.StringVar()
        self.column_box = ttk.Combobox(column_row, textvariable=self.column_var, state="disabled",
                                       font=(FONT, 10), width=14)
        self.column_box.pack(side="left", fill="x", expand=True)
        self.column_box.bind("<<ComboboxSelected>>", lambda e: self._load_values())
        self.header_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            column_row,
            text="First row is header",
            variable=self.header_var,
            command=self._load_values,
            bg=CARD,
            fg=TEXT,
            activebackground=CARD,
            selectcolor=CARD,
            font=(FONT, 9),
            bd=0,
            highlightthickness=0,
        ).pack(side="left", padx=(8, 0))

    def _build_sequence_panel(self, parent):
        grid = tk.Frame(parent, bg=CARD)
        grid.pack(fill="x", pady=(8, 0))
        self.sequence_vars = {}
        fields = [("From", "1"), ("To", "6"), ("Step", "1"), ("Prefix", ""), ("Suffix", ""), ("Min digits", "0")]
        for i, (name, default) in enumerate(fields):
            grid.columnconfigure(i % 3, weight=1, uniform="sequence")
            cell = tk.Frame(grid, bg=CARD)
            cell.grid(row=i // 3, column=i % 3, sticky="ew", padx=(0 if i % 3 == 0 else 8, 0), pady=(0, 6))
            tk.Label(cell, text=name, bg=CARD, fg=MUTED, font=(FONT, 8)).pack(anchor="w")
            var = tk.StringVar(value=default)
            self._small_entry(cell, var).pack(fill="x")
            var.trace_add("write", lambda *args: self._load_sequence())
            self.sequence_vars[name] = var

    def _small_entry(self, parent, variable, width=6):
        box = tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground=BORDER, highlightcolor=BORDER, padx=4)
        entry = tk.Entry(box, textvariable=variable, font=(FONT, 10), bg=CARD, fg=TEXT, relief="flat", width=width,
                         insertbackground=TEXT, disabledbackground=BG)
        entry.pack(fill="x", ipady=3)
        box.entry = entry
        return box

    def _build_preview(self, parent):
        preview_box = tk.Frame(
            parent,
            bg=BG,
            width=PREVIEW_SIZE[0] + 20,
            height=PREVIEW_SIZE[1] + 20,
            highlightthickness=1,
            highlightbackground=BORDER,
        )
        preview_box.pack()
        preview_box.pack_propagate(False)
        self.preview_label = tk.Label(preview_box, bg=BG, fg=MUTED, font=(FONT, 10))
        self.preview_label.pack(expand=True)

        self.size_label = tk.Label(parent, bg=CARD, fg=MUTED, font=(FONT, 9), anchor="e")
        self.size_label.pack(fill="x", pady=(6, 0))
        self.status = tk.Label(parent, bg=CARD, font=(FONT, 9), anchor="w", justify="left",
                               wraplength=PREVIEW_SIZE[0])
        self.status.pack(fill="x", pady=(2, 0))

        actions = tk.Frame(parent, bg=CARD)
        actions.pack(fill="x", side="bottom")
        self.save_button = self._button(actions, "Save image", self.save)
        self.save_button.pack(side="left", expand=True, fill="x", padx=(0, 6))
        self.print_button = self._button(actions, "Print…", lambda: self.open_print_dialog([self.image_data]))
        self.print_button.pack(side="left", expand=True, fill="x", padx=6)
        self._button(actions, "Clear", self.clear).pack(side="left", expand=True, fill="x", padx=(6, 0))

    def _label(self, parent, text, pady=(0, 4)):
        tk.Label(parent, text=text, bg=CARD, fg=TEXT, font=(FONT, 9, "bold")).pack(anchor="w", pady=pady)

    def _slider(self, parent, text, variable):
        header = tk.Frame(parent, bg=CARD)
        header.pack(fill="x", pady=(14, 2))
        tk.Label(header, text=text, bg=CARD, fg=TEXT, font=(FONT, 9, "bold")).pack(side="left")
        tk.Label(header, textvariable=variable, bg=CARD, fg=MUTED, font=(FONT, 9)).pack(side="right")

        def on_move(value):
            if variable.get() != round(float(value)):
                variable.set(round(float(value)))
                if self.image is not None:
                    self.generate()
                elif self.showing_example:
                    self._show_example()

        slider = ttk.Scale(parent, from_=1, to=10, value=variable.get(), command=on_move)
        slider.pack(fill="x")
        return slider

    def _button(self, parent, text, command, primary=False, pady=8):
        bg, hover, fg = (ACCENT, ACCENT_HOVER, "#FFFFFF") if primary else (SECONDARY, SECONDARY_HOVER, TEXT)
        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=hover,
            activeforeground=fg,
            disabledforeground="#B0B5BD",
            font=(FONT, 10, "bold" if primary else "normal"),
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=12,
            pady=pady,
        )
        button.bind("<Enter>", lambda e: button["state"] == "normal" and button.configure(bg=hover))
        button.bind("<Leave>", lambda e: button.configure(bg=bg))
        return button

    def _make_image(self, data, for_print=False):
        """for_print renders a small exact image; print_images enlarges it by a whole number to fit the label."""
        size = 2 if for_print else self.size_var.get()
        barcode_type = self.type_var.get()
        if barcode_type == QR_CODE:
            return generate_qr(data, box_size=1 if for_print else 2 * size).get_image()

        scale = 2 * size if BARCODE_TYPES[barcode_type].layout == "matrix" and not for_print else size
        return generate_barcode(data, barcode_type, scale=scale, bar_height=self.height_var.get() * 10 * size)

    def _error_message(self, error):
        if self.type_var.get() == QR_CODE:
            return "The text is too long for a QR code."
        return str(error)

    def _show_preview(self, image, caption=""):
        preview = image.convert("RGB")
        preview.thumbnail(PREVIEW_SIZE, Image.LANCZOS)
        self.preview = ImageTk.PhotoImage(preview)
        self.preview_label.configure(image=self.preview, text=caption, compound="bottom")
        self.size_label.configure(text=f"{image.width} × {image.height} px")

    def _show_example(self):
        self._reset_preview()
        example = BARCODE_TYPES[self.type_var.get()].example
        self._show_preview(self._make_image(example), caption=f"Example: {example}")
        self.showing_example = True

    def generate(self, event=None):
        data = self.data_var.get().strip()
        barcode_type = self.type_var.get()
        self._reset_preview()

        if not data:
            self._show_error("Please enter some text or numbers.")
            return

        try:
            image = self._make_image(data)
        except ValueError as e:
            self._show_error(self._error_message(e))
            return

        self.image = image
        self.image_data = data
        self.image_name = _file_name(data)
        self._show_preview(image)
        self.save_button.configure(state="normal")
        self.print_button.configure(state="normal")
        self._show_status(f"{barcode_type} generated.", SUCCESS)

    def save(self):
        if self.image is None:
            return

        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Save image",
            defaultextension=".png",
            initialfile=f"{self.image_name}.png",
            filetypes=[("PNG image", "*.png")],
        )
        if not file_path:
            return

        try:
            self.image.save(file_path)
        except OSError as e:
            self._show_error(f"Could not save the image: {e.strerror or e}")
            return

        self._show_status(f"Saved to {file_path}", SUCCESS)

    def import_excel(self):
        file_path = filedialog.askopenfilename(
            parent=self,
            title="Import Excel",
            filetypes=[("Excel workbook", "*.xlsx *.xlsm")],
        )
        if not file_path:
            return

        try:
            columns = read_excel(file_path)
        except Exception as e:
            self._show_error(f"Could not read the Excel file: {e}")
            return

        if not any(any(column) for column in columns.values()):
            self._show_error("The first sheet of this Excel file is empty.")
            return

        self.columns = {
            f"{letter} · {cells[0]}" if cells[0] else letter: cells for letter, cells in columns.items() if any(cells)
        }
        self.file_label.configure(text=os.path.basename(file_path), fg=TEXT)
        self.column_box.configure(values=list(self.columns), state="readonly")
        self.column_box.current(0)
        self._load_values()

    def _load_values(self):
        cells = self.columns.get(self.column_var.get())
        if cells is None:
            return

        if self.header_var.get():
            cells = cells[1:]
        self._set_values([cell for cell in cells if cell])
        self._show_status(f"{len(self.values)} values loaded. Click one to preview it.", MUTED)

    def _load_sequence(self):
        if self.source != "sequence":
            return

        fields = {name: var.get().strip() for name, var in self.sequence_vars.items()}
        try:
            start, end = int(fields["From"]), int(fields["To"])
            step, digits = int(fields["Step"] or 1), int(fields["Min digits"] or 0)
        except ValueError:
            self._set_values([])
            self._show_status("From, To, Step and Min digits must be whole numbers.", ERROR)
            return

        try:
            if not 0 <= digits <= 20:
                raise ValueError("Min digits must be between 0 and 20.")
            values = make_sequence(start, end, step, fields["Prefix"], fields["Suffix"], digits)
        except ValueError as e:
            self._set_values([])
            self._show_status(str(e), ERROR)
            return

        self._set_values(values)
        self._show_status(f"{len(values)} values: {values[0]} … {values[-1]}. Click one to preview it.", MUTED)

    def _set_values(self, values):
        self.values = values
        self.listbox.delete(0, "end")
        for value in values:
            self.listbox.insert("end", value)
        self._update_batch_buttons()

    def _chosen_values(self):
        """The selected values, or every value when nothing is selected."""
        selection = self.listbox.curselection()
        return [self.values[i] for i in selection] if selection else self.values

    def _update_batch_buttons(self):
        count = len(self.listbox.curselection())
        state = "normal" if self.values else "disabled"
        self.save_all_button.configure(state=state, text=f"Save {count} as PNG…" if count else "Save all as PNG…")
        self.print_all_button.configure(state=state, text=f"Print {count}…" if count else "Print all…")

    def _on_list_click(self, event):
        # runs before the Listbox class binding, so remember which row was clicked for the preview
        self.clicked_index = self.listbox.nearest(event.y)
        self.listbox.focus_set()

    def _select_all_values(self, event=None):
        self.listbox.selection_set(0, "end")
        self._update_batch_buttons()
        self._show_status(f"All {len(self.values)} values selected.", MUTED)
        return "break"

    def _show_source(self, source):
        self.source = source
        for name, tab in self.source_tabs.items():
            selected = name == source
            tab.configure(bg=CARD if selected else SECONDARY, fg=TEXT if selected else MUTED,
                          font=(FONT, 9, "bold" if selected else "normal"))
            self.source_panels[name].pack_forget()
        self.source_panels[source].pack(fill="x")

        if source == "sequence":
            self._load_sequence()
        elif self.columns:
            self._load_values()
        else:
            self._set_values([])
            self._show_status("", MUTED)

    def _on_value_select(self, event=None):
        self._update_batch_buttons()
        selection = self.listbox.curselection()
        if not selection:
            return

        # preview the row just clicked if it is selected, otherwise the first selected one
        clicked = getattr(self, "clicked_index", None)
        index = clicked if clicked in selection else selection[0]
        self.data_var.set(self.values[index])
        self.generate()
        if len(selection) > 1 and self.image is not None:
            self._show_status(f"{len(selection)} of {len(self.values)} selected. Showing {self.values[index]}.", MUTED)

    def _on_type_change(self, event=None):
        kind = BARCODE_TYPES[self.type_var.get()]
        self.height_slider.state(["!disabled" if kind.layout == "linear" else "disabled"])
        self.hint_label.configure(text=kind.hint)
        if self.data_var.get().strip():
            self.generate()
        else:
            self._show_status("", MUTED)
            self._show_example()

    def save_all(self):
        folder = filedialog.askdirectory(parent=self, title="Choose a folder for the images")
        if not folder:
            return

        values = self._chosen_values()
        saved, skipped, used_names = 0, [], set()
        for i, value in enumerate(values, start=1):
            self._show_status(f"Saving {i} of {len(values)}…", MUTED)
            self.update_idletasks()

            try:
                image = self._make_image(value)
            except ValueError as e:
                skipped.append(f"{value}: {self._error_message(e)}")
                continue

            name = _file_name(value)
            unique_name, n = name, 2
            while unique_name.lower() in used_names:
                unique_name, n = f"{name}_{n}", n + 1
            used_names.add(unique_name.lower())

            try:
                image.save(os.path.join(folder, f"{unique_name}.png"))
            except OSError as e:
                self._show_error(f"Could not save to {folder}: {e.strerror or e}")
                return
            saved += 1

        if skipped:
            self._show_status(f"Saved {saved} of {len(values)} images. {len(skipped)} skipped.", ERROR)
            self._report_skipped(skipped)
        else:
            self._show_status(f"Saved {saved} images to {folder}", SUCCESS)

    def _report_skipped(self, skipped):
        details = "\n".join(skipped[:15]) + (f"\n…and {len(skipped) - 15} more" if len(skipped) > 15 else "")
        messagebox.showwarning("Some values were skipped", details, parent=self)

    def open_print_dialog(self, values):
        try:
            printers, default = list_printers()
        except Exception as e:
            self._show_error(f"Could not list the printers: {e}")
            return
        if not printers:
            self._show_error("No printers are installed in Windows.")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Print")
        dialog.configure(bg=CARD)
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        body = tk.Frame(dialog, bg=CARD, padx=24, pady=20)
        body.pack()

        title = f"Print {len(values)} barcodes" if len(values) > 1 else f"Print \u201c{values[0]}\u201d"
        tk.Label(body, text=title, bg=CARD, fg=TEXT, font=(FONT, 13, "bold")).pack(anchor="w")
        tk.Label(body, text=f"Type: {self.type_var.get()}", bg=CARD, fg=MUTED, font=(FONT, 9)).pack(
            anchor="w", pady=(2, 14))

        self._label(body, "Printer")
        printer_var = tk.StringVar(value=default if default in printers else printers[0])
        ttk.Combobox(body, textvariable=printer_var, values=printers, state="readonly", font=(FONT, 10),
                     width=36).pack(fill="x")

        self._label(body, "Layout", pady=(14, 4))
        layout_var = tk.StringVar(value="single")
        columns_var, rows_var, copies_var = tk.StringVar(value="3"), tk.StringVar(value="8"), tk.StringVar(value="1")
        grid_boxes = []

        def update_layout():
            state = "normal" if layout_var.get() == "grid" else "disabled"
            for box in grid_boxes:
                box.entry.configure(state=state)

        for value, text in (("single", "One per page or label (label printers)"),
                            ("grid", "Several per page (sticker sheets)")):
            tk.Radiobutton(body, text=text, variable=layout_var, value=value, command=update_layout, bg=CARD, fg=TEXT,
                           activebackground=CARD, selectcolor=CARD, font=(FONT, 9), anchor="w", bd=0,
                           highlightthickness=0).pack(fill="x", pady=1)

        grid_row = tk.Frame(body, bg=CARD)
        grid_row.pack(fill="x", padx=(22, 0), pady=(4, 0))
        for text, var in (("Columns", columns_var), ("Rows", rows_var)):
            tk.Label(grid_row, text=text, bg=CARD, fg=MUTED, font=(FONT, 9)).pack(side="left", padx=(0, 4))
            box = self._small_entry(grid_row, var, width=4)
            box.pack(side="left", padx=(0, 12))
            grid_boxes.append(box)
        update_layout()

        copies_row = tk.Frame(body, bg=CARD)
        copies_row.pack(fill="x", pady=(14, 0))
        tk.Label(copies_row, text="Copies of each", bg=CARD, fg=TEXT, font=(FONT, 9, "bold")).pack(side="left")
        self._small_entry(copies_row, copies_var, width=4).pack(side="left", padx=(8, 0))

        tk.Label(body, text="The page or label size comes from the printer's settings in Windows.", bg=CARD,
                 fg=MUTED, font=(FONT, 8)).pack(anchor="w", pady=(14, 0))
        error_label = tk.Label(body, bg=CARD, fg=ERROR, font=(FONT, 9), anchor="w")
        error_label.pack(fill="x")

        def submit():
            try:
                columns, rows = (int(columns_var.get()), int(rows_var.get())) if layout_var.get() == "grid" else (1, 1)
                copies = int(copies_var.get())
                if not (1 <= columns <= 20 and 1 <= rows <= 40 and 1 <= copies <= 100):
                    raise ValueError
            except ValueError:
                error_label.configure(text="Use whole numbers: columns 1-20, rows 1-40, copies 1-100.")
                return
            dialog.destroy()
            self._print(values, printer_var.get(), columns, rows, copies)

        actions = tk.Frame(body, bg=CARD)
        actions.pack(fill="x", pady=(10, 0))
        self._button(actions, "Cancel", dialog.destroy).pack(side="left", expand=True, fill="x", padx=(0, 6))
        self._button(actions, "Print", submit, primary=True).pack(side="left", expand=True, fill="x", padx=(6, 0))
        dialog.bind("<Return>", lambda e: submit())
        dialog.bind("<Escape>", lambda e: dialog.destroy())
        self.print_dialog = dialog

    def _print(self, values, printer, columns, rows, copies):
        images, skipped = [], []
        for value in values:
            try:
                images.extend([self._make_image(value, for_print=True)] * copies)
            except ValueError as e:
                skipped.append(f"{value}: {self._error_message(e)}")

        if not images:
            self._show_error(f"Nothing to print. {skipped[0]}")
            return

        self._show_status(f"Sending {len(images)} barcodes to {printer}…", MUTED)
        self.update_idletasks()
        try:
            print_images(images, printer, columns, rows, title=f"Barcodes ({self.type_var.get()})")
        except Exception as e:
            self._show_error(f"Printing failed: {e}")
            return

        pages = -(-len(images) // (columns * rows))
        message = (f"Sent {len(images)} barcode{'s' if len(images) > 1 else ''} on {pages} "
                   f"page{'s' if pages > 1 else ''} to {printer}.")
        if skipped:
            self._show_status(f"{message} {len(skipped)} skipped.", ERROR)
            self._report_skipped(skipped)
        else:
            self._show_status(message, SUCCESS)

    def clear(self):
        self.data_var.set("")
        self.listbox.selection_clear(0, "end")
        self._update_batch_buttons()
        self._on_type_change()
        self.entry.focus_set()

    def _reset_preview(self):
        self.image = None
        self.preview = None
        self.showing_example = False
        self.preview_label.configure(image="", text="Your code will appear here")
        self.size_label.configure(text="")
        self.save_button.configure(state="disabled")
        self.print_button.configure(state="disabled")

    def _show_error(self, message):
        self._show_status(message, ERROR)
        self.entry.focus_set()

    def _show_status(self, message, color):
        self.status.configure(text=message, fg=color)


def _file_name(value):
    return re.sub(r'[\\/:*?"<>|\s]+', "_", value).strip("._")[:80] or "code"


if __name__ == "__main__":
    App().mainloop()
