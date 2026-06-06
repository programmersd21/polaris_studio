from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QTableView


class FreezeManager:
    def __init__(self, main_view: QTableView) -> None:
        self._main_view = main_view
        self._frozen_col = 0
        self._frozen_row = 0
        self._frozen_view: Optional[QTableView] = None
        self._setup()

    def _setup(self) -> None:
        pass

    def freeze_column(self, col_index: int) -> None:
        self._frozen_col = max(0, col_index)
        self._update()

    def freeze_row(self, row_index: int) -> None:
        self._frozen_row = max(0, row_index)
        self._update()

    def _update(self) -> None:
        pass

    def unfreeze_all(self) -> None:
        self._frozen_col = 0
        self._frozen_row = 0
        self._update()

    @property
    def frozen_columns(self) -> int:
        return self._frozen_col

    @property
    def frozen_rows(self) -> int:
        return self._frozen_row
