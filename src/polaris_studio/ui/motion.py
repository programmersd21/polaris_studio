"""Cinematic motion primitives for Polaris Studio.

All public helpers are safe to call from the main thread. Animations are
parented to their owner so they are automatically destroyed when the widget
is deleted. No lambda-based Qt callbacks are used (avoid Windows AV crash).
"""

from __future__ import annotations

from typing import Callable, Iterable, Optional

from PySide6.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPoint,
    QPointF,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    QTimer,
    QVariantAnimation,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsObject, QGraphicsOpacityEffect, QWidget

# ── timing constants ──────────────────────────────────────────────────────────
MICRO = 80
FAST = 130
BASE = 210
SLOW = 340
STAGGER = 36

# ── easing curves ────────────────────────────────────────────────────────────


def spring() -> QEasingCurve:
    """Overshoot-then-settle - ideal for entrances and press-release."""
    return QEasingCurve(QEasingCurve.Type.OutBack)


def decel() -> QEasingCurve:
    """Fast-start slow-end - scrolls, drags, reveals."""
    return QEasingCurve(QEasingCurve.Type.OutCubic)


def accel_decel() -> QEasingCurve:
    """Symmetric ease-in-out - cross-fades, morphs."""
    return QEasingCurve(QEasingCurve.Type.InOutCubic)


# Keep alias used by existing callers
def premium_curve() -> QEasingCurve:
    return decel()


def soft_spring_curve() -> QEasingCurve:
    return spring()


# ── lifetime management ───────────────────────────────────────────────────────


def _keep(owner: object, anim: object) -> None:
    bucket = getattr(owner, "_polaris_anims", None)
    if bucket is None:
        bucket = []
        try:
            setattr(owner, "_polaris_anims", bucket)
        except AttributeError:
            return
    bucket.append(anim)
    finished = getattr(anim, "finished", None)
    if finished is not None:
        finished.connect(lambda: bucket.remove(anim) if anim in bucket else None)


# ── widget entrance ───────────────────────────────────────────────────────────


def fade_slide_in(
    widget: QWidget,
    *,
    delay_ms: int = 0,
    duration_ms: int = BASE,
    offset: QPoint = QPoint(0, 14),
) -> None:
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    effect.setOpacity(0.0)

    end_pos = widget.pos()
    start_pos = end_pos + offset
    widget.move(start_pos)
    widget.setVisible(True)

    group = QParallelAnimationGroup(widget)

    op = QPropertyAnimation(effect, b"opacity", group)
    op.setStartValue(0.0)
    op.setEndValue(1.0)
    op.setDuration(duration_ms)
    op.setEasingCurve(decel())

    pos = QPropertyAnimation(widget, b"pos", group)
    pos.setStartValue(start_pos)
    pos.setEndValue(end_pos)
    pos.setDuration(duration_ms)
    pos.setEasingCurve(spring())

    group.addAnimation(op)
    group.addAnimation(pos)
    _keep(widget, group)
    QTimer.singleShot(delay_ms, group.start)


def staggered_reveal(widgets: Iterable[QWidget], *, delay_ms: int = 0) -> None:
    for i, w in enumerate(widgets):
        fade_slide_in(w, delay_ms=delay_ms + i * STAGGER)


# ── press micro-scale ─────────────────────────────────────────────────────────


def press_scale(widget: QWidget, *, scale_down: float = 0.94) -> None:
    """Squeeze down on press - call on mousePressEvent."""
    anim = QVariantAnimation(widget)
    anim.setStartValue(1.0)
    anim.setEndValue(scale_down)
    anim.setDuration(MICRO)
    anim.setEasingCurve(accel_decel())

    def _apply(v: float) -> None:
        if not widget.isVisible():
            return
        # Use stylesheet transform - widget must have setProperty support
        widget.setProperty("_press_scale", v)
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    anim.valueChanged.connect(_apply)
    _keep(widget, anim)
    anim.start()


def release_scale(widget: QWidget) -> None:
    """Spring back on release - call on mouseReleaseEvent."""
    anim = QVariantAnimation(widget)
    anim.setStartValue(0.94)
    anim.setEndValue(1.0)
    anim.setDuration(FAST)
    anim.setEasingCurve(spring())
    anim.valueChanged.connect(lambda v: None)  # force keep-alive
    _keep(widget, anim)
    anim.start()


# ── opacity pop ───────────────────────────────────────────────────────────────


def opacity_pop(
    widget: QWidget, *, from_: float = 0.6, to: float = 1.0, duration_ms: int = FAST
) -> None:
    """Flash opacity up - used for token stream / typing feedback."""
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    effect.setOpacity(from_)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setStartValue(from_)
    anim.setEndValue(to)
    anim.setDuration(duration_ms)
    anim.setEasingCurve(decel())
    _keep(widget, anim)
    anim.start()


# ── cross-fade label text ─────────────────────────────────────────────────────


