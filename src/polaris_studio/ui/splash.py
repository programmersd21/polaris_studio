from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QRect,
    QTimer,
    Qt,
    QVariantAnimation,
)
from PySide6.QtGui import QBrush, QColor, QFont, QFontMetrics, QPixmap, QRadialGradient
from PySide6.QtWidgets import QLabel, QWidget

from polaris_studio.ui.theme import PALETTE, font_instrument_serif


class IntroOverlay(QWidget):
    def __init__(
        self,
        parent: QWidget,
        icon_path: str,
        target_icon: QLabel,
        target_wordmark: QLabel,
    ) -> None:
        super().__init__(parent)
        self._target_icon = target_icon
        self._target_wordmark = target_wordmark

        self.setGeometry(parent.rect())
        self.setAutoFillBackground(True)
        palette = self.palette()
        cx, cy = parent.width() / 2, parent.height() / 2
        radius = max(parent.width(), parent.height()) / 1.4
        gradient = QRadialGradient(cx, cy, radius)
        gradient.setColorAt(0.0, QColor(PALETTE.bg_app))
        gradient.setColorAt(1.0, QColor(PALETTE.bg_panel))
        palette.setBrush(self.backgroundRole(), QBrush(gradient))
        self.setPalette(palette)

        self._intro_icon = 280
        self._intro_point = 200
        self._final_point = 24
        self._gap = 56
        self._slide_offset = 36
        self._hold_ms = 2600

        text_w, text_h = self._measure_text(self._intro_point, bold=True)
        icon_w = icon_h = self._intro_icon
        total_w = max(icon_w, text_w)
        total_h = icon_h + self._gap + text_h
        ox = (parent.width() - total_w) // 2
        oy = (parent.height() - total_h) // 2

        self._icon_label = QLabel(self)
        self._icon_label.setScaledContents(True)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            self._icon_label.setPixmap(
                pixmap.scaled(
                    icon_w,
                    icon_h,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        self._icon_x_center = ox + (total_w - icon_w) // 2
        self._icon_y_center = oy
        self._icon_label.setGeometry(self._icon_x_center, self._icon_y_center, icon_w, icon_h)

        self._text_label = QLabel("Polaris Studio", self)
        self._text_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
        self._apply_text_style(self._intro_point, bold=True)
        self._text_x_center = ox + (total_w - text_w) // 2
        self._text_y_center = oy + icon_h + self._gap
        self._text_label.setGeometry(self._text_x_center, self._text_y_center, text_w, text_h)

        self._icon_label.setWindowOpacity(0.0)
        self._text_label.setWindowOpacity(0.0)

        self.raise_()
        self.show()

    def _measure_text(self, point: int, bold: bool) -> tuple[int, int]:
        font = font_instrument_serif(point)
        font.setWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
        fm = QFontMetrics(font)
        w = fm.horizontalAdvance("Polaris Studio")
        h = int(point * 1.3)
        return w, h

    def _apply_text_style(self, point: int, bold: bool) -> None:
        weight_css = "900" if bold else "400"
        self._text_label.setStyleSheet(
            f"color: {PALETTE.text_primary}; font-family: 'Instrument Serif'; "
            f"font-weight: {weight_css}; font-size: {point}px; "
            f"letter-spacing: -2px; "
            f"background: transparent;"
        )
        font = font_instrument_serif(point)
        font.setWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        self._text_label.setFont(font)

    def animate_in(self) -> None:
        icon_start = self._icon_label.geometry().adjusted(
            0, self._slide_offset, 0, self._slide_offset
        )
        self._icon_label.setGeometry(icon_start)
        text_start = self._text_label.geometry().adjusted(
            0, self._slide_offset, 0, self._slide_offset
        )
        self._text_label.setGeometry(text_start)

        self._icon_slide = QPropertyAnimation(self._icon_label, b"geometry", self)
        self._icon_slide.setDuration(1100)
        self._icon_slide.setStartValue(icon_start)
        self._icon_slide.setEndValue(
            icon_start.adjusted(0, -self._slide_offset, 0, -self._slide_offset)
        )
        self._icon_slide.setEasingCurve(QEasingCurve.Type.OutQuart)

        self._icon_fade = QPropertyAnimation(self._icon_label, b"windowOpacity", self)
        self._icon_fade.setDuration(1100)
        self._icon_fade.setStartValue(0.0)
        self._icon_fade.setEndValue(1.0)
        self._icon_fade.setEasingCurve(QEasingCurve.Type.OutQuart)

        self._icon_slide.start()
        self._icon_fade.start()

        QTimer.singleShot(280, self._animate_text)
        QTimer.singleShot(self._hold_ms, self._morph_to_toolbar)

    def _animate_text(self) -> None:
        text_geom = self._text_label.geometry()
        text_start = text_geom.adjusted(0, self._slide_offset, 0, self._slide_offset)
        self._text_label.setGeometry(text_start)

        self._text_slide = QPropertyAnimation(self._text_label, b"geometry", self)
        self._text_slide.setDuration(1300)
        self._text_slide.setStartValue(text_start)
        self._text_slide.setEndValue(
            text_start.adjusted(0, -self._slide_offset, 0, -self._slide_offset)
        )
        self._text_slide.setEasingCurve(QEasingCurve.Type.OutQuart)

        self._text_fade = QPropertyAnimation(self._text_label, b"windowOpacity", self)
        self._text_fade.setDuration(1300)
        self._text_fade.setStartValue(0.0)
        self._text_fade.setEndValue(1.0)
        self._text_fade.setEasingCurve(QEasingCurve.Type.OutQuart)

        self._text_slide.start()
        self._text_fade.start()

    def _target_rect_for(self, widget: QLabel) -> QRect:
        parent = self.parent()
        if not isinstance(parent, QWidget):
            return QRect(widget.geometry())
        g = widget.geometry()
        top_left = widget.mapTo(parent, g.topLeft())
        return QRect(top_left.x(), top_left.y(), g.width(), g.height())

    def _morph_to_toolbar(self) -> None:
        icon_target = self._target_rect_for(self._target_icon)
        word_target = self._target_rect_for(self._target_wordmark)

        self._icon_label.setMinimumSize(0, 0)
        self._icon_label.setMaximumSize(16777215, 16777215)
        self._text_label.setMinimumSize(0, 0)
        self._text_label.setMaximumSize(16777215, 16777215)

        self._icon_anim = QPropertyAnimation(self._icon_label, b"geometry", self)
        self._icon_anim.setDuration(1100)
        self._icon_anim.setStartValue(self._icon_label.geometry())
        self._icon_anim.setEndValue(icon_target)
        self._icon_anim.setEasingCurve(QEasingCurve.Type.InOutQuart)

        end_text_w, end_text_h = self._measure_text(self._final_point, bold=False)
        end_text_w = max(end_text_w, word_target.width())
        end_text_h = max(end_text_h, word_target.height())
        self._text_anim = QPropertyAnimation(self._text_label, b"geometry", self)
        self._text_anim.setDuration(1100)
        self._text_anim.setStartValue(self._text_label.geometry())
        self._text_anim.setEndValue(QRect(word_target.x(), word_target.y(), end_text_w, end_text_h))
        self._text_anim.setEasingCurve(QEasingCurve.Type.InOutQuart)

        self._size_anim = QVariantAnimation(self)
        self._size_anim.setDuration(1100)
        self._size_anim.setStartValue(self._intro_point)
        self._size_anim.setEndValue(self._final_point)
        self._size_anim.setEasingCurve(QEasingCurve.Type.InOutQuart)
        self._size_anim.valueChanged.connect(self._on_size_changed)

        self._fade_anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade_anim.setDuration(1100)
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.Linear)
        self._fade_anim.finished.connect(self.deleteLater)

        self._icon_anim.start()
        self._text_anim.start()
        self._size_anim.start()
        self._fade_anim.start()

    def _on_size_changed(self, point: object) -> None:
        p = int(point)  # type: ignore[call-overload]
        bold = p > 80
        self._apply_text_style(p, bold)
        w, h = self._measure_text(p, bold)
        if self._text_anim is not None:
            current = self._text_anim.currentValue()
            if isinstance(current, QRect):
                self._text_label.setGeometry(current.x(), current.y(), w, h)
