#!/usr/bin/python

"""
Quick Bezier profile editor

...Sorta

"""

from __future__ import division # Need to get floats when dividing intergers
from Qt import QtWidgets, QtGui, QtCore, QtCompat
import maya.OpenMayaUI as mui
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Debug mode: Enable curve sampling visualization
DEBUG = True

# Thank you Freya Holmer | Neat Corp
# https://youtu.be/NzjF1pdlK7Y

def lerp(a, b, t):
    return ((1.0 - t) * a + b * t)
    
def inv_lerp(a, b, v):
    return ((v - a) / (b - a))

def remap(iMin, iMax, oMin, oMax, v):
    t = inv_lerp(iMin, iMax, v)
    return lerp(oMin, oMax, t)

def cubic_bezier(p0, p1, p2, p3, t):
    """Evaluate a cubic Bezier curve at parameter t (0 to 1)"""
    u = 1.0 - t
    tt = t * t
    uu = u * u
    uuu = uu * u
    ttt = tt * t

    # B(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃
    return uuu * p0 + 3 * uu * t * p1 + 3 * u * tt * p2 + ttt * p3

def cubic_bezier_derivative(p0, p1, p2, p3, t):
    """Evaluate the derivative of a cubic Bezier curve at parameter t"""
    u = 1.0 - t
    uu = u * u
    tt = t * t

    # B'(t) = 3(1-t)²(P₁-P₀) + 6(1-t)t(P₂-P₁) + 3t²(P₃-P₂)
    return 3 * uu * (p1 - p0) + 6 * u * t * (p2 - p1) + 3 * tt * (p3 - p2)

def _get_maya_window():
    ptr = mui.MQtUtil.mainWindow()
    return QtCompat.wrapInstance(int(ptr), QtWidgets.QMainWindow)


class EphemeralHotkeyFilter(QtCore.QObject):
    """
    Global event filter to detect hotkey press/release for ephemeral mode.
    This allows the curve editor to show/hide even when it doesn't have focus.
    """

    def __init__(self, curve_editor, hotkey):
        super(EphemeralHotkeyFilter, self).__init__()
        self.curve_editor = curve_editor
        self.hotkey = hotkey
        self.hotkey_pressed = False

    def eventFilter(self, obj, event):
        # Only process key events
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() == self.hotkey and not event.isAutoRepeat():
                if not self.hotkey_pressed:
                    self.hotkey_pressed = True
                    self.curve_editor.show()
                    self.curve_editor.raise_()
                    self.curve_editor.activateWindow()
                    if DEBUG:
                        logger.debug("Global hotkey pressed - showing curve editor")
        elif event.type() == QtCore.QEvent.KeyRelease:
            if event.key() == self.hotkey and not event.isAutoRepeat():
                if self.hotkey_pressed:
                    self.hotkey_pressed = False
                    self.curve_editor.hide()
                    if DEBUG:
                        logger.debug("Global hotkey released - hiding curve editor")

        # Always pass the event through
        return False 

