from __future__ import annotations

import copy
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

import ribbonengine as engine


class LayoutTunerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Ribbon Layout Tuner")
        self.root.geometry("1280x860")

        initialProfileName = self._resolveInitialProfileName()
        self.profileNameVar = tk.StringVar(value=initialProfileName)
        self.profile = engine.ensureProfileFile(initialProfileName)
        self.lastValidProfile = copy.deepcopy(self.profile)
        self.fieldControls: dict[str, dict] = {}
        self.updateJob = None
        self.previewImage = None
        self.loadingFields = False

        self.nameplateVar = tk.StringVar(value="PREVIEW")
        self.previewScaleVar = tk.IntVar(value=4)
        self.selectedShirtVar = tk.StringVar(value=str(self.profile.get("selected_shirt", "")))
        self.statusVar = tk.StringVar(value="")

        self._buildLayout()
        self._registerFields()
        self._loadProfileToFields(self.profile)
        self._updatePreview()

    def _buildLayout(self) -> None:
        rootFrame = ttk.Frame(self.root)
        rootFrame.pack(fill="both", expand=True)

        toolbar = ttk.Frame(rootFrame)
        toolbar.pack(fill="x", padx=10, pady=10)

        ttk.Label(toolbar, text="Profile Name:").pack(side="left")
        profileNameEntry = ttk.Entry(toolbar, textvariable=self.profileNameVar, width=18)
        profileNameEntry.pack(side="left", padx=(6, 6))
        profileNameEntry.bind("<KeyRelease>", lambda _event: self._scheduleUpdate())
        ttk.Button(toolbar, text="Load Name", command=self._loadNamedProfile).pack(side="left", padx=(0, 12))

        ttk.Label(toolbar, text="Nameplate:").pack(side="left")
        nameplateEntry = ttk.Entry(toolbar, textvariable=self.nameplateVar, width=20)
        nameplateEntry.pack(side="left", padx=(6, 12))
        nameplateEntry.bind("<KeyRelease>", lambda _event: self._scheduleUpdate())

        ttk.Label(toolbar, text="Preview Scale:").pack(side="left")
        previewScaleSpin = tk.Spinbox(
            toolbar,
            from_=1,
            to=12,
            width=4,
            textvariable=self.previewScaleVar,
            command=self._scheduleUpdate,
        )
        previewScaleSpin.pack(side="left", padx=(6, 12))
        previewScaleSpin.bind("<KeyRelease>", lambda _event: self._scheduleUpdate())

        ttk.Button(toolbar, text="Save Profile", command=self._saveProfile).pack(side="left", padx=(0, 6))
        ttk.Button(toolbar, text="Reload Profile", command=self._reloadProfile).pack(side="left")

        ttk.Label(rootFrame, textvariable=self.statusVar).pack(anchor="w", padx=10)

        body = ttk.Panedwindow(rootFrame, orient=tk.HORIZONTAL)
        body.pack(fill="both", expand=True, padx=10, pady=(6, 10))

        controlPanel = ttk.Frame(body)
        body.add(controlPanel, weight=3)

        previewPanel = ttk.Frame(body)
        body.add(previewPanel, weight=2)

        self.canvas = tk.Canvas(controlPanel, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(controlPanel, orient="vertical", command=self.canvas.yview)
        scroll.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=scroll.set)

        self.formFrame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.formFrame, anchor="nw")
        self.formFrame.bind("<Configure>", lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.controlPanel = controlPanel
        self.root.bind_all("<MouseWheel>", self._onMousewheel, add="+")
        self.root.bind_all("<Button-4>", self._onMousewheel, add="+")
        self.root.bind_all("<Button-5>", self._onMousewheel, add="+")

        ttk.Label(previewPanel, text="Live Preview").pack(pady=(0, 8))
        self.previewLabel = ttk.Label(previewPanel)
        self.previewLabel.pack()

    def _isDescendant(self, widget: tk.Widget | None, ancestor: tk.Widget) -> bool:
        current = widget
        while current is not None:
            if current == ancestor:
                return True
            current = current.master
        return False

    def _onMousewheel(self, event) -> str | None:
        target = self.root.winfo_containing(event.x_root, event.y_root)
        if not self._isDescendant(target, self.controlPanel):
            return None

        if getattr(event, "num", None) == 4:
            steps = -1
        elif getattr(event, "num", None) == 5:
            steps = 1
        else:
            delta = getattr(event, "delta", 0)
            if not delta:
                return None
            if abs(delta) >= 120:
                steps = int(-delta / 120)
            else:
                steps = -1 if delta > 0 else 1

        self.canvas.yview_scroll(steps, "units")
        return "break"

    def _addSection(self, title: str) -> ttk.LabelFrame:
        section = ttk.LabelFrame(self.formFrame, text=title)
        section.pack(fill="x", padx=4, pady=6)
        return section

    def _addIntField(self, parent, key: str, label: str, path: tuple):
        row = ttk.Frame(parent)
        row.pack(fill="x", padx=6, pady=3)
        ttk.Label(row, text=label, width=32).pack(side="left")

        var = tk.StringVar()
        entry = tk.Entry(row, textvariable=var, width=12)
        entry.pack(side="left")
        entry.bind("<KeyRelease>", lambda _event: self._scheduleUpdate())
        entry.bind("<FocusOut>", lambda _event: self._scheduleUpdate())

        self.fieldControls[key] = {
            "var": var,
            "entry": entry,
            "path": path,
        }

    def _resolveInitialProfileName(self) -> str:
        settings = engine.ensureSettingsDefaults(engine.loadSettings())
        return engine.normalizeProfileName(settings.get("profile", engine.defaultProfileName))

    def _profileExists(self, profileName: str) -> bool:
        return profileName in set(engine.listProfileNames())

    def _registerFields(self) -> None:
        general = self._addSection("General")
        self._addIntField(general, "ribbonAreaWidth", "ribbon_area_width", ("ribbon_area_width",))
        self._addIntField(general, "maxMedals", "max_medals_per_side", ("max_medals_per_side",))
        self._addIntField(general, "hoverPreviewSize", "hover_preview_size", ("hover_preview_size",))

        offsets = self._addSection("Offsets")
        self._addIntField(offsets, "pocketColSpacing", "pocket_col_spacing", ("offsets", "pocket_col_spacing"))
        self._addIntField(offsets, "pocketRightOffset", "pocket_right_offset", ("offsets", "pocket_right_offset"))
        self._addIntField(offsets, "pocketXOffset", "pocket_x_offset", ("offsets", "pocket_x_offset"))
        self._addIntField(offsets, "corpusXOffset", "corpus_x_offset", ("offsets", "corpus_x_offset"))
        self._addIntField(offsets, "ribbonsRightAlignOffset", "ribbons_right_align_offset", ("offsets", "ribbons_right_align_offset"))

        ribbonRows = self._addSection("Ribbon Rows")
        self._addIntField(ribbonRows, "centeredRowCapacity", "centered_row_capacity", ("ribbon_rows", "centered_row_capacity"))
        self._addIntField(ribbonRows, "rightStartRow", "right_start_row", ("ribbon_rows", "right_start_row"))
        self._addIntField(ribbonRows, "firstRightRowCapacity", "first_right_row_capacity", ("ribbon_rows", "first_right_row_capacity"))
        self._addIntField(ribbonRows, "subsequentRightRowCapacity", "subsequent_right_row_capacity", ("ribbon_rows", "subsequent_right_row_capacity"))

        partCoords = self._addSection("Part Coordinates")
        for name in ("corpus", "nametape", "sacks", "commendations", "ribbons", "gorget", "spbadge"):
            self._addIntField(partCoords, f"{name}X", f"{name}.x", ("part_coords", name, 0))
            self._addIntField(partCoords, f"{name}Y", f"{name}.y", ("part_coords", name, 1))

        overlay = self._addSection("Overlay Crop")
        self._addIntField(overlay, "overlayTemplateW", "template_size.width", ("preview_overlay", "template_size", 0))
        self._addIntField(overlay, "overlayTemplateH", "template_size.height", ("preview_overlay", "template_size", 1))
        self._addIntField(overlay, "overlayCropX1", "front_crop_box.x1", ("preview_overlay", "front_crop_box", 0))
        self._addIntField(overlay, "overlayCropY1", "front_crop_box.y1", ("preview_overlay", "front_crop_box", 1))
        self._addIntField(overlay, "overlayCropX2", "front_crop_box.x2", ("preview_overlay", "front_crop_box", 2))
        self._addIntField(overlay, "overlayCropY2", "front_crop_box.y2", ("preview_overlay", "front_crop_box", 3))

        selectedShirt = self._addSection("Selected Shirt")
        shirtRow = ttk.Frame(selectedShirt)
        shirtRow.pack(fill="x", padx=6, pady=3)
        ttk.Label(shirtRow, text="selected_shirt", width=32).pack(side="left")
        shirtEntry = ttk.Entry(shirtRow, textvariable=self.selectedShirtVar)
        shirtEntry.pack(side="left", fill="x", expand=True)
        shirtEntry.bind("<KeyRelease>", lambda _event: self._scheduleUpdate())
        ttk.Button(shirtRow, text="Browse", command=self._browseSelectedShirt).pack(side="left", padx=(6, 0))

    def _getByPath(self, data: dict, path: tuple):
        current = data
        for token in path:
            current = current[token]
        return current

    def _setByPath(self, data: dict, path: tuple, value: int) -> None:
        current = data
        for token in path[:-1]:
            current = current[token]
        current[path[-1]] = value

    def _normalizedProfileName(self) -> str:
        return engine.normalizeProfileName(self.profileNameVar.get())

    def _loadNamedProfile(self) -> None:
        profileName = self._normalizedProfileName()
        self.profileNameVar.set(profileName)
        if self._profileExists(profileName):
            self.profile = engine.loadProfile(profileName)
            statusText = f"Loaded profile: {profileName}"
        else:
            # Start new profiles from the current mapping so only diffs need editing.
            self.profile = copy.deepcopy(self.lastValidProfile)
            engine.saveProfile(self.profile, profileName)
            statusText = f"Created profile from current mapping: {profileName}"
        self.lastValidProfile = copy.deepcopy(self.profile)
        self.selectedShirtVar.set(str(self.profile.get("selected_shirt", "")))
        self._loadProfileToFields(self.profile)
        self.statusVar.set(statusText)
        self._updatePreview()

    def _browseSelectedShirt(self) -> None:
        path = filedialog.askopenfilename(
            title="Select Shirt Image For Profile",
            filetypes=[
                ("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.webp"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        self.selectedShirtVar.set(path)
        self._scheduleUpdate()

    def _loadProfileToFields(self, profile: dict) -> None:
        self.loadingFields = True
        try:
            for control in self.fieldControls.values():
                value = self._getByPath(profile, control["path"])
                control["var"].set(str(value))
                control["entry"].configure(bg="white")
        finally:
            self.loadingFields = False

    def _buildEditedProfile(self) -> tuple[dict, list[str]]:
        edited = copy.deepcopy(self.profile)
        invalidKeys: list[str] = []
        for key, control in self.fieldControls.items():
            raw = control["var"].get().strip()
            try:
                value = int(raw)
            except Exception:
                invalidKeys.append(key)
                control["entry"].configure(bg="#ffd8d8")
                continue
            control["entry"].configure(bg="white")
            self._setByPath(edited, control["path"], value)
        edited["selected_shirt"] = self.selectedShirtVar.get().strip()
        return edited, invalidKeys

    def _buildSelectionSet(self, groups) -> set[str]:
        selected: set[str] = set()
        for item in groups.get("ribbons", [])[:27]:
            selected.add(item.name)
        for category in ("sacks", "commendations", "corpus", "spbadge"):
            for item in groups.get(category, []):
                selected.add(item.name)
        gorgets = groups.get("gorget", [])
        if gorgets:
            selected.add(gorgets[0].name)
        return selected

    def _scheduleUpdate(self) -> None:
        if self.loadingFields:
            return
        if self.updateJob is not None:
            self.root.after_cancel(self.updateJob)
        self.updateJob = self.root.after(120, self._updatePreview)

    def _updatePreview(self) -> None:
        self.updateJob = None
        editedProfile, invalidKeys = self._buildEditedProfile()
        if invalidKeys:
            self.statusVar.set(f"Invalid integer input in {len(invalidKeys)} field(s).")
            return

        engine.applyProfile(editedProfile)
        groups = engine.loadRibbonGroups()
        renderer = engine.RibbonRenderer(groups)
        selectedNames = self._buildSelectionSet(groups)
        nameplateText = self.nameplateVar.get().strip() or "PREVIEW"

        errors: list[str] = []
        image, _, missing = renderer.buildImage(
            selectedNames=selectedNames,
            nameplateText=nameplateText,
            baseImage=None,
            requireNameForNew=False,
            errorCallback=lambda message: errors.append(message),
        )
        if image is None:
            self.statusVar.set(errors[0] if errors else "Preview render failed.")
            return

        scale = max(1, int(self.previewScaleVar.get()))
        preview = image.resize((image.width * scale, image.height * scale), Image.NEAREST)
        self.previewImage = ImageTk.PhotoImage(preview)
        self.previewLabel.configure(image=self.previewImage)
        self.previewLabel.image = self.previewImage

        self.lastValidProfile = editedProfile
        missingCount = len(missing) if missing else 0
        status = f"Preview updated. Ribbons: {min(27, len(groups.get('ribbons', [])))} / Missing assets: {missingCount}"
        if errors:
            status += f" / Note: {errors[0]}"
        self.statusVar.set(status)

    def _saveProfile(self) -> None:
        editedProfile, invalidKeys = self._buildEditedProfile()
        if invalidKeys:
            messagebox.showerror("Error", "Fix invalid fields before saving.")
            return

        profileName = self._normalizedProfileName()
        self.profileNameVar.set(profileName)
        engine.saveProfile(editedProfile, profileName)
        self.profile = copy.deepcopy(editedProfile)
        self.lastValidProfile = copy.deepcopy(editedProfile)
        self.statusVar.set(f"Saved profile: {profileName}")
        self._updatePreview()

    def _reloadProfile(self) -> None:
        profileName = self._normalizedProfileName()
        self.profileNameVar.set(profileName)
        self.profile = engine.loadProfile(profileName)
        self.lastValidProfile = copy.deepcopy(self.profile)
        self.selectedShirtVar.set(str(self.profile.get("selected_shirt", "")))
        self._loadProfileToFields(self.profile)
        self.statusVar.set(f"Reloaded profile: {profileName}")
        self._updatePreview()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = LayoutTunerApp()
    app.run()


if __name__ == "__main__":
    main()
