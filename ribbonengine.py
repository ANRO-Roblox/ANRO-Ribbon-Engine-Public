from __future__ import annotations

import datetime
import json
import os
import shutil
import tkinter as tk
from copy import deepcopy
from dataclasses import dataclass
from tkinter import colorchooser, filedialog, messagebox, simpledialog, ttk
from typing import Callable, Optional

from PIL import Image, ImageGrab, ImageTk, PngImagePlugin


# Image/layout constants
imageSize = 128
ribbonAreaWidth = 43
maxMedalsPerSide = 3
defaultNameplateWidth = 31
nameplateLetterSpacing = 1
hoverPreviewSize = 96
expandedIcon = "\u25be"
collapsedIcon = "\u25b8"

# -------------------------------
# Layout values are profile-driven; these are safe bootstrap defaults until a profile is loaded.
partCoordsKeys = (
    "corpus",
    "nametape",
    "sacks",
    "commendations",
    "certifications",
    "ribbons",
    "gorget",
    "spbadge",
    "hicom",
    "brackets",
)
partCoords = {key: (0, 0) for key in partCoordsKeys}
pocketColSpacing = 0
pocketRightOffset = 0
pocketXOffset = 0
corpusXOffset = 0
ribbonsRightAlignOffset = 0

# Medal name lists (filenames without .png)
awardMedalNames = {
    "Diamond Medal",
    "Galaxy Medal",
    "Quantum Medal",
}
bonusMedalNames = {
    "Teto Medal",
    "Teto Medal Shiny",
    "ANROSOC Medal",
}

# -------------------------------
# Paths and manifests
baseDir = os.path.dirname(os.path.abspath(__file__))
assetsDirCandidates = [os.path.join(baseDir, "Images"), os.path.join(baseDir, "images")]
assetsDir = next((path for path in assetsDirCandidates if os.path.isdir(path)), None)
def resolveAssetPath(*parts: str) -> str:
    if assetsDir:
        candidate = os.path.join(assetsDir, *parts)
        if os.path.exists(candidate):
            return candidate
    return os.path.join(baseDir, *parts)

ribbonsDir = resolveAssetPath("Ribbons")
commendationsDir = resolveAssetPath("Commendations")
awardsDir = resolveAssetPath("Awards")
bracketsDir = resolveAssetPath("Brackets")
hicomDir = resolveAssetPath("HICOM Badges")
charactersDir = os.path.join(baseDir, "Characters")
settingsPath = os.path.join(baseDir, "settings.json")
themesDir = os.path.join(baseDir, "Themes")
profilesDir = os.path.join(baseDir, "Engine Profiles")
legacyProfilePath = os.path.join(baseDir, "engine_profile.json")

# New consolidated image source (preferred when present)
defaultProfileName = "default"
themeColorKeys = (
    "bg",
    "panel_bg",
    "text",
    "accent",
    "header_bg",
    "header_fg",
    "status",
    "theme_selector_bg",
    "theme_selector_text",
    "profile_selector_bg",
    "profile_selector_text",
    "nametape_bg",
    "nametape_text",
    "search_bg",
    "search_text",
)

builtInThemes: dict[str, dict[str, str]] = {
    "xp": {
        "bg": "#ece9d8",
        "panel_bg": "#ece9d8",
        "text": "#000000",
        "accent": "#0a246a",
        "header_bg": "#0a246a",
        "header_fg": "#ffffff",
        "status": "#a80000",
        "theme_selector_bg": "#ffffff",
        "theme_selector_text": "#000000",
        "profile_selector_bg": "#ffffff",
        "profile_selector_text": "#000000",
        "nametape_bg": "#ffffff",
        "nametape_text": "#000000",
        "search_bg": "#ffffff",
        "search_text": "#000000",
    },
    "dark": {
        "bg": "#1e1e1e",
        "panel_bg": "#252526",
        "text": "#e6e6e6",
        "accent": "#7aa2f7",
        "header_bg": "#2d2d30",
        "header_fg": "#ffffff",
        "status": "#ff6b6b",
        "theme_selector_bg": "#ffffff",
        "theme_selector_text": "#000000",
        "profile_selector_bg": "#ffffff",
        "profile_selector_text": "#000000",
        "nametape_bg": "#ffffff",
        "nametape_text": "#000000",
        "search_bg": "#ffffff",
        "search_text": "#000000",
    },
    "light": {
        "bg": "#f5f5f5",
        "panel_bg": "#ffffff",
        "text": "#1f2933",
        "accent": "#2b6cb0",
        "header_bg": "#e6e6e6",
        "header_fg": "#111111",
        "status": "#b91c1c",
        "theme_selector_bg": "#ffffff",
        "theme_selector_text": "#000000",
        "profile_selector_bg": "#ffffff",
        "profile_selector_text": "#000000",
        "nametape_bg": "#ffffff",
        "nametape_text": "#000000",
        "search_bg": "#ffffff",
        "search_text": "#000000",
    },
}

characterAliases = {" ": "Space", ".": "Period"}
previewOverlayPath = os.path.join(charactersDir, "anro_hr_formals_template.png")
uiBadgePath = resolveAssetPath("ANRO.png")
uiBadgeMaxSize = 42

categoryLabels = {
    "sacks": "Awards",
    "gorget": "Gorgets",
    "spbadge": "Special Badges",
    "commendations": "Commendations",
    "corpus": "Corpus Commendations",
    "ribbons": "Ribbons",
    "anrocom": "ANROCOM Ribbons",
    "hicom": "HICOM Badges",
    "brackets": "Brackets",
    "certifications": "Certifications",
}
categoryPlacement = {
    "sacks": "right",
    "gorget": "right",
    "spbadge": "right",
    "commendations": "right",
    "corpus": "right",
    "ribbons": "left",
    "anrocom": "left",
    "hicom": "left",      # moved one category to other side
    "brackets": "right",
    "certifications": "left",
}

# Profile-driven behavior defaults
enabledCategories = set(categoryLabels.keys())
allowedAssetsByCategory: dict[str, set[str]] = {}
certificationKeyword = "certification"
certificationsSectionLabel = "Certifications"
anrocomSectionLabel = "ANROCOM Ribbons"
anrocomSettingsKey = "ANROCOM"
ribbonCenteredRowCapacity = 4
ribbonRightStartRow = 5
ribbonRightFirstRowCapacity = 3
ribbonRightSubsequentRowCapacity = 2
medalSingleOrder = ("middle", "left", "right")
medalMultiOrder = ("left", "middle", "right")
quartermasterBracketTopOffset = -2
quartermasterBracketXOffset = -1
quartermasterLowerMedalOffset = 11
overlayTemplateSize = (585, 559)
overlayFrontCropBox = (132, 74, 260, 202)
profileSelectedShirt = ""
tutorialSlides = (
    (
        "Step 1",
        "Click the Add Ribbon button in the header.\n\n"
        "That opens the in-app importer for adding a new ribbon PNG without manually sorting files first.",
    ),
    (
        "Step 2",
        "Enter the ribbon name and choose the ribbon type.\n\n"
        "The type decides which suffix gets added and which category the PNG will be placed into.",
    ),
    (
        "Step 3",
        "Click Add PNG and choose the file you want to import.\n\n"
        "When you finish, the engine moves the PNG into the Images folder, puts it in the right category folder, and renames it automatically.",
    ),
    (
        "Step 4",
        "The importer uses these suffixes at the end of the filename:\n\n"
        "RBN = Ribbons\n"
        "CMD = Commendations\n"
        "CCMD = Corpus Commendations\n"
        "BDG = Special Badges\n"
        "AWD = Awards / Sacks\n"
        "BRK = Brackets\n"
        "QMBRK = Quartermaster pocket bracket\n"
        "ANROCOM = ANROCOM Ribbons\n"
        "HICOM = HICOM Badges\n"
        "GORGET = Gorgets\n"
        "CERT = Certifications\n\n"
        "Example:\n"
        "Merit Ribbon-RBN.png",
    ),
    (
        "Step 5",
        "Keep the image format simple.\n\n"
        "Use PNG files. Transparent backgrounds work best.",
    ),
    (
        "Step 6",
        "After adding files, click the Reload button next to Profile in the main window.\n\n"
        "The Add Ribbon window already reloads automatically, but Reload is still useful if you manually changed files outside the app.",
    ),
    (
        "Step 7",
        "If the Add Ribbon tool ever breaks, you can still add files manually.\n\n"
        "Open your Ribbon Engine files, then open the Images folder. If it does not exist yet, create an Images folder in the root of the app.",
    ),
    (
        "Step 8",
        "Add your PNG files manually.\n\n"
        "The engine scans Images recursively, so you can place files directly in Images or inside subfolders to stay organized.",
    ),
    (
        "Step 9",
        "Use the Search box to quickly confirm the new ribbon appears in the correct category.\n\n"
        "If a ribbon shows up in the wrong section, rename the file with a clearer suffix and reload again.\n\n"
        "If a file has no suffix, the engine falls back to keyword matching, but suffixes are more reliable.\n\n"
        "If you are working on a new uniform layout, use layoutTuner.py to help line everything up.",
    ),
)

defaultProfile = {
    "image_size": imageSize,
    "ribbon_area_width": ribbonAreaWidth,
    "max_medals_per_side": maxMedalsPerSide,
    "default_nameplate_width": defaultNameplateWidth,
    "nameplate_letter_spacing": nameplateLetterSpacing,
    "hover_preview_size": hoverPreviewSize,
    "part_coords": {key: [0, 0] for key in partCoordsKeys},
    "offsets": {
        "pocket_col_spacing": pocketColSpacing,
        "pocket_right_offset": pocketRightOffset,
        "pocket_x_offset": pocketXOffset,
        "corpus_x_offset": corpusXOffset,
        "ribbons_right_align_offset": ribbonsRightAlignOffset,
    },
    "medals": {
        "award_names": sorted(awardMedalNames),
        "bonus_names": sorted(bonusMedalNames),
        "single_order": list(medalSingleOrder),
        "multi_order": list(medalMultiOrder),
    },
    "ribbon_rows": {
        "centered_row_capacity": ribbonCenteredRowCapacity,
        "right_start_row": ribbonRightStartRow,
        "first_right_row_capacity": ribbonRightFirstRowCapacity,
        "subsequent_right_row_capacity": ribbonRightSubsequentRowCapacity,
    },
    "character_aliases": deepcopy(characterAliases),
    "ui": {
        "expanded_icon": expandedIcon,
        "collapsed_icon": collapsedIcon,
        "certification_keyword": certificationKeyword,
        "certifications_label": certificationsSectionLabel,
        "anrocom_label": anrocomSectionLabel,
        "anrocom_settings_key": anrocomSettingsKey,
    },
    "categories": {
        "labels": deepcopy(categoryLabels),
        "enabled": sorted(categoryLabels.keys()),
        "allowed_assets": {},
    },
    "preview_overlay": {
        "template_size": list(overlayTemplateSize),
        "front_crop_box": list(overlayFrontCropBox),
    },
    "selected_shirt": "",
}


@dataclass(frozen=True)
class AssetItem:
    name: str
    path: str


@dataclass
class SectionUI:
    key: str
    header: ttk.Frame
    toggle: ttk.Button
    content: ttk.Frame
    items: list[dict]
    collapsed: bool = False


def listPngs(directory: str) -> list[AssetItem]:
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"Missing folder: {directory}")

    items: list[AssetItem] = []
    for filename in sorted(os.listdir(directory), key=str.lower):
        if not filename.lower().endswith(".png"):
            continue
        name = os.path.splitext(filename)[0]
        items.append(AssetItem(name=name, path=os.path.join(directory, filename)))
    return items


def listPngsRecursive(directory: str) -> list[AssetItem]:
    if not os.path.isdir(directory):
        return []

    items: list[AssetItem] = []
    for root, _, files in os.walk(directory):
        for filename in sorted(files, key=str.lower):
            if not filename.lower().endswith(".png"):
                continue
            name = os.path.splitext(filename)[0]
            items.append(AssetItem(name=name, path=os.path.join(root, filename)))
    return items


def categorizeAssetName(name: str) -> Optional[str]:
    if not isinstance(name, str) or not name.strip():
        return None
    token = name.strip().rsplit("-", 1)[-1].strip().lower()
    suffixMap = {
        "rbn": "ribbons",
        "ribbon": "ribbons",
        "cmd": "commendations",
        "commendation": "commendations",
        "ccmd": "corpus",
        "bdg": "spbadge",
        "badge": "spbadge",
        "awd": "sacks",
        "award": "sacks",
        "qmbrk": "brackets",
        "brk": "brackets",
        "bracket": "brackets",
        "hicom": "hicom",
        "gorget": "gorget",
        "corpus": "corpus",
        "anrocom": "anrocom",
        "cert": "certifications",
        "certification": "certifications",
    }
    if token in suffixMap:
        return suffixMap[token]

    lowerName = name.lower()
    if "gorget" in lowerName:
        return "gorget"
    if lowerName.startswith(("mr ", "hr ")):
        return "corpus"
    if "anrocom" in lowerName:
        return "anrocom"
    if "badge" in lowerName:
        return "spbadge"
    if "hicom" in lowerName:
        return "hicom"
    if "bracket" in lowerName:
        return "brackets"
    if "award" in lowerName or "sack" in lowerName:
        return "sacks"
    if "commendation" in lowerName:
        return "commendations"
    if "certification" in lowerName:
        return "certifications"
    if "ribbon" in lowerName:
        return "ribbons"

    return None


