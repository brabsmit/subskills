import sys

from PyQt5.Qt import Qt
from PyQt5.QtGui import QPen, QBrush, QFont
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsItem, \
    QGraphicsEllipseItem, QDialog, QFormLayout, QDialogButtonBox, QLineEdit, QLabel
from PyQt5.QtCore import QRectF
from numpy import sqrt, arctan2, degrees, sin, cos, radians


# TODO: background
# TODO: target class

class Coordinate:

    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon


def range_to_target(ownship, target):
    # sqrt((os_x - tgt_x)^2 + (os_y - tgt_y)^2)

    os_x = abs(ownship.coord.lat)
    os_y = abs(ownship.coord.lon)

    tgt_x = abs(target.coord.lat)
    tgt_y = abs(target.coord.lon)

    return int(10 * sqrt((os_x - tgt_x) ** 2 + (os_y - tgt_y) ** 2))


def bearing_to_target(ownship, target):
    # normalize coordinates to ownship
    offset_x = target.coord.lat
    offset_y = target.coord.lon

    os_normal = Coordinate(ownship.coord.lat-offset_x, ownship.coord.lon-offset_y)
    phi = arctan2(os_normal.lat, os_normal.lon)
    bearing = degrees(phi)

    if bearing <= 0:
        return round(abs(bearing), 0)
    else:
        return round(360 - bearing, 0)


def cart_to_polar(lat, lon):
    rho = sqrt(lat**2 + lon**2)
    phi = arctan2(lon, lat)
    return rho, phi


def polar_to_cart(rho, phi):
    lon = rho/10 * cos(radians(phi))
    lat = rho/10 * sin(radians(phi))
    return round(lat,1), round(lon,1)


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
        self.coord = Coordinate(0, 0)

    def set_solution(self, solution):
        self.solution = solution

    def __str__(self):
        return "<Ownship> {0} ({1}, {2})".format(self.solution, self.coord.lat, self.coord.lon)


class Warship:

    def __init__(self, ship_type, desig):
        self.ship_type = ship_type
        self.desig = desig
        self.coord = Coordinate(0, 0)

    def set_solution(self, solution):
        self.solution = solution

    def get_solution(self, bearing, rng, course, speed):
        # special function that calculates bearing and range based on x,y pos of warship
        return self.solution

    def __str__(self):
        return "<Warship {0}> {1} ({2}, {3})".format(self.desig, self.solution, self.coord.lat, self.coord.lon)


class TargetDetailWindow(QDialog):

    def __init__(self, warship):
        super().__init__()
        self.warship = warship

        try:
            self.setWindowTitle("Warship {0} Details".format(self.warship.desig))
        except(BaseException):
            self.setWindowTitle("Ownship Details")

        self.bearing = QLineEdit(self)
        self.rng = QLineEdit(self)
        self.course = QLineEdit(self)
        self.speed = QLineEdit(self)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)

        self.bearing.setText(str(self.warship.solution.bearing))
        self.rng.setText(str(self.warship.solution.rng))
        self.course.setText(str(self.warship.solution.course))
        self.speed.setText(str(self.warship.solution.speed))

        layout = QFormLayout(self)
        layout.addRow("Bearing", self.bearing)
        layout.addRow("Range", self.rng)
        layout.addRow("Course", self.course)
        layout.addRow("Speed", self.speed)
        layout.addWidget(button_box)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

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

            # now calculate the ellipse movement
            # get coordinates based on bearing and range
            (lat, lon) = polar_to_cart(self.warship.solution.rng, self.warship.solution.bearing)
            self.warship.coord.lat = lat
            self.warship.coord.lon = lon

            global_pos = event.scenePos()

            dx = self.warship.coord.lat - global_pos.x()
            dy = self.warship.coord.lon - global_pos.y()

            self.moveBy(dx, dy)

        print(self.warship)

    def mouseReleaseEvent(self, event):
        super(ShipEllipse, self).mouseReleaseEvent(event)
        pass

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            global_pos = event.scenePos()

            self.warship.coord.lat = global_pos.x()
            self.warship.coord.lon = global_pos.y()

            super(ShipEllipse, self).mouseMoveEvent(event)

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
 
        self.init_window()
 
    def init_window(self):
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
        self.ownship.coord.lat = 0
        self.ownship.coord.lon = 0
        ownship_ellipse.bind_warship(self.ownship)
        ownship_ellipse.bind_ownship(self.ownship)
        ownship_ellipse.setPen(self.whitePen)
        ownship_ellipse.setBrush(self.cyanBrush)
        self.scene.addItem(ownship_ellipse)

        warship1_ellipse = ShipEllipse(-200, -900, 50, 50)
        self.warship1.coord.lat = -200
        self.warship1.coord.lon = -900
        solution = Solution(bearing_to_target(self.ownship, self.warship1),
                            range_to_target(self.ownship, self.warship1),
                            0, 0)
        self.warship1.set_solution(solution)
        warship1_ellipse.bind_warship(self.warship1)
        warship1_ellipse.bind_ownship(self.ownship)
        warship1_ellipse.setPen(self.whitePen)
        warship1_ellipse.setBrush(self.blueBrush)
        self.scene.addItem(warship1_ellipse)

        warship1_label = QLabel(str(self.warship1.solution.rng))
        warship1_label.setAutoFillBackground(False)
        warship1_label.setStyleSheet('background-color: transparent')
        warship1_label.setFont(self.font)

        warship2_ellipse = ShipEllipse(200, -900, 50, 50)
        self.warship2.coord.lat = 200
        self.warship2.coord.lon = -900
        solution = Solution(bearing_to_target(self.ownship, self.warship2),
                            range_to_target(self.ownship, self.warship2),
                            0, 0)
        self.warship2.set_solution(solution)
        warship2_ellipse.bind_warship(self.warship2)
        warship2_ellipse.bind_ownship(self.ownship)
        warship2_ellipse.setPen(self.whitePen)
        warship2_ellipse.setBrush(self.redBrush)
        self.scene.addItem(warship2_ellipse)

        warship2_label = QLabel(str(self.warship2.solution.rng))
        warship2_label.setAutoFillBackground(False)
        warship2_label.setStyleSheet('background-color: transparent')
        warship2_label.setFont(self.font)

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