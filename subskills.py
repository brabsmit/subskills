import sys

from PyQt5.Qt import Qt
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPen, QBrush, QFont, QPolygonF
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsItem, \
    QGraphicsEllipseItem, QDialog, QFormLayout, QDialogButtonBox, QLineEdit, QGraphicsLineItem
from numpy import sqrt, arctan2, degrees, sin, cos, radians


# TODO: background
# TODO: target class


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

    os_normal = Coordinate(ownship.coord.lat - offset_x, ownship.coord.lon - offset_y)
    phi = arctan2(os_normal.lat, os_normal.lon)
    bearing = degrees(phi)

    if bearing <= 0:
        return round(abs(bearing), 0)
    else:
        return round(360 - bearing, 0)


def bearing_and_range_to_coord(ownship, target):
    # accepts the user input solution and transforms target to specified coordinate
    offset_x = ownship.coord.lat
    offset_y = ownship.coord.lon

    os_normal = Coordinate(ownship.coord.lat - offset_x, ownship.coord.lon - offset_y)

    rho = target.solution.rng
    phi = (180 - target.solution.bearing) % 360  # because I don't know how else to do it

    lon = rho / 10 * cos(radians(phi))
    lat = rho / 10 * sin(radians(phi))

    lat_centered = lat + os_normal.lat
    lon_centered = lon + os_normal.lon

    return round(lat_centered, 1), round(lon_centered, 1)


def target_course_and_speed_to_coord(target):
    phi = (target.solution.course - 90) % 360
    rho = target.solution.speed * 333

    x_offset = rho / 10 * cos(radians(phi))
    y_offset = rho / 10 * sin(radians(phi))

    lat = x_offset + target.coord.lat
    lon = y_offset + target.coord.lon

    return round(lat, 1), round(lon, 1)


def course_vector_to_coord(course_vector):
    phi = (course_vector.course - 90) % 360
    rho = course_vector.speed * course_vector.duration * (1/3) * 100

    x_offset = rho / 10 * cos(radians(phi))
    y_offset = rho / 10 * sin(radians(phi))

    return round(x_offset, 1), round(y_offset, 1)


def cart_to_polar(lat, lon):
    rho = sqrt(lat ** 2 + lon ** 2)
    phi = arctan2(lon, lat)
    return rho, phi


def polar_to_cart(rho, phi):
    lon = rho / 10 * cos(radians(phi))
    lat = rho / 10 * sin(radians(phi))
    return round(lat, 1), round(lon, 1)


class Coordinate:

    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon


class CourseVector:

    def __init__(self, course, speed, duration):
        self.course = course
        self.speed = speed
        self.duration = duration
        self.start_coord = Coordinate(0, 0)

        (lat, lon) = course_vector_to_coord(self)
        self.end_coord = Coordinate(lat, lon)

    def set_line(self, parent):
        self.start_coord = Coordinate(parent.coord.lat, parent.coord.lon)
        self.end_coord = Coordinate(self.end_coord.lat + parent.coord.lat, self.end_coord.lon + parent.coord.lon)

    def __str__(self):
        return "C-{0}, S-{1}, D-{2} ({3}, {4}) -> ({5}, {6})".format(self.course, self.speed, self.duration,
                                                                     self.start_coord.lat, self.start_coord.lon,
                                                                     self.end_coord.lat, self.end_coord.lon)


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
        self.solution = Solution(0, 0, 0, 0)
        self.course_vector = CourseVector(0, 0, 0)

    def set_solution(self, solution):
        self.solution = solution
        self.course_vector = CourseVector(self.solution.course, self.solution.speed, 10)

    def __str__(self):
        return "<Ownship> {0} ({1}, {2})".format(self.solution, self.coord.lat, self.coord.lon)

    def tooltip(self):
        return "Ownship \nCourse:\t{0}\nSpeed:\t{1}".format(self.solution.course, self.solution.speed)