def loadRibbonGroups() -> dict[str, list[AssetItem]]:
    groups: dict[str, list[AssetItem]] = {
        "sacks": [],
        "gorget": [],
        "spbadge": [],
        "commendations": [],
        "corpus": [],
        "ribbons": [],
        "anrocom": [],
        "hicom": [],
        "brackets": [],
        "certifications": [],
    }

    if assetsDir and os.path.isdir(assetsDir):
        for item in listPngsRecursive(assetsDir):
            category = categorizeAssetName(item.name)
            if category in groups:
                groups[category].append(item)
            else:
                # Fallback to existing classification logic, e.g. unrouted commendations style.
                lowerName = item.name.lower()
                if "gorget" in lowerName:
                    groups["gorget"].append(item)
                elif lowerName.startswith(("mr ", "hr ")):
                    groups["corpus"].append(item)
                elif lowerName.startswith("anrocom "):
                    groups["anrocom"].append(item)
                elif "badge" in lowerName:
                    groups["spbadge"].append(item)
                else:
                    groups["commendations"].append(item)
    else:
        # Backward compatibility: keep old directories working.
        groups["sacks"] = listPngs(awardsDir)
        groups["ribbons"] = listPngs(ribbonsDir)
        groups["hicom"] = listPngs(hicomDir)
        groups["brackets"] = listPngs(bracketsDir)

        # Reclassify ribbons folder entries by face suffix/keyword (cert, anrocom, etc.)
        rerouted = []
        for item in groups["ribbons"]:
            newCat = categorizeAssetName(item.name)
            if newCat and newCat != "ribbons":
                groups.setdefault(newCat, []).append(item)
                rerouted.append(item)
        groups["ribbons"] = [item for item in groups["ribbons"] if item not in rerouted]

        for item in listPngs(commendationsDir):
            cat = categorizeAssetName(item.name)
            if cat:
                groups.setdefault(cat, []).append(item)
            else:
                lowerName = item.name.lower()
                if "gorget" in lowerName:
                    groups["gorget"].append(item)
                elif lowerName.startswith(("mr ", "hr ")):
                    groups["corpus"].append(item)
                elif "anrocom" in lowerName:
                    groups["anrocom"].append(item)
                elif "certification" in lowerName or "cert" in lowerName:
                    groups["certifications"].append(item)
                elif "badge" in lowerName:
                    groups["spbadge"].append(item)
                else:
                    groups["commendations"].append(item)

    for category in list(groups.keys()):
        if category not in enabledCategories:
            groups[category] = []
            continue
        allowedAssets = allowedAssetsByCategory.get(category)
        if allowedAssets:
            groups[category] = [item for item in groups[category] if item.name in allowedAssets]
    return groups


def loadRibbonImage(item: AssetItem) -> Image.Image:
    if not item.path:
        raise FileNotFoundError("Missing ribbon image path.")
    if not os.path.exists(item.path):
        raise FileNotFoundError(f"Missing ribbon image: {item.path}")
    with Image.open(item.path) as img:
        return img.convert("RGBA")


def displayAssetName(name: str) -> str:
    if not isinstance(name, str) or not name.strip():
        return ""
    tokens = name.strip().rsplit("-", 1)
    if len(tokens) == 2:
        return tokens[0].strip()
    return name


def _sanitizeAssetFilenamePart(value: str) -> str:
    cleaned = "".join(ch for ch in str(value or "").strip() if ch.isalnum() or ch in (" ", "-", "_", ".", "'"))
    collapsed = " ".join(cleaned.split())
    return collapsed.strip(" .-_")


def loadCharacterImage(ch: str) -> Image.Image:
    token = characterAliases.get(ch, ch)
    path = os.path.join(charactersDir, f"{token}.png")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing character image: {path}")
    with Image.open(path) as img:
        return img.convert("RGBA")


