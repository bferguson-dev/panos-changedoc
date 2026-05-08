from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from panos_changedoc.commands import run_diff
from panos_changedoc.generate import (
    GenerateValidationError,
    build_from_spec,
    default_spec,
    list_change_templates,
    write_outputs,
)


class ChangeRow:
    def __init__(self, parent: ttk.Frame, key: str, description: str) -> None:
        self.key = key
        self.before_var = tk.BooleanVar(value=False)
        self.after_var = tk.BooleanVar(value=False)

        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=key, width=28).pack(side="left")
        ttk.Checkbutton(row, text="Before", variable=self.before_var).pack(
            side="left"
        )
        ttk.Checkbutton(row, text="After", variable=self.after_var).pack(
            side="left"
        )
        ttk.Label(row, text=description, width=70).pack(side="left", padx=8)


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("PAN-OS ChangeDoc")
        self.root.geometry("1200x720")

        self.before_path = tk.StringVar(value="sample_configs/before.xml")
        self.after_path = tk.StringVar(value="sample_configs/after.xml")
        self.manifest_path = tk.StringVar(value="sample_configs/manifest.json")
        self.diff_json_path = tk.StringVar(value="reports/change-summary.json")
        self.diff_md_path = tk.StringVar(value="reports/change-summary.md")

        self.test_mode = tk.BooleanVar(value=True)
        self.rows: dict[str, ChangeRow] = {}

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True)

        self._build_generate_tab(notebook)
        self._build_diff_tab(notebook)

    def _build_generate_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Generate")

        controls = ttk.Frame(tab)
        controls.pack(fill="x", padx=8, pady=8)

        ttk.Label(controls, text="Before XML:").grid(row=0, column=0, sticky="w")
        ttk.Entry(controls, textvariable=self.before_path, width=80).grid(
            row=0, column=1, sticky="we", padx=6
        )
        ttk.Button(
            controls,
            text="Browse",
            command=lambda: self._browse_save(self.before_path),
        ).grid(row=0, column=2)

        ttk.Label(controls, text="After XML:").grid(row=1, column=0, sticky="w")
        ttk.Entry(controls, textvariable=self.after_path, width=80).grid(
            row=1, column=1, sticky="we", padx=6
        )
        ttk.Button(
            controls,
            text="Browse",
            command=lambda: self._browse_save(self.after_path),
        ).grid(row=1, column=2)

        ttk.Label(controls, text="Manifest:").grid(row=2, column=0, sticky="w")
        ttk.Entry(controls, textvariable=self.manifest_path, width=80).grid(
            row=2, column=1, sticky="we", padx=6
        )
        ttk.Button(
            controls,
            text="Browse",
            command=lambda: self._browse_save(self.manifest_path),
        ).grid(row=2, column=2)
        controls.columnconfigure(1, weight=1)

        buttons = ttk.Frame(tab)
        buttons.pack(fill="x", padx=8, pady=6)
        ttk.Button(
            buttons,
            text="Load Default Selections",
            command=self._load_defaults,
        ).pack(side="left")
        ttk.Button(
            buttons,
            text="Generate Before/After",
            command=self._generate,
        ).pack(side="left", padx=8)

        grid_wrap = ttk.Frame(tab)
        grid_wrap.pack(fill="both", expand=True, padx=8, pady=8)

        canvas = tk.Canvas(grid_wrap)
        scroll = ttk.Scrollbar(
            grid_wrap, orient="vertical", command=canvas.yview
        )
        self.changes_frame = ttk.Frame(canvas)
        self.changes_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self.changes_frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        for item in list_change_templates():
            row = ChangeRow(
                self.changes_frame,
                key=item["key"],
                description=item["description"],
            )
            self.rows[item["key"]] = row

        validation_wrap = ttk.LabelFrame(tab, text="Validation Results")
        validation_wrap.pack(fill="both", expand=False, padx=8, pady=6)
        self.validation_text = tk.Text(validation_wrap, height=8, wrap="word")
        self.validation_text.pack(fill="both", expand=True)
        self._set_validation(
            "Validation status will appear here. "
            "Generation fails on any logical issue."
        )

    def _build_diff_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Diff")

        frm = ttk.Frame(tab)
        frm.pack(fill="x", padx=8, pady=8)

        ttk.Checkbutton(
            frm,
            text="Test mode (generate before diff)",
            variable=self.test_mode,
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=4)

        ttk.Label(frm, text="Before XML:").grid(row=1, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.before_path, width=80).grid(
            row=1, column=1, padx=6, sticky="we"
        )
        ttk.Button(
            frm,
            text="Browse",
            command=lambda: self._browse_open(self.before_path),
        ).grid(row=1, column=2)

        ttk.Label(frm, text="After XML:").grid(row=2, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.after_path, width=80).grid(
            row=2, column=1, padx=6, sticky="we"
        )
        ttk.Button(
            frm,
            text="Browse",
            command=lambda: self._browse_open(self.after_path),
        ).grid(row=2, column=2)

        ttk.Label(frm, text="JSON out:").grid(row=3, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.diff_json_path, width=80).grid(
            row=3, column=1, padx=6, sticky="we"
        )
        ttk.Button(
            frm,
            text="Browse",
            command=lambda: self._browse_save(self.diff_json_path),
        ).grid(row=3, column=2)

        ttk.Label(frm, text="Markdown out:").grid(row=4, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.diff_md_path, width=80).grid(
            row=4, column=1, padx=6, sticky="we"
        )
        ttk.Button(
            frm,
            text="Browse",
            command=lambda: self._browse_save(self.diff_md_path),
        ).grid(row=4, column=2)

        frm.columnconfigure(1, weight=1)

        ttk.Button(tab, text="Run Diff", command=self._run_diff).pack(
            anchor="w", padx=8, pady=8
        )

    def _browse_open(self, var: tk.StringVar) -> None:
        p = filedialog.askopenfilename()
        if p:
            var.set(p)

    def _browse_save(self, var: tk.StringVar) -> None:
        p = filedialog.asksaveasfilename()
        if p:
            var.set(p)

    def _load_defaults(self) -> None:
        spec = default_spec()
        for row in self.rows.values():
            row.before_var.set(False)
            row.after_var.set(False)
        for item in spec["settings"]:
            row = self.rows[item["key"]]
            row.before_var.set(item["before"])
            row.after_var.set(item["after"])

    def _spec_from_ui(self) -> dict:
        settings = []
        for key, row in self.rows.items():
            if row.before_var.get() or row.after_var.get():
                settings.append(
                    {
                        "key": key,
                        "before": row.before_var.get(),
                        "after": row.after_var.get(),
                    }
                )

        return {
            "version": 1,
            "panos_version": "12.1",
            "profile": "standalone_vsys1",
            "settings": settings,
        }

    def _set_validation(self, text: str) -> None:
        self.validation_text.configure(state="normal")
        self.validation_text.delete("1.0", "end")
        self.validation_text.insert("1.0", text.strip() + "\n")
        self.validation_text.configure(state="disabled")

    def _generate(self) -> bool:
        spec = self._spec_from_ui()
        try:
            before_xml, after_xml, manifest = build_from_spec(spec)
            write_outputs(
                before_xml=before_xml,
                after_xml=after_xml,
                manifest=manifest,
                before_out=self.before_path.get(),
                after_out=self.after_path.get(),
                manifest_out=self.manifest_path.get(),
            )
            messagebox.showinfo(
                "Generate", "Generated before/after XML and manifest successfully."
            )
            self._set_validation("Validation passed. Files generated successfully.")
            return True
        except GenerateValidationError as exc:
            lines = ["Validation failed:"]
            for issue in exc.issues:
                lines.append(f"- {issue.message}")
                lines.append(f"  Fix: {issue.solution}")
            self._set_validation("\n".join(lines))
            messagebox.showerror("Generate Failed", str(exc))
            return False
        except Exception as exc:
            self._set_validation(f"Unexpected error:\n{exc}")
            messagebox.showerror("Generate Failed", str(exc))
            return False

    def _run_diff(self) -> None:
        if self.test_mode.get():
            if not self._generate():
                return
        rc = run_diff(
            before=self.before_path.get(),
            after=self.after_path.get(),
            json_out=self.diff_json_path.get(),
            markdown_out=self.diff_md_path.get(),
            manifest=None,
            verbose=False,
            quiet=True,
        )
        if rc == 0:
            messagebox.showinfo(
                "Diff", "Diff completed. JSON/Markdown reports were written."
            )
        else:
            messagebox.showerror(
                "Diff Failed", f"Diff command failed with exit code {rc}."
            )


def launch_gui() -> int:
    root = tk.Tk()
    app = App(root)
    app._load_defaults()
    root.mainloop()
    return 0