class Example(QtWidgets.QDialog):

    def __init__(self, ephemeral_mode=False, hotkey=QtCore.Qt.Key_Shift):
        super(Example, self).__init__()

        self.ephemeral_mode = ephemeral_mode
        self.hotkey = hotkey
        self.hotkey_pressed = False

        self.setParent(_get_maya_window())

        if self.ephemeral_mode:
            # Ephemeral mode: frameless, transparent, always on top
            self.setWindowFlags(
                QtCore.Qt.FramelessWindowHint |
                QtCore.Qt.WindowStaysOnTopHint |
                QtCore.Qt.Tool
            )
            self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        else:
            # Traditional dialog mode
            self.setWindowFlags(
                QtCore.Qt.Dialog |
                QtCore.Qt.WindowCloseButtonHint
            )

        self.setProperty("saveWindowPref", True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)  # Need strong focus for key events
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        self.lmb = True
        self.rmb = True
        self.mmb = False

        self.sample_x = None  # X position for sampling line

        self.margin = 20

        self.x1 = 200
        self.y1 = 200

        self.x2 = 200
        self.y2 = 200

        self.red  = QtGui.QColor(250, 0, 0  , 150)
        self.blue = QtGui.QColor(  0, 0, 255, 150)

        self.initUI()


    def initUI(self):
        if self.ephemeral_mode:
            # Ephemeral mode: larger size, centered on screen
            # Get Maya main window geometry to center on it
            maya_window = self.parent()
            if maya_window:
                maya_geom = maya_window.geometry()
                # Create a larger window (600x600) centered on Maya
                size = 600
                x = maya_geom.x() + (maya_geom.width() - size) / 2
                y = maya_geom.y() + (maya_geom.height() - size) / 2
                self.setGeometry(int(x), int(y), size, size)
            else:
                # Fallback if no parent
                self.setGeometry(300, 300, 600, 600)

            # Don't show immediately in ephemeral mode - wait for hotkey
            self.hide()

            if DEBUG:
                key_name = QtGui.QKeySequence(self.hotkey).toString()
                logger.info(f"Curve Profile Editor started in EPHEMERAL mode (hotkey: {key_name})")
        else:
            # Traditional mode: fixed size dialog
            self.setGeometry(300, 300, 400, 400)
            self.setFixedSize(400, 400)
            self.setWindowTitle('Bezier curve')
            self.show()

            if DEBUG:
                logger.info("Curve Profile Editor started with DEBUG mode enabled")


    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.setRenderHint(QtGui.QPainter.Antialiasing)

        # Get current widget dimensions
        width = self.geometry().width()
        height = self.geometry().height()

        # In ephemeral mode, draw a semi-transparent background overlay
        if self.ephemeral_mode:
            # Fill entire window with semi-transparent background
            qp.fillRect(self.rect(), QtGui.QColor(10, 25, 25, 100))

        self.drawRectangle(qp, self.margin, self.margin, width-(2*self.margin), height-(2*self.margin))

        if self.lmb:
            self.drawBezierCurve(qp, self.x1, self.margin, self.x2, height - self.margin)

            self.drawLine(qp, self.margin, self.margin, self.x1, self.margin)
            self.drawLine(qp, width - self.margin, height - self.margin, self.x2, height - self.margin)
            self.drawDots(qp, self.x1, self.margin, self.red)
            self.drawDots(qp, self.x2, height - self.margin, self.red)

        if self.rmb:
            self.drawBezierCurve(qp, self.margin, self.y1, width - self.margin, self.y2)

            self.drawLine(qp, self.margin, self.margin, self.margin, self.y1)
            self.drawLine(qp, width - self.margin, height - self.margin, width - self.margin, self.y2)
            self.drawDots(qp, self.margin, self.y1, self.blue)
            self.drawDots(qp, width - self.margin, self.y2, self.blue)

        # Debug mode: draw sampling line and value
        if DEBUG and self.sample_x is not None:
            self.drawSampleLine(qp, self.sample_x)

        qp.end()        


    def drawRectangle(self, qp, x, y, width, height):
        brush = QtGui.QBrush(QtGui.QColor(50, 50, 50))
        pen = QtGui.QPen()
        pen.setColor(QtGui.QColor(192, 192, 192))
        pen.setWidth(1)
        qp.setPen(pen)
        qp.setBrush(brush)
        qp.drawRect(x, y, width, height)
        qp.setBrush(QtCore.Qt.NoBrush)

    
    def drawDots(self, qp, x, y, color):
        pen = QtGui.QPen()
        pen.setColor(color)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        pen.setWidth(10)
        qp.setPen(pen)
        qp.drawPoint(x,y)


    def drawBezierCurve(self, qp, x1, y1, x2, y2):
        pen = QtGui.QPen()
        pen.setColor(QtGui.QColor(192, 192, 192))
        pen.setWidth(1)
        qp.setPen(pen)
        path = QtGui.QPainterPath()

        width = self.geometry().width()
        height = self.geometry().height()

        path.moveTo(self.margin, self.margin)
        path.cubicTo(x1, y1, x2, y2, width - self.margin, height - self.margin)
        qp.drawPath(path)


    def drawLine(self, qp, x0, y0, x1, y1):
        pen = QtGui.QPen()
        pen.setCapStyle(QtCore.Qt.RoundCap)
        pen.setStyle(QtCore.Qt.DotLine)
        pen.setColor(QtGui.QColor(192, 192, 192))
        pen.setWidth(2)
        qp.setPen(pen)

        path = QtGui.QPainterPath()
        path.moveTo(x0, y0)
        path.lineTo(x1, y1)
        qp.drawPath(path)

    def drawSampleLine(self, qp, x):
        """Draw a vertical sampling line and display the Y value at that X position"""
        width = self.geometry().width()
        height = self.geometry().height()

        # Clamp x to the drawable area
        x = max(self.margin, min(width - self.margin, x))

        # Draw vertical line
        pen = QtGui.QPen()
        pen.setColor(QtGui.QColor(0, 255, 0, 200))  # Green with some transparency
        pen.setWidth(2)
        qp.setPen(pen)

        path = QtGui.QPainterPath()
        path.moveTo(x, self.margin)
        path.lineTo(x, height - self.margin)
        qp.drawPath(path)

        # Sample the curve at this X position
        y_value = self.sample_curve_at_x(x, use_lmb=self.lmb)

        # Draw a dot at the sampled point
        pen.setColor(QtGui.QColor(0, 255, 0))
        pen.setCapStyle(QtCore.Qt.RoundCap)
        pen.setWidth(8)
        qp.setPen(pen)
        qp.drawPoint(int(x), int(y_value))

        # Get normalized value (0 to 1)
        time_norm = inv_lerp(self.margin, width - self.margin, x)
        amount_norm = self.sample_curve_normalized(time_norm, use_lmb=self.lmb)

        # Draw text label below the line
        pen.setColor(QtGui.QColor(255, 255, 255))
        pen.setWidth(1)
        qp.setPen(pen)

        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        qp.setFont(font)

        # Format the text
        text = "T: {:.3f} | V: {:.3f}".format(time_norm, amount_norm)

        # Calculate text position (below the drawable area)
        text_rect = qp.fontMetrics().boundingRect(text)
        text_x = x - text_rect.width() / 2
        text_y = height - self.margin + 15

        # Draw text background for better visibility
        bg_rect = QtCore.QRectF(text_x - 2, text_y - text_rect.height(),
                                 text_rect.width() + 4, text_rect.height() + 2)
        qp.fillRect(bg_rect, QtGui.QColor(0, 0, 0, 180))

        # Draw the text
        qp.drawText(int(text_x), int(text_y), text)
        
        
    def mouseMoveEvent(self, event):

        width = self.geometry().width()
        height = self.geometry().height()

        # Start doing math here to symmetrize the vertical
        # and do opposite the horizontal

        # Qt6 compatibility: use position() instead of pos()
        if hasattr(event, 'position'):
            pos = event.position().toPoint()  # Qt6
        else:
            pos = event.pos()  # Qt5

        pX = pos.x() / width
        pY = pos.y() / height

        percentageX = remap(0.0, 1.0, 0.0, 1.0, pX)
        percentageY = remap(0.0, 1.0, 0.0, 1.0, pY)

        x1Value = min(max(self.margin, pos.x()), width - self.margin)
        y1Value = min(max(self.margin, pos.y()), height - self.margin)

        x2Value = min(max(self.margin, width * (1.0 - percentageY)), width - self.margin)
        y2Value = min(max(self.margin, height * (1.0 - percentageX)), height - self.margin)

        # Debug mode: update sample position when middle mouse is held
        if DEBUG and self.mmb:
            self.sample_x = pos.x()
        elif not self.mmb:
            # Update control points when not sampling
            self.x1 = x1Value
            self.y1 = y1Value

            self.x2 = x2Value
            self.y2 = y2Value

        self.update() # Repaint


    def mousePressEvent(self, event):
        check  = QtWidgets.QApplication.instance().mouseButtons()
        self.lmb  = bool(QtCore.Qt.LeftButton & check)
        self.rmb  = bool(QtCore.Qt.RightButton & check)
        self.mmb  = bool(QtCore.Qt.MiddleButton & check)

        if DEBUG and self.mmb:
            logger.debug("Started curve sampling with middle mouse button")

        super(Example, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        check  = QtWidgets.QApplication.instance().mouseButtons()
        self.lmb  = bool(QtCore.Qt.LeftButton & check)
        self.rmb  = bool(QtCore.Qt.RightButton & check)
        self.mmb  = bool(QtCore.Qt.MiddleButton & check)
        super(Example, self).mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        """Handle key press events for ephemeral mode hotkey"""
        if self.ephemeral_mode:
            if event.key() == self.hotkey and not event.isAutoRepeat():
                self.hotkey_pressed = True
                self.show()
                self.raise_()
                self.activateWindow()
                if DEBUG:
                    logger.debug("Hotkey pressed - showing curve editor")
        super(Example, self).keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """Handle key release events for ephemeral mode hotkey"""
        if self.ephemeral_mode:
            if event.key() == self.hotkey and not event.isAutoRepeat():
                self.hotkey_pressed = False
                self.hide()
                if DEBUG:
                    logger.debug("Hotkey released - hiding curve editor")
        super(Example, self).keyReleaseEvent(event)

    def find_t_for_x(self, target_x, p0_x, p1_x, p2_x, p3_x, tolerance=0.0001, max_iterations=10):
        """
        Find the parameter t that produces the target_x coordinate on the Bezier curve.
        Uses Newton-Raphson iteration for fast convergence.

        Args:
            target_x: The X coordinate to find
            p0_x, p1_x, p2_x, p3_x: The X coordinates of the Bezier control points
            tolerance: Acceptable error (default 0.0001)
            max_iterations: Maximum number of iterations (default 10)

        Returns:
            t value (0 to 1) that produces target_x
        """
        # Start with a reasonable initial guess
        t = (target_x - p0_x) / (p3_x - p0_x) if p3_x != p0_x else 0.5
        t = max(0.0, min(1.0, t))  # Clamp to valid range

        for _ in range(max_iterations):
            # Evaluate current X position
            current_x = cubic_bezier(p0_x, p1_x, p2_x, p3_x, t)

            # Check if we're close enough
            if abs(current_x - target_x) < tolerance:
                return t

            # Get derivative (slope) at current t
            dx_dt = cubic_bezier_derivative(p0_x, p1_x, p2_x, p3_x, t)

            # Avoid division by zero
            if abs(dx_dt) < 1e-6:
                break

            # Newton-Raphson step: t_new = t - f(t)/f'(t)
            t = t - (current_x - target_x) / dx_dt

            # Clamp t to valid range [0, 1]
            t = max(0.0, min(1.0, t))

        return t

    def sample_curve_at_x(self, x_value, use_lmb=True):
        """
        Sample the Bezier curve at a specific X coordinate to get the Y value.

        Args:
            x_value: The X coordinate to sample (in widget coordinates)
            use_lmb: If True, use the horizontal curve (red), otherwise use vertical curve (blue)

        Returns:
            y_value: The Y coordinate at the given X (in widget coordinates)
        """
        width = self.geometry().width()
        height = self.geometry().height()

        if use_lmb:
            # Horizontal curve: x varies, y is locked at top and bottom
            p0_x, p0_y = self.margin, self.margin
            p1_x, p1_y = self.x1, self.margin
            p2_x, p2_y = self.x2, height - self.margin
            p3_x, p3_y = width - self.margin, height - self.margin
        else:
            # Vertical curve: y varies, x is locked at left and right
            p0_x, p0_y = self.margin, self.margin
            p1_x, p1_y = self.margin, self.y1
            p2_x, p2_y = width - self.margin, self.y2
            p3_x, p3_y = width - self.margin, height - self.margin

        # Find the t parameter for the given x coordinate
        t = self.find_t_for_x(x_value, p0_x, p1_x, p2_x, p3_x)

        # Evaluate the y coordinate at that t
        y_value = cubic_bezier(p0_y, p1_y, p2_y, p3_y, t)

        return y_value

    def sample_curve_normalized(self, time_normalized, use_lmb=True):
        """
        Sample the curve using normalized coordinates (0 to 1).
        Perfect for animation systems!

        Args:
            time_normalized: Time value from 0.0 to 1.0
            use_lmb: If True, use the horizontal curve (red), otherwise use vertical curve (blue)

        Returns:
            amount_normalized: Amount value from 0.0 to 1.0
        """
        width = self.geometry().width()
        height = self.geometry().height()

        # Convert normalized time (0-1) to widget X coordinate
        x_value = lerp(self.margin, width - self.margin, time_normalized)

        # Sample the curve
        y_value = self.sample_curve_at_x(x_value, use_lmb)

        # Convert widget Y coordinate back to normalized amount (0-1)
        # Note: Y axis is inverted in screen coordinates (0 is top)
        amount_normalized = inv_lerp(self.margin, height - self.margin, y_value)

        # Invert because screen Y increases downward
        amount_normalized = 1.0 - amount_normalized

        return amount_normalized

    def get_curve_values(self, use_lmb=True):
        """
        Get the current control point values in normalized form (0 to 1).
        Useful for saving/loading curve presets.

        Args:
            use_lmb: If True, get horizontal curve values, otherwise vertical curve

        Returns:
            Dictionary with normalized control point coordinates
        """
        width = self.geometry().width()
        height = self.geometry().height()

        if use_lmb:
            return {
                'p0': (0.0, 0.0),
                'p1': (inv_lerp(self.margin, width - self.margin, self.x1), 0.0),
                'p2': (inv_lerp(self.margin, width - self.margin, self.x2), 1.0),
                'p3': (1.0, 1.0)
            }
        else:
            return {
                'p0': (0.0, 0.0),
                'p1': (0.0, inv_lerp(self.margin, height - self.margin, self.y1)),
                'p2': (1.0, inv_lerp(self.margin, height - self.margin, self.y2)),
                'p3': (1.0, 1.0)
            }


# Global state for ephemeral mode
_EPHEMERAL_UI = None
_EPHEMERAL_FILTER = None


def activate_ephemeral_mode(hotkey=QtCore.Qt.Key_Shift):
    """
    Activate the ephemeral curve editor mode.

    Args:
        hotkey: The Qt key constant to use as the hotkey (default: Shift key)
                Examples: QtCore.Qt.Key_Shift, QtCore.Qt.Key_Control, QtCore.Qt.Key_Alt

    Usage:
        import curveProfileEditor
        curveProfileEditor.activate_ephemeral_mode(QtCore.Qt.Key_Shift)

        # Now hold Shift to show the curve editor, release to hide
    """
    global _EPHEMERAL_UI, _EPHEMERAL_FILTER

    # Clean up any existing instance
    deactivate_ephemeral_mode()

    # Create the curve editor in ephemeral mode
    _EPHEMERAL_UI = Example(ephemeral_mode=True, hotkey=hotkey)

    # Install global event filter to detect hotkey
    _EPHEMERAL_FILTER = EphemeralHotkeyFilter(_EPHEMERAL_UI, hotkey)
    QtWidgets.QApplication.instance().installEventFilter(_EPHEMERAL_FILTER)

    key_name = QtGui.QKeySequence(hotkey).toString()
    logger.info(f"Ephemeral curve editor activated. Hold '{key_name}' to show, release to hide.")


def deactivate_ephemeral_mode():
    """
    Deactivate and clean up the ephemeral curve editor.

    Usage:
        import curveProfileEditor
        curveProfileEditor.deactivate_ephemeral_mode()
    """
    global _EPHEMERAL_UI, _EPHEMERAL_FILTER

    # Remove event filter
    if _EPHEMERAL_FILTER is not None:
        QtWidgets.QApplication.instance().removeEventFilter(_EPHEMERAL_FILTER)
        _EPHEMERAL_FILTER = None

    # Close and clean up UI
    if _EPHEMERAL_UI is not None:
        try:
            _EPHEMERAL_UI.close()
            _EPHEMERAL_UI.deleteLater()
        except:
            pass
        _EPHEMERAL_UI = None

    logger.info("Ephemeral curve editor deactivated.")


def main():
    """
    Create the curve editor in traditional dialog mode.

    Usage:
        import curveProfileEditor
        curveProfileEditor.main()
    """
    global _UI
    try:
        _UI.close()
        _UI.deleteLater()
        _UI = None
    except:
        pass
    finally:
        _UI = Example(ephemeral_mode=False)


# ============================================================================
# USAGE EXAMPLES
# ============================================================================
#
# TWO MODES OF OPERATION:
# -----------------------
#
# 1. TRADITIONAL DIALOG MODE (main):
#    - Creates a standard dialog window
#    - Stays visible until manually closed
#    - Good for detailed curve editing
#
# 2. EPHEMERAL MODE (activate_ephemeral_mode):
#    - Frameless, semi-transparent overlay
#    - Appears when hotkey is held down
#    - Disappears when hotkey is released
#    - Perfect for quick adjustments in your workflow
#
# ============================================================================
#
# EPHEMERAL MODE - Quick access curve editor
# -------------------------------------------
# import curveProfileEditor
# from Qt import QtCore
#
# # Activate ephemeral mode with Shift key
# curveProfileEditor.activate_ephemeral_mode(QtCore.Qt.Key_Shift)
#
# # Now:
# # - Hold Shift to show the curve editor
# # - Drag to adjust the curve
# # - Release Shift to hide the editor
#
# # Try different hotkeys:
# curveProfileEditor.activate_ephemeral_mode(QtCore.Qt.Key_Control)  # Use Ctrl
# curveProfileEditor.activate_ephemeral_mode(QtCore.Qt.Key_Alt)      # Use Alt
#
# # Deactivate when done:
# curveProfileEditor.deactivate_ephemeral_mode()
#
# # Access the curve values even when hidden:
# if curveProfileEditor._EPHEMERAL_UI:
#     value = curveProfileEditor._EPHEMERAL_UI.sample_curve_normalized(0.5)
#
# ============================================================================
#
# TRADITIONAL MODE - Standard dialog
# -----------------------------------
# import curveProfileEditor
# curveProfileEditor.main()
#
# # After creating the UI with main(), you can sample the curve like this:
#
# Example 1: Sample at normalized time (most common for animation)
# ------------------------------------------------------------------
# time = 0.5  # 50% through the animation
# amount = curveProfileEditor._UI.sample_curve_normalized(time, use_lmb=True)
# print("At time {}, amount is {}".format(time, amount))
#
# Example 2: Sample multiple points to create an animation curve
# ---------------------------------------------------------------
# samples = []
# for i in range(11):
#     time = i / 10.0  # 0.0, 0.1, 0.2, ... 1.0
#     amount = curveProfileEditor._UI.sample_curve_normalized(time, use_lmb=True)
#     samples.append((time, amount))
# print("Curve samples:", samples)
#
# Example 3: Get the control point values for saving/loading
# -----------------------------------------------------------
# curve_data = curveProfileEditor._UI.get_curve_values(use_lmb=True)
# print("Control points:", curve_data)
# # Output: {'p0': (0.0, 0.0), 'p1': (x1, 0.0), 'p2': (x2, 1.0), 'p3': (1.0, 1.0)}
#
# Example 4: Use with Maya animation
# -----------------------------------
# import maya.cmds as cmds
# # Sample the curve at different frames
# start_frame = 1
# end_frame = 100
# for frame in range(start_frame, end_frame + 1):
#     time = (frame - start_frame) / float(end_frame - start_frame)
#     value = curveProfileEditor._UI.sample_curve_normalized(time, use_lmb=True)
#     # Apply to an attribute
#     cmds.setKeyframe('pSphere1.translateY', time=frame, value=value * 10)
#
# ============================================================================


if __name__ == '__main__':
    main()
