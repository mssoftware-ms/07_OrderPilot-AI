from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

class FunctionInfo:
    """Information über eine Funktion/Methode."""
    name: str
    file_path: str
    line_start: int
    line_end: int
    signature: str
    decorators: List[str]
    is_async: bool
    docstring: Optional[str]
    class_name: Optional[str] = None

class ClassInfo:
    """Information über eine Klasse."""
    name: str
    file_path: str
    line_start: int
    line_end: int
    bases: List[str]
    methods: List[str]
    decorators: List[str]
    docstring: Optional[str]
    is_ui_component: bool = False

class ImportInfo:
    """Information über einen Import."""
    module: str
    names: List[str]
    file_path: str
    line_number: int
    is_from_import: bool

class EventHandlerInfo:
    """Information über Event-Handler."""
    name: str
    file_path: str
    line_number: int
    signal_name: Optional[str]
    handler_type: str

class UIComponentInfo:
    """Information über UI-Komponenten."""
    class_name: str
    file_path: str
    line_start: int
    line_end: int
    widget_type: str
    parent_class: str
    signals: List[str]
    slots: List[str]

class FileInventory:
    """Inventur einer einzelnen Datei."""
    file_path: str
    line_count: int
    code_lines: int  # Ohne Leerzeilen und Kommentare
    checksum: str
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    imports: List[ImportInfo] = field(default_factory=list)
    event_handlers: List[EventHandlerInfo] = field(default_factory=list)
    ui_components: List[UIComponentInfo] = field(default_factory=list)
    constants: List[Dict[str, Any]] = field(default_factory=list)
    global_variables: List[Dict[str, Any]] = field(default_factory=list)

class ProjectInventory:
    """Gesamtinventur des Projekts."""
    timestamp: str
    project_root: str
    total_files: int
    total_lines: int
    total_code_lines: int
    total_functions: int
    total_classes: int
    total_ui_components: int
    total_event_handlers: int
    total_imports: int
    files: Dict[str, FileInventory] = field(default_factory=dict)
