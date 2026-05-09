from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import queue
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any, cast
from zipfile import ZipFile

from panos_changedoc.gui_summary import build_gui_diff_results


class ChangeRow:
    def __init__(self, parent: ttk.Frame, key: str, description: str) -> None:
        self.key = key
        self.before_var = tk.BooleanVar(value=False)
        self.after_var = tk.BooleanVar(value=False)

        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=key, width=28).pack(side="left")
        ttk.Checkbutton(row, text="Before", variable=self.before_var).pack(side="left")
        ttk.Checkbutton(row, text="After", variable=self.after_var).pack(side="left")
        ttk.Label(row, text=description, width=70).pack(side="left", padx=8)


@dataclass(frozen=True)
class ProgressUpdate:
    overall_step: int
    current_percent: int
    text: str


@dataclass(frozen=True)
class DiffDone:
    text: str


@dataclass(frozen=True)
class DiffFailed:
    text: str


type ProgressEvent = ProgressUpdate | DiffDone | DiffFailed


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
        self.evidence_bundle_path = tk.StringVar(value="evidence/change-bundle.zip")

        self.test_mode = tk.BooleanVar(value=True)
        self.create_evidence_bundle = tk.BooleanVar(value=False)
        self.rows: dict[str, ChangeRow] = {}
        self.diff_events: queue.Queue[ProgressEvent] = queue.Queue()
        self.diff_running = False
        self.generator_loaded = False
        self.last_diff_results: str | None = None
        self.progress_value = tk.IntVar(value=0)
        self.progress_status = tk.StringVar(value="Idle")
        self.current_progress_value = tk.IntVar(value=0)
        self.current_progress_status = tk.StringVar(value="Idle")

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True)

        self._build_diff_tab(notebook)
        self._build_generate_tab(notebook)
        notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _build_generate_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Test Generator")

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
        scroll = ttk.Scrollbar(grid_wrap, orient="vertical", command=canvas.yview)
        self.changes_frame = ttk.Frame(canvas)
        self.changes_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self.changes_frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.generator_placeholder = ttk.Label(
            self.changes_frame,
            text="Generator templates will load when this tab is opened.",
        )
        self.generator_placeholder.pack(anchor="w", padx=8, pady=8)

        validation_wrap = ttk.LabelFrame(tab, text="Validation Results")
        validation_wrap.pack(fill="both", expand=False, padx=8, pady=6)
        self.validation_text = tk.Text(validation_wrap, height=8, wrap="word")
        self.validation_text.pack(fill="both", expand=True)
        self._set_validation(
            "Validation status will appear here. Generation fails on any logical issue."
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

        ttk.Checkbutton(
            frm,
            text="Create evidence bundle",
            variable=self.create_evidence_bundle,
        ).grid(row=5, column=0, sticky="w", pady=4)
        ttk.Entry(frm, textvariable=self.evidence_bundle_path, width=80).grid(
            row=5, column=1, padx=6, sticky="we"
        )
        ttk.Button(
            frm,
            text="Browse",
            command=lambda: self._browse_zip(self.evidence_bundle_path),
        ).grid(row=5, column=2)

        frm.columnconfigure(1, weight=1)

        actions = ttk.Frame(tab)
        actions.pack(fill="x", padx=8, pady=8)
        self.run_diff_button = ttk.Button(
            actions, text="Run Diff", command=self._run_diff
        )
        self.run_diff_button.pack(side="left")
        self.view_results_button = ttk.Button(
            actions,
            text="View Results",
            command=self._view_last_results,
            state="disabled",
        )
        self.view_results_button.pack(side="left", padx=8)

        progress_wrap = ttk.Frame(tab)
        progress_wrap.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Label(progress_wrap, textvariable=self.current_progress_status).pack(
            anchor="w"
        )
        self.current_task_progress = ttk.Progressbar(
            progress_wrap,
            maximum=100,
            variable=self.current_progress_value,
            mode="determinate",
        )
        self.current_task_progress.pack(fill="x", pady=(0, 6))
        ttk.Label(progress_wrap, textvariable=self.progress_status).pack(anchor="w")
        self.diff_progress = ttk.Progressbar(
            progress_wrap,
            maximum=6,
            variable=self.progress_value,
            mode="determinate",
        )
        self.diff_progress.pack(fill="x")

        diff_wrap = ttk.LabelFrame(tab, text="Diff Results")
        diff_wrap.pack(fill="both", expand=True, padx=8, pady=8)
        text_wrap = ttk.Frame(diff_wrap)
        text_wrap.pack(fill="both", expand=True)
        self.diff_text = tk.Text(text_wrap, height=18, wrap="word")
        yscroll = ttk.Scrollbar(
            text_wrap, orient="vertical", command=self.diff_text.yview
        )
        self.diff_text.configure(yscrollcommand=yscroll.set)
        self.diff_text.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")
        self._set_diff_results("Diff summary will appear here after clicking Run Diff.")

    def _browse_open(self, var: tk.StringVar) -> None:
        p = filedialog.askopenfilename()
        if p:
            var.set(p)

    def _on_tab_changed(self, event: tk.Event) -> None:
        notebook = cast(ttk.Notebook, event.widget)
        selected_tab = notebook.tab(notebook.select(), "text")
        if selected_tab == "Test Generator":
            # Keep the initial GUI light by loading the generator catalog only
            # when the user opens the generator tab.
            self._ensure_generator_loaded()

    def _ensure_generator_loaded(self) -> None:
        if self.generator_loaded:
            return
        from panos_changedoc.generate import list_change_templates

        # Build the generator rows on demand so startup stays responsive.
        self.generator_placeholder.destroy()
        for item in list_change_templates():
            row = ChangeRow(
                self.changes_frame,
                key=item["key"],
                description=item["description"],
            )
            self.rows[item["key"]] = row
        self.generator_loaded = True
        self._load_defaults()

    def _browse_save(self, var: tk.StringVar) -> None:
        p = filedialog.asksaveasfilename()
        if p:
            var.set(p)

    def _browse_directory(self, var: tk.StringVar) -> None:
        p = filedialog.askdirectory()
        if p:
            var.set(p)

    def _browse_zip(self, var: tk.StringVar) -> None:
        # Evidence bundles are delivered as zip archives, so use a save dialog
        # that makes the archive filename explicit.
        p = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("Zip archive", "*.zip"), ("All files", "*.*")],
        )
        if p:
            var.set(p)

    def _load_defaults(self) -> None:
        if not self.generator_loaded:
            self._ensure_generator_loaded()
            return
        from panos_changedoc.generate import default_spec

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

    def _set_diff_results(self, text: str) -> None:
        self.diff_text.configure(state="normal")
        self.diff_text.delete("1.0", "end")
        self.diff_text.insert("1.0", text.strip() + "\n")
        self.diff_text.configure(state="disabled")

    def _append_diff_results(self, text: str) -> None:
        self.diff_text.configure(state="normal")
        self.diff_text.insert("end", text.rstrip() + "\n")
        self.diff_text.see("end")
        self.diff_text.configure(state="disabled")

    def _set_diff_busy(self, busy: bool) -> None:
        self.diff_running = busy
        self.run_diff_button.configure(state="disabled" if busy else "normal")
        if busy:
            self.view_results_button.configure(state="disabled")

    def _generate(self) -> bool:
        from panos_changedoc.generate import (
            GenerateValidationError,
            build_from_spec,
            write_outputs,
        )

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
        if self.diff_running:
            return
        if self.test_mode.get():
            self._ensure_generator_loaded()
        config = {
            "before": self.before_path.get(),
            "after": self.after_path.get(),
            "json_out": self.diff_json_path.get() or None,
            "markdown_out": self.diff_md_path.get() or None,
            "evidence_bundle": (
                self.evidence_bundle_path.get()
                if self.create_evidence_bundle.get()
                else None
            ),
            "manifest_out": self.manifest_path.get(),
            "test_mode": self.test_mode.get(),
            "spec": self._spec_from_ui() if self.test_mode.get() else None,
        }
        self.last_diff_results = None
        self.progress_value.set(0)
        self.current_progress_value.set(0)
        self.progress_status.set("Overall: starting diff run")
        self.current_progress_status.set("Waiting to start")
        self._set_diff_results("Progress:\n- Overall: starting diff run")
        self._set_diff_busy(True)
        worker = threading.Thread(
            target=self._run_diff_worker,
            args=(config,),
            daemon=True,
        )
        worker.start()
        self.root.after(100, self._drain_diff_events)

    def _emit_progress(
        self, overall_step: int, current_percent: int, text: str
    ) -> None:
        self.diff_events.put(ProgressUpdate(overall_step, current_percent, text))

    def _pause_between_tasks(self) -> None:
        # Give the UI time to repaint between the visible workflow steps.
        time.sleep(1)

    def _run_diff_worker(self, config: dict[str, Any]) -> None:
        from panos_changedoc.commands import run_diff
        from panos_changedoc.generate import (
            GenerateValidationError,
            build_from_spec,
            write_outputs,
        )

        try:
            if config["test_mode"]:
                self._emit_progress(1, 0, "Build selected generator scenario")
                before_xml, after_xml, manifest = build_from_spec(config["spec"])
                self._emit_progress(2, 0, "Write generated before/after XML")
                self._pause_between_tasks()
                self._emit_progress(2, 10, "Write generated before/after XML")
                write_outputs(
                    before_xml=before_xml,
                    after_xml=after_xml,
                    manifest=manifest,
                    before_out=config["before"],
                    after_out=config["after"],
                    manifest_out=config["manifest_out"],
                )
                self._emit_progress(3, 0, "Parse XML and compare supported sections")
                self._pause_between_tasks()
            else:
                self._emit_progress(3, 0, "Parse XML and compare supported sections")
                self._pause_between_tasks()

            self._emit_progress(3, 10, "Parse XML and compare supported sections")
            if config["evidence_bundle"]:
                # Surface evidence bundle creation as its own visible step.
                self._emit_progress(4, 0, "Create evidence bundle")
            rc = run_diff(
                before=config["before"],
                after=config["after"],
                json_out=config["json_out"],
                markdown_out=config["markdown_out"],
                evidence_bundle=config["evidence_bundle"],
                manifest=None,
                verbose=False,
                quiet=True,
            )
            if rc != 0:
                self.diff_events.put(
                    DiffFailed(
                        f"Diff failed with exit code {rc}.\n"
                        "Check generated inputs and try again."
                    )
                )
                return
            if config["evidence_bundle"]:
                # The bundle is already built inside run_diff, but the UI still
                # calls out the zip step so operators can follow the workflow.
                self._emit_progress(4, 60, "Zip evidence bundle")
                self._pause_between_tasks()
            self._emit_progress(5, 0, "Load generated report details")
            self._pause_between_tasks()

            self._emit_progress(5, 10, "Load generated report details")
            report = self._load_report(config)
            summary_text = build_gui_diff_results(
                report,
                json_path=self._report_json_label(config),
                markdown_path=self._report_markdown_path(config),
                evidence_bundle=config["evidence_bundle"],
            )
            self.diff_events.put(DiffDone(summary_text))
        except GenerateValidationError as exc:
            lines = ["Validation failed:"]
            for issue in exc.issues:
                lines.append(f"- {issue.message}")
                lines.append(f"  Fix: {issue.solution}")
            self.diff_events.put(DiffFailed("\n".join(lines)))
        except Exception as exc:
            self.diff_events.put(DiffFailed(f"Unexpected error:\n{exc}"))

    def _report_json_path(self, config: dict[str, Any]) -> Path:
        if config["json_out"]:
            return Path(config["json_out"])
        raise ValueError("No JSON report path is available.")

    def _report_json_label(self, config: dict[str, Any]) -> str:
        if config["json_out"]:
            return str(config["json_out"])
        if config["evidence_bundle"]:
            return "change-summary.json inside " + str(
                self._evidence_zip_path(config["evidence_bundle"])
            )
        return ""

    def _load_report(self, config: dict[str, Any]) -> dict:
        if config["json_out"]:
            return json.loads(
                self._report_json_path(config).read_text(encoding="utf-8")
            )
        if config["evidence_bundle"]:
            # Evidence mode stores the report inside the zip archive instead of
            # on the filesystem.
            with ZipFile(self._evidence_zip_path(config["evidence_bundle"])) as archive:
                with archive.open("change-summary.json") as fh:
                    return json.loads(fh.read().decode("utf-8"))
        raise ValueError("No JSON report path is available.")

    def _evidence_zip_path(self, bundle_path: str) -> Path:
        target = Path(bundle_path)
        if target.suffix.lower() != ".zip":
            target = target.with_suffix(".zip")
        return target

    def _report_markdown_path(self, config: dict[str, Any]) -> str:
        if config["markdown_out"]:
            return str(config["markdown_out"])
        if config["evidence_bundle"]:
            return "change-summary.md inside " + str(
                self._evidence_zip_path(config["evidence_bundle"])
            )
        return ""

    def _drain_diff_events(self) -> None:
        while not self.diff_events.empty():
            event = self.diff_events.get()
            if isinstance(event, ProgressUpdate):
                if event.overall_step:
                    self.progress_value.set(event.overall_step)
                self.current_progress_value.set(event.current_percent)
                self.current_progress_status.set(event.text)
                if event.overall_step:
                    self.progress_status.set(
                        f"Overall progress: step {event.overall_step} of 6"
                    )
                self._append_diff_results(f"- {event.text}")
            elif isinstance(event, DiffDone):
                self.progress_value.set(6)
                self.current_progress_value.set(100)
                self.progress_status.set("Overall progress: complete")
                self.current_progress_status.set("Complete")
                self.last_diff_results = event.text
                self._append_diff_results("- Diff completed")
                self._append_diff_results("- Click View Results to inspect details")
                self.view_results_button.configure(state="normal")
                self._set_diff_busy(False)
                messagebox.showinfo(
                    "Diff", "Diff completed. Click View Results to inspect details."
                )
                return
            elif isinstance(event, DiffFailed):
                self.progress_status.set("Diff failed")
                self._set_diff_results(event.text)
                self._set_diff_busy(False)
                messagebox.showerror("Diff Failed", event.text)
                return

        if self.diff_running:
            self.root.after(100, self._drain_diff_events)

    def _view_last_results(self) -> None:
        if self.last_diff_results is None:
            return
        self._set_diff_results(self.last_diff_results)


def launch_gui() -> int:
    root = tk.Tk()
    App(root)
    root.mainloop()
    return 0