class Warship:

    def __init__(self, ship_type, desig):
        self.ship_type = ship_type
        self.desig = desig
        self.coord = Coordinate(0, 0)
        self.solution = Solution(0, 0, 0, 0)
        self.course_vector = CourseVector(0, 0, 0)

    def set_solution(self, solution):
        self.solution = solution
        self.course_vector = CourseVector(self.solution.course, self.solution.speed, 10)

    def get_solution(self, bearing, rng, course, speed):
        # special function that calculates bearing and range based on x,y pos of warship
        return self.solution

    def __str__(self):
        return "<Warship {0}> {1} ({2}, {3})".format(self.desig, self.solution, self.coord.lat, self.coord.lon)

    def tooltip(self):
        return "Warship {0}\nBearing:\t{1}\nRange:\t{2}\nCourse:\t{3}\nSpeed:\t{4}".format(self.desig,
                                                                                           self.solution.bearing,
                                                                                           self.solution.rng,
                                                                                           self.solution.course,
                                                                                           self.solution.speed)


class BuilderArrow(QGraphicsLineItem):

    def __init__(self, course_vector):
        super().__init__()
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setPen(QPen(Qt.black))
        self.arrow_head = QPolygonF()
        self.start_coord = QPointF(course_vector.start_coord.lat, course_vector.start_coord.lon)
        self.end_coord = QPointF(course_vector.end_coord.lat, course_vector.end_coord.lon)

        self.setLine(self.start_coord.x(), self.start_coord.y(), self.end_coord.x(), self.end_coord.y())


class TargetDetailWindow(QDialog):

    def __init__(self, warship):
        super().__init__()
        self.warship = warship

        try:
            self.setWindowTitle("Warship {0} Details".format(self.warship.desig))
        except BaseException:
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
        solution = Solution(float(self.bearing.text()), float(self.rng.text()), float(self.course.text()),
                            float(self.speed.text()))
        return solution