def loadSettings() -> dict:
    if not os.path.exists(settingsPath):
        return {}
    try:
        # Use utf-8-sig so settings authored by Windows editors with BOM still parse.
        with open(settingsPath, "r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            return data
    except Exception:
        return {}
    return {}


def saveSettings(settings: dict) -> None:
    try:
        with open(settingsPath, "w", encoding="utf-8") as handle:
            json.dump(settings, handle, indent=2)
    except Exception:
        return


def ensureSettingsDefaults(settings: dict) -> dict:
    data = dict(settings) if isinstance(settings, dict) else {}
    data.setdefault("presets", {})
    if not isinstance(data.get("presets"), dict):
        data["presets"] = {}
    data.setdefault("theme", "xp")
    data.setdefault("profile", defaultProfileName)
    data.setdefault("selected_preset", "")
    data.setdefault("sections", {anrocomSettingsKey: []})
    if isinstance(data.get("sections"), dict):
        data["sections"].setdefault(anrocomSettingsKey, [])
    data.setdefault("collapsed_sections", {})
    data.setdefault("preview_scale", 1.0)
    data.setdefault("only_show_selected", False)
    data.setdefault("preview_overlay", False)
    data.setdefault("case_sensitive_search", False)
    return data


def ensureThemesDir() -> None:
    os.makedirs(themesDir, exist_ok=True)


def _sanitizeThemeName(name: str) -> str:
    cleaned = "".join(ch for ch in str(name or "").strip() if ch.isalnum() or ch in (" ", "-", "_"))
    return " ".join(cleaned.split())


def _isValidHexColor(value) -> bool:
    if not isinstance(value, str):
        return False
    token = value.strip()
    if len(token) != 7 or not token.startswith("#"):
        return False
    return all(ch in "0123456789abcdefABCDEF" for ch in token[1:])


def _normalizeThemePalette(value, fallback: Optional[dict[str, str]] = None) -> Optional[dict[str, str]]:
    base = dict(fallback) if isinstance(fallback, dict) else dict(builtInThemes["xp"])
    if not isinstance(value, dict):
        return base if fallback is not None else None

    palette = dict(base)
    found = False
    for key in themeColorKeys:
        color = value.get(key)
        if _isValidHexColor(color):
            palette[key] = color.strip()
            found = True
    if not found and fallback is None:
        return None
    return palette


def _themeFilePath(themeName: str) -> str:
    return os.path.join(themesDir, f"{_sanitizeThemeName(themeName)}.json")


def loadCustomThemes() -> dict[str, dict[str, str]]:
    ensureThemesDir()
    themes: dict[str, dict[str, str]] = {}
    for filename in sorted(os.listdir(themesDir), key=str.lower):
        if not filename.lower().endswith(".json"):
            continue
        path = os.path.join(themesDir, filename)
        try:
            with open(path, "r", encoding="utf-8-sig") as handle:
                payload = json.load(handle)
        except Exception:
            continue

        if not isinstance(payload, dict):
            continue

        rawName = payload.get("name")
        themeName = _sanitizeThemeName(rawName if isinstance(rawName, str) else os.path.splitext(filename)[0])
        if not themeName:
            continue

        palette = _normalizeThemePalette(payload.get("colors"), fallback=None)
        if palette is None:
            palette = _normalizeThemePalette(payload, fallback=None)
        if palette is None:
            continue

        if themeName.lower() in {name.lower() for name in builtInThemes}:
            continue
        themes[themeName] = palette
    return themes


def loadThemeRegistry() -> dict[str, dict[str, str]]:
    themes = {name: dict(palette) for name, palette in builtInThemes.items()}
    themes.update(loadCustomThemes())
    return themes


def saveCustomTheme(themeName: str, colors: dict[str, str], sourcePath: str = "") -> str:
    ensureThemesDir()
    sanitizedName = _sanitizeThemeName(themeName)
    if not sanitizedName:
        raise ValueError("Theme name cannot be empty.")
    if sanitizedName.lower() in {name.lower() for name in builtInThemes}:
        raise ValueError("That theme name is reserved for a built-in theme.")

    palette = _normalizeThemePalette(colors, fallback=None)
    if palette is None:
        raise ValueError("Theme file is missing one or more valid colors.")

    path = _themeFilePath(sanitizedName)
    payload = {
        "name": sanitizedName,
        "colors": {key: palette[key] for key in themeColorKeys},
    }
    if sourcePath:
        payload["shared_from"] = sourcePath
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return path


def _deepMerge(base: dict, override: dict) -> dict:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deepMerge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _normalizeOrder(value, fallback: tuple[str, str, str]) -> tuple[str, str, str]:
    if not isinstance(value, list):
        return fallback
    tokens = []
    for token in value:
        if not isinstance(token, str):
            continue
        normalized = token.strip().lower()
        if normalized in ("left", "middle", "right") and normalized not in tokens:
            tokens.append(normalized)
    if len(tokens) != 3:
        return fallback
    return (tokens[0], tokens[1], tokens[2])


def _normalizeCategoryAssets(value) -> dict[str, set[str]]:
    parsed: dict[str, set[str]] = {}
    if not isinstance(value, dict):
        return parsed
    for category, names in value.items():
        if not isinstance(category, str) or not isinstance(names, list):
            continue
        cleaned = set()
        for name in names:
            if not isinstance(name, str):
                continue
            normalized = name.strip()
            if normalized.lower().endswith(".png"):
                normalized = normalized[:-4]
            if normalized:
                cleaned.add(normalized)
        if cleaned:
            parsed[category] = cleaned
    return parsed


def _normalizeSizePair(value, fallback: tuple[int, int]) -> tuple[int, int]:
    if not isinstance(value, list) or len(value) != 2:
        return fallback
    try:
        width = int(value[0])
        height = int(value[1])
    except Exception:
        return fallback
    if width <= 0 or height <= 0:
        return fallback
    return (width, height)


def _normalizeCropBox(value, fallback: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    if not isinstance(value, list) or len(value) != 4:
        return fallback
    try:
        x1, y1, x2, y2 = (int(value[0]), int(value[1]), int(value[2]), int(value[3]))
    except Exception:
        return fallback
    if x2 <= x1 or y2 <= y1:
        return fallback
    return (x1, y1, x2, y2)


def _normalizeProfileName(name: Optional[str]) -> str:
    raw = str(name or "").strip()
    if raw.lower().endswith(".json"):
        raw = raw[:-5]
    cleaned = "".join(ch for ch in raw if ch.isalnum() or ch in ("-", "_", " ")).strip()
    if not cleaned:
        return defaultProfileName
    return cleaned.replace(" ", "_")


def normalizeProfileName(name: Optional[str]) -> str:
    return _normalizeProfileName(name)


def _profilePathForName(profileName: Optional[str]) -> str:
    normalized = _normalizeProfileName(profileName)
    return os.path.join(profilesDir, f"{normalized}.json")


def listProfileNames() -> list[str]:
    if not os.path.isdir(profilesDir):
        return [defaultProfileName]
    names = []
    for filename in sorted(os.listdir(profilesDir), key=str.lower):
        if not filename.lower().endswith(".json"):
            continue
        names.append(os.path.splitext(filename)[0])
    if not names:
        return [defaultProfileName]
    return names


def _loadProfileFromPath(path: str) -> dict:
    if not os.path.exists(path):
        return deepcopy(defaultProfile)
    try:
        # Use utf-8-sig so profile files with BOM do not silently fall back to defaults.
        with open(path, "r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            return deepcopy(defaultProfile)
        return _deepMerge(defaultProfile, data)
    except Exception:
        return deepcopy(defaultProfile)


def loadProfile(profileName: Optional[str] = None) -> dict:
    if not os.path.isdir(profilesDir):
        os.makedirs(profilesDir, exist_ok=True)

    targetPath = _profilePathForName(profileName)
    if os.path.exists(targetPath):
        return _loadProfileFromPath(targetPath)

    if os.path.exists(legacyProfilePath):
        return _loadProfileFromPath(legacyProfilePath)
    return deepcopy(defaultProfile)


def saveProfile(profile: dict, profileName: Optional[str] = None) -> None:
    if not os.path.isdir(profilesDir):
        os.makedirs(profilesDir, exist_ok=True)
    targetPath = _profilePathForName(profileName)
    try:
        with open(targetPath, "w", encoding="utf-8") as handle:
            json.dump(profile, handle, indent=2)
    except Exception:
        return


def ensureProfileFile(profileName: Optional[str] = None) -> dict:
    if not os.path.isdir(profilesDir):
        os.makedirs(profilesDir, exist_ok=True)

    normalized = _normalizeProfileName(profileName)
    targetPath = _profilePathForName(normalized)
    if os.path.exists(targetPath):
        return loadProfile(normalized)

    if os.path.exists(legacyProfilePath):
        profile = _loadProfileFromPath(legacyProfilePath)
    else:
        profile = deepcopy(defaultProfile)

    saveProfile(profile, normalized)
    return profile


def applyProfile(profile: dict) -> None:
    global imageSize
    global ribbonAreaWidth
    global maxMedalsPerSide
    global defaultNameplateWidth
    global nameplateLetterSpacing
    global hoverPreviewSize
    global pocketColSpacing
    global pocketRightOffset
    global pocketXOffset
    global corpusXOffset
    global ribbonsRightAlignOffset
    global awardMedalNames
    global bonusMedalNames
    global characterAliases
    global partCoords
    global categoryLabels
    global enabledCategories
    global allowedAssetsByCategory
    global certificationKeyword
    global certificationsSectionLabel
    global anrocomSectionLabel
    global anrocomSettingsKey
    global ribbonCenteredRowCapacity
    global ribbonRightStartRow
    global ribbonRightFirstRowCapacity
    global ribbonRightSubsequentRowCapacity
    global medalSingleOrder
    global medalMultiOrder
    global expandedIcon
    global collapsedIcon
    global overlayTemplateSize
    global overlayFrontCropBox
    global profileSelectedShirt

    imageSize = max(1, _safeInt(profile.get("image_size", imageSize), imageSize))
    ribbonAreaWidth = max(1, _safeInt(profile.get("ribbon_area_width", ribbonAreaWidth), ribbonAreaWidth))
    maxMedalsPerSide = max(1, _safeInt(profile.get("max_medals_per_side", maxMedalsPerSide), maxMedalsPerSide))
    defaultNameplateWidth = max(1, _safeInt(profile.get("default_nameplate_width", defaultNameplateWidth), defaultNameplateWidth))
    nameplateLetterSpacing = max(0, _safeInt(profile.get("nameplate_letter_spacing", nameplateLetterSpacing), nameplateLetterSpacing))
    hoverPreviewSize = max(16, _safeInt(profile.get("hover_preview_size", hoverPreviewSize), hoverPreviewSize))

    offsets = profile.get("offsets", {})
    if isinstance(offsets, dict):
        pocketColSpacing = _safeInt(offsets.get("pocket_col_spacing", pocketColSpacing), pocketColSpacing)
        pocketRightOffset = _safeInt(offsets.get("pocket_right_offset", pocketRightOffset), pocketRightOffset)
        pocketXOffset = _safeInt(offsets.get("pocket_x_offset", pocketXOffset), pocketXOffset)
        corpusXOffset = _safeInt(offsets.get("corpus_x_offset", corpusXOffset), corpusXOffset)
        ribbonsRightAlignOffset = _safeInt(offsets.get("ribbons_right_align_offset", ribbonsRightAlignOffset), ribbonsRightAlignOffset)

    coords = profile.get("part_coords", {})
    if isinstance(coords, dict):
        updated = dict(partCoords)
        for key, value in coords.items():
            if key not in updated:
                continue
            if isinstance(value, list) and len(value) == 2:
                try:
                    updated[key] = (int(value[0]), int(value[1]))
                except Exception:
                    continue
        partCoords = updated

    medals = profile.get("medals", {})
    if isinstance(medals, dict):
        awardNames = medals.get("award_names")
        bonusNames = medals.get("bonus_names")
        if isinstance(awardNames, list):
            awardMedalNames = {name.strip() for name in awardNames if isinstance(name, str) and name.strip()}
        if isinstance(bonusNames, list):
            bonusMedalNames = {name.strip() for name in bonusNames if isinstance(name, str) and name.strip()}
        medalSingleOrder = _normalizeOrder(medals.get("single_order"), medalSingleOrder)
        medalMultiOrder = _normalizeOrder(medals.get("multi_order"), medalMultiOrder)

    rowCfg = profile.get("ribbon_rows", {})
    if isinstance(rowCfg, dict):
        ribbonCenteredRowCapacity = max(1, _safeInt(rowCfg.get("centered_row_capacity", ribbonCenteredRowCapacity), ribbonCenteredRowCapacity))
        ribbonRightStartRow = max(1, _safeInt(rowCfg.get("right_start_row", ribbonRightStartRow), ribbonRightStartRow))
        ribbonRightFirstRowCapacity = max(1, _safeInt(rowCfg.get("first_right_row_capacity", ribbonRightFirstRowCapacity), ribbonRightFirstRowCapacity))
        ribbonRightSubsequentRowCapacity = max(1, _safeInt(rowCfg.get("subsequent_right_row_capacity", ribbonRightSubsequentRowCapacity), ribbonRightSubsequentRowCapacity))

    aliases = profile.get("character_aliases")
    if isinstance(aliases, dict):
        cleanedAliases = {}
        for k, v in aliases.items():
            if isinstance(k, str) and isinstance(v, str) and k:
                cleanedAliases[k] = v
        if cleanedAliases:
            characterAliases = cleanedAliases

    uiCfg = profile.get("ui", {})
    if isinstance(uiCfg, dict):
        expandedIcon = str(uiCfg.get("expanded_icon", expandedIcon))
        collapsedIcon = str(uiCfg.get("collapsed_icon", collapsedIcon))
        certificationKeyword = str(uiCfg.get("certification_keyword", certificationKeyword)).lower()
        certificationsSectionLabel = str(uiCfg.get("certifications_label", certificationsSectionLabel))
        anrocomSectionLabel = str(uiCfg.get("anrocom_label", anrocomSectionLabel))
        anrocomSettingsKey = str(uiCfg.get("anrocom_settings_key", anrocomSettingsKey))

    categoriesCfg = profile.get("categories", {})
    if isinstance(categoriesCfg, dict):
        labels = categoriesCfg.get("labels")
        if isinstance(labels, dict):
            for key, label in labels.items():
                if key in categoryLabels and isinstance(label, str) and label.strip():
                    categoryLabels[key] = label.strip()

        placement = categoriesCfg.get("placement")
        if isinstance(placement, dict):
            for key, side in placement.items():
                if key in categoryLabels and isinstance(side, str) and side.strip().lower() in ("left", "right"):
                    categoryPlacement[key] = side.strip().lower()

        enabled = categoriesCfg.get("enabled")
        if isinstance(enabled, list):
            normalized = {key for key in enabled if isinstance(key, str) and key in categoryLabels}
            if normalized:
                # Any new category is implicitly enabled for forwards compatibility
                normalized.update(set(categoryLabels.keys()) - set(enabled))
                enabledCategories = normalized

        allowedAssetsByCategory = _normalizeCategoryAssets(categoriesCfg.get("allowed_assets"))

    previewOverlayCfg = profile.get("preview_overlay", {})
    if isinstance(previewOverlayCfg, dict):
        overlayTemplateSize = _normalizeSizePair(
            previewOverlayCfg.get("template_size"),
            overlayTemplateSize,
        )
        overlayFrontCropBox = _normalizeCropBox(
            previewOverlayCfg.get("front_crop_box"),
            overlayFrontCropBox,
        )

    selectedShirt = profile.get("selected_shirt", "")
    if isinstance(selectedShirt, str):
        profileSelectedShirt = selectedShirt.strip()
    else:
        profileSelectedShirt = ""


def _hexToRgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def getThemePalette(name: str, registry: Optional[dict[str, dict[str, str]]] = None) -> dict[str, str]:
    themes = registry if isinstance(registry, dict) else loadThemeRegistry()
    palette = themes.get(name)
    if palette is None:
        palette = builtInThemes["xp"]
    return dict(palette)


def _normalizeSectionNames(values) -> set[str]:
    names: set[str] = set()
    if not isinstance(values, list):
        return names
    for value in values:
        if not isinstance(value, str):
            continue
        cleaned = value.strip()
        if cleaned.lower().endswith(".png"):
            cleaned = cleaned[:-4]
        if cleaned:
            names.add(cleaned)
    return names


def _safeFloat(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safeInt(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _buildPocketCenters(baseX: int, selectedCount: int) -> list[int]:
    slotMap = {
        "left": baseX,
        "middle": baseX + pocketColSpacing,
        "right": baseX + (pocketColSpacing * 2),
    }
    order = medalSingleOrder if selectedCount == 1 else medalMultiOrder
    return [slotMap[token] for token in order]


def _buildWrapAroundCenters(baseX: int, selectedCount: int) -> list[int]:
    slotMap = {
        "left": baseX,
        "middle": baseX + pocketColSpacing,
        "right": baseX + (pocketColSpacing * 2),
    }
    if selectedCount <= 1:
        order = ("middle",)
    elif selectedCount == 2:
        order = ("left", "right")
    else:
        order = ("left", "right", "middle")
    return [slotMap[token] for token in order[:selectedCount]]


def _buildQuartermasterAwardAnchors(baseX: int, yTop: int, selectedCount: int) -> list[tuple[int, int]]:
    slotMap = {
        "left": (baseX, yTop),
        "right": (baseX + (pocketColSpacing * 2), yTop),
        "lower": (baseX + pocketColSpacing, yTop + quartermasterLowerMedalOffset),
    }
    if selectedCount <= 1:
        order = ("left",)
    elif selectedCount == 2:
        order = ("left", "right")
    else:
        order = ("left", "right", "lower")
    return [slotMap[token] for token in order[:selectedCount]]


def _isQuartermasterBracket(item: AssetItem) -> bool:
    token = item.name.strip().rsplit("-", 1)[-1].strip().lower()
    return token == "qmbrk"


def _assetMatchesConfiguredName(item: AssetItem, configuredNames: set[str]) -> bool:
    rawName = item.name.strip()
    displayName = displayAssetName(rawName).strip()
    return rawName in configuredNames or displayName in configuredNames


def _buildRowImages(items: list[AssetItem], safeLoad: Callable[[AssetItem], Optional[Image.Image]]) -> tuple[list[tuple[AssetItem, Image.Image, int, int]], int, int]:
    rowImages: list[tuple[AssetItem, Image.Image, int, int]] = []
    totalWidth = 0
    rowHeight = 0
    for item in items:
        piece = safeLoad(item)
        if piece is None:
            continue
        w, h = piece.size
        rowImages.append((item, piece, w, h))
        totalWidth += w
        rowHeight = max(rowHeight, h)
    return rowImages, totalWidth, rowHeight


def _centeredRowStart(totalWidth: int, areaX: int, areaWidth: int, itemCount: int, offset: int = 0) -> int:
    rowCenter = areaX + areaWidth // 2
    if itemCount == 1:
        return rowCenter - totalWidth // 2 - 1 + offset
    if itemCount == 4:
        return rowCenter - totalWidth // 2 + 1 + offset
    return rowCenter - totalWidth // 2 + offset


def _rightAlignedRowStart(totalWidth: int, itemCount: int, areaX: int, areaWidth: int, offset: int = 0) -> int:
    widthWithSpacing = totalWidth - max(itemCount - 1, 0)
    rightEdge = areaX + areaWidth - 1
    return rightEdge - widthWithSpacing + offset


def _defaultOutputFilename(nameplate: str) -> str:
    rawName = nameplate.strip()
    safeName = "".join(ch for ch in rawName if ch.isalnum() or ch in (" ", "_", "-")).strip()
    safeName = safeName.replace(" ", "_")
    datePrefix = datetime.date.today().strftime("%Y-%m-%d")
    if safeName:
        return f"{datePrefix}_{safeName}.png"
    return f"{datePrefix}.png"


class RibbonRenderer:
    def __init__(self, groups: dict[str, list[AssetItem]]):
        self.groups = groups

    @staticmethod
    def _newUsedSlots() -> dict[str, set[str]]:
        return {
            "sacks": set(),
            "corpus": set(),
            "gorget": set(),
            "spbadge": set(),
            "commendations": set(),
            "certifications": set(),
            "ribbons": set(),
            "hicom": set(),
            "brackets": set(),
        }

    def buildImage(
        self,
        selectedNames: set[str],
        nameplateText: str,
        baseImage: Optional[Image.Image],
        requireNameForNew: bool,
        errorCallback: Optional[Callable[[str], None]],
    ) -> tuple[Optional[Image.Image], Optional[dict[str, set[str]]], Optional[set[str]]]:
        try:
            if baseImage is None:
                if requireNameForNew and nameplateText.strip() == "":
                    raise ValueError("Nametape cannot be blank for a new image.")
                baseImg = Image.new("RGBA", (imageSize, imageSize), (255, 255, 255, 0))
            else:
                baseImg = baseImage.copy().convert("RGBA")

            usedSlots = self._newUsedSlots()

            nameplateImg = None
            nameplateWidth = defaultNameplateWidth
            nameplatePath = os.path.join(charactersDir, "Nameplate.png")
            if os.path.exists(nameplatePath):
                with Image.open(nameplatePath) as img:
                    nameplateImg = img.convert("RGBA")
                    nameplateWidth = nameplateImg.size[0]

            missingAssets: set[str] = set()

            def safeLoad(item: AssetItem) -> Optional[Image.Image]:
                try:
                    return loadRibbonImage(item)
                except Exception:
                    missingAssets.add(item.name)
                    return None

            def selectedItems(category: str) -> list[AssetItem]:
                return [item for item in self.groups[category] if item.name in selectedNames]

            def pasteRibbonRows(
                category: str,
                items: list[AssetItem],
                yStart: int,
                startRow: int = 1,
            ) -> int:
                rowNumber = startRow
                pending = list(items)

                while pending:
                    if rowNumber < ribbonRightStartRow:
                        maxInRow = ribbonCenteredRowCapacity
                        alignRight = False
                    elif rowNumber == ribbonRightStartRow:
                        maxInRow = ribbonRightFirstRowCapacity
                        alignRight = True
                    else:
                        maxInRow = ribbonRightSubsequentRowCapacity
                        alignRight = True

                    row = pending[:maxInRow]
                    pending = pending[maxInRow:]

                    rowImages, totalWidth, rowHeight = _buildRowImages(row, safeLoad)
                    if not rowImages:
                        rowNumber += 1
                        continue

                    if alignRight:
                        xCursor = _rightAlignedRowStart(
                            totalWidth=totalWidth,
                            itemCount=len(rowImages),
                            areaX=partCoords[category][0],
                            areaWidth=ribbonAreaWidth,
                            offset=ribbonsRightAlignOffset,
                        )
                    else:
                        widthWithSpacing = totalWidth - max(len(rowImages) - 1, 0)
                        xCursor = partCoords[category][0] + (
                            (ribbonAreaWidth - widthWithSpacing) // 2
                        ) + ribbonsRightAlignOffset

                    for item, piece, w, _ in rowImages:
                        if item.name not in usedSlots[category]:
                            baseImg.paste(piece, (xCursor, yStart), piece)
                            xCursor += w - 1
                            usedSlots[category].add(item.name)

                    yStart -= rowHeight - 1
                    rowNumber += 1

                return rowNumber

            # Awards / Bonus medals (pocket layout)
            selectedMedals = selectedItems("sacks")
            selectedBrackets = selectedItems("brackets")
            hasQuartermasterBracket = any(_isQuartermasterBracket(item) for item in selectedBrackets)
            awardMedals = [item for item in selectedMedals if _assetMatchesConfiguredName(item, awardMedalNames)]
            bonusMedals = [item for item in selectedMedals if _assetMatchesConfiguredName(item, bonusMedalNames)]

            if len(awardMedals) > maxMedalsPerSide:
                if errorCallback:
                    errorCallback("Only 3 award medals can be applied; extra selections are ignored.")
                awardMedals = awardMedals[:maxMedalsPerSide]
            if len(bonusMedals) > maxMedalsPerSide:
                if errorCallback:
                    errorCallback("Only 3 bonus medals can be applied; extra selections are ignored.")
                bonusMedals = bonusMedals[:maxMedalsPerSide]

            if awardMedals or bonusMedals:
                nametapeCenterX = partCoords["nametape"][0] + (nameplateWidth // 2)
                rightCenterX = nametapeCenterX + pocketRightOffset
                yTop = partCoords["sacks"][1]

                leftSlotX = nametapeCenterX + pocketXOffset
                rightSlotX = rightCenterX + pocketXOffset

                if hasQuartermasterBracket:
                    pocketAnchorsLeft = _buildQuartermasterAwardAnchors(leftSlotX, yTop, len(awardMedals))
                else:
                    pocketAnchorsLeft = [(cx, yTop) for cx in _buildPocketCenters(leftSlotX, len(awardMedals))]
                pocketCentersRight = _buildPocketCenters(rightSlotX, len(bonusMedals))

                for item, (cx, cy) in zip(awardMedals, pocketAnchorsLeft):
                    piece = safeLoad(item)
                    if piece is None:
                        continue
                    w, _ = piece.size
                    if item.name not in usedSlots["sacks"]:
                        baseImg.paste(piece, (int(cx - w / 2), cy), piece)
                        usedSlots["sacks"].add(item.name)

                for item, cx in zip(bonusMedals, pocketCentersRight):
                    piece = safeLoad(item)
                    if piece is None:
                        continue
                    w, _ = piece.size
                    if item.name not in usedSlots["sacks"]:
                        baseImg.paste(piece, (int(cx - w / 2), yTop), piece)
                        usedSlots["sacks"].add(item.name)

            # Gorgets
            for item in self.groups["gorget"]:
                if item.name in selectedNames and item.name not in usedSlots["gorget"]:
                    piece = safeLoad(item)
                    if piece is not None:
                        baseImg.paste(piece, partCoords["gorget"], piece)
                        usedSlots["gorget"].add(item.name)

            # Special badges
            for item in self.groups["spbadge"]:
                if item.name in selectedNames and item.name not in usedSlots["spbadge"]:
                    piece = safeLoad(item)
                    if piece is not None:
                        baseImg.paste(piece, partCoords["spbadge"], piece)
                        usedSlots["spbadge"].add(item.name)

            # HICOM Badges
            for item in self.groups["hicom"]:
                if item.name in selectedNames and item.name not in usedSlots["hicom"]:
                    piece = safeLoad(item)
                    if piece is not None:
                        baseImg.paste(piece, partCoords["hicom"], piece)
                        usedSlots["hicom"].add(item.name)

            # Brackets
            if selectedBrackets:
                yStart = partCoords["brackets"][1]
                pocketY = partCoords["sacks"][1]
                nametapeCenterX = partCoords["nametape"][0] + (nameplateWidth // 2)
                rightCenterX = nametapeCenterX + pocketRightOffset
                leftSlotX = nametapeCenterX + pocketXOffset
                rightSlotX = rightCenterX + pocketXOffset

                quartermasterBracket = next(
                    (item for item in selectedBrackets if _isQuartermasterBracket(item)),
                    None,
                )
                remainingBrackets = [
                    item for item in selectedBrackets if quartermasterBracket is None or item.name != quartermasterBracket.name
                ]

                if len(remainingBrackets) > maxMedalsPerSide * 2:
                    if errorCallback:
                        errorCallback("Only 6 bottom brackets can be applied; extra selections are ignored.")
                    remainingBrackets = remainingBrackets[: maxMedalsPerSide * 2]

                if quartermasterBracket is not None and quartermasterBracket.name not in usedSlots["brackets"]:
                    piece = safeLoad(quartermasterBracket)
                    if piece is not None:
                        w, h = piece.size
                        quartermasterCenterX = leftSlotX + pocketColSpacing + quartermasterBracketXOffset
                        baseImg.paste(
                            piece,
                            (int(quartermasterCenterX - w / 2), int(pocketY + quartermasterBracketTopOffset)),
                            piece,
                        )
                        usedSlots["brackets"].add(quartermasterBracket.name)

                leftCapacity = maxMedalsPerSide
                leftBrackets = remainingBrackets[:leftCapacity]
                rightBrackets = remainingBrackets[leftCapacity:leftCapacity + maxMedalsPerSide]

                bracketColumns = (
                    (
                        leftBrackets,
                        _buildPocketCenters(leftSlotX, len(leftBrackets)),
                    ),
                    (rightBrackets, _buildPocketCenters(rightSlotX, len(rightBrackets))),
                )

                for bracketItems, centers in bracketColumns:
                    for item, cx in zip(bracketItems, centers):
                        piece = safeLoad(item)
                        if piece is None:
                            continue
                        w, _ = piece.size
                        if item.name not in usedSlots["brackets"]:
                            baseImg.paste(piece, (int(cx - w / 2), yStart), piece)
                            usedSlots["brackets"].add(item.name)

            # Commendations
            selectedComm = selectedItems("commendations")
            yStart = partCoords["commendations"][1]
            maxPerRow = 4
            rowCount = 0
            secondRow = False

            while selectedComm:
                rowCount += 1
                if rowCount >= 2:
                    secondRow = True

                row = selectedComm[:maxPerRow]
                selectedComm = selectedComm[maxPerRow:]

                rowImages, totalWidth, rowHeight = _buildRowImages(row, safeLoad)
                if not rowImages:
                    continue

                xCursor = _centeredRowStart(
                    totalWidth=totalWidth,
                    areaX=partCoords["commendations"][0],
                    areaWidth=ribbonAreaWidth,
                    itemCount=len(row),
                )

                for item, piece, w, _ in rowImages:
                    if item.name not in usedSlots["commendations"]:
                        baseImg.paste(piece, (xCursor, yStart), piece)
                        xCursor += w - 1
                        usedSlots["commendations"].add(item.name)
                yStart -= rowHeight - 1

            # Corpus commendations
            selectedCorpus = selectedItems("corpus")
            if selectedCorpus:
                yStart = partCoords["corpus"][1]
                if not secondRow:
                    yStart += 3

                while selectedCorpus:
                    row = selectedCorpus[:maxPerRow]
                    selectedCorpus = selectedCorpus[maxPerRow:]

                    rowImages, totalWidth, rowHeight = _buildRowImages(row, safeLoad)
                    if not rowImages:
                        continue

                    xCursor = _centeredRowStart(
                        totalWidth=totalWidth,
                        areaX=partCoords["corpus"][0],
                        areaWidth=ribbonAreaWidth,
                        itemCount=len(row),
                        offset=corpusXOffset,
                    )

                    for item, piece, w, _ in rowImages:
                        if item.name not in usedSlots["corpus"]:
                            baseImg.paste(piece, (xCursor, yStart), piece)
                            xCursor += w - 1
                            usedSlots["corpus"].add(item.name)

                    yStart -= rowHeight

            # Ribbons / certifications share one continuous row stack.
            selectedRibbons = (
                selectedItems("certifications")
                + selectedItems("ribbons")
                + selectedItems("anrocom")
            )
            pasteRibbonRows(
                category="ribbons",
                items=selectedRibbons,
                yStart=partCoords["ribbons"][1],
            )

            # Nametape
            if nameplateText.strip():
                npX, npY = partCoords["nametape"]
                if nameplateImg is None:
                    if not os.path.exists(nameplatePath):
                        raise FileNotFoundError(f"Missing nameplate image: {nameplatePath}")
                    with Image.open(nameplatePath) as img:
                        nameplateImg = img.convert("RGBA")

                baseImg.paste(nameplateImg, (npX, npY), nameplateImg)

                letters: list[tuple[Optional[Image.Image], int]] = []
                totalWidth = 0
                for ch in nameplateText.upper():
                    try:
                        letterImg = loadCharacterImage(ch)
                    except FileNotFoundError:
                        if ch == " ":
                            letters.append((None, 2))
                            totalWidth += 2
                        continue
                    w, _ = letterImg.size
                    letters.append((letterImg, w))
                    totalWidth += w

                if letters:
                    totalWidth += nameplateLetterSpacing * (len(letters) - 1)
                    startX = npX + (nameplateImg.size[0] - totalWidth) // 2
                    for index, (letterImg, width) in enumerate(letters):
                        if letterImg is not None:
                            baseImg.paste(letterImg, (startX, npY + 1), letterImg)
                        startX += width
                        if index < len(letters) - 1:
                            startX += nameplateLetterSpacing

            if missingAssets and errorCallback:
                missingList = ", ".join(sorted(missingAssets))
                errorCallback(f"Missing assets: {missingList}")

            return baseImg, usedSlots, missingAssets

        except Exception as exc:
            if errorCallback:
                errorCallback(str(exc))
            return None, None, None


class RibbonEngineApp:
    def __init__(self):
        self.settingsData = ensureSettingsDefaults(loadSettings())
        self.profileName = _normalizeProfileName(self.settingsData.get("profile", defaultProfileName))
        self.profileData = ensureProfileFile(self.profileName)
        applyProfile(self.profileData)

        self.themeRegistry = loadThemeRegistry()
        self.themeName = self.settingsData.get("theme", "xp")
        if self.themeName not in self.themeRegistry:
            self.themeName = "xp"
        self.theme = getThemePalette(self.themeName, self.themeRegistry)
        self.themeBgRgb = _hexToRgb(self.theme["bg"])

        self.baseImage: Optional[Image.Image] = None
        self.previewImg: Optional[ImageTk.PhotoImage] = None
        self.hoverPreviewImg: Optional[ImageTk.PhotoImage] = None
        self.previewJob: Optional[str] = None
        self.themeEditorWindow: Optional[tk.Toplevel] = None
        self.ribbonTutorialWindow: Optional[tk.Toplevel] = None
        self.assetImporterWindow: Optional[tk.Toplevel] = None
        self.themeEditorNameVar: Optional[tk.StringVar] = None
        self.themeEditorColorVars: dict[str, tk.StringVar] = {}
        self.themeEditorPreviewLabels: dict[str, tk.Label] = {}
        self.themeEditorOriginalPalette: Optional[dict[str, str]] = None
        self.uiBadgeImg: Optional[ImageTk.PhotoImage] = None

        self.root = tk.Tk()
        self.root.title("ANRO Ribbon Engine")
        self.root.geometry("700x500")
        self.root.option_add("*Font", ("Tahoma", 9))
        self.profileVar = tk.StringVar(master=self.root, value=self.profileName)
        self.presetVar = tk.StringVar(master=self.root, value=str(self.settingsData.get("selected_preset", "")).strip())
        self.overlaySourcePath = self._resolveProfileShirtPath(profileSelectedShirt)
        if not self.overlaySourcePath and os.path.exists(previewOverlayPath):
            self.overlaySourcePath = previewOverlayPath

        self._configureStyle()

        try:
            self.ribbonGroups = loadRibbonGroups()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            self.ribbonGroups = {key: [] for key in categoryLabels}

        self.renderer = RibbonRenderer(self.ribbonGroups)

        self.checkboxVars: dict[str, tk.IntVar] = {}
        self.categorySections: list[SectionUI] = []

        self._buildLayout()
        self._buildSections()
        self._loadCollapsedSettings()
        self.applyFilter()
        self.updatePreviewScaleLabel()
        self.updatePreview()
        self.clearHoverPreview()

    def _configureStyle(self) -> None:
        style = ttk.Style(self.root)
        for systemTheme in ("xpnative", "vista", "winnative", "clam"):
            if systemTheme in style.theme_names():
                style.theme_use(systemTheme)
                break

        style.configure("TFrame", background=self.theme["bg"])
        style.configure("TLabel", background=self.theme["bg"], foreground=self.theme["text"])
        style.configure(
            "TCombobox",
            fieldbackground=self.theme["panel_bg"],
            background=self.theme["panel_bg"],
            foreground=self.theme["text"],
            arrowcolor=self.theme["text"],
        )
        style.configure(
            "Header.TCombobox",
            fieldbackground=self.theme["theme_selector_bg"],
            background=self.theme["theme_selector_bg"],
            foreground=self.theme["theme_selector_text"],
            arrowcolor=self.theme["theme_selector_text"],
            padding=3,
        )
        style.configure(
            "Profile.TCombobox",
            fieldbackground=self.theme["profile_selector_bg"],
            background=self.theme["profile_selector_bg"],
            foreground=self.theme["profile_selector_text"],
            arrowcolor=self.theme["profile_selector_text"],
            padding=3,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", self.theme["panel_bg"])],
            selectbackground=[("readonly", self.theme["accent"])],
            selectforeground=[("readonly", self.theme["header_fg"])],
            foreground=[("readonly", self.theme["text"])],
        )
        style.map(
            "Header.TCombobox",
            fieldbackground=[("readonly", self.theme["theme_selector_bg"])],
            selectbackground=[("readonly", self.theme["accent"])],
            selectforeground=[("readonly", self.theme["header_fg"])],
            foreground=[("readonly", self.theme["theme_selector_text"])],
        )
        style.map(
            "Profile.TCombobox",
            fieldbackground=[("readonly", self.theme["profile_selector_bg"])],
            selectbackground=[("readonly", self.theme["accent"])],
            selectforeground=[("readonly", self.theme["header_fg"])],
            foreground=[("readonly", self.theme["profile_selector_text"])],
        )
        style.configure(
            "TEntry",
            padding=4,
            fieldbackground=self.theme["panel_bg"],
            foreground=self.theme["text"],
            insertcolor=self.theme["text"],
        )
        style.configure(
            "Nametape.TEntry",
            padding=4,
            fieldbackground=self.theme["nametape_bg"],
            foreground=self.theme["nametape_text"],
            insertcolor=self.theme["nametape_text"],
        )
        style.configure(
            "Search.TEntry",
            padding=4,
            fieldbackground=self.theme["search_bg"],
            foreground=self.theme["search_text"],
            insertcolor=self.theme["search_text"],
        )
        style.map(
            "Search.TEntry",
            fieldbackground=[("!disabled", self.theme["search_bg"])],
            foreground=[("!disabled", self.theme["search_text"])],
        )
        style.configure(
            "Section.TLabel",
            background=self.theme["bg"],
            foreground=self.theme["accent"],
            font=("Tahoma", 9, "bold"),
        )
        style.configure("Toggle.TButton", font=("Tahoma", 7, "bold"), padding=(0, 0))
        style.configure("TButton", padding=(10, 6))
        style.configure("TCheckbutton", background=self.theme["bg"], foreground=self.theme["text"])
        self.root.configure(background=self.theme["bg"])

    def _buildLayout(self) -> None:
        self.headerFrame = tk.Frame(self.root, bg=self.theme["header_bg"])
        self.headerFrame.pack(fill="x")

        self.headerTitle = tk.Label(
            self.headerFrame,
            text="ANRO Ribbon Engine",
            bg=self.theme["header_bg"],
            fg=self.theme["header_fg"],
            font=("Tahoma", 11, "bold"),
            padx=10,
            pady=6,
        )
        self.headerTitle.pack(side="left")

        self.helpButton = tk.Button(
            self.headerFrame,
            text="How to Add Ribbons",
            command=self.openRibbonTutorial,
            bg=self.theme["header_bg"],
            fg=self.theme["header_fg"],
            activebackground=self.theme["accent"],
            activeforeground=self.theme["header_fg"],
            relief="raised",
            bd=1,
            padx=8,
            pady=3,
            font=("Tahoma", 9, "bold"),
            highlightthickness=0,
        )
        self.helpButton.pack(side="right", padx=(0, 8), pady=4)

        self.addRibbonButton = tk.Button(
            self.headerFrame,
            text="Add Ribbon",
            command=self.openAssetImporter,
            bg=self.theme["header_bg"],
            fg=self.theme["header_fg"],
            activebackground=self.theme["accent"],
            activeforeground=self.theme["header_fg"],
            relief="raised",
            bd=1,
            padx=8,
            pady=3,
            font=("Tahoma", 9, "bold"),
            highlightthickness=0,
        )
        self.addRibbonButton.pack(side="right", padx=(0, 8), pady=4)

        self.themeRow = tk.Frame(self.headerFrame, bg=self.theme["header_bg"])
        self.themeRow.pack(side="right", padx=8, pady=4)
        self.themeLabel = tk.Label(
            self.themeRow,
            text="Current Theme:",
            bg=self.theme["header_bg"],
            fg=self.theme["header_fg"],
            font=("Tahoma", 10, "bold"),
        )
        self.themeLabel.pack(side="left", padx=(0, 6))
        self.themeVar = tk.StringVar(master=self.root, value=self.themeName)
        self.themeCombo = ttk.Combobox(
            self.themeRow,
            textvariable=self.themeVar,
            state="readonly",
            width=18,
            style="Header.TCombobox",
            font=("Tahoma", 9, "bold"),
        )
        self.themeCombo.pack(side="left")
        self.themeCombo.bind("<<ComboboxSelected>>", self._onThemeChanged)
        ttk.Button(self.themeRow, text="New", width=7, command=self.createThemeFromCurrent).pack(side="left", padx=(6, 2))
        ttk.Button(self.themeRow, text="Settings", width=8, command=self.openThemeSettings).pack(side="left", padx=2)
        ttk.Button(self.themeRow, text="Import", width=7, command=self.importTheme).pack(side="left", padx=2)
        ttk.Button(self.themeRow, text="Export", width=7, command=self.exportTheme).pack(side="left", padx=2)
        ttk.Button(self.themeRow, text="Folder", width=7, command=self.openThemesFolder).pack(side="left", padx=(2, 0))
        self.refreshThemeChoices()
        self._buildUiBadge()

        self.mainFrame = tk.Frame(self.root, bg=self.theme["bg"])
        self.mainFrame.pack(fill="both", expand=True)

        self.leftFrame = tk.Frame(self.mainFrame, bg=self.theme["bg"])
        self.leftFrame.pack(side="left", fill="both", expand=True)

        self.rightFrame = tk.Frame(self.mainFrame, bg=self.theme["panel_bg"], bd=1, relief="sunken")
        self.rightFrame.pack(side="right", fill="y", padx=10, pady=10)

        self.canvas = tk.Canvas(self.leftFrame, background=self.theme["bg"], highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(self.leftFrame, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.scrollableFrame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.scrollableFrame, anchor="nw")
        self.scrollableFrame.bind("<Configure>", self._onCanvasConfigure)

        self.root.bind_all("<MouseWheel>", self._onMousewheel)
        self.root.bind_all("<Button-4>", self._onMousewheel)
        self.root.bind_all("<Button-5>", self._onMousewheel)

        profileRow = ttk.Frame(self.scrollableFrame)
        profileRow.pack(fill="x", pady=(6, 4))
        ttk.Label(profileRow, text="Profile:").pack(side="left")
        self.profileCombo = ttk.Combobox(
            profileRow,
            textvariable=self.profileVar,
            state="readonly",
            width=24,
            style="Profile.TCombobox",
        )
        self.profileCombo.pack(side="left", padx=(6, 6))
        self.profileCombo.bind("<<ComboboxSelected>>", self._onProfileChanged)
        ttk.Button(profileRow, text="Reload", width=8, command=self.reloadCurrentProfile).pack(side="left")
        self.refreshProfileChoices()

        presetRow = ttk.Frame(self.scrollableFrame)
        presetRow.pack(fill="x", pady=(2, 6))
        ttk.Label(presetRow, text="Preset:").pack(side="left")
        self.presetCombo = ttk.Combobox(
            presetRow,
            textvariable=self.presetVar,
            state="readonly",
            width=24,
            style="Profile.TCombobox",
        )
        self.presetCombo.pack(side="left", padx=(10, 6))
        self.presetCombo.bind("<<ComboboxSelected>>", self._onPresetChanged)
        ttk.Button(presetRow, text="Load", width=8, command=self.loadSelectedPreset).pack(side="left", padx=(0, 4))
        ttk.Button(presetRow, text="Save", width=8, command=self.savePreset).pack(side="left", padx=4)
        ttk.Button(presetRow, text="Delete", width=8, command=self.deleteSelectedPreset).pack(side="left", padx=(4, 0))
        self.refreshPresetChoices()

        ttk.Label(self.scrollableFrame, text="Nametape:").pack(pady=5)
        self.entry = ttk.Entry(self.scrollableFrame, style="Nametape.TEntry")
        self.entry.pack(pady=5)
        self.entry.bind("<KeyRelease>", lambda _event: self.schedulePreview())

        ttk.Label(self.scrollableFrame, text="Search:").pack(pady=(10, 5))
        self.searchVar = tk.StringVar()
        self.searchEntry = tk.Entry(
            self.scrollableFrame,
            textvariable=self.searchVar,
            bg=self.theme["search_bg"],
            fg=self.theme["search_text"],
            insertbackground=self.theme["search_text"],
            selectbackground=self.theme["accent"],
            selectforeground=self.theme["header_fg"],
            relief="sunken",
            bd=1,
            width=24,
        )
        self.searchEntry.pack(pady=(0, 10))
        self.searchEasterEggActive = False
        self.searchEntry.bind("<KeyRelease>", self._onSearchKeyRelease)
        self.caseSensitiveSearchVar = tk.BooleanVar(
            value=bool(self.settingsData.get("case_sensitive_search", False))
        )
        ttk.Checkbutton(
            self.scrollableFrame,
            text="Case-sensitive search",
            variable=self.caseSensitiveSearchVar,
            command=self._onToggleCaseSensitiveSearch,
        ).pack(pady=(0, 10))

        self.showSelectedVar = tk.BooleanVar(value=bool(self.settingsData.get("only_show_selected", False)))
        ttk.Checkbutton(
            self.scrollableFrame,
            text="Only show selected",
            variable=self.showSelectedVar,
            command=self._onToggleShowSelected,
        ).pack(pady=(0, 10))

        self.overlayVar = tk.BooleanVar(value=bool(self.settingsData.get("preview_overlay", False)))
        ttk.Checkbutton(
            self.scrollableFrame,
            text="Show shirt preview",
            variable=self.overlayVar,
            command=self._onToggleOverlay,
        ).pack(pady=(0, 10))

        self.overlaySourceLabel = ttk.Label(self.scrollableFrame, text="")
        self.overlaySourceLabel.pack(anchor="w", pady=(0, 8))
        self.updateOverlaySourceLabel()

        columnsFrame = ttk.Frame(self.scrollableFrame)
        columnsFrame.pack(fill="x", expand=True)

        self.leftColumn = ttk.Frame(columnsFrame)
        self.leftColumn.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.rightColumn = ttk.Frame(columnsFrame)
        self.rightColumn.pack(side="right", fill="both", expand=True)

        ttk.Button(self.scrollableFrame, text="Paste Image from Clipboard", command=self.pasteFromClipboard).pack(pady=5)
        ttk.Button(self.scrollableFrame, text="Clear All", command=self.clearAll).pack(pady=5)
        ttk.Button(self.scrollableFrame, text="Generate Image", command=self.generateImage).pack(pady=10)

        ttk.Label(self.rightFrame, text="Preview", style="Section.TLabel").pack(pady=(4, 0))
        self.labelPreview = ttk.Label(self.rightFrame)
        self.labelPreview.pack(pady=10)

        self.labelStatus = tk.Label(
            self.rightFrame,
            text="",
            fg=self.theme["status"],
            bg=self.theme["panel_bg"],
            justify="left",
        )
        self.labelStatus.pack(pady=(0, 10))

        self.previewScale = _safeFloat(self.settingsData.get("preview_scale", 1.0), 1.0)
        if self.previewScale < 1.0:
            self.previewScale = 1.0

        self.previewSizeLabel = ttk.Label(self.rightFrame, text="Preview size: 1.0x")
        self.previewSizeLabel.pack()

        previewControls = ttk.Frame(self.rightFrame)
        previewControls.pack(pady=(5, 10))
        ttk.Button(previewControls, text="-", width=3, command=lambda: self.adjustPreviewScale(-0.5)).pack(side="left", padx=2)
        ttk.Button(previewControls, text="+", width=3, command=lambda: self.adjustPreviewScale(0.5)).pack(side="left", padx=2)

        ttk.Label(self.rightFrame, text="Hover Preview", style="Section.TLabel").pack(pady=(10, 0))
        self.hoverPreviewLabel = ttk.Label(self.rightFrame)
        self.hoverPreviewLabel.pack(pady=6)
        self.hoverNameLabel = ttk.Label(self.rightFrame, text="")
        self.hoverNameLabel.pack()

        self.root.bind_all("<Control-f>", self.focusSearch)
        self.root.bind_all("<KeyPress-slash>", self.focusSearch)

    def _buildUiBadge(self) -> None:
        self.uiBadgeLabel = tk.Label(self.headerFrame, bg=self.theme["header_bg"], bd=0)
        self.uiBadgeLabel.pack(side="right", padx=(0, 8), pady=3)
        self._refreshUiBadge()

    def _refreshUiBadge(self) -> None:
        self.uiBadgeImg = None
        if os.path.exists(uiBadgePath):
            try:
                with Image.open(uiBadgePath) as img:
                    badge = img.convert("RGBA")
                    scale = min(uiBadgeMaxSize / badge.width, uiBadgeMaxSize / badge.height, 1.0)
                    targetSize = (
                        max(1, int(round(badge.width * scale))),
                        max(1, int(round(badge.height * scale))),
                    )
                    if targetSize != badge.size:
                        badge = badge.resize(targetSize, Image.LANCZOS)
                    self.uiBadgeImg = ImageTk.PhotoImage(badge)
            except Exception:
                self.uiBadgeImg = None
        self.uiBadgeLabel.configure(image=self.uiBadgeImg)

    def refreshThemeChoices(self) -> None:
        self.themeRegistry = loadThemeRegistry()
        names = list(self.themeRegistry.keys())
        self.themeCombo["values"] = names
        if self.themeName not in self.themeRegistry:
            self.themeName = "xp"
        self.themeVar.set(self.themeName)

    def _updateTkWidgetColors(self) -> None:
        self.root.configure(background=self.theme["bg"])
        self.headerFrame.configure(bg=self.theme["header_bg"])
        self.headerTitle.configure(bg=self.theme["header_bg"], fg=self.theme["header_fg"])
        self.helpButton.configure(
            bg=self.theme["header_bg"],
            fg=self.theme["header_fg"],
            activebackground=self.theme["accent"],
            activeforeground=self.theme["header_fg"],
        )
        self.themeRow.configure(bg=self.theme["header_bg"])
        self.themeLabel.configure(bg=self.theme["header_bg"], fg=self.theme["header_fg"])
        self.uiBadgeLabel.configure(bg=self.theme["header_bg"])
        self.mainFrame.configure(bg=self.theme["bg"])
        self.leftFrame.configure(bg=self.theme["bg"])
        self.rightFrame.configure(bg=self.theme["panel_bg"])
        self.canvas.configure(background=self.theme["bg"])
        self.labelStatus.configure(bg=self.theme["panel_bg"], fg=self.theme["status"])
        self.searchEntry.configure(
            bg=self.theme["search_bg"],
            fg=self.theme["search_text"],
            insertbackground=self.theme["search_text"],
            selectbackground=self.theme["accent"],
            selectforeground=self.theme["header_fg"],
        )
        self.root.option_add("*TCombobox*Listbox.background", self.theme["profile_selector_bg"])
        self.root.option_add("*TCombobox*Listbox.foreground", self.theme["profile_selector_text"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", self.theme["accent"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", self.theme["header_fg"])

    def _clearThemeHighlight(self) -> None:
        try:
            self.themeCombo.selection_clear()
        except Exception:
            pass
        try:
            self.themeCombo.icursor(tk.END)
        except Exception:
            pass
        try:
            self.root.focus_set()
        except Exception:
            pass

    def _applyTheme(self, themeName: str, *, persist: bool = True) -> None:
        self.refreshThemeChoices()
        if themeName not in self.themeRegistry:
            themeName = "xp"
        self.themeName = themeName
        self.themeVar.set(self.themeName)
        self.theme = getThemePalette(self.themeName, self.themeRegistry)
        self.themeBgRgb = _hexToRgb(self.theme["bg"])
        self._configureStyle()
        self._updateTkWidgetColors()
        self.updatePreview()
        self.clearHoverPreview()
        self.root.after_idle(self._clearThemeHighlight)
        if persist:
            self.saveCurrentSettings()

    def _onThemeChanged(self, _event=None) -> None:
        self._applyTheme(self.themeVar.get())

    def createThemeFromCurrent(self) -> None:
        suggestedName = f"{self.themeName.title()} Copy"
        themeName = simpledialog.askstring(
            "Create Theme",
            "Theme name:",
            initialvalue=suggestedName,
            parent=self.root,
        )
        if themeName is None:
            return
        try:
            path = saveCustomTheme(themeName, self.theme)
        except Exception as exc:
            messagebox.showerror("Theme Error", str(exc))
            return
        savedName = os.path.splitext(os.path.basename(path))[0]
        self.refreshThemeChoices()
        self._applyTheme(savedName)
        messagebox.showinfo(
            "Theme Created",
            f"Saved {savedName}.json in the Themes folder.\nYou can edit and share that file with other people.",
        )

    def openThemeSettings(self) -> None:
        if self.themeEditorWindow is not None and self.themeEditorWindow.winfo_exists():
            self.themeEditorWindow.lift()
            self.themeEditorWindow.focus_force()
            return

        window = tk.Toplevel(self.root)
        window.title("Theme Settings")
        window.geometry("540x620")
        window.configure(bg=self.theme["bg"])
        window.transient(self.root)
        window.resizable(True, True)
        window.minsize(540, 420)
        self.themeEditorWindow = window
        self.themeEditorNameVar = tk.StringVar(value=f"{self.themeName.title()} Custom")
        self.themeEditorColorVars = {}
        self.themeEditorPreviewLabels = {}
        self.themeEditorOriginalPalette = dict(self.theme)

        def onClose() -> None:
            if self.themeEditorOriginalPalette is not None:
                self._applyThemePalette(self.themeEditorOriginalPalette)
            self.themeEditorWindow = None
            self.themeEditorNameVar = None
            self.themeEditorColorVars = {}
            self.themeEditorPreviewLabels = {}
            self.themeEditorOriginalPalette = None
            window.destroy()

        window.protocol("WM_DELETE_WINDOW", onClose)

        outerFrame = tk.Frame(window, bg=self.theme["bg"])
        outerFrame.pack(fill="both", expand=True)

        editorCanvas = tk.Canvas(outerFrame, bg=self.theme["bg"], highlightthickness=0)
        editorCanvas.pack(side="left", fill="both", expand=True)
        editorScrollbar = ttk.Scrollbar(outerFrame, orient="vertical", command=editorCanvas.yview)
        editorScrollbar.pack(side="right", fill="y")
        editorCanvas.configure(yscrollcommand=editorScrollbar.set)

        contentFrame = tk.Frame(editorCanvas, bg=self.theme["bg"])
        editorCanvasWindow = editorCanvas.create_window((0, 0), window=contentFrame, anchor="nw")

        def syncEditorScrollregion(_event=None) -> None:
            editorCanvas.configure(scrollregion=editorCanvas.bbox("all"))

        def syncEditorWidth(event) -> None:
            editorCanvas.itemconfigure(editorCanvasWindow, width=event.width)

        def scrollEditor(delta: int) -> None:
            first, last = editorCanvas.yview()
            if (delta < 0 and first <= 0.0) or (delta > 0 and last >= 1.0):
                return
            editorCanvas.yview_scroll(delta, "units")

        def onEditorMousewheel(event) -> str | None:
            widget = window.winfo_containing(event.x_root, event.y_root)
            if widget is None:
                return None
            parent = widget
            while parent is not None and parent is not window:
                if parent is contentFrame or parent is editorCanvas:
                    break
                parent = parent.master
            else:
                return None

            if getattr(event, "delta", 0):
                delta = -1 if event.delta > 0 else 1
                if abs(event.delta) >= 120:
                    delta = int(-event.delta / 120)
                scrollEditor(delta)
                return "break"
            if getattr(event, "num", None) == 4:
                scrollEditor(-1)
                return "break"
            if getattr(event, "num", None) == 5:
                scrollEditor(1)
                return "break"
            return None

        contentFrame.bind("<Configure>", syncEditorScrollregion)
        editorCanvas.bind("<Configure>", syncEditorWidth)
        window.bind("<MouseWheel>", onEditorMousewheel)
        window.bind("<Button-4>", onEditorMousewheel)
        window.bind("<Button-5>", onEditorMousewheel)

        titleLabel = tk.Label(
            contentFrame,
            text="Theme Settings",
            bg=self.theme["bg"],
            fg=self.theme["text"],
            font=("Tahoma", 11, "bold"),
        )
        titleLabel.pack(anchor="w", padx=14, pady=(12, 6))

        helpLabel = tk.Label(
            contentFrame,
            text="Pick colors below, then apply them now or save them as a shareable theme.",
            bg=self.theme["bg"],
            fg=self.theme["text"],
            justify="left",
        )
        helpLabel.pack(anchor="w", padx=14, pady=(0, 10))

        nameRow = tk.Frame(contentFrame, bg=self.theme["bg"])
        nameRow.pack(fill="x", padx=14, pady=(0, 8))
        tk.Label(nameRow, text="Theme name:", bg=self.theme["bg"], fg=self.theme["text"], width=12, anchor="w").pack(side="left")
        nameEntry = tk.Entry(
            nameRow,
            textvariable=self.themeEditorNameVar,
            width=28,
            bg=self.theme["theme_selector_bg"],
            fg=self.theme["theme_selector_text"],
            insertbackground=self.theme["theme_selector_text"],
            selectbackground=self.theme["accent"],
            selectforeground=self.theme["header_fg"],
            relief="sunken",
            bd=1,
        )
        nameEntry.pack(side="left", fill="x", expand=True)

        colorsFrame = tk.Frame(contentFrame, bg=self.theme["bg"])
        colorsFrame.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        colorLabels = {
            "bg": "Main background",
            "panel_bg": "Panel background",
            "text": "Text",
            "accent": "Accent",
            "header_bg": "Header background",
            "header_fg": "Header text",
            "status": "Status text",
            "theme_selector_bg": "Theme selector bg",
            "theme_selector_text": "Theme selector text",
            "profile_selector_bg": "Profile selector bg",
            "profile_selector_text": "Profile selector text",
            "nametape_bg": "Nametape bg",
            "nametape_text": "Nametape text",
            "search_bg": "Search bg",
            "search_text": "Search text",
        }

        for key in themeColorKeys:
            row = tk.Frame(colorsFrame, bg=self.theme["bg"])
            row.pack(fill="x", pady=4)
            tk.Label(row, text=f"{colorLabels[key]}:", bg=self.theme["bg"], fg=self.theme["text"], width=20, anchor="w").pack(side="left")
            colorVar = tk.StringVar(value=self.theme[key])
            self.themeEditorColorVars[key] = colorVar
            valueLabel = tk.Label(row, textvariable=colorVar, bg=self.theme["bg"], fg=self.theme["text"], width=10, anchor="w")
            valueLabel.pack(side="left", padx=(0, 8))
            preview = tk.Label(row, bg=colorVar.get(), width=3, relief="solid", bd=1)
            preview.pack(side="left", padx=(0, 8))
            self.themeEditorPreviewLabels[key] = preview
            ttk.Button(row, text="Choose", width=8, command=lambda themeKey=key: self._chooseThemeColor(themeKey)).pack(side="left")

        actions = tk.Frame(contentFrame, bg=self.theme["bg"])
        actions.pack(fill="x", padx=14, pady=(0, 12))
        ttk.Button(actions, text="Apply Now", command=self.applyThemeEditorChanges).pack(side="left")
        ttk.Button(actions, text="Save Theme", command=self.saveThemeEditorChanges).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Reset", command=self.resetThemeEditorFields).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Close", command=onClose).pack(side="right")

    def _chooseThemeColor(self, themeKey: str) -> None:
        if themeKey not in self.themeEditorColorVars:
            return
        initial = self.themeEditorColorVars[themeKey].get()
        _rgb, color = colorchooser.askcolor(color=initial, title=f"Choose {themeKey}", parent=self.themeEditorWindow)
        if not color:
            return
        self.themeEditorColorVars[themeKey].set(color)
        preview = self.themeEditorPreviewLabels.get(themeKey)
        if preview is not None:
            preview.configure(bg=color)
        self._previewThemeEditorChanges()

    def _applyThemePalette(self, palette: dict[str, str]) -> None:
        self.theme = dict(palette)
        self.themeBgRgb = _hexToRgb(self.theme["bg"])
        self._configureStyle()
        self._updateTkWidgetColors()
        self._refreshThemeEditorWindowColors()
        self.updatePreview()
        self.clearHoverPreview()

    def _previewThemeEditorChanges(self) -> None:
        try:
            palette = self._collectThemeEditorPalette()
        except Exception:
            return
        self._applyThemePalette(palette)

    def _refreshThemeEditorWindowColors(self) -> None:
        window = self.themeEditorWindow
        if window is None or not window.winfo_exists():
            return

        def repaint(widget) -> None:
            try:
                if widget in self.themeEditorPreviewLabels.values():
                    return
                if isinstance(widget, tk.Canvas):
                    widget.configure(bg=self.theme["bg"])
                elif isinstance(widget, tk.Frame):
                    widget.configure(bg=self.theme["bg"])
                elif isinstance(widget, tk.Label):
                    widget.configure(bg=self.theme["bg"], fg=self.theme["text"])
                elif isinstance(widget, tk.Entry):
                    widget.configure(
                        bg=self.theme["theme_selector_bg"],
                        fg=self.theme["theme_selector_text"],
                        insertbackground=self.theme["theme_selector_text"],
                        selectbackground=self.theme["accent"],
                        selectforeground=self.theme["header_fg"],
                    )
                elif isinstance(widget, tk.Toplevel):
                    widget.configure(bg=self.theme["bg"])
            except Exception:
                pass

            for child in widget.winfo_children():
                repaint(child)

        repaint(window)

    def _collectThemeEditorPalette(self) -> dict[str, str]:
        palette: dict[str, str] = {}
        for key in themeColorKeys:
            colorVar = self.themeEditorColorVars.get(key)
            value = colorVar.get().strip() if colorVar is not None else ""
            if not _isValidHexColor(value):
                raise ValueError(f"{key} must be a hex color like #1e1e1e.")
            palette[key] = value
        return palette

    def applyThemeEditorChanges(self) -> None:
        try:
            palette = self._collectThemeEditorPalette()
        except Exception as exc:
            messagebox.showerror("Theme Error", str(exc), parent=self.themeEditorWindow)
            return

        self._applyThemePalette(palette)
        self.themeEditorOriginalPalette = dict(self.theme)

    def saveThemeEditorChanges(self) -> None:
        if self.themeEditorNameVar is None:
            return
        try:
            palette = self._collectThemeEditorPalette()
            themeName = self.themeEditorNameVar.get().strip()
            path = saveCustomTheme(themeName, palette)
        except Exception as exc:
            messagebox.showerror("Theme Error", str(exc), parent=self.themeEditorWindow)
            return

        savedName = os.path.splitext(os.path.basename(path))[0]
        self.refreshThemeChoices()
        self._applyTheme(savedName)
        self.themeEditorOriginalPalette = dict(self.theme)
        if self.themeEditorNameVar is not None:
            self.themeEditorNameVar.set(savedName)
        for key, value in self.theme.items():
            if key in self.themeEditorColorVars:
                self.themeEditorColorVars[key].set(value)
                preview = self.themeEditorPreviewLabels.get(key)
                if preview is not None:
                    preview.configure(bg=value)
        messagebox.showinfo("Theme Saved", f"Saved {savedName}.json in the Themes folder.", parent=self.themeEditorWindow)

    def resetThemeEditorFields(self) -> None:
        if self.themeEditorNameVar is not None:
            self.themeEditorNameVar.set(f"{self.themeName.title()} Custom")
        for key in themeColorKeys:
            if key in self.themeEditorColorVars:
                self.themeEditorColorVars[key].set(self.theme[key])
            preview = self.themeEditorPreviewLabels.get(key)
            if preview is not None:
                preview.configure(bg=self.theme[key])
        self._previewThemeEditorChanges()

    def importTheme(self) -> None:
        path = filedialog.askopenfilename(
            title="Import Theme",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8-sig") as handle:
                payload = json.load(handle)
            if not isinstance(payload, dict):
                raise ValueError("Theme file must contain a JSON object.")
            themeName = payload.get("name")
            if not isinstance(themeName, str) or not _sanitizeThemeName(themeName):
                themeName = os.path.splitext(os.path.basename(path))[0]
            savePath = saveCustomTheme(themeName, payload.get("colors", payload), sourcePath=path)
        except Exception as exc:
            messagebox.showerror("Theme Error", str(exc))
            return

        importedName = os.path.splitext(os.path.basename(savePath))[0]
        self.refreshThemeChoices()
        self._applyTheme(importedName)
        messagebox.showinfo("Theme Imported", f"Imported {importedName}. You can now share it from the Themes folder too.")

    def exportTheme(self) -> None:
        suggestedName = f"{self.themeName}.json"
        path = filedialog.asksaveasfilename(
            title="Export Theme",
            initialfile=suggestedName,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            payload = {
                "name": self.themeName,
                "colors": {key: self.theme[key] for key in themeColorKeys},
            }
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
        except Exception as exc:
            messagebox.showerror("Theme Error", str(exc))
            return
        messagebox.showinfo("Theme Exported", f"Saved {os.path.basename(path)}.")

    def openThemesFolder(self) -> None:
        ensureThemesDir()
        try:
            os.startfile(themesDir)
        except Exception:
            messagebox.showerror("Theme Error", f"Could not open:\n{themesDir}")

    def _assetImportTypeChoices(self) -> list[tuple[str, str, str]]:
        return [
            ("Ribbon", "ribbons", "RBN"),
            ("Commendation", "commendations", "CMD"),
            ("Corpus Commendation", "corpus", "CCMD"),
            ("Special Badge", "spbadge", "BDG"),
            ("Award / Sack", "sacks", "AWD"),
            ("Bracket", "brackets", "BRK"),
            ("Quartermaster Bracket", "brackets", "QMBRK"),
            ("ANROCOM Ribbon", "anrocom", "ANROCOM"),
            ("HICOM Badge", "hicom", "HICOM"),
            ("Gorget", "gorget", "GORGET"),
            ("Certification", "certifications", "CERT"),
        ]

    def _assetImportFolder(self, categoryKey: str) -> str:
        categoryName = categoryLabels.get(categoryKey, categoryKey.title())
        folderName = _sanitizeAssetFilenamePart(categoryName) or "Imported"
        targetRoot = assetsDir if assetsDir else os.path.join(baseDir, "Images")
        return os.path.join(targetRoot, folderName)

    def openAssetImporter(self) -> None:
        if self.assetImporterWindow is not None and self.assetImporterWindow.winfo_exists():
            self.assetImporterWindow.lift()
            self.assetImporterWindow.focus_force()
            return

        typeChoices = self._assetImportTypeChoices()
        typeLabels = [label for label, _, _ in typeChoices]
        typeByLabel = {label: (categoryKey, suffix) for label, categoryKey, suffix in typeChoices}

        window = tk.Toplevel(self.root)
        window.title("Add Ribbon")
        window.geometry("520x260")
        window.configure(bg=self.theme["bg"])
        window.transient(self.root)
        window.resizable(False, False)
        self.assetImporterWindow = window

        nameVar = tk.StringVar()
        typeVar = tk.StringVar(value=typeLabels[0])
        fileVar = tk.StringVar()

        def onClose() -> None:
            self.assetImporterWindow = None
            window.destroy()

        def browseFile() -> None:
            path = filedialog.askopenfilename(
                parent=window,
                title="Add PNG",
                filetypes=[("PNG files", "*.png")],
            )
            if path:
                fileVar.set(path)

        def saveAsset() -> None:
            ribbonName = _sanitizeAssetFilenamePart(nameVar.get())
            if not ribbonName:
                messagebox.showerror("Add Ribbon", "Enter a ribbon name.", parent=window)
                return

            selectedType = typeVar.get().strip()
            if selectedType not in typeByLabel:
                messagebox.showerror("Add Ribbon", "Choose a valid ribbon type.", parent=window)
                return

            sourcePath = fileVar.get().strip()
            if not sourcePath:
                messagebox.showerror("Add Ribbon", "Add a PNG file first.", parent=window)
                return
            if not os.path.isfile(sourcePath):
                messagebox.showerror("Add Ribbon", "That PNG file could not be found.", parent=window)
                return
            if not sourcePath.lower().endswith(".png"):
                messagebox.showerror("Add Ribbon", "Only PNG files are supported.", parent=window)
                return

            categoryKey, suffix = typeByLabel[selectedType]
            targetDir = self._assetImportFolder(categoryKey)
            os.makedirs(targetDir, exist_ok=True)

            newFilename = f"{ribbonName}-{suffix}.png"
            targetPath = os.path.join(targetDir, newFilename)

            if os.path.exists(targetPath):
                messagebox.showerror(
                    "Add Ribbon",
                    f"That ribbon already exists:\n{newFilename}",
                    parent=window,
                )
                return

            try:
                shutil.move(sourcePath, targetPath)
            except Exception as exc:
                messagebox.showerror("Add Ribbon", str(exc), parent=window)
                return

            self._applySelectedProfile(self.profileVar.get())
            if newFilename[:-4] in self.checkboxVars:
                self.checkboxVars[newFilename[:-4]].set(1)
            self.applyFilter()
            self.schedulePreview()
            messagebox.showinfo(
                "Add Ribbon",
                f"Added {newFilename} to:\n{targetDir}",
                parent=window,
            )
            onClose()

        window.protocol("WM_DELETE_WINDOW", onClose)

        outerFrame = tk.Frame(window, bg=self.theme["bg"], padx=14, pady=14)
        outerFrame.pack(fill="both", expand=True)

        tk.Label(
            outerFrame,
            text="Add Ribbon PNG",
            bg=self.theme["bg"],
            fg=self.theme["text"],
            font=("Tahoma", 11, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 6))

        tk.Label(
            outerFrame,
            text="Enter the ribbon info, add the PNG, and the engine will move and rename it for you.",
            bg=self.theme["bg"],
            fg=self.theme["text"],
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(0, 12))

        nameRow = tk.Frame(outerFrame, bg=self.theme["bg"])
        nameRow.pack(fill="x", pady=(0, 10))
        tk.Label(nameRow, text="Ribbon name:", bg=self.theme["bg"], fg=self.theme["text"], width=12, anchor="w").pack(side="left")
        nameEntry = tk.Entry(
            nameRow,
            textvariable=nameVar,
            width=34,
            bg="#ffffff",
            fg="#000000",
            insertbackground="#000000",
            selectbackground=self.theme["accent"],
            selectforeground=self.theme["header_fg"],
            relief="sunken",
            bd=1,
        )
        nameEntry.pack(side="left", fill="x", expand=True)

        typeRow = tk.Frame(outerFrame, bg=self.theme["bg"])
        typeRow.pack(fill="x", pady=(0, 10))
        tk.Label(typeRow, text="Type:", bg=self.theme["bg"], fg=self.theme["text"], width=12, anchor="w").pack(side="left")
        style = ttk.Style(window)
        style.configure(
            "Importer.TCombobox",
            fieldbackground="#ffffff",
            background="#ffffff",
            foreground="#000000",
            arrowcolor="#000000",
        )
        style.map(
            "Importer.TCombobox",
            fieldbackground=[("readonly", "#ffffff")],
            background=[("readonly", "#ffffff")],
            foreground=[("readonly", "#000000")],
            selectbackground=[("readonly", self.theme["accent"])],
            selectforeground=[("readonly", "#ffffff")],
        )
        typeCombo = ttk.Combobox(typeRow, textvariable=typeVar, values=typeLabels, state="readonly", width=31)
        typeCombo.configure(style="Importer.TCombobox")
        typeCombo.pack(side="left", fill="x", expand=True)

        fileRow = tk.Frame(outerFrame, bg=self.theme["bg"])
        fileRow.pack(fill="x", pady=(0, 10))
        tk.Label(fileRow, text="PNG file:", bg=self.theme["bg"], fg=self.theme["text"], width=12, anchor="w").pack(side="left")
        fileEntry = tk.Entry(
            fileRow,
            textvariable=fileVar,
            width=34,
            bg="#ffffff",
            fg="#000000",
            insertbackground="#000000",
            selectbackground=self.theme["accent"],
            selectforeground=self.theme["header_fg"],
            relief="sunken",
            bd=1,
        )
        fileEntry.pack(side="left", fill="x", expand=True)
        ttk.Button(fileRow, text="Add PNG", width=10, command=browseFile).pack(side="left", padx=(8, 0))

        buttonRow = tk.Frame(outerFrame, bg=self.theme["bg"])
        buttonRow.pack(fill="x", pady=(8, 0))
        ttk.Button(buttonRow, text="Cancel", command=onClose).pack(side="right")
        ttk.Button(buttonRow, text="Add Ribbon", command=saveAsset).pack(side="right", padx=(0, 8))

        nameEntry.focus_set()

    def openRibbonTutorial(self) -> None:
        if self.ribbonTutorialWindow is not None and self.ribbonTutorialWindow.winfo_exists():
            self.ribbonTutorialWindow.lift()
            self.ribbonTutorialWindow.focus_force()
            return

        window = tk.Toplevel(self.root)
        window.title("How to Add Ribbons")
        window.geometry("640x520")
        window.configure(bg=self.theme["bg"])
        window.transient(self.root)
        window.resizable(True, True)
        window.minsize(520, 380)
        self.ribbonTutorialWindow = window

        def onClose() -> None:
            self.ribbonTutorialWindow = None
            window.destroy()

        window.protocol("WM_DELETE_WINDOW", onClose)

        outerFrame = tk.Frame(window, bg=self.theme["bg"])
        outerFrame.pack(fill="both", expand=True)

        titleLabel = tk.Label(
            outerFrame,
            text="How to Add New Ribbons",
            bg=self.theme["bg"],
            fg=self.theme["text"],
            font=("Tahoma", 11, "bold"),
            anchor="w",
        )
        titleLabel.pack(fill="x", padx=14, pady=(14, 6))

        subtitleLabel = tk.Label(
            outerFrame,
            text="Use the arrows to move through the tutorial.",
            bg=self.theme["bg"],
            fg=self.theme["text"],
            justify="left",
            anchor="w",
        )
        subtitleLabel.pack(fill="x", padx=14, pady=(0, 8))

        slideIndex = tk.IntVar(value=0)

        slideFrame = tk.Frame(
            outerFrame,
            bg=self.theme["panel_bg"],
            bd=1,
            relief="sunken",
            padx=14,
            pady=14,
        )
        slideFrame.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        slideCounterLabel = tk.Label(
            slideFrame,
            text="",
            bg=self.theme["panel_bg"],
            fg=self.theme["accent"],
            font=("Tahoma", 9, "bold"),
            anchor="w",
        )
        slideCounterLabel.pack(fill="x", pady=(0, 8))

        slideTitleLabel = tk.Label(
            slideFrame,
            text="",
            bg=self.theme["panel_bg"],
            fg=self.theme["text"],
            font=("Tahoma", 11, "bold"),
            justify="left",
            anchor="w",
        )
        slideTitleLabel.pack(fill="x", pady=(0, 10))

        slideBodyLabel = tk.Label(
            slideFrame,
            text="",
            bg=self.theme["panel_bg"],
            fg=self.theme["text"],
            font=("Tahoma", 10),
            justify="left",
            anchor="nw",
        )
        slideBodyLabel.pack(fill="both", expand=True)

        buttonRow = tk.Frame(outerFrame, bg=self.theme["bg"])
        buttonRow.pack(fill="x", padx=14, pady=(0, 14))

        navRow = tk.Frame(buttonRow, bg=self.theme["bg"])
        navRow.pack(side="left")

        backButton = ttk.Button(navRow, text="Back", width=8)
        backButton.pack(side="left")

        nextButton = ttk.Button(navRow, text="Next", width=8)
        nextButton.pack(side="left", padx=(8, 0))

        ttk.Button(buttonRow, text="Close", command=onClose).pack(side="right")

        def renderSlide() -> None:
            index = slideIndex.get()
            title, body = tutorialSlides[index]
            slideCounterLabel.configure(text=f"Slide {index + 1} of {len(tutorialSlides)}")
            slideTitleLabel.configure(text=title)
            slideBodyLabel.configure(text=body)
            backButton.configure(state="normal" if index > 0 else "disabled")
            nextButton.configure(text="Finish" if index == len(tutorialSlides) - 1 else "Next")

        def previousSlide() -> None:
            if slideIndex.get() <= 0:
                return
            slideIndex.set(slideIndex.get() - 1)
            renderSlide()

        def nextSlide() -> None:
            if slideIndex.get() >= len(tutorialSlides) - 1:
                onClose()
                return
            slideIndex.set(slideIndex.get() + 1)
            renderSlide()

        backButton.configure(command=previousSlide)
        nextButton.configure(command=nextSlide)
        window.bind("<Left>", lambda _event: previousSlide())
        window.bind("<Right>", lambda _event: nextSlide())
        renderSlide()

    def _onCanvasConfigure(self, _event=None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _onMousewheel(self, event) -> None:
        widget = self.root.winfo_containing(event.x_root, event.y_root)
        parent = widget
        while parent is not None and parent is not self.root:
            if parent is self.leftFrame:
                break
            parent = parent.master
        else:
            return

        if getattr(event, "delta", 0):
            delta = -1 if event.delta > 0 else 1
            if abs(event.delta) >= 120:
                delta = int(-event.delta / 120)
            self.canvas.yview_scroll(delta, "units")
        elif getattr(event, "num", None) == 4:
            self.canvas.yview_scroll(-1, "units")
        elif getattr(event, "num", None) == 5:
            self.canvas.yview_scroll(1, "units")

    def _resolveProfileShirtPath(self, value: str) -> str:
        path = str(value or "").strip()
        if not path:
            return ""
        if os.path.isabs(path):
            return path
        return os.path.join(baseDir, path)

    def refreshProfileChoices(self) -> None:
        names = listProfileNames()
        self.profileCombo["values"] = names
        if self.profileName not in names:
            self.profileName = names[0]
        self.profileVar.set(self.profileName)

    def refreshPresetChoices(self) -> None:
        presets = self.settingsData.get("presets", {})
        names = sorted(presets.keys(), key=str.lower) if isinstance(presets, dict) else []
        self.presetCombo["values"] = names
        current = self.presetVar.get().strip()
        if current and current not in names:
            self.presetVar.set("")

    def _onPresetChanged(self, _event=None) -> None:
        self.saveCurrentSettings()

    def savePreset(self) -> None:
        suggestedName = self.presetVar.get().strip() or self.entry.get().strip() or "New Preset"
        presetName = simpledialog.askstring(
            "Save Preset",
            "Preset name:",
            parent=self.root,
            initialvalue=suggestedName,
        )
        if presetName is None:
            return

        presetName = " ".join(presetName.split()).strip()
        if not presetName:
            messagebox.showerror("Preset Error", "Preset name cannot be blank.")
            return

        settings = dict(self.settingsData)
        presets = dict(settings.get("presets", {})) if isinstance(settings.get("presets"), dict) else {}
        presets[presetName] = self.buildMetadata()
        settings["presets"] = presets
        settings["selected_preset"] = presetName
        saveSettings(settings)
        self.settingsData = ensureSettingsDefaults(settings)
        self.presetVar.set(presetName)
        self.refreshPresetChoices()
        messagebox.showinfo("Preset Saved", f"Saved preset: {presetName}")

    def loadSelectedPreset(self) -> None:
        presetName = self.presetVar.get().strip()
        if not presetName:
            messagebox.showerror("Preset Error", "Choose a preset to load.")
            return

        presets = self.settingsData.get("presets", {})
        if not isinstance(presets, dict):
            messagebox.showerror("Preset Error", "No presets were found.")
            return

        metadata = presets.get(presetName)
        if not isinstance(metadata, dict):
            messagebox.showerror("Preset Error", f"Preset not found: {presetName}")
            return

        if not self.applyMetadata(metadata):
            messagebox.showerror("Preset Error", f"Could not load preset: {presetName}")
            return

        self.baseImage = None
        self.setStatus("")
        self.schedulePreview()
        self.saveCurrentSettings()

    def deleteSelectedPreset(self) -> None:
        presetName = self.presetVar.get().strip()
        if not presetName:
            messagebox.showerror("Preset Error", "Choose a preset to delete.")
            return

        presets = self.settingsData.get("presets", {})
        if not isinstance(presets, dict) or presetName not in presets:
            messagebox.showerror("Preset Error", f"Preset not found: {presetName}")
            return

        if not messagebox.askyesno("Delete Preset", f"Delete preset '{presetName}'?"):
            return

        settings = dict(self.settingsData)
        updatedPresets = dict(presets)
        updatedPresets.pop(presetName, None)
        settings["presets"] = updatedPresets
        settings["selected_preset"] = ""
        saveSettings(settings)
        self.settingsData = ensureSettingsDefaults(settings)
        self.presetVar.set("")
        self.refreshPresetChoices()

    def _applySelectedProfile(self, profileName: str) -> None:
        normalized = _normalizeProfileName(profileName)
        selectedBefore = self.getSelectedRibbonNames() if self.checkboxVars else []

        self.profileName = normalized
        self.profileData = ensureProfileFile(self.profileName)
        applyProfile(self.profileData)

        profileShirt = self._resolveProfileShirtPath(profileSelectedShirt)
        if profileShirt:
            self.overlaySourcePath = profileShirt
        else:
            self.overlaySourcePath = previewOverlayPath if os.path.exists(previewOverlayPath) else ""
        self.updateOverlaySourceLabel()

        try:
            self.ribbonGroups = loadRibbonGroups()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            self.ribbonGroups = {key: [] for key in categoryLabels}
        self.renderer = RibbonRenderer(self.ribbonGroups)

        self._rebuildSections(selectedBefore)
        self.refreshProfileChoices()
        self.applyFilter()
        self.schedulePreview()
        self.saveCurrentSettings()

    def _rebuildSections(self, selectedNames: list[str]) -> None:
        for widget in list(self.leftColumn.winfo_children()):
            widget.destroy()
        for widget in list(self.rightColumn.winfo_children()):
            widget.destroy()
        self.checkboxVars = {}
        self.categorySections = []
        self._buildSections()
        self._loadCollapsedSettings()
        for name in selectedNames:
            if name in self.checkboxVars:
                self.checkboxVars[name].set(1)

    def _onProfileChanged(self, _event=None) -> None:
        self._applySelectedProfile(self.profileVar.get())

    def reloadCurrentProfile(self) -> None:
        self._applySelectedProfile(self.profileVar.get())

    def _buildSections(self) -> None:
        explicitAnrocomItems = self.ribbonGroups.get("anrocom", [])
        anrocomSectionBuilt = False

        for category, items in self.ribbonGroups.items():
            if not items:
                continue
            if category == "ribbons":
                sectionsConfig = self.settingsData.get("sections", {})
                anrocomNames = _normalizeSectionNames(sectionsConfig.get(anrocomSettingsKey, []))

                anrocomItems = list(explicitAnrocomItems)
                anrocomItemNames = {item.name for item in explicitAnrocomItems}
                anrocomItems.extend(
                    [item for item in items if item.name in anrocomNames and item.name not in anrocomItemNames]
                )
                otherItems = [item for item in items if item.name not in anrocomNames]

                self._addSection(self.leftColumn, categoryLabels.get(category, category), otherItems)
                self._addSection(self.leftColumn, anrocomSectionLabel, anrocomItems)
                anrocomSectionBuilt = True
                continue
            if category == "anrocom" and anrocomSectionBuilt:
                continue

            if categoryPlacement.get(category, "right") == "left":
                parent = self.leftColumn
            else:
                parent = self.rightColumn

            self._addSection(parent, categoryLabels.get(category, category), items)

    def _addSection(self, parent, labelText: str, items: list[AssetItem]) -> None:
        if not items:
            return

        header = ttk.Frame(parent)
        header.pack(fill="x", pady=(10, 0))

        label = ttk.Label(header, text=labelText, style="Section.TLabel")
        label.pack(side="left", anchor="w")

        toggleBtn = ttk.Button(header, text=expandedIcon, width=1, style="Toggle.TButton")
        toggleBtn.pack(side="right")

        content = ttk.Frame(parent)
        content.pack(fill="x")

        sectionItems = []
        for item in items:
            var = tk.IntVar()
            self.checkboxVars[item.name] = var
            displayName = displayAssetName(item.name)
            widget = ttk.Checkbutton(
                content,
                text=displayName,
                variable=var,
                command=self._onCheckboxChanged,
            )
            widget.pack(anchor="w")
            sectionItems.append({"name": item.name, "widget": widget, "path": item.path})
            widget.bind("<Enter>", lambda _event, p=item.path, n=displayName: self.setHoverPreview(p, n))
            widget.bind("<Leave>", lambda _event: self.clearHoverPreview())

        section = SectionUI(
            key=labelText,
            header=header,
            toggle=toggleBtn,
            content=content,
            items=sectionItems,
            collapsed=False,
        )

        def toggleSection() -> None:
            section.collapsed = not section.collapsed
            section.toggle.config(text=collapsedIcon if section.collapsed else expandedIcon)
            self.applyFilter()
            self.saveCurrentSettings()

        toggleBtn.config(command=toggleSection)
        self.categorySections.append(section)

    def _loadCollapsedSettings(self) -> None:
        collapsedSettings = self.settingsData.get("collapsed_sections", {})
        if not isinstance(collapsedSettings, dict):
            return
        for section in self.categorySections:
            if section.key in collapsedSettings:
                section.collapsed = bool(collapsedSettings[section.key])
                section.toggle.config(text=collapsedIcon if section.collapsed else expandedIcon)

    def _onCheckboxChanged(self) -> None:
        if self.showSelectedVar.get():
            self.applyFilter()
        self.schedulePreview()

    def _onToggleShowSelected(self) -> None:
        self.applyFilter()
        self.saveCurrentSettings()

    def _onToggleOverlay(self) -> None:
        self.updatePreview()
        self.saveCurrentSettings()

    def _onToggleCaseSensitiveSearch(self) -> None:
        self.applyFilter()
        self.saveCurrentSettings()

    def updateOverlaySourceLabel(self) -> None:
        path = self.overlaySourcePath.strip()
        if path:
            source = os.path.basename(path)
        elif os.path.exists(previewOverlayPath):
            source = os.path.basename(previewOverlayPath)
        else:
            source = "None"
        self.overlaySourceLabel.config(text=f"Shirt source: {source}")

    def schedulePreview(self) -> None:
        if self.previewJob is not None:
            self.root.after_cancel(self.previewJob)
        self.previewJob = self.root.after(150, self.updatePreview)

    def _onSearchKeyRelease(self, _event=None) -> None:
        query = self.searchVar.get().strip()
        if query == "67":
            if not self.searchEasterEggActive:
                self.searchEasterEggActive = True
                messagebox.showinfo("67", "67")
        else:
            self.searchEasterEggActive = False
        self.applyFilter()

    def applyFilter(self) -> None:
        query = self.searchVar.get().strip()
        caseSensitive = bool(self.caseSensitiveSearchVar.get())
        normalizedQuery = query if caseSensitive else query.lower()
        onlySelected = self.showSelectedVar.get()
        filterActive = bool(query) or onlySelected

        for section in self.categorySections:
            section.header.pack_forget()
            section.content.pack_forget()
            for item in section.items:
                item["widget"].pack_forget()

            visibleItems = [
                item
                for item in section.items
                if normalizedQuery in (item["name"] if caseSensitive else item["name"].lower())
                and (not onlySelected or self.checkboxVars[item["name"]].get())
            ]

            if visibleItems:
                section.header.pack(fill="x", pady=(10, 0))
                if filterActive or not section.collapsed:
                    section.content.pack(fill="x")
                    for item in visibleItems:
                        item["widget"].pack(anchor="w")

        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def saveCurrentSettings(self) -> None:
        settings = dict(self.settingsData)
        settings["preview_scale"] = self.previewScale
        settings["only_show_selected"] = bool(self.showSelectedVar.get())
        settings["case_sensitive_search"] = bool(self.caseSensitiveSearchVar.get())
        settings["collapsed_sections"] = {
            section.key: bool(section.collapsed) for section in self.categorySections
        }
        settings["preview_overlay"] = bool(self.overlayVar.get())
        settings["profile"] = self.profileName
        settings["theme"] = self.themeName
        settings.setdefault("presets", {})
        settings["selected_preset"] = self.presetVar.get().strip()
        settings.setdefault("sections", {anrocomSettingsKey: []})
        if isinstance(settings.get("sections"), dict):
            settings["sections"].setdefault(anrocomSettingsKey, [])
        saveSettings(settings)
        self.settingsData = ensureSettingsDefaults(settings)

    def focusSearch(self, _event=None):
        current = self.root.focus_get()
        if current == self.searchEntry:
            return None

        try:
            if isinstance(current, (tk.Entry, ttk.Entry)):
                cursor = current.index(tk.INSERT)
                text = current.get()
                if cursor > 0 and cursor <= len(text) and text[cursor - 1] == "/":
                    current.delete(cursor - 1)
        except Exception:
            pass

        self.searchEntry.focus_set()
        self.searchEntry.select_range(0, tk.END)
        return "break"

    def adjustPreviewScale(self, delta: float) -> None:
        self.previewScale = max(1.0, self.previewScale + delta)
        self.updatePreviewScaleLabel()
        self.updatePreview()
        self.ensureWindowSize()
        self.saveCurrentSettings()

    def updatePreviewScaleLabel(self) -> None:
        self.previewSizeLabel.config(text=f"Preview size: {self.previewScale:.1f}x")

    def ensureWindowSize(self) -> None:
        self.root.update_idletasks()
        reqWidth = self.root.winfo_reqwidth()
        reqHeight = self.root.winfo_reqheight()
        currentWidth = self.root.winfo_width()
        currentHeight = self.root.winfo_height()
        newWidth = max(currentWidth, reqWidth)
        newHeight = max(currentHeight, reqHeight)
        if newWidth != currentWidth or newHeight != currentHeight:
            self.root.geometry(f"{newWidth}x{newHeight}")

    def setStatus(self, message: str) -> None:
        self.labelStatus.config(text=message or "")

    def getSelectedRibbonNames(self) -> list[str]:
        return sorted([name for name, var in self.checkboxVars.items() if var.get()])

    def buildMetadata(self) -> dict:
        return {
            "ribbons": self.getSelectedRibbonNames(),
            "nameplate": self.entry.get().strip(),
        }

    def applyMetadata(self, metadata: dict) -> bool:
        if not isinstance(metadata, dict):
            return False

        ribbons = metadata.get("ribbons", [])
        if isinstance(ribbons, list):
            for var in self.checkboxVars.values():
                var.set(0)
            for name in ribbons:
                if name in self.checkboxVars:
                    self.checkboxVars[name].set(1)

        nameplate = metadata.get("nameplate")
        if isinstance(nameplate, str):
            self.entry.delete(0, tk.END)
            self.entry.insert(0, nameplate)

        if self.showSelectedVar.get():
            self.applyFilter()

        return True

    def _centeredPreview(self, image: Image.Image, size: int, bgColor: tuple[int, int, int, int]) -> Image.Image:
        w, h = image.size
        scale = min(size / w, size / h)
        newW = max(1, int(w * scale))
        newH = max(1, int(h * scale))
        resized = image.resize((newW, newH), Image.NEAREST)
        canvasImg = Image.new("RGBA", (size, size), bgColor)
        x = (size - newW) // 2
        y = (size - newH) // 2
        canvasImg.paste(resized, (x, y), resized)
        return canvasImg

    def _resolveOverlaySourcePath(self) -> Optional[str]:
        path = self.overlaySourcePath.strip()
        if path and os.path.exists(path):
            return path
        if os.path.exists(previewOverlayPath):
            return previewOverlayPath
        return None

    def _scaledOverlayCropBox(self, sourceSize: tuple[int, int]) -> Optional[tuple[int, int, int, int]]:
        sourceW, sourceH = sourceSize
        refW, refH = overlayTemplateSize
        if refW <= 0 or refH <= 0:
            return None

        x1, y1, x2, y2 = overlayFrontCropBox
        scaleX = sourceW / refW
        scaleY = sourceH / refH
        sx1 = int(round(x1 * scaleX))
        sy1 = int(round(y1 * scaleY))
        sx2 = int(round(x2 * scaleX))
        sy2 = int(round(y2 * scaleY))
        sx1 = max(0, min(sx1, sourceW - 1))
        sy1 = max(0, min(sy1, sourceH - 1))
        sx2 = max(sx1 + 1, min(sx2, sourceW))
        sy2 = max(sy1 + 1, min(sy2, sourceH))
        if sx2 <= sx1 or sy2 <= sy1:
            return None
        return (sx1, sy1, sx2, sy2)

    def _prepareOverlayImage(self, image: Image.Image) -> Image.Image:
        if image.size == (imageSize, imageSize):
            return image

        box = self._scaledOverlayCropBox(image.size)
        if box is not None:
            cropped = image.crop(box)
        else:
            side = min(image.size)
            x = (image.size[0] - side) // 2
            y = (image.size[1] - side) // 2
            cropped = image.crop((x, y, x + side, y + side))
        if cropped.size != (imageSize, imageSize):
            cropped = cropped.resize((imageSize, imageSize), Image.NEAREST)
        return cropped

    def _loadOverlayImage(self) -> Optional[Image.Image]:
        overlayPath = self._resolveOverlaySourcePath()
        if not overlayPath:
            return None
        try:
            with Image.open(overlayPath) as overlay:
                prepared = self._prepareOverlayImage(overlay.convert("RGBA"))
            return prepared
        except Exception:
            return None

    def setHoverPreview(self, path: str, name: str) -> None:
        if not path or not os.path.exists(path):
            self.clearHoverPreview()
            return

        try:
            with Image.open(path) as img:
                preview = img.convert("RGBA")
        except Exception:
            self.clearHoverPreview()
            return

        preview = self._centeredPreview(preview, hoverPreviewSize, self.themeBgRgb + (255,))
        self.hoverPreviewImg = ImageTk.PhotoImage(preview)
        self.hoverPreviewLabel.config(image=self.hoverPreviewImg)
        self.hoverPreviewLabel.image = self.hoverPreviewImg
        self.hoverNameLabel.config(text=name)

    def clearHoverPreview(self) -> None:
        blank = Image.new("RGBA", (hoverPreviewSize, hoverPreviewSize), self.themeBgRgb + (255,))
        self.hoverPreviewImg = ImageTk.PhotoImage(blank)
        self.hoverPreviewLabel.config(image=self.hoverPreviewImg)
        self.hoverPreviewLabel.image = self.hoverPreviewImg
        self.hoverNameLabel.config(text="")

    def buildImage(self, requireNameForNew: bool, errorCallback: Optional[Callable[[str], None]]):
        selectedNames = set(self.getSelectedRibbonNames())
        return self.renderer.buildImage(
            selectedNames=selectedNames,
            nameplateText=self.entry.get().strip(),
            baseImage=self.baseImage,
            requireNameForNew=requireNameForNew,
            errorCallback=errorCallback,
        )

    def _setPreviewImage(self, image: Image.Image) -> None:
        previewSize = int(imageSize * self.previewScale)
        self.previewImg = ImageTk.PhotoImage(image.resize((previewSize, previewSize), Image.NEAREST))
        self.labelPreview.config(image=self.previewImg)
        self.labelPreview.image = self.previewImg

    def updatePreview(self) -> None:
        self.previewJob = None

        def statusError(message: str) -> None:
            self.setStatus(message)

        image, _, missingAssets = self.buildImage(requireNameForNew=False, errorCallback=statusError)
        if image is None:
            blank = Image.new("RGBA", (imageSize, imageSize), (255, 255, 255, 0))
            self._setPreviewImage(blank)
            return

        if not missingAssets:
            self.setStatus("")

        if self.overlayVar.get():
            overlayImg = self._loadOverlayImage()
            if overlayImg is not None:
                composite = overlayImg.copy()
                composite.paste(image, (0, 0), image)
                image = composite

        self._setPreviewImage(image)

    def pasteFromClipboard(self) -> None:
        try:
            clip = ImageGrab.grabclipboard()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return

        metadata = None
        loaded = False
        tempImage = None

        if isinstance(clip, Image.Image):
            metadata = getattr(clip, "info", None)
            tempImage = clip.convert("RGBA")
            loaded = True
        elif isinstance(clip, (list, tuple)) and clip:
            path = clip[0]
            if isinstance(path, str) and os.path.isfile(path):
                try:
                    with Image.open(path) as img:
                        metadata = img.info
                        tempImage = img.convert("RGBA")
                    loaded = True
                except Exception as exc:
                    messagebox.showerror("Error", str(exc))
                    return

        if not loaded:
            messagebox.showerror("Error", "No image found in clipboard.")
            return

        applied = False
        if isinstance(metadata, dict):
            payload = metadata.get("ribbonengine")
            if isinstance(payload, str):
                try:
                    applied = self.applyMetadata(json.loads(payload))
                except Exception:
                    applied = False

        if applied:
            self.baseImage = None
        else:
            self.baseImage = tempImage

        self.schedulePreview()
        if applied:
            messagebox.showinfo("Info", "Loaded image + ribbon metadata!")
        else:
            messagebox.showinfo("Info", "Loaded image (no ribbon metadata found).")

    def generateImage(self) -> None:
        missing = [
            path for path in (ribbonsDir, commendationsDir, awardsDir, charactersDir)
            if not os.path.isdir(path)
        ]
        if missing:
            messagebox.showerror("Error", "Missing folder(s):\n" + "\n".join(missing))
            return

        def showError(message: str) -> None:
            messagebox.showerror("Error", message)

        image, _, _ = self.buildImage(requireNameForNew=True, errorCallback=showError)
        if image is None:
            return

        self._setPreviewImage(image)
        self.setStatus("")

        savePath = os.path.join(baseDir, _defaultOutputFilename(self.entry.get()))
        try:
            metadata = self.buildMetadata()
            pnginfo = PngImagePlugin.PngInfo()
            pnginfo.add_text("ribbonengine", json.dumps(metadata, separators=(",", ":")))
            image.save(savePath, pnginfo=pnginfo)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return

        messagebox.showinfo("Success", "Saved image!")

    def clearAll(self) -> None:
        self.baseImage = None

        self.entry.delete(0, tk.END)
        for var in self.checkboxVars.values():
            var.set(0)

        self.setStatus("")
        if self.showSelectedVar.get():
            self.applyFilter()
        self.schedulePreview()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = RibbonEngineApp()
    app.run()


if __name__ == "__main__":
    main()
