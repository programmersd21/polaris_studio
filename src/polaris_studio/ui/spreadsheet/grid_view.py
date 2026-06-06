from __future__ import annotations

from typing import Any, List, Optional, Set

from PySide6.QtCore import QItemSelection, QModelIndex, Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QAbstractItemView, QApplication, QMenu, QTableView, QWidget

from polaris_studio.ui.spreadsheet.grid_model import PolarisGridModel
from polaris_studio.ui.motion import viewport_flash


class SpreadsheetGrid(QTableView):
    cell_selected = Signal(int, int, str)
    range_selected = Signal(QItemSelection)
    edit_committed = Signal(int, int, Any)
    column_action_requested = Signal(str, str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self) -> None:
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.setDragEnabled(False)
        self.setAlternatingRowColors(False)
        self.setShowGrid(True)
        self.setSortingEnabled(True)
        self.setWordWrap(False)
        self.verticalHeader().setDefaultSectionSize(28)
        self.horizontalHeader().setDefaultSectionSize(160)
        self.horizontalHeader().setMinimumSectionSize(80)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.horizontalHeader().customContextMenuRequested.connect(self._show_header_context_menu)
        self.verticalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.verticalHeader().customContextMenuRequested.connect(self._show_row_context_menu)
        self.setStyleSheet(self._style())

    def _setup_connections(self) -> None:
        self.clicked.connect(self._on_clicked)
        if self.selectionModel():
            self.selectionModel().selectionChanged.connect(self._on_selection_changed)

    def _style(self) -> str:
        return """
        QTableView {
            border: none;
            gridline-color: #e8e8e8;
            font-family: "JetBrains Mono", "Inter";
            font-size: 12px;
            outline: none;
        }
        QTableView::item {
            padding: 2px 8px;
            border-right: 1px solid #e8e8e8;
            border-bottom: 1px solid #e8e8e8;
        }
        QTableView::item:selected {
            border-color: #5b4bd6;
        }
        QHeaderView::section {
            border: none;
            border-right: 1px solid #d4d4d4;
            border-bottom: 1px solid #d4d4d4;
            padding: 4px 8px;
            font-size: 11px;
            font-weight: 600;
            font-family: "Inter";
        }
        """

    def set_model(self, model: PolarisGridModel) -> None:
        self.setModel(model)
        model.data_changed.connect(self._on_model_data_changed)
        if self.selectionModel():
            self.selectionModel().selectionChanged.connect(self._on_selection_changed)

    def _on_clicked(self, index: QModelIndex) -> None:
        if index.isValid() and self.model():
            model = self.model()  # type: ignore[assignment]
            if not isinstance(model, PolarisGridModel):
                return
            col_name = model.get_column_names()[index.column()]
            self.cell_selected.emit(index.row(), index.column(), col_name)

    def _on_selection_changed(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        self.range_selected.emit(selected)

    def _on_model_data_changed(self) -> None:
        viewport_flash(self.viewport())
        self.resizeColumnsToContents()

    def _show_header_context_menu(self, pos) -> None:
        col = self.horizontalHeader().logicalIndexAt(pos)
        if col < 0 or not self.model():
            return
        model = self.model()  # type: ignore[assignment]
        if not isinstance(model, PolarisGridModel):
            return
        col_name = model.get_column_names()[col]

        menu = QMenu(self)

        sort_asc = QAction("Sort Ascending", self)
        sort_asc.triggered.connect(lambda: self.sortByColumn(col, Qt.SortOrder.AscendingOrder))
        menu.addAction(sort_asc)

        sort_desc = QAction("Sort Descending", self)
        sort_desc.triggered.connect(lambda: self.sortByColumn(col, Qt.SortOrder.DescendingOrder))
        menu.addAction(sort_desc)

        menu.addSeparator()

        filter_act = QAction("Filter by this column...", self)
        filter_act.triggered.connect(lambda: self.column_action_requested.emit("filter", col_name))
        menu.addAction(filter_act)

        menu.addSeparator()

        rename_act = QAction("Rename Column", self)
        rename_act.triggered.connect(lambda: self.column_action_requested.emit("rename", col_name))
        menu.addAction(rename_act)

        change_type_menu = QMenu("Change Type", self)
        for dt in ["Int32", "Int64", "Float32", "Float64", "Utf8", "Boolean", "Date", "Datetime"]:
            act = QAction(dt, self)
            act.triggered.connect(
                lambda checked, d=dt: self.column_action_requested.emit("cast", f"{col_name}|{d}")
            )
            change_type_menu.addAction(act)
        menu.addMenu(change_type_menu)

        fill_menu = QMenu("Fill Nulls", self)
        for strat in ["Forward Fill", "Backward Fill", "Mean", "Median", "Zero", "Empty String"]:
            act = QAction(strat, self)
            act.triggered.connect(
                lambda checked, s=strat: self.column_action_requested.emit(
                    "fill_null", f"{col_name}|{s}"
                )
            )
            fill_menu.addAction(act)
        menu.addMenu(fill_menu)

        menu.addSeparator()

        stats_act = QAction("Column Statistics...", self)
        stats_act.triggered.connect(lambda: self.column_action_requested.emit("stats", col_name))
        menu.addAction(stats_act)

        freeze_act = QAction("Freeze at This Column", self)
        freeze_act.triggered.connect(lambda: self.column_action_requested.emit("freeze", str(col)))
        menu.addAction(freeze_act)

        menu.exec(self.horizontalHeader().viewport().mapToGlobal(pos))

    def _show_row_context_menu(self, pos) -> None:
        row = self.verticalHeader().logicalIndexAt(pos)
        menu = QMenu(self)
        delete_act = QAction("Delete Row", self)
        delete_act.triggered.connect(
            lambda: self.column_action_requested.emit("delete_row", str(row))
        )
        menu.addAction(delete_act)

        insert_above = QAction("Insert Row Above", self)
        insert_above.triggered.connect(
            lambda: self.column_action_requested.emit("insert_row_above", str(row))
        )
        menu.addAction(insert_above)

        insert_below = QAction("Insert Row Below", self)
        insert_below.triggered.connect(
            lambda: self.column_action_requested.emit("insert_row_below", str(row))
        )
        menu.addAction(insert_below)

        menu.exec(self.verticalHeader().viewport().mapToGlobal(pos))

    def copy_selection(self) -> None:
        sel = self.selectionModel()
        if not sel or not sel.hasSelection():
            return
        indexes = sel.selectedIndexes()
        if not indexes:
            return
        rows: Set[int] = set()
        cols: Set[int] = set()
        for idx in indexes:
            rows.add(idx.row())
            cols.add(idx.column())

        sorted_rows = sorted(rows)
        sorted_cols = sorted(cols)

        model = self.model()  # type: ignore[assignment]
        if not isinstance(model, PolarisGridModel):
            return
        lines: List[str] = []
        header = "\t".join(model.get_column_names()[c] for c in sorted_cols)
        lines.append(header)

        for r in sorted_rows:
            vals = []
            for c in sorted_cols:
                val = model.data(model.index(r, c), Qt.ItemDataRole.DisplayRole)
                vals.append(str(val) if val is not None else "")
            lines.append("\t".join(vals))

        clipboard = QApplication.clipboard()
        clipboard.setText("\n".join(lines))

    def keyPressEvent(self, event) -> None:
        if event.matches(QKeySequence.StandardKey.Copy):
            self.copy_selection()
            event.accept()
            return
        if event.matches(QKeySequence.StandardKey.SelectAll):
            self.selectAll()
            event.accept()
            return
        if event.key() == Qt.Key.Key_F2:
            idx = self.currentIndex()
            if idx.isValid():
                self.edit(idx)
            event.accept()
            return
        if event.key() == Qt.Key.Key_Delete:
            idx = self.currentIndex()
            if idx.isValid() and self.model():
                self.model().setData(idx, None, Qt.ItemDataRole.EditRole)
            event.accept()
            return
        super().keyPressEvent(event)