class ShipEllipse(QGraphicsEllipseItem):

    def __init__(self, *args, **kwargs):
        super(ShipEllipse, self).__init__(*args, **kwargs)
        self.course_lines = []

    def mouseDoubleClickEvent(self, event):
        self.w = TargetDetailWindow(self.warship)
        self.w.show()

        if self.w.exec():
            solution = self.w.get_inputs()
            self.warship.set_solution(solution)

            # now calculate the ellipse movement
            # get coordinates based on bearing and range
            (lat, lon) = bearing_and_range_to_coord(self.ownship, self.warship)
            self.warship.coord.lat = lat
            self.warship.coord.lon = lon

            global_pos = event.scenePos()

            dx = self.warship.coord.lat - global_pos.x()
            dy = self.warship.coord.lon - global_pos.y()

            self.moveBy(dx, dy)

            # this also affects the target's first vector so update that too
            self.course_lines[0].setLine(lat, lon, self.course_lines[0].end_coord.x(),
                                         self.course_lines[0].end_coord.y())

        print(self.warship)

    def mouseReleaseEvent(self, event):
        super(ShipEllipse, self).mouseReleaseEvent(event)
        pass

    def mouseMoveEvent(self, event):
        # <Warship A> B-317.0T, R-5171.0yds, C-0.0T, S-0.0kts (-352.7, 378.2)
        # <Warship A> B-223.0T, R-5130yds, C-0.0T, S-0.0kts (-349.0, 376.0)
        if event.buttons() == Qt.LeftButton:
            global_pos = event.scenePos()

            self.warship.coord.lat = global_pos.x()
            self.warship.coord.lon = global_pos.y()

            super(ShipEllipse, self).mouseMoveEvent(event)

            self.warship.solution.rng = range_to_target(self.ownship, self.warship)
            self.warship.solution.bearing = bearing_to_target(self.ownship, self.warship)

            self.course_lines[0].setLine(self.warship.coord.lat, self.warship.coord.lon,
                                         self.course_lines[0].end_coord.x(),
                                         self.course_lines[0].end_coord.y())

            print(self.warship)

    def hoverMoveEvent(self, event):
        self.setToolTip(self.warship.tooltip())

    def bind_warship(self, warship):
        self.warship = warship
        self.course_lines.append(BuilderArrow(warship.course_vector))

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

        self.scene = QGraphicsScene()
        self.blueBrush = QBrush(Qt.blue)
        self.redBrush = QBrush(Qt.red)
        self.cyanBrush = QBrush(Qt.cyan)

        self.whitePen = QPen(Qt.white)

        self.font = QFont('Times', 8)
        self.font.setBold(True)

        self.init_window()

    def init_window(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.create_graphic_view()

        self.show()

    def create_graphic_view(self):
        graphic_view = QGraphicsView(self.scene, self)
        graphic_view.setGeometry(0, 0, 1800, 1800)

        self.shapes()

    def shapes(self):
        ownship_ellipse = ShipEllipse(0, 0, 50, 50)
        self.ownship.coord.lat = 0
        self.ownship.coord.lon = 0
        ownship_ellipse.bind_warship(self.ownship)
        ownship_ellipse.bind_ownship(self.ownship)
        ownship_ellipse.setPen(self.whitePen)
        ownship_ellipse.setBrush(self.cyanBrush)
        ownship_ellipse.setAcceptHoverEvents(True)
        ownship_ellipse.setToolTip("Ownship")
        solution = Solution(0, 0, 0, 3.5)
        self.ownship.set_solution(solution)
        self.ownship.course_vector.set_line(self.ownship)
        self.scene.addItem(ownship_ellipse)

        warship1_ellipse = ShipEllipse(-200, -900, 50, 50)
        self.warship1.coord.lat = -200
        self.warship1.coord.lon = -900
        solution = Solution(bearing_to_target(self.ownship, self.warship1),
                            range_to_target(self.ownship, self.warship1),
                            180, 27)
        self.warship1.set_solution(solution)
        self.warship1.course_vector.set_line(self.warship1)
        warship1_ellipse.bind_warship(self.warship1)
        warship1_ellipse.bind_ownship(self.ownship)
        warship1_ellipse.setPen(self.whitePen)
        warship1_ellipse.setBrush(self.blueBrush)
        warship1_ellipse.setAcceptHoverEvents(True)
        warship1_ellipse.setToolTip("Warship {0}".format(self.warship1.desig))
        self.scene.addItem(warship1_ellipse)

        warship2_ellipse = ShipEllipse(200, -900, 50, 50)
        self.warship2.coord.lat = 200
        self.warship2.coord.lon = -900
        solution = Solution(bearing_to_target(self.ownship, self.warship2),
                            range_to_target(self.ownship, self.warship2),
                            180, 20)
        self.warship2.set_solution(solution)
        self.warship2.course_vector.set_line(self.warship2)
        warship2_ellipse.bind_warship(self.warship2)
        warship2_ellipse.bind_ownship(self.ownship)
        warship2_ellipse.setPen(self.whitePen)
        warship2_ellipse.setBrush(self.redBrush)
        warship2_ellipse.setAcceptHoverEvents(True)
        warship2_ellipse.setToolTip("Warship {0}".format(self.warship2.desig))
        self.scene.addItem(warship2_ellipse)

        warship1_ellipse.setFlag(QGraphicsItem.ItemIsMovable)
        warship1_ellipse.setFlag(QGraphicsItem.ItemIsSelectable)

        warship2_ellipse.setFlag(QGraphicsItem.ItemIsMovable)
        warship2_ellipse.setFlag(QGraphicsItem.ItemIsSelectable)

        self.scene.addItem(warship1_ellipse.course_lines[0])
        self.scene.addItem(warship2_ellipse.course_lines[0])

        ownship_line = BuilderArrow(self.ownship.course_vector)
        self.scene.addItem(ownship_line)

        print(self.ownship)
        print(self.warship1)
        print(self.warship2)


def main():
    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
