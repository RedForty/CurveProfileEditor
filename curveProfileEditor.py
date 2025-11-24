#!/usr/bin/python

"""
Quick Bezier profile editor

...Sorta

"""

from __future__ import division # Need to get floats when dividing intergers
from Qt import QtWidgets, QtGui, QtCore, QtCompat
import maya.OpenMayaUI as mui

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

class Example(QtWidgets.QDialog):

    def __init__(self):
        super(Example, self).__init__()
        
        self.setParent(_get_maya_window())
        self.setWindowFlags(
            QtCore.Qt.Dialog |
            QtCore.Qt.WindowCloseButtonHint
        )

        self.setProperty("saveWindowPref", True)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        
        self.lmb = True
        self.rmb = True
        
        self.margin = 20
        
        self.x1 = 200
        self.y1 = 200
        
        self.x2 = 200
        self.y2 = 200
        
        self.red  = QtGui.QColor(250, 0, 0  , 150)
        self.blue = QtGui.QColor(  0, 0, 255, 150)
        
        self.initUI()


    def initUI(self):
        self.setGeometry(300, 300, 400, 400)
        self.setFixedSize(400, 400)
        self.setWindowTitle('Bezier curve')
        self.show()


    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.setRenderHint(QtGui.QPainter.Antialiasing)
        
        self.drawRectangle(qp, self.margin, self.margin, self.geometry().width()-(2*self.margin), self.geometry().height()-(2*self.margin))
        
        if self.lmb:
            self.drawBezierCurve(qp, self.x1, self.margin, self.x2, 400 - self.margin)
            
            self.drawLine(qp, self.margin, self.margin, self.x1, self.margin)
            self.drawLine(qp, 400 - self.margin, 400 - self.margin, self.x2, 400 - self.margin)
            self.drawDots(qp, self.x1, self.margin, self.red)
            self.drawDots(qp, self.x2, 400 - self.margin, self.red)
        
        if self.rmb:
            self.drawBezierCurve(qp, self.margin, self.y1, 400 - self.margin, self.y2)
            
            self.drawLine(qp, self.margin, self.margin, self.margin, self.y1)
            self.drawLine(qp, 400 - self.margin, 400 - self.margin, 400 - self.margin, self.y2)
            self.drawDots(qp, self.margin, self.y1, self.blue)
            self.drawDots(qp, 400 - self.margin, self.y2, self.blue)
        
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
        path.moveTo(self.margin, self.margin)
        path.cubicTo(x1, y1, x2, y2, 400 - (self.margin), 400 - (self.margin))
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
        
        
    def mouseMoveEvent(self, pos):
        
        width = self.geometry().width()
        height = self.geometry().height()
        
        # Start doing math here to symmetrize the vertical
        # and do opposite the horizontal
        
        pX = pos.x() / width 
        pY = pos.y() / height
        
        percentageX = remap(0.0, 1.0, 0.0, 1.0, pX)
        percentageY = remap(0.0, 1.0, 0.0, 1.0, pY)
        
        x1Value = min(max(self.margin, pos.x()), 400 - self.margin)
        y1Value = min(max(self.margin, pos.y()), 400 - self.margin)
        
        x2Value = min(max(self.margin, 400 * (1.0 - percentageY)), 400 - self.margin)
        y2Value = min(max(self.margin, 400 * (1.0 - percentageX)), 400 - self.margin)

        self.x1 = x1Value
        self.y1 = y1Value
        
        self.x2 = x2Value 
        self.y2 = y2Value
            
        self.update() # Repaint


    def mousePressEvent(self, event):
        check  = QtWidgets.QApplication.instance().mouseButtons()
        self.lmb  = bool(QtCore.Qt.LeftButton & check)
        self.rmb  = bool(QtCore.Qt.RightButton & check)
        
        super(Example, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        check  = QtWidgets.QApplication.instance().mouseButtons()
        self.lmb  = bool(QtCore.Qt.LeftButton & check)
        self.rmb  = bool(QtCore.Qt.RightButton & check)
        super(Example, self).mouseReleaseEvent(event)

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
        if use_lmb:
            # Horizontal curve: x varies, y is locked at top and bottom
            p0_x, p0_y = self.margin, self.margin
            p1_x, p1_y = self.x1, self.margin
            p2_x, p2_y = self.x2, 400 - self.margin
            p3_x, p3_y = 400 - self.margin, 400 - self.margin
        else:
            # Vertical curve: y varies, x is locked at left and right
            p0_x, p0_y = self.margin, self.margin
            p1_x, p1_y = self.margin, self.y1
            p2_x, p2_y = 400 - self.margin, self.y2
            p3_x, p3_y = 400 - self.margin, 400 - self.margin

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
        # Convert normalized time (0-1) to widget X coordinate
        x_value = lerp(self.margin, 400 - self.margin, time_normalized)

        # Sample the curve
        y_value = self.sample_curve_at_x(x_value, use_lmb)

        # Convert widget Y coordinate back to normalized amount (0-1)
        # Note: Y axis is inverted in screen coordinates (0 is top)
        amount_normalized = inv_lerp(self.margin, 400 - self.margin, y_value)

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
        if use_lmb:
            return {
                'p0': (0.0, 0.0),
                'p1': (inv_lerp(self.margin, 400 - self.margin, self.x1), 0.0),
                'p2': (inv_lerp(self.margin, 400 - self.margin, self.x2), 1.0),
                'p3': (1.0, 1.0)
            }
        else:
            return {
                'p0': (0.0, 0.0),
                'p1': (0.0, inv_lerp(self.margin, 400 - self.margin, self.y1)),
                'p2': (1.0, inv_lerp(self.margin, 400 - self.margin, self.y2)),
                'p3': (1.0, 1.0)
            }


def main():
    global _UI
    try:
        _UI.close()
        _UI.deleteLater()
        _UI = None
    except:
        pass
    finally:
        _UI = Example()


# ============================================================================
# USAGE EXAMPLES
# ============================================================================
#
# After creating the UI with main(), you can sample the curve like this:
#
# Example 1: Sample at normalized time (most common for animation)
# ------------------------------------------------------------------
# time = 0.5  # 50% through the animation
# amount = _UI.sample_curve_normalized(time, use_lmb=True)
# print("At time {}, amount is {}".format(time, amount))
#
# Example 2: Sample multiple points to create an animation curve
# ---------------------------------------------------------------
# samples = []
# for i in range(11):
#     time = i / 10.0  # 0.0, 0.1, 0.2, ... 1.0
#     amount = _UI.sample_curve_normalized(time, use_lmb=True)
#     samples.append((time, amount))
# print("Curve samples:", samples)
#
# Example 3: Get the control point values for saving/loading
# -----------------------------------------------------------
# curve_data = _UI.get_curve_values(use_lmb=True)
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
#     value = _UI.sample_curve_normalized(time, use_lmb=True)
#     # Apply to an attribute
#     cmds.setKeyframe('pSphere1.translateY', time=frame, value=value * 10)
#
# ============================================================================


if __name__ == '__main__':
    main()
