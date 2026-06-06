from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List, Optional

import polars as pl
from PySide6.QtCore import QPoint, QSettings, Qt, QThread, QTimer
from PySide6.QtCore import Signal as ThreadSignal
from PySide6.QtGui import QAction, QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QDockWidget,
    QFileDialog,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QTabBar,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from polaris_studio.agent.ai_backend import AIBackendRouter
from polaris_studio.agent.chat_session import ChatSession
from polaris_studio.agent.command_pipeline import CommandContext
from polaris_studio.agent.interpreter import AgentInterpreter
from polaris_studio.agent.schemas import AppCommandBatch, PipelineMutationBatch
from polaris_studio.core.graph import Node, NodeCategory
from polaris_studio.core.node_registry import NODE_REGISTRY
from polaris_studio.state.app_state import AppState
from polaris_studio.state.workspace import Workspace
from polaris_studio.ui.command_palette import Command, CommandPalette
from polaris_studio.ui.graph.canvas import GraphCanvas
from polaris_studio.ui.motion import fade_slide_in, viewport_flash
from polaris_studio.ui.panels.ai_panel import AIPanel
from polaris_studio.ui.panels.chart_panel import ChartPanel
from polaris_studio.ui.panels.node_palette import NodePalette
from polaris_studio.ui.panels.profile_panel import ProfilePanel
from polaris_studio.ui.panels.properties_panel import PropertiesPanel
from polaris_studio.ui.spreadsheet.cell_delegate import PolarisDelegate
from polaris_studio.ui.spreadsheet.formula_bar import FormulaBar
from polaris_studio.ui.spreadsheet.grid_model import PolarisGridModel
from polaris_studio.ui.spreadsheet.grid_view import SpreadsheetGrid
from polaris_studio.ui.status_bar import StatusBar
from polaris_studio.ui.theme import PALETTE, RADII, font_instrument_serif, font_inter
from polaris_studio.ui.view_mode import ViewMode


class AsyncRunner(QThread):
    chat_event_signal = ThreadSignal(str, object)  # type: ignore[assignment]

    def __init__(
        self, chat_session: ChatSession, text: str, attached_node_id: Optional[str]
    ) -> None:
        super().__init__()
        self._chat_session = chat_session
        self._text = text
        self._attached_node_id = attached_node_id

    def run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._send())
        except Exception as exc:
            self.chat_event_signal.emit("error", str(exc))
        finally:
            loop.close()

    async def _send(self) -> None:
        async for chat_event in self._chat_session.send(self._text, self._attached_node_id):
            if chat_event.type == "token":
                self.chat_event_signal.emit("token", chat_event.text)
            elif chat_event.type == "message":
                self.chat_event_signal.emit("message", chat_event.text)
            elif chat_event.type in {"action_batch", "command_batch"} and chat_event.batch:
                self.chat_event_signal.emit(chat_event.type, chat_event.batch)
            elif chat_event.type == "error":
                self.chat_event_signal.emit("error", chat_event.message)
            elif chat_event.type == "done":
                self.chat_event_signal.emit("done", None)


class PolarisMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._settings_manager = QSettings("PolarisStudio", "PolarisStudio")
        self._view_mode = ViewMode.GRAPH
        self._workspace = Workspace()
        self._workspace.new_tab("Sheet1")
        self._app_state = AppState(self)
        self._app_state.graph = self._workspace.active_graph
        self._ai_backend = AIBackendRouter()
        self._ai_runner: Optional[AsyncRunner] = None
        self._ai_auto_approve = False
        self._interpreter = AgentInterpreter(self._app_state.graph)
        self._chat_session = ChatSession(
            self._app_state.graph,
            self._ai_backend,
        )
        self._chat_session.set_context_provider(self._build_ai_context)
        self._chat_session.set_command_context_provider(self._build_command_context)
        self._grid_model = PolarisGridModel()
        self._cell_delegate = PolarisDelegate()

        self.setWindowTitle("Polaris Studio")
        self.setMinimumSize(1280, 800)
        self.resize(1600, 1000)

        self._setup_menus()
        self._setup_toolbar()
        self._setup_central()
        self._setup_docks()
        self._setup_connections()
        self._setup_shortcuts()
        self._setup_command_palette()
        self._setup_tab_bar()

        self._app_state.graph_changed.connect(self._on_graph_changed)
        self._update_title()
        self._load_and_apply_settings()
        QTimer.singleShot(0, self._run_launch_reveal)

    def _run_launch_reveal(self) -> None:
        reveal_targets = [
            self.menuBar(),
            self._node_palette_dock,
            self._central_splitter,
            self._properties_panel_dock,
            self._ai_panel_dock,
            self._status_bar,
        ]
        for index, widget in enumerate(reveal_targets):
            fade_slide_in(
                widget,
                delay_ms=70 + index * 52,
                duration_ms=320,
                offset=QPoint(0, 18 if widget is self._central_splitter else 10),
            )

    def _setup_menus(self) -> None:
        menubar = self.menuBar()
        menubar.setFont(font_inter(12, QFont.Weight.Medium))
        menubar.setStyleSheet(f"""
            QMenuBar {{
                background: {PALETTE.bg_panel};
                color: {PALETTE.text_primary};
                padding: 4px 6px;
                font-family: 'Inter';
                font-size: 12px;
                border-bottom: 1px solid {PALETTE.border};
            }}
            QMenuBar::item {{
                background: transparent;
                padding: 7px 14px;
                border-radius: {RADII.sm}px;
                margin: 2px;
                font-family: 'Inter';
                font-weight: 500;
            }}
            QMenuBar::item:selected {{
                background: {PALETTE.bg_node_alt};
                color: {PALETTE.text_primary};
            }}
            QMenu {{
                background: {PALETTE.bg_panel};
                color: {PALETTE.text_primary};
                border: 1px solid {PALETTE.border};
                border-radius: {RADII.md}px;
                padding: 6px;
            }}
            QMenu::item {{
                padding: 8px 28px;
                border-radius: {RADII.sm}px;
                font-family: 'Inter';
                font-size: 12px;
            }}
            QMenu::item:selected {{
                background: {PALETTE.accent};
                color: #ffffff;
            }}
            QMenu::separator {{
                height: 1px;
                background: {PALETTE.border};
                margin: 4px 8px;
            }}
        """)

        file_menu = menubar.addMenu("File")
        new_action = QAction("New Workflow", self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.triggered.connect(self._new_workflow)
        file_menu.addAction(new_action)

        open_action = QAction("Open Workflow...", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self._open_workflow)
        file_menu.addAction(open_action)

        save_action = QAction("Save Workflow", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self._save_workflow)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save As...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self._save_as_workflow)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        import_csv = QAction("Import CSV...", self)
        import_csv.triggered.connect(lambda: self._import_file("csv"))
        file_menu.addAction(import_csv)

        import_xlsx = QAction("Import XLSX...", self)
        import_xlsx.triggered.connect(lambda: self._import_file("xlsx"))
        file_menu.addAction(import_xlsx)

        import_parquet = QAction("Import Parquet...", self)
        import_parquet.triggered.connect(lambda: self._import_file("parquet"))
        file_menu.addAction(import_parquet)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        edit_menu = menubar.addMenu("Edit")
        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        undo_action.triggered.connect(self._app_state.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("Redo", self)
        redo_action.setShortcut(QKeySequence("Ctrl+Shift+Z"))
        redo_action.triggered.connect(self._app_state.redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()
        settings_action = QAction("Settings...", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self._show_settings)
        edit_menu.addAction(settings_action)

        view_menu = menubar.addMenu("View")
        spreadsheet_mode = QAction("Spreadsheet Mode", self)
        spreadsheet_mode.setShortcut(QKeySequence("F1"))
        spreadsheet_mode.triggered.connect(lambda: self._set_view_mode(ViewMode.SPREADSHEET))
        view_menu.addAction(spreadsheet_mode)

        graph_mode = QAction("Graph Mode", self)
        graph_mode.setShortcut(QKeySequence("F2"))
        graph_mode.triggered.connect(lambda: self._set_view_mode(ViewMode.GRAPH))
        view_menu.addAction(graph_mode)

        split_mode = QAction("Split Mode", self)
        split_mode.setShortcut(QKeySequence("F3"))
        split_mode.triggered.connect(lambda: self._set_view_mode(ViewMode.SPLIT))
        view_menu.addAction(split_mode)

        view_menu.addSeparator()
        toggle_palette = QAction("Node Palette", self)
        toggle_palette.setCheckable(True)
        toggle_palette.setChecked(True)
        toggle_palette.triggered.connect(lambda b: self._node_palette_dock.setVisible(b))
        view_menu.addAction(toggle_palette)

        toggle_properties = QAction("Properties Panel", self)
        toggle_properties.setCheckable(True)
        toggle_properties.setChecked(True)
        toggle_properties.triggered.connect(lambda b: self._properties_panel_dock.setVisible(b))
        view_menu.addAction(toggle_properties)

        toggle_table = QAction("Table View", self)
        toggle_table.setCheckable(True)
        toggle_table.setChecked(True)
        toggle_table.triggered.connect(lambda b: self._table_view.setVisible(b))
        view_menu.addAction(toggle_table)

        graph_menu = menubar.addMenu("Graph")
        auto_layout = QAction("Auto Layout", self)
        auto_layout.setShortcut(QKeySequence("Ctrl+Shift+L"))
        auto_layout.triggered.connect(self._auto_layout)
        graph_menu.addAction(auto_layout)

        execute_all = QAction("Execute All", self)
        execute_all.setShortcut(QKeySequence("F5"))
        execute_all.triggered.connect(self._execute_all)
        graph_menu.addAction(execute_all)

        clear_graph = QAction("Clear Graph", self)
        clear_graph.triggered.connect(self._clear_graph)
        graph_menu.addAction(clear_graph)

        data_menu = menubar.addMenu("Data")
        profile_action = QAction("Profile Selected Node", self)
        profile_action.triggered.connect(self._profile_selected)
        data_menu.addAction(profile_action)

        ai_menu = menubar.addMenu("AI")
        toggle_ai = QAction("AI Chat Panel", self)
        toggle_ai.setShortcut(QKeySequence("Ctrl+Shift+A"))
        toggle_ai.triggered.connect(lambda: self._toggle_drawer("ai"))
        ai_menu.addAction(toggle_ai)

    def _setup_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        toolbar.setStyleSheet(f"""
            QToolBar {{
                background: {PALETTE.bg_panel};
                border-bottom: 1px solid {PALETTE.border};
                spacing: 4px;
                padding: 8px 12px;
            }}
            QToolButton {{
                background: transparent;
                color: {PALETTE.text_secondary};
                border: 1px solid transparent;
                border-radius: {RADII.sm}px;
                padding: 8px 14px;
                font-family: 'Inter';
                font-size: 12px;
                font-weight: 500;
            }}
            QToolButton:hover {{
                background: {PALETTE.bg_node};
                color: {PALETTE.text_primary};
                border: 1px solid {PALETTE.border};
            }}
            QToolButton:checked {{
                background: {PALETTE.accent_dim};
                color: {PALETTE.text_primary};
                border: 1px solid {PALETTE.accent};
            }}
        """)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        self._wordmark = QLabel("Polaris Studio")
        wordmark_font = font_instrument_serif(24)
        wordmark_font.setStyleName("Regular")
        wordmark_font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        self._wordmark.setFont(wordmark_font)
        self._wordmark.setStyleSheet(
            f"color: {PALETTE.text_primary}; padding: 0 16px 0 4px;"
            f"font-family: 'Instrument Serif'; font-size: 24px; letter-spacing: 0px;"
        )
        self._wordmark.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        toolbar.addWidget(self._wordmark)

        sep_label = QLabel("|")
        sep_label.setStyleSheet(f"color: {PALETTE.border_strong}; padding: 0 4px;")
        sep_label.setFont(font_inter(14))
        toolbar.addWidget(sep_label)

        mode_group = QButtonGroup(self)
        mode_group.setExclusive(True)

        spreadsheet_btn = QToolButton()
        spreadsheet_btn.setText("Grid")
        spreadsheet_btn.setCheckable(True)
        spreadsheet_btn.setChecked(True)
        toolbar.addWidget(spreadsheet_btn)
        mode_group.addButton(spreadsheet_btn)
        spreadsheet_btn.clicked.connect(lambda: self._set_view_mode(ViewMode.SPREADSHEET))

        graph_btn = QToolButton()
        graph_btn.setText("Graph")
        graph_btn.setCheckable(True)
        toolbar.addWidget(graph_btn)
        mode_group.addButton(graph_btn)
        graph_btn.clicked.connect(lambda: self._set_view_mode(ViewMode.GRAPH))

        split_btn = QToolButton()
        split_btn.setText("Split")
        split_btn.setCheckable(True)
        toolbar.addWidget(split_btn)
        mode_group.addButton(split_btn)
        split_btn.clicked.connect(lambda: self._set_view_mode(ViewMode.SPLIT))

        toolbar.addSeparator()

        undo_btn = toolbar.addAction("Undo")
        undo_btn.triggered.connect(self._app_state.undo)

        redo_btn = toolbar.addAction("Redo")
        redo_btn.triggered.connect(self._app_state.redo)

        toolbar.addSeparator()

        execute_btn = toolbar.addAction("Execute All")
        execute_btn.triggered.connect(self._execute_all)

        toolbar.addSeparator()

        ai_btn = toolbar.addAction("AI")
        ai_btn.triggered.connect(lambda: self._toggle_drawer("ai"))

    def _setup_central(self) -> None:
        self._central_splitter = QSplitter(Qt.Orientation.Vertical)
        self._central_splitter.setHandleWidth(1)
        self._central_splitter.setStyleSheet(
            f"""
            QSplitter::handle {{
                background-color: {PALETTE.border};
            }}
            QSplitter::handle:hover {{
                background-color: {PALETTE.accent};
            }}
            """
        )
        self.setCentralWidget(self._central_splitter)

        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)

        self._formula_bar = FormulaBar()
        top_layout.addWidget(self._formula_bar)

        self._tab_bar = QTabBar()
        self._tab_bar.setTabsClosable(True)
        self._tab_bar.setMovable(True)
        self._tab_bar.setStyleSheet(
            f"""
            QTabBar {{
                background-color: {PALETTE.bg_panel};
                border-bottom: 1px solid {PALETTE.border};
            }}
            QTabBar::tab {{
                padding: 10px 24px;
                font-family: 'Inter';
                font-size: 12px;
                font-weight: 500;
                min-width: 100px;
                color: {PALETTE.text_secondary};
                background-color: transparent;
                border-right: 1px solid {PALETTE.border};
            }}
            QTabBar::tab:selected {{
                color: {PALETTE.text_primary};
                background-color: {PALETTE.bg_canvas};
                border-bottom: 2px solid {PALETTE.accent};
            }}
            QTabBar::tab:hover {{
                color: {PALETTE.text_primary};
            }}
            QTabBar::close-button {{ margin: 2px; }}
            """
        )
        top_layout.addWidget(self._tab_bar)

        self._graph_canvas = GraphCanvas()
        self._graph_canvas.setMinimumHeight(400)
        top_layout.addWidget(self._graph_canvas, 1)

        self._central_splitter.addWidget(top_widget)

        self._table_view = SpreadsheetGrid()
        self._table_view.set_model(self._grid_model)
        self._table_view.setItemDelegate(self._cell_delegate)
        self._table_view.setMinimumHeight(120)
        self._central_splitter.addWidget(self._table_view)

        self._central_splitter.setStretchFactor(0, 1)
        self._central_splitter.setStretchFactor(1, 0)
        self._central_splitter.setSizes([1000, 200])

    def _setup_docks(self) -> None:
        dock_style = f"""
            QDockWidget {{
                color: {PALETTE.text_primary};
                titlebar-close-icon: none;
                font-family: 'Inter';
            }}
            QDockWidget::title {{
                background-color: {PALETTE.bg_panel};
                padding: 9px 12px;
                font-family: 'Inter';
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: {PALETTE.text_secondary};
                border-bottom: 1px solid {PALETTE.border};
            }}
            """

        self._node_palette = NodePalette()
        self._node_palette_dock = QDockWidget("Node Library", self)
        self._node_palette_dock.setWidget(self._node_palette)
        self._node_palette_dock.setMinimumWidth(240)
        self._node_palette_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self._node_palette_dock.setStyleSheet(dock_style)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._node_palette_dock)

        self._properties_panel = PropertiesPanel()
        self._properties_panel_dock = QDockWidget("Properties", self)
        self._properties_panel_dock.setWidget(self._properties_panel)
        self._properties_panel_dock.setMinimumWidth(280)
        self._properties_panel_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self._properties_panel_dock.setStyleSheet(dock_style)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._properties_panel_dock)

        self._profile_panel = ProfilePanel()
        self._profile_panel_dock = QDockWidget("Data Profile", self)
        self._profile_panel_dock.setWidget(self._profile_panel)
        self._profile_panel_dock.setMinimumWidth(300)
        self._profile_panel_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self._profile_panel_dock.setStyleSheet(dock_style)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._profile_panel_dock)
        self._profile_panel_dock.hide()

        self._chart_panel = ChartPanel()
        self._chart_panel_dock = QDockWidget("Chart View", self)
        self._chart_panel_dock.setWidget(self._chart_panel)
        self._chart_panel_dock.setMinimumWidth(380)
        self._chart_panel_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self._chart_panel_dock.setStyleSheet(dock_style)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._chart_panel_dock)
        self._chart_panel_dock.hide()

        self._ai_panel = AIPanel()
        self._ai_panel_dock = QDockWidget("AI Assistant", self)
        self._ai_panel_dock.setWidget(self._ai_panel)
        self._ai_panel_dock.setMinimumWidth(420)
        self._ai_panel_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self._ai_panel_dock.setStyleSheet(dock_style)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._ai_panel_dock)
        self._ai_panel_dock.show()

        self._status_bar = StatusBar()
        self.setStatusBar(self._status_bar)

    def _setup_tab_bar(self) -> None:
        self._tab_bar.tabCloseRequested.connect(self._close_tab)
        self._tab_bar.currentChanged.connect(self._switch_tab)
        self._tab_bar.tabBarDoubleClicked.connect(self._rename_tab)

    def _setup_connections(self) -> None:
        self._graph_canvas.node_selected.connect(self._on_node_selected)
        self._graph_canvas.node_moved.connect(self._on_node_moved)
        self._graph_canvas.node_deleted.connect(self._on_canvas_node_deleted)
        self._graph_canvas.node_duplicated.connect(self._on_canvas_node_duplicated)
        self._graph_canvas.node_create_requested.connect(self._create_node_at)
        self._graph_canvas.connection_requested.connect(self._on_connection_requested)
        self._graph_canvas.selection_changed.connect(self._on_canvas_selection_changed)

        self._node_palette.node_double_clicked.connect(self._create_node_centered)

        self._properties_panel.param_changed.connect(self._app_state.update_node_param)
        self._properties_panel.execute_requested.connect(self._app_state.request_execute)
        self._properties_panel.preview_requested.connect(self._on_preview_requested)

        self._app_state.node_selected.connect(self._show_node_properties)
        self._app_state.graph_changed.connect(self._on_graph_changed)
        self._app_state.compute_started.connect(self._on_compute_started)
        self._app_state.compute_finished.connect(self._on_compute_finished)
        self._app_state.compute_error.connect(self._on_compute_error)
        self._app_state.table_data_ready.connect(self._on_table_data_ready)
        self._app_state.execution_status.connect(self._status_bar.set_status)

        self._ai_panel.message_sent.connect(self._on_ai_message)
        self._ai_panel.apply_batch_clicked.connect(self._on_ai_apply)
        self._ai_panel.reject_batch_clicked.connect(self._on_ai_reject)
        self._ai_panel.settings_clicked.connect(self._show_settings)

        self._formula_bar.expression_committed.connect(self._on_expression_committed)
        self._formula_bar.nlp_query_submitted.connect(self._on_nlp_query)

        self._table_view.cell_selected.connect(self._on_cell_selected)
        self._table_view.column_action_requested.connect(self._on_column_action)

        self._status_bar.set_status("Ready")

    def _setup_shortcuts(self) -> None:
        self._execute_selected_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        self._execute_selected_shortcut.activated.connect(self._execute_selected)
        self._undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        self._undo_shortcut.activated.connect(self._app_state.undo)
        self._redo_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Z"), self)
        self._redo_shortcut.activated.connect(self._app_state.redo)
        self._auto_layout_shortcut = QShortcut(QKeySequence("Ctrl+Shift+L"), self)
        self._auto_layout_shortcut.activated.connect(self._auto_layout)
        self._execute_all_shortcut = QShortcut(QKeySequence("F5"), self)
        self._execute_all_shortcut.activated.connect(self._execute_all)
        self._ai_toggle_shortcut = QShortcut(QKeySequence("Ctrl+Shift+A"), self)
        self._ai_toggle_shortcut.activated.connect(lambda: self._toggle_drawer("ai"))

    def _setup_command_palette(self) -> None:
        commands: List[Command] = []

        def add_cmd(id: str, label: str, shortcut: str, category: str, action):
            commands.append(
                Command(id=id, label=label, shortcut=shortcut, category=category, action=action)
            )

        add_cmd("new", "New Workflow", "Ctrl+N", "File", self._new_workflow)
        add_cmd("open", "Open Workflow...", "Ctrl+O", "File", self._open_workflow)
        add_cmd("save", "Save Workflow", "Ctrl+S", "File", self._save_workflow)
        add_cmd("undo", "Undo", "Ctrl+Z", "Edit", self._app_state.undo)
        add_cmd("redo", "Redo", "Ctrl+Shift+Z", "Edit", self._app_state.redo)
        add_cmd("settings", "Open Settings", "Ctrl+,", "Edit", self._show_settings)
        add_cmd(
            "spreadsheet",
            "Switch to Spreadsheet Mode",
            "F1",
            "View",
            lambda: self._set_view_mode(ViewMode.SPREADSHEET),
        )
        add_cmd(
            "graph",
            "Switch to Graph Mode",
            "F2",
            "View",
            lambda: self._set_view_mode(ViewMode.GRAPH),
        )
        add_cmd(
            "split",
            "Switch to Split Mode",
            "F3",
            "View",
            lambda: self._set_view_mode(ViewMode.SPLIT),
        )
        add_cmd("auto_layout", "Auto Layout Graph", "Ctrl+Shift+L", "Graph", self._auto_layout)
        add_cmd("execute_all", "Execute All Nodes", "F5", "Graph", self._execute_all)
        add_cmd("profile", "Profile Selected Node", "", "Data", self._profile_selected)
        add_cmd(
            "toggle_ai", "Open AI Panel", "Ctrl+Shift+A", "AI", lambda: self._toggle_drawer("ai")
        )
        add_cmd("export_csv", "Export as CSV...", "", "Export", lambda: self._export_as("csv"))
        add_cmd("export_xlsx", "Export as XLSX...", "", "Export", lambda: self._export_as("xlsx"))
        add_cmd(
            "export_parquet",
            "Export as Parquet...",
            "",
            "Export",
            lambda: self._export_as("parquet"),
        )

        self._command_palette = CommandPalette.install_shortcut(self, commands)

    def _set_view_mode(self, mode: ViewMode) -> None:
        if mode == self._view_mode:
            return
        self._view_mode = mode
        if mode == ViewMode.SPREADSHEET:
            self._graph_canvas.setVisible(False)
            self._table_view.setVisible(True)
            self._central_splitter.setSizes([0, 600])
            viewport_flash(self._table_view.viewport())
        elif mode == ViewMode.GRAPH:
            self._graph_canvas.setVisible(True)
            self._table_view.setVisible(False)
            self._central_splitter.setSizes([600, 0])
            viewport_flash(self._graph_canvas.viewport())
        elif mode == ViewMode.SPLIT:
            self._graph_canvas.setVisible(True)
            self._table_view.setVisible(True)
            size = self._central_splitter.height()
            self._central_splitter.setSizes([int(size * 0.8), int(size * 0.2)])
            viewport_flash(self._central_splitter)

    def _toggle_drawer(self, drawer: str) -> None:
        if drawer == "ai":
            visible = self._ai_panel_dock.isVisible()
            self._ai_panel_dock.setVisible(not visible)
            if not visible:
                self._ai_panel_dock.raise_()
                fade_slide_in(self._ai_panel_dock, offset=QPoint(16, 0))
        elif drawer == "properties":
            visible = self._properties_panel_dock.isVisible()
            self._properties_panel_dock.setVisible(not visible)
            if not visible:
                self._properties_panel_dock.raise_()
                fade_slide_in(self._properties_panel_dock, offset=QPoint(16, 0))
        elif drawer == "profile":
            visible = self._profile_panel_dock.isVisible()
            self._profile_panel_dock.setVisible(not visible)
            if not visible:
                self._profile_panel_dock.raise_()
                fade_slide_in(self._profile_panel_dock, offset=QPoint(0, 12))
        elif drawer == "chart":
            visible = self._chart_panel_dock.isVisible()
            self._chart_panel_dock.setVisible(not visible)
            if not visible:
                self._chart_panel_dock.raise_()
                fade_slide_in(self._chart_panel_dock, offset=QPoint(0, 12))
        elif drawer == "nodes":
            visible = self._node_palette_dock.isVisible()
            self._node_palette_dock.setVisible(not visible)
            if not visible:
                self._node_palette_dock.raise_()

    def _new_workflow(self) -> None:
        self._workspace.new_tab()
        self._sync_tab_bar()
        self._app_state.graph = self._workspace.active_graph
        self._grid_model.update_dataframe(pl.DataFrame())
        self._graph_canvas.sync_to_graph(self._workspace.active_graph)
        self._current_path = ""
        self._update_title()

    def _open_workflow(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Workflow", "", "Polaris Files (*.polaris)"
        )
        if path:
            try:
                self._workspace.load_all(path)
                self._current_path = path
                self._sync_tab_bar()
                self._app_state.graph = self._workspace.active_graph
                self._graph_canvas.sync_to_graph(self._workspace.active_graph)
                # Mark all nodes dirty so engine cache is rebuilt (save does not persist cache)
                for node in self._workspace.active_graph.get_nodes().values():
                    node.is_dirty = True
                self._app_state.request_execute_all()
                self._update_title()
                self._status_bar.set_status(f"Loaded: {os.path.basename(path)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load workflow: {e}")

    def _save_workflow(self) -> None:
        if not hasattr(self, "_current_path") or not self._current_path:
            self._save_as_workflow()
            return
        try:
            self._workspace.save_all(self._current_path)
            self._update_title()
            self._status_bar.set_status(f"Saved: {os.path.basename(self._current_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")

    def _save_as_workflow(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Workflow", "", "Polaris Files (*.polaris)"
        )
        if path:
            if not path.endswith(".polaris"):
                path += ".polaris"
            self._current_path = path
            self._save_workflow()
            self._update_title()

    def _import_file(self, file_type: str) -> None:
        filter_map = {
            "csv": "CSV Files (*.csv)",
            "xlsx": "Excel Files (*.xlsx)",
            "parquet": "Parquet Files (*.parquet)",
        }
        path, _ = QFileDialog.getOpenFileName(
            self, f"Import {file_type.upper()}", "", filter_map.get(file_type, "All Files (*)")
        )
        if path:
            node_type = f"{file_type}_reader"
            node_id = f"{file_type}_reader_{len(self._app_state.graph.get_nodes()) + 1}"
            node = Node(
                node_id=node_id,
                node_type=node_type,
                category=NodeCategory.SOURCE,
                params={"file_path": path},
                position=(100.0, 100.0 + len(self._app_state.graph.get_nodes()) * 80),
            )
            self._app_state.add_node(node, record_history=False)
            self._app_state.select_node(node_id)
            from PySide6.QtCore import QTimer

            QTimer.singleShot(100, lambda nid=node_id: self._app_state.request_execute(nid))

    def _export_as(self, fmt: str) -> None:
        selected = self._app_state.selected_node_ids
        if not selected:
            return
        node_id = selected[0]
        node = self._app_state.graph.get_node(node_id)
        if node is None:
            return
        ext_map = {"csv": "CSV (*.csv)", "xlsx": "Excel (*.xlsx)", "parquet": "Parquet (*.parquet)"}
        path, _ = QFileDialog.getSaveFileName(
            self, f"Export as {fmt.upper()}", "", ext_map.get(fmt, "")
        )
        if path:
            export_node_id = f"export_{node_id}"
            export_node = Node(
                node_id=export_node_id,
                node_type=f"export_{fmt}",
                category=NodeCategory.OUTPUT,
                params={"file_path": path},
            )
            self._app_state.graph.add_node(export_node)
            self._app_state.graph.add_edge(node_id, export_node_id)
            self._app_state.request_execute(export_node_id)

    def _sync_tab_bar(self) -> None:
        self._tab_bar.blockSignals(True)
        while self._tab_bar.count():
            self._tab_bar.removeTab(0)
        for tab in self._workspace.get_tab_list():
            idx = self._tab_bar.addTab(tab.name)
            if tab.tab_id == self._workspace.active_tab_id:
                self._tab_bar.setCurrentIndex(idx)
        self._tab_bar.blockSignals(False)

    def _close_tab(self, index: int) -> None:
        tab_id = list(self._workspace.get_tabs().keys())[index]
        self._workspace.close_tab(tab_id)
        self._sync_tab_bar()
        self._app_state.graph = self._workspace.active_graph
        self._graph_canvas.sync_to_graph(self._workspace.active_graph)

    def _switch_tab(self, index: int) -> None:
        tabs = list(self._workspace.get_tabs().keys())
        if 0 <= index < len(tabs):
            self._workspace.switch_to(tabs[index])
            self._app_state.graph = self._workspace.active_graph
            self._graph_canvas.sync_to_graph(self._workspace.active_graph)

    def _rename_tab(self, index: int) -> None:
        tabs = self._workspace.get_tab_list()
        if not (0 <= index < len(tabs)):
            return
        tab = tabs[index]
        current = tab.name
        name, ok = QInputDialog.getText(self, "Rename Tab", "Tab name:", text=current)
        if ok:
            name = name.strip()
            if name:
                self._workspace.rename_tab(tab.tab_id, name)
                self._sync_tab_bar()
                self._update_title()

    def _update_title(self) -> None:
        name = (
            os.path.basename(getattr(self, "_current_path", ""))
            if hasattr(self, "_current_path") and self._current_path
            else "Untitled"
        )
        self.setWindowTitle(f"Polaris Studio - {name}")

    def _build_ai_context(self) -> str:
        graph = self._workspace.active_graph
        df = self._grid_model.get_dataframe()

        lines: List[str] = []
        lines.append(f"View mode: {self._view_mode.name.lower()}")
        lines.append(f"Selected nodes: {', '.join(self._app_state.selected_node_ids) or 'none'}")
        lines.append(f"Graph nodes: {graph.get_node_count()} | edges: {graph.get_edge_count()}")

        if graph.get_nodes():
            lines.append("Graph summary:")
            for node_id, node in graph.get_nodes().items():
                params = (
                    ", ".join(f"{k}={v}" for k, v in list(node.params.items())[:4]) or "no params"
                )
                lines.append(f"- {node_id} ({node.node_type}) [{params}]")

        if len(df) > 0:
            lines.append(f"Table rows: {len(df)}")
            lines.append("Columns:")
            for col in df.columns:
                dtype = str(df.schema.get(col, ""))
                lines.append(f"- {col}: {dtype}")
            preview = df.head(5)
            lines.append("Preview:")
            for row in preview.iter_rows(named=True):
                lines.append(f"- {row}")
        else:
            lines.append("Table rows: 0")

        return "\n".join(lines)

    def _on_graph_changed(self, graph: Any) -> None:
        active_graph = graph if graph is not None else self._workspace.active_graph
        self._graph_canvas.sync_to_graph(active_graph)
        count = active_graph.get_node_count()
        ecount = active_graph.get_edge_count()
        self._status_bar.set_status(f"{count} nodes, {ecount} edges")

    def _on_node_selected(self, node_id: str) -> None:
        self._app_state.select_node(node_id)

    def _show_node_properties(self, nodes: List[Node]) -> None:
        if nodes:
            self._properties_panel.show_node(nodes[0])
            self._status_bar.set_node_info(nodes[0].node_id, nodes[0].node_type)
            self._on_node_selected_chart(nodes[0])
        else:
            self._properties_panel.show_node(None)
            self._status_bar.clear_node_info()

    def _create_node_at(self, node_type: str, x: float, y: float) -> None:
        count = len(self._app_state.graph.get_nodes()) + 1
        base = node_type
        node_id = f"{base}_{count}"
        spec = NODE_REGISTRY.get(node_type)
        cat = NodeCategory.TRANSFORM
        if spec:
            cat_map = {
                "Source": NodeCategory.SOURCE,
                "Transform": NodeCategory.TRANSFORM,
                "Filter": NodeCategory.FILTER,
                "Aggregate": NodeCategory.AGGREGATE,
                "Join": NodeCategory.JOIN,
                "Sort": NodeCategory.SORT,
                "Chart": NodeCategory.CHART,
                "Output": NodeCategory.OUTPUT,
            }
            cat = cat_map.get(spec.category, NodeCategory.TRANSFORM)

        node = Node(node_id=node_id, node_type=node_type, category=cat, position=(x, y))
        self._app_state.add_node(node)

    def _create_node_centered(self, node_type: str) -> None:
        viewport = self._graph_canvas.viewport().rect()
        center = self._graph_canvas.mapToScene(viewport.center())
        self._create_node_at(node_type, center.x(), center.y())

    def _on_connection_requested(
        self, source_id: str, source_port: str, target_id: str, target_port: str
    ) -> None:
        if not source_id or not target_id:
            return
        try:
            self._app_state.connect_nodes(source_id, target_id, source_port, target_port)
        except Exception as exc:
            self._status_bar.set_status(f"Connection failed: {exc}")

    def _on_node_moved(self, node_id: str, x: float, y: float) -> None:
        self._app_state.update_node_position(node_id, x, y)
        self._status_bar.set_status(f"Moved {node_id}")

    def _on_canvas_node_deleted(self, node_id: str) -> None:
        self._app_state.remove_node(node_id)
        self._status_bar.set_status(f"Deleted {node_id}")

    def _on_canvas_node_duplicated(self, node_id: str) -> None:
        node = self._app_state.graph.get_node(node_id)
        if node is None:
            return
        new_id = f"{node.node_id}_copy_{len(self._app_state.graph.get_nodes()) + 1}"
        new_pos = (node.position[0] + 40.0, node.position[1] + 40.0)
        new_node = Node(
            node_id=new_id,
            node_type=node.node_type,
            category=node.category,
            params=dict(node.params),
            position=new_pos,
        )
        self._app_state.add_node(new_node)
        self._status_bar.set_status(f"Duplicated {node_id} → {new_id}")

    def _on_node_selected_chart(self, node: Node) -> None:
        CHART_TYPES = {
            "bar_chart",
            "line_chart",
            "scatter_chart",
            "histogram",
            "box_chart",
            "heatmap",
        }
        if node.node_type in CHART_TYPES:
            self._chart_panel.set_chart_type(node.node_type)
            self._chart_panel.set_params(node.params)
            df = self._app_state._engine.get_cached(node.node_id)  # type: ignore[attr-defined]
            if df is not None:
                self._chart_panel.update_data(df)
            self._chart_panel_dock.show()

    def _on_canvas_selection_changed(self, node_ids: List[str]) -> None:
        if node_ids:
            self._app_state.select_multiple_nodes(node_ids)

    def _on_compute_started(self, node_id: str) -> None:
        if node_id == "all":
            self._graph_canvas.start_edge_animation()
            for item in self._graph_canvas._node_items.values():  # type: ignore[attr-defined]
                item.set_computing(True)
        else:
            target = self._graph_canvas.get_node_item(node_id)
            if target is not None:
                target.set_computing(True)

    def _on_cell_selected(self, row: int, col: int, col_name: str) -> None:
        self._formula_bar.set_cell_reference(f"R{row + 1}C{col + 1}")
        val = self._grid_model.get_cell_value(row, col)
        self._formula_bar.set_expression(str(val) if val is not None else "")

    def _on_expression_committed(self, col_name: str, expr: str) -> None:
        graph = self._workspace.active_graph
        node = Node(
            node_id=f"expr_{len(graph.get_nodes()) + 1}",
            node_type="add_column",
            category=NodeCategory.TRANSFORM,
            params={"column_name": col_name, "expression": expr},
        )
        self._app_state.add_node(node)
        terminals = [
            n
            for nid, n in graph.get_nodes().items()
            if not any(e.source_id == nid for e in graph.get_edges())
        ]
        if terminals:
            self._app_state.connect_nodes(terminals[-1].node_id, node.node_id)

    def _on_nlp_query(self, query: str) -> None:
        self._on_ai_message(query, None)

    def _on_ai_message(self, text: str, attached_node_id: Optional[str]) -> None:
        if self._ai_runner is not None:
            self._ai_runner.quit()
            self._ai_runner.wait()
        self._ai_runner = AsyncRunner(self._chat_session, text, attached_node_id)
        self._ai_runner.chat_event_signal.connect(self._on_ai_event)
        self._ai_runner.start()

    def _on_ai_event(self, event_type: str, data: Any) -> None:
        if event_type == "token":
            self._ai_panel.on_token(data)
        elif event_type == "message":
            self._ai_panel.on_message(data)
        elif event_type in {"action_batch", "command_batch"} and data:
            self._ai_panel.on_action_batch(data, auto_approved=self._ai_auto_approve)
            if self._ai_auto_approve:
                self._on_ai_apply(data)
        elif event_type == "error":
            self._ai_panel.on_error(data)
        elif event_type == "done":
            self._ai_panel.on_done()

    def _on_ai_apply(self, batch: AppCommandBatch | PipelineMutationBatch) -> None:
        messages = self._chat_session.apply_pending_batch()
        self._graph_canvas.sync_to_graph(self._workspace.active_graph)
        viewport_flash(self._graph_canvas.viewport())
        report = self._chat_session.pending_report
        if report is not None:
            self._ai_panel.on_execution_report(report)
        for m in messages:
            self._status_bar.set_status(m)

    def _on_ai_reject(self, _batch: AppCommandBatch | PipelineMutationBatch) -> None:
        self._chat_session.reject_pending_batch()
        self._status_bar.set_status("AI batch skipped")

    def _build_command_context(self) -> CommandContext:
        return CommandContext(
            graph=self._app_state.graph,
            on_node_added=lambda _node: self._graph_canvas.sync_to_graph(
                self._workspace.active_graph
            ),
            on_edge_added=lambda _src, _tgt: self._graph_canvas.sync_to_graph(
                self._workspace.active_graph
            ),
            on_node_removed=lambda _nid: self._graph_canvas.sync_to_graph(
                self._workspace.active_graph
            ),
            on_cell_update=self._apply_cell_update,
            on_view_mode=self._on_view_mode_command,
            on_panel_toggle=self._on_panel_toggle_command,
            on_auto_layout=self._auto_layout,
            on_execute=self._on_execute_command,
        )

    def _apply_cell_update(self, row: int, column: int, value: Any) -> bool:
        return self._grid_model.set_cell_value(row, column, value)

    def _on_view_mode_command(self, mode: str) -> None:
        mapping = {
            "spreadsheet": ViewMode.SPREADSHEET,
            "graph": ViewMode.GRAPH,
            "split": ViewMode.SPLIT,
        }
        target = mapping.get(mode)
        if target is not None:
            self._set_view_mode(target)

    def _on_panel_toggle_command(self, panel: str, visible: Optional[bool]) -> None:
        self._toggle_drawer(panel)
        if visible is not None:
            panel_map = {
                "ai": self._ai_panel_dock,
                "properties": self._properties_panel_dock,
                "profile": self._profile_panel_dock,
                "chart": self._chart_panel_dock,
                "nodes": self._node_palette_dock,
            }
            dock = panel_map.get(panel)
            if dock is not None:
                dock.setVisible(visible)

    def _on_execute_command(self, node_id: Optional[str]) -> None:
        if node_id:
            self._app_state.request_execute(node_id)
        else:
            self._app_state.request_execute_all()

    def _on_compute_finished(self, node_id: str, duration_ms: float) -> None:
        self._graph_canvas.stop_edge_animation()
        self._status_bar.set_execution_time(duration_ms)
        viewport_flash(self._graph_canvas.viewport())

    def _on_compute_error(self, node_id: str, error: str) -> None:
        self._graph_canvas.stop_edge_animation()
        self._status_bar.set_status(f"Error: {error}")

    def _on_table_data_ready(self, node_id: str, data: Any) -> None:
        if isinstance(data, pl.DataFrame):
            self._grid_model.update_dataframe(data)
            self._status_bar.set_row_count(len(data))
            CHART_TYPES = {
                "bar_chart",
                "line_chart",
                "scatter_chart",
                "histogram",
                "box_chart",
                "heatmap",
            }
            node = self._workspace.active_graph.get_node(node_id)
            if node is not None and node.node_type in CHART_TYPES:
                self._chart_panel.set_chart_type(node.node_type)
                self._chart_panel.set_params(node.params)
                self._chart_panel.update_data(data)
                self._chart_panel_dock.show()
            else:
                self._chart_panel.update_data(data)
        elif isinstance(data, str) and str(node_id).startswith("preview:"):
            try:
                import json

                preview_data = json.loads(data)
                columns = preview_data.get("columns", [])
                rows = preview_data.get("rows", [])
                preview_df = (
                    pl.DataFrame(rows, schema=columns, orient="row")
                    if columns
                    else pl.DataFrame(rows)
                )
                self._grid_model.update_dataframe(preview_df)
                self._status_bar.set_row_count(len(preview_df))
                self._chart_panel.update_data(preview_df)
                self._status_bar.set_status(f"Preview loaded for {node_id.split(':', 1)[1]}")
            except Exception as exc:
                self._status_bar.set_status(f"Preview failed: {exc}")
        elif isinstance(data, str) and str(node_id).startswith("profile:"):
            try:
                import json

                profile_data = json.loads(data)
                from polaris_studio.core.profiler import DataProfile

                profile = DataProfile(**profile_data)
                self._profile_panel.set_profile(profile)
                self._profile_panel_dock.show()
            except Exception:
                pass

    def _on_preview_requested(self, node_id: str) -> None:
        self._app_state.request_preview(node_id)

    def _on_column_action(self, action: str, data: str) -> None:
        if action == "stats":
            try:
                from polaris_studio.core.profiler import DataProfiler
                from polaris_studio.ui.dialogs.column_stats_dialog import ColumnStatsDialog

                df = self._grid_model.get_dataframe()
                profile = DataProfiler.profile(df, "table")
                for col_profile in profile.columns:
                    if col_profile.name == data:
                        dialog = ColumnStatsDialog(col_profile, parent=self)
                        dialog.exec()
                        break
            except Exception as exc:
                self._status_bar.set_status(f"Stats unavailable: {exc}")
            return

        if action == "filter":
            try:
                from polaris_studio.ui.dialogs.expression_editor import ExpressionEditorDialog

                df = self._grid_model.get_dataframe()
                expr_dialog = ExpressionEditorDialog(
                    columns=df.columns, initial_expr=f"pl.col('{data}')", parent=self
                )
                if expr_dialog.exec() == QDialog.DialogCode.Accepted:
                    expr = expr_dialog.get_expression()
                    if expr:
                        graph = self._workspace.active_graph
                        existing_ids = set(graph.get_nodes().keys())
                        node_id = f"filter_{len(existing_ids) + 1}"
                        node = Node(
                            node_id=node_id,
                            node_type="filter",
                            category=NodeCategory.FILTER,
                            params={"expression": expr},
                        )
                        self._app_state.add_node(node)
                        sources = [
                            n
                            for nid, n in graph.get_nodes().items()
                            if nid in existing_ids
                            and not any(e.source_id == nid for e in graph.get_edges())
                        ]
                        if sources:
                            self._app_state.connect_nodes(sources[-1].node_id, node_id)
                        self._status_bar.set_status(f"Added filter node for {data}")
            except Exception as exc:
                self._status_bar.set_status(f"Filter unavailable: {exc}")
            return

        if action == "rename":
            old_name = data
            new_name, ok = QInputDialog.getText(self, "Rename Column", f"Rename '{old_name}' to:")
            if ok and new_name.strip():
                if self._grid_model.rename_column(old_name, new_name.strip()):
                    self._status_bar.set_status(f"Renamed {old_name} to {new_name.strip()}")
                else:
                    QMessageBox.warning(self, "Rename Column", f"Could not rename '{old_name}'.")
            return

        if action == "cast":
            parts = data.split("|", 1)
            if len(parts) == 2 and self._grid_model.cast_column(parts[0], parts[1]):
                self._status_bar.set_status(f"Casted {parts[0]} to {parts[1]}")
            return

        if action == "fill_null":
            parts = data.split("|", 1)
            if len(parts) == 2:
                strategy_map = {
                    "Forward Fill": "forward",
                    "Backward Fill": "backward",
                    "Mean": "mean",
                    "Median": "median",
                    "Zero": "zero",
                    "Empty String": "empty string",
                }
                strategy = strategy_map.get(parts[1], parts[1].lower())
                if self._grid_model.fill_null(parts[0], strategy):
                    self._status_bar.set_status(f"Filled nulls in {parts[0]}")
            return

        if action == "delete_row":
            try:
                row = int(data)
                if self._grid_model.delete_rows([row]):
                    self._status_bar.set_status(f"Deleted row {row + 1}")
            except ValueError:
                pass
            return

        if action == "insert_row_above":
            try:
                row = int(data)
                if self._grid_model.insert_row(row):
                    self._status_bar.set_status(f"Inserted row above {row + 1}")
            except ValueError:
                pass
            return

        if action == "insert_row_below":
            try:
                row = int(data)
                if self._grid_model.insert_row(row + 1):
                    self._status_bar.set_status(f"Inserted row below {row + 1}")
            except ValueError:
                pass
            return

        if action == "freeze":
            self._status_bar.set_status("Column freezing is not wired yet")
            return

    def _auto_layout(self) -> None:
        from polaris_studio.ui.graph.layout_engine import auto_layout

        graph = self._workspace.active_graph
        positions = auto_layout(graph)
        for nid, (x, y) in positions.items():
            node = graph.get_node(nid)
            if node:
                node.position = (x, y)
        self._graph_canvas.sync_to_graph(graph)

    def _execute_all(self) -> None:
        self._app_state.request_execute_all()

    def _execute_selected(self) -> None:
        if self._app_state.selected_node_ids:
            self._app_state.request_execute(self._app_state.selected_node_ids[0])

    def _profile_selected(self) -> None:
        if self._app_state.selected_node_ids:
            self._app_state.request_profile(self._app_state.selected_node_ids[0])

    def _clear_graph(self) -> None:
        reply = QMessageBox.question(
            self,
            "Clear Graph",
            "Remove all nodes and edges?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._workspace.active_graph.clear()
            self._graph_canvas.sync_to_graph(self._workspace.active_graph)
            self._grid_model.update_dataframe(pl.DataFrame())
            self._chart_panel.clear()

    def _show_settings(self) -> None:
        from polaris_studio.ui.dialogs.settings_dialog import SettingsDialog

        current = self._get_all_settings()
        dialog = SettingsDialog(current_settings=current, parent=self)
        dialog.settings_applied.connect(self._on_settings_applied)
        dialog.exec()

    def _on_settings_applied(self, settings: Dict[str, Any]) -> None:
        self._settings_manager.setValue("ai/gemini_key", settings.get("gemini_key", ""))
        self._settings_manager.setValue(
            "ai/gemini_model", settings.get("gemini_model", "gemma-4-31b-it")
        )
        self._settings_manager.setValue(
            "ai/auto_approve",
            "true" if settings.get("ai_auto_approve", False) else "false",
        )
        self._settings_manager.setValue(
            "ai/show_action_json",
            "true" if settings.get("ai_show_action_json", True) else "false",
        )
        self._settings_manager.setValue(
            "appearance/theme", settings.get("theme", "Dark Glass (Default)")
        )
        self._settings_manager.setValue("appearance/font_size", settings.get("font_size", 11))
        self._settings_manager.setValue("performance/worker_count", settings.get("worker_count", 2))
        self._settings_manager.setValue("performance/cache_size", settings.get("cache_size", 1024))
        self._settings_manager.setValue(
            "performance/auto_profile",
            "true" if settings.get("auto_profile", True) else "false",
        )

        self._ai_backend.configure(
            api_key=settings.get("gemini_key"),
            model=settings.get("gemini_model", "gemma-4-31b-it"),
        )
        self._ai_auto_approve = bool(settings.get("ai_auto_approve", False))
        self._ai_panel.set_auto_approve_enabled(self._ai_auto_approve)
        self._ai_panel.set_show_action_json(bool(settings.get("ai_show_action_json", True)))
        self._status_bar.set_status("Settings applied and saved")

    def _load_and_apply_settings(self) -> None:
        settings = self._get_all_settings()
        self._on_settings_applied(settings)

    def _get_all_settings(self) -> Dict[str, Any]:
        return {
            "gemini_key": self._settings_manager.value("ai/gemini_key", ""),
            "gemini_model": self._settings_manager.value("ai/gemini_model", "gemma-4-31b-it"),
            "ai_auto_approve": str(self._settings_manager.value("ai/auto_approve", "false"))
            == "true",
            "ai_show_action_json": str(self._settings_manager.value("ai/show_action_json", "true"))
            == "true",
            "theme": self._settings_manager.value("appearance/theme", "Dark Glass (Default)"),
            "font_size": int(str(self._settings_manager.value("appearance/font_size", 11))),
            "worker_count": int(str(self._settings_manager.value("performance/worker_count", 2))),
            "cache_size": int(str(self._settings_manager.value("performance/cache_size", 1024))),
            "auto_profile": str(self._settings_manager.value("performance/auto_profile", "true"))
            == "true",
        }

    def closeEvent(self, event) -> None:
        self._app_state.history.clear()
        self._workspace.cleanup_temp()
        super().closeEvent(event)