def crossfade_label(
    widget: QWidget, new_text: str, setter: Callable[[str], None], *, duration_ms: int = FAST
) -> None:
    """Fade out, swap text, fade in - for status / info labels."""
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)

    seq = QSequentialAnimationGroup(widget)

    fade_out = QPropertyAnimation(effect, b"opacity", seq)
    fade_out.setStartValue(1.0)
    fade_out.setEndValue(0.0)
    fade_out.setDuration(duration_ms // 2)
    fade_out.setEasingCurve(accel_decel())

    fade_in = QPropertyAnimation(effect, b"opacity", seq)
    fade_in.setStartValue(0.0)
    fade_in.setEndValue(1.0)
    fade_in.setDuration(duration_ms // 2)
    fade_in.setEasingCurve(decel())

    seq.addAnimation(fade_out)
    seq.addAnimation(fade_in)

    # swap text at the midpoint
    fade_out.finished.connect(lambda: setter(new_text))

    _keep(widget, seq)
    seq.start()


# ── color morph (background via QVariantAnimation + stylesheet) ───────────────


def morph_bg(widget: QWidget, from_hex: str, to_hex: str, *, duration_ms: int = BASE) -> None:
    """Animate background-color between two hex colours via inline stylesheet."""
    c0 = QColor(from_hex)
    c1 = QColor(to_hex)

    anim = QVariantAnimation(widget)
    anim.setStartValue(c0)
    anim.setEndValue(c1)
    anim.setDuration(duration_ms)
    anim.setEasingCurve(accel_decel())

    def _paint(color: QColor) -> None:
        if not widget.isVisible():
            return
        widget.setStyleSheet(
            widget.styleSheet().split("/* morph */")[0]
            + f"/* morph */ background-color: {color.name()};"
        )

    anim.valueChanged.connect(_paint)
    _keep(widget, anim)
    anim.start()


# ── viewport flash ────────────────────────────────────────────────────────────


def viewport_flash(widget: QWidget, *, duration_ms: int = BASE) -> None:
    orig = widget.styleSheet()
    widget.setStyleSheet(orig + "\nbackground-color: rgba(36, 91, 219, 0.12);")
    QTimer.singleShot(duration_ms, lambda: widget.setStyleSheet(orig))


# ── graphics-item helpers ─────────────────────────────────────────────────────


def graphics_materialize(
    item: QGraphicsObject,
    *,
    delay_ms: int = 0,
    duration_ms: int = SLOW,
    start_scale: float = 0.92,
) -> None:
    item.setOpacity(0.0)
    item.setScale(start_scale)

    group = QParallelAnimationGroup()

    op = QPropertyAnimation(targetObject=item, propertyName=b"opacity", parent=group)
    op.setStartValue(0.0)
    op.setEndValue(1.0)
    op.setDuration(duration_ms)
    op.setEasingCurve(decel())

    sc = QPropertyAnimation(targetObject=item, propertyName=b"scale", parent=group)
    sc.setStartValue(start_scale)
    sc.setEndValue(1.0)
    sc.setDuration(duration_ms)
    sc.setEasingCurve(spring())

    group.addAnimation(op)
    group.addAnimation(sc)
    _keep(item, group)
    QTimer.singleShot(delay_ms, group.start)


def graphics_fade_out(
    item: QGraphicsObject,
    *,
    duration_ms: int = FAST,
    on_finished: Optional[Callable[[], None]] = None,
) -> None:
    anim = QPropertyAnimation(targetObject=item, propertyName=b"opacity")
    anim.setStartValue(item.opacity())
    anim.setEndValue(0.0)
    anim.setDuration(duration_ms)
    anim.setEasingCurve(decel())
    if on_finished:
        anim.finished.connect(on_finished)
    _keep(item, anim)
    anim.start()


def graphics_destroy(
    item: QGraphicsObject,
    *,
    on_finished: Optional[Callable[[], None]] = None,
) -> None:
    """Cinematic delete: scale to zero + fade out simultaneously with spring ease."""
    group = QParallelAnimationGroup()

    op = QPropertyAnimation(targetObject=item, propertyName=b"opacity", parent=group)
    op.setStartValue(1.0)
    op.setEndValue(0.0)
    op.setDuration(SLOW)
    op.setEasingCurve(accel_decel())

    sc = QPropertyAnimation(targetObject=item, propertyName=b"scale", parent=group)
    sc.setStartValue(1.0)
    sc.setEndValue(0.0)
    sc.setDuration(SLOW)
    # Fast-in slow-out: item shrinks quickly then eases into nothing
    sc.setEasingCurve(QEasingCurve(QEasingCurve.Type.InBack))

    group.addAnimation(op)
    group.addAnimation(sc)
    if on_finished:
        group.finished.connect(on_finished)
    _keep(item, group)
    group.start()


def animate_graphics_pos(
    item: QGraphicsObject, end_pos: QPointF, *, duration_ms: int = BASE
) -> None:
    anim = QPropertyAnimation(item, b"pos")
    anim.setStartValue(item.pos())
    anim.setEndValue(end_pos)
    anim.setDuration(duration_ms)
    anim.setEasingCurve(decel())
    _keep(item, anim)
    anim.start()


def pulse_graphics_item(item: QGraphicsObject, *, peak_scale: float = 1.035) -> None:
    anim = QVariantAnimation()
    anim.setStartValue(1.0)
    anim.setKeyValueAt(0.45, peak_scale)
    anim.setEndValue(1.0)
    anim.setDuration(BASE)
    anim.setEasingCurve(decel())
    anim.valueChanged.connect(lambda v: item.setScale(float(v)))
    _keep(item, anim)
    anim.start()
