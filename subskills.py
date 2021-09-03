import math
import sys

from PyQt5.Qt import Qt
from PyQt5.QtGui import QPen, QBrush, QFont
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsItem, \
    QGraphicsEllipseItem, QDialog, QFormLayout, QDialogButtonBox, QLineEdit, QLabel
from numpy import degrees, arcsin


# TODO: background
# Testing pycharm github integrations

def range_to_target(ownship, target):
    # sqrt((os_x - tgt_x)^2 + (os_y - tgt_y)^2)

    os_x = abs(ownship.x)
    os_y = abs(ownship.y)

    tgt_x = abs(target.x)
    tgt_y = abs(target.y)

    return int(10* math.sqrt((os_x - tgt_x) ** 2 + (os_y - tgt_y) ** 2))


def bearing_to_target(ownship, target):
    print(ownship)
    print(target)
    os_x = abs(ownship.x)
    os_y = abs(ownship.y)

    tgt_x = abs(target.x)
    tgt_y = abs(target.y)

    if os_y-tgt_y == 0 or os_x-tgt_x == 0: return None

    try:
        bearing = arcsin((os_y-tgt_y)/(os_x-tgt_x))
    except:
        bearing = 0

    return round(90-abs(degrees(bearing)),0)


class Solution:

    def __init__(self, bearing, rng, course, speed):
        self.bearing = bearing
        self.rng = rng
        self.course = course
        self.speed = speed

    def __str__(self):
        return "B-{0}T, R-{1}yds, C-{2}T, S-{3}kts".format(self.bearing, self.rng, self.course, self.speed)


class Ownship:

    def __init__(self):
        self.x = 0
        self.y = 0

    def set_solution(self, solution):
        self.solution = solution

    def __str__(self):
        return "<Ownship> {0} ({1}, {2})".format(self.solution, self.x, self.y)


class Warship:

    def __init__(self, ship_type, desig):
        self.ship_type = ship_type
        self.desig = desig
        self.x = 0
        self.y = 0

    def set_solution(self, solution):
        self.solution = solution

    def get_solution(self, bearing, rng, course, speed):
        # special function that calculates bearing and range based on x,y pos of warship
        return self.solution

    def __str__(self):
        return "<Warship {0}> {1} ({2}, {3})".format(self.desig, self.solution, self.x, self.y)


class TargetDetailWindow(QDialog):

    def __init__(self, warship):
        super().__init__()
        self.warship = warship

        self.bearing = QLineEdit(self)
        self.rng = QLineEdit(self)
        self.course = QLineEdit(self)
        self.speed = QLineEdit(self)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)

        self.bearing.setText(str(self.warship.solution.bearing))
        self.rng.setText(str(self.warship.solution.rng))
        self.course.setText(str(self.warship.solution.course))
        self.speed.setText(str(self.warship.solution.speed))

        layout = QFormLayout(self)
        layout.addRow("Bearing", self.bearing)
        layout.addRow("Range", self.rng)
        layout.addRow("Course", self.course)
        layout.addRow("Speed", self.speed)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def get_inputs(self):
        solution = Solution(float(self.bearing.text()), float(self.rng.text()), float(self.course.text()), float(self.speed.text()))
        return solution


class ShipEllipse(QGraphicsEllipseItem):

    def __init__(self, *args, **kwargs):
        super(ShipEllipse, self).__init__(*args, **kwargs)

    def mouseDoubleClickEvent(self, event):
        self.w = TargetDetailWindow(self.warship)
        self.w.show()
        if self.w.exec():
            solution = self.w.get_inputs()
            self.warship.set_solution(solution)

    def mouseReleaseEvent(self, event):
        super(ShipEllipse, self).mouseReleaseEvent(event)
        pass

    def mouseMoveEvent(self, event):
        super(ShipEllipse, self).mouseMoveEvent(event)
        self.warship.x = self.pos().x()
        self.warship.y = self.pos().y()
        self.warship.solution.rng = range_to_target(self.ownship, self.warship)
        self.warship.solution.bearing = bearing_to_target(self.ownship, self.warship)
        print(self.warship)

    def bind_warship(self, warship):
        self.warship = warship

    def bind_ownship(self, ownship):
        self.ownship = ownship


class Window(QMainWindow):

    def __init__(self):
        super().__init__()
 
        self.title = "SubSkills"
        self.top = 0
        self.left = 0
        self.width = 1800
        self.height = 1800
        self.ownship = Ownship()
        self.warship1 = Warship(None, "A")
        self.warship2 = Warship(None, "B")

        self.ownship.set_solution(Solution(0, 0, 0, 3.5))
        self.warship1.set_solution(Solution(0, 0, 0, 0))
        self.warship2.set_solution(Solution(0, 0, 0, 0))
 
        self.InitWindow()
 
    def InitWindow(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
 
        self.createGraphicView()
 
        self.show()
 
    def createGraphicView(self):
        self.scene = QGraphicsScene()
        self.blueBrush = QBrush(Qt.blue)
        self.redBrush = QBrush(Qt.red)
        self.cyanBrush = QBrush(Qt.cyan)
 
        self.whitePen = QPen(Qt.white)

        self.font = QFont('Times', 8)
        self.font.setBold(True)
 
        graphicView = QGraphicsView(self.scene, self)
        graphicView.setGeometry(0,0,1800,1800)
 
        self.shapes()
 
    def shapes(self):
        ownship_ellipse = ShipEllipse(0, 0, 50, 50)
        self.ownship.x = 0
        self.ownship.y = 0
        ownship_ellipse.bind_warship(self.ownship)
        ownship_ellipse.bind_ownship(self.ownship)
        ownship_ellipse.setPen(self.whitePen)
        ownship_ellipse.setBrush(self.cyanBrush)
        self.scene.addItem(ownship_ellipse)

        warship1_ellipse = ShipEllipse(-200,-900, 50, 50)
        self.warship1.x = -200
        self.warship1.y = -900
        warship1_ellipse.bind_warship(self.warship1)
        warship1_ellipse.bind_ownship(self.ownship)
        warship1_ellipse.setPen(self.whitePen)
        warship1_ellipse.setBrush(self.blueBrush)
        self.scene.addItem(warship1_ellipse)

        warship1_label = QLabel(str(self.warship1.solution.rng))
        warship1_label.setAutoFillBackground(False)
        warship1_label.setStyleSheet('background-color: transparent')
        warship1_label.setFont(self.font)

        warship2_ellipse = ShipEllipse(200,-900, 50, 50)
        self.warship2.x = 200
        self.warship2.y = -900
        warship2_ellipse.bind_warship(self.warship2)
        warship2_ellipse.bind_ownship(self.ownship)
        warship2_ellipse.setPen(self.whitePen)
        warship2_ellipse.setBrush(self.redBrush)
        self.scene.addItem(warship2_ellipse)

        warship2_label = QLabel(str(self.warship2.solution.rng))
        warship2_label.setAutoFillBackground(False)
        warship2_label.setStyleSheet('background-color: transparent')
        warship2_label.setFont(self.font)

        ownship_ellipse.setFlag(QGraphicsItem.ItemIsSelectable)

        warship1_ellipse.setFlag(QGraphicsItem.ItemIsMovable)
        warship1_ellipse.setFlag(QGraphicsItem.ItemIsSelectable)

        warship2_ellipse.setFlag(QGraphicsItem.ItemIsMovable)
        warship2_ellipse.setFlag(QGraphicsItem.ItemIsSelectable)


def main():
    App = QApplication(sys.argv)
    window = Window()
    sys.exit(App.exec())


if __name__ == "__main__":
    main()