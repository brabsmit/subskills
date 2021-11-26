import sys

from PyQt5.Qt import Qt
from PyQt5.QtCore import QPropertyAnimation, QObject, QRectF, pyqtSignal, pyqtProperty, QAbstractTableModel, QTimer
from PyQt5.QtGui import QPen, QBrush, QFont
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsItem, \
    QGraphicsEllipseItem, QDialog, QFormLayout, QDialogButtonBox, QLineEdit, QGraphicsLineItem, QTableView, \
    QAbstractScrollArea
from numpy import sqrt, arctan2, degrees, sin, cos, radians, pi


# TODO: background
# TODO: target class

# TODO: click and drag CourseLine
# TODO: add more than one CourseLine


def range_to_target(ownship, target):
    # sqrt((os_x - tgt_x)^2 + (os_y - tgt_y)^2)

    os_x = abs(ownship.coord.lat)
    os_y = abs(ownship.coord.lon)

    tgt_x = abs(target.coord.lat)
    tgt_y = abs(target.coord.lon)

    return int(10 * sqrt((os_x - tgt_x) ** 2 + (os_y - tgt_y) ** 2))


def range_to_point(start_coord, end_coord):
    x1 = abs(start_coord.lat)
    y1 = abs(start_coord.lon)

    x2 = abs(end_coord.lat)
    y2 = abs(end_coord.lon)

    return int(10 * sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2))


def bearing_to_target(ownship, target):
    # normalize coordinates to ownship
    offset_x = target.coord.lat
    offset_y = target.coord.lon

    os_normal = Coordinate(ownship.coord.lat - offset_x, ownship.coord.lon - offset_y)
    phi = arctan2(os_normal.lat, os_normal.lon)
    bearing = degrees(phi)

    if bearing <= 0:
        return round(abs(bearing), 1)
    else:
        return round(360 - bearing, 1)


def bearing_to_point(start_coord, end_coord):
    offset_x = end_coord.lat
    offset_y = end_coord.lon

    normal = Coordinate(start_coord.lat - offset_x, start_coord.lon - offset_y)
    phi = arctan2(normal.lat, normal.lon)
    bearing = degrees(phi)

    if bearing <= 0:
        return round(abs(bearing), 1)
    else:
        return round(360 - bearing, 1)


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
    phi = target.solution.course
    rho = target.solution.speed * 333

    x_offset = rho / 10 * cos(radians(phi))
    y_offset = rho / 10 * sin(radians(phi))

    lat = x_offset + target.coord.lat
    lon = y_offset + target.coord.lon

    return round(lat, 1), round(lon, 1)


def course_vector_to_coord(course_vector):
    phi = course_vector.course
    rho = course_vector.speed * course_vector.duration * (1/3) * 100

    x_offset = rho / 10 * cos(radians(phi))
    y_offset = rho / 10 * sin(radians(phi))

    return round(x_offset, 1), round(y_offset, 1)


def cart_to_polar(lat, lon):
    rho = sqrt(lat ** 2 + lon ** 2)
    phi = arctan2(lon, lat)
    return rho, phi


def polar_to_cart(rho, phi):
    trans_phi = (phi - 90) % 360
    lat = rho / 10 * cos(radians(trans_phi))
    lon = rho / 10 * sin(radians(trans_phi))
    return round(lat, 1), round(lon, 1)


def coordinates_to_bearing_range(start_coord, end_coord):
    rng = range_to_point(start_coord, end_coord)
    bearing = bearing_to_point(start_coord, end_coord)

    return bearing, rng

def cpa(ownship, warship):
    dtr = pi / 180
    x = warship.solution.rng/2000 * cos(dtr*warship.solution.bearing)
    y = warship.solution.rng/2000 * sin(dtr*warship.solution.bearing)
    xvel = warship.solution.speed * cos(dtr * warship.solution.course) - ownship.solution.speed * cos(dtr * ownship.solution.course)
    yvel = warship.solution.speed * sin(dtr * warship.solution.course) - ownship.solution.speed * sin(dtr * ownship.solution.course)
    dot = (x * xvel) + (y * yvel)
    if dot >= 0:
        return [-1, -1]
    a = xvel**2 + yvel**2
    b = 2 * dot
    cpa_range = sqrt((warship.solution.rng/2000)**2 - ((b**2)/(4*a))) # yards
    cpa_time = 60*(-b/(2*a)) # minutes
    return [cpa_range*2000, cpa_time]


class Coordinate:

    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def __str__(self):
        return "({0},{1})".format(round(self.lat, 0), round(self.lon, 0))


class Solution:

    def __init__(self, bearing, rng, course, speed, cpa_range, cpa_time):
        self.bearing = bearing
        self.rng = rng
        self.course = course
        self.speed = speed
        self.cpa_range = cpa_range
        self.cpa_time = cpa_time

    def __str__(self):
        bearing_string = ""
        if self.bearing < 100:
            bearing_string += "0"
            if self.bearing < 10:
                bearing_string += "0"
        bearing_string += str(self.bearing)

        course_string = ""
        if self.course < 100:
            course_string += "0"
            if self.course < 10:
                course_string += "0"
        course_string += str(self.course)

        if self.rng > 999:
            range_string = str(round(self.rng / 1000, 1))
            range_string += "kyds"
        else:
            range_string = str(round(self.rng, 1))
            range_string += "yds"

        return "B-{0}T, R-{1}, C-{2}T, S-{3}kts".format(bearing_string, range_string, course_string, self.speed)


class CourseVector:

    def __init__(self, course, speed, duration):
        self.course = course
        self.speed = speed
        self.duration = duration

        self.direction = self.course
        self.length = self.speed * self.duration * (1/4.5) * 100

    def __str__(self):
        return "D-{0}, rho-{1}, phi-{2}".format(self.duration, self.length, self.direction)


class ShipDatabase:

    def __init__(self):
        self.total = 0
        self.warships = []

    def add(self, warships):
        if type(warships) is not list: to_select = [warships]
        for warship in warships:
            warship.id = self.total
            self.warships.append(warship)
            self.total += 1

class Ownship:

    def __init__(self):
        self.coord = Coordinate(0, 0)
        self.solution = Solution(0, 0, 0, 0, 0, 0)
        self.course_vectors = []

    def set_solution(self, solution):
        self.solution.bearing = solution.bearing
        self.solution.rng = solution.rng
        self.solution.course = solution.course
        self.solution.speed = solution.speed
        self.course_vectors.append(CourseVector(self.solution.course, self.solution.speed, 10))

    def update_solution(self, solution):
        self.solution.bearing = solution.bearing
        self.solution.rng = solution.rng
        self.solution.course = solution.course
        self.solution.speed = solution.speed
        self.course_vectors[0] = CourseVector(self.solution.course, self.solution.speed, 10)

    def __str__(self):
        return "<Ownship> {0} ({1}, {2})".format(self.solution, self.coord.lat, self.coord.lon)

    def tooltip(self):
        return "Ownship \nCourse:\t{0}\nSpeed:\t{1}kts".format(self.solution.course, self.solution.speed)


class Warship:

    def __init__(self, ship_type, desig, ownship):
        self.id = 0
        self.ship_type = ship_type
        self.desig = desig
        self.coord = Coordinate(0, 0)
        self.solution = Solution(0, 0, 0, 0, 0, 0)
        self.course_vectors = []
        self.ship_ellipse = ShipEllipse(0, 0, 0, 0)
        self.ownship = ownship

    def set_solution(self, solution):
        self.solution.bearing = solution.bearing
        self.solution.rng = solution.rng
        self.solution.course = solution.course
        self.solution.speed = solution.speed
        [cpa_range, cpa_time] = cpa(self.ownship, self)
        self.solution.cpa_range = cpa_range
        self.solution.cpa_time = cpa_time
        self.course_vectors.append(CourseVector(self.solution.course, self.solution.speed, 10))

    def update_solution(self, solution):
        self.solution.bearing = solution.bearing
        self.solution.rng = solution.rng
        self.solution.course = solution.course
        self.solution.speed = solution.speed
        [cpa_range, cpa_time] = cpa(self.ownship, self)
        self.solution.cpa_range = cpa_range
        self.solution.cpa_time = cpa_time
        self.course_vectors[0] = CourseVector(self.solution.course, self.solution.speed, 10)

    def bind_ellipse(self, ship_ellipse):
        self.ship_ellipse = ship_ellipse

    def __str__(self):
        return "<Warship {0}>[{1}] {2} ({3}, {4})".format(self.desig, self.id, self.solution, self.coord.lat,
                                                     self.coord.lon)

    def tooltip(self):
        return "Warship {0}\nBearing:\t{1}\nRange:\t{2}yds\nCourse:\t{3}\nSpeed:\t{4}kts".format(self.desig,
                                                                                                 self.solution.bearing,
                                                                                                 self.solution.rng,
                                                                                                 self.solution.course,
                                                                                                 self.solution.speed)


class ArrowHead(QGraphicsEllipseItem):

    def __init__(self, parent):
        super(ArrowHead, self).__init__()
        self.parent = parent

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            #super(ArrowHead, self).mouseMoveEvent(event)
            self.parent.ship_ellipse.course_lines[0].rotate_line(event)


class CourseLine(QGraphicsLineItem):

    def __init__(self, parent):
        super().__init__()
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setPen(QPen(Qt.black))
        self.arrow_left = QGraphicsLineItem()
        self.arrow_right = QGraphicsLineItem()
        self.arrow_head_center = Coordinate(0, 0)
        self.parent = parent
        self.arrow_length = 150
        self.arrow_head = ArrowHead(self.parent)

        self.start_coord = Coordinate(self.parent.coord.lat + 10, self.parent.coord.lon + 10)
        (lat, lon) = polar_to_cart(self.parent.course_vectors[0].length, self.parent.course_vectors[0].direction)
        self.end_coord = Coordinate(self.parent.coord.lat + lat + 10, self.parent.coord.lon + lon + 10)

        self.setLine(self.start_coord.lat, self.start_coord.lon, self.end_coord.lat, self.end_coord.lon)

        (arrow_left_end_lat, arrow_left_end_lon) = polar_to_cart(self.arrow_length,
                                                                 (self.parent.course_vectors[0].direction + 150) % 360)
        self.arrow_left.setLine(self.end_coord.lat, self.end_coord.lon,
                                self.end_coord.lat + arrow_left_end_lat,
                                self.end_coord.lon + arrow_left_end_lon)

        (arrow_right_end_lat, arrow_right_end_lon) = polar_to_cart(self.arrow_length,
                                                                   (self.parent.course_vectors[0].direction
                                                                    - 150) % 360)
        self.arrow_right.setLine(self.end_coord.lat, self.end_coord.lon,
                                 self.end_coord.lat + arrow_right_end_lat,
                                 self.end_coord.lon + arrow_right_end_lon)

        self.arrow_head.setRect(self.end_coord.lat - 15, self.end_coord.lon - 15, 30, 30)
        self.arrow_head.setPen(QPen(Qt.transparent))

    def translate_line(self):
        self.start_coord = Coordinate(self.parent.coord.lat + 10, self.parent.coord.lon + 10)
        (lat, lon) = polar_to_cart(self.parent.course_vectors[0].length, self.parent.course_vectors[0].direction)
        self.end_coord = Coordinate(self.parent.coord.lat + lat + 10, self.parent.coord.lon + lon + 10)
        self.setLine(self.start_coord.lat, self.start_coord.lon, self.end_coord.lat, self.end_coord.lon)

        (arrow_left_end_lat, arrow_left_end_lon) = polar_to_cart(self.arrow_length,
                                                                 (self.parent.course_vectors[0].direction + 150) % 360)
        self.arrow_left.setLine(self.end_coord.lat, self.end_coord.lon,
                                self.end_coord.lat + arrow_left_end_lat,
                                self.end_coord.lon + arrow_left_end_lon)

        (arrow_right_end_lat, arrow_right_end_lon) = polar_to_cart(self.arrow_length,
                                                                   (self.parent.course_vectors[0].direction
                                                                    - 150) % 360)
        self.arrow_right.setLine(self.end_coord.lat, self.end_coord.lon,
                                 self.end_coord.lat + arrow_right_end_lat,
                                 self.end_coord.lon + arrow_right_end_lon)

        self.arrow_head.setRect(self.end_coord.lat - 15, self.end_coord.lon - 15, 30, 30)

    def rotate_line(self, event):
        self.start_coord = Coordinate(self.parent.coord.lat + 10, self.parent.coord.lon + 10)

        global_pos = event.scenePos()

        lat = global_pos.x()
        lon = global_pos.y()

        end_coord = Coordinate(lat, lon)

        (bearing, rng) = coordinates_to_bearing_range(self.start_coord, end_coord)
        self.parent.course_vectors[0].direction = bearing
        self.parent.solution.course = bearing
        self.parent.course_vectors[0].length = rng
        print("{0}".format(rng))

        self.translate_line()

    def __str__(self):
        return "({0}, {1}) -> ({2}, {3})".format(self.start_coord.lat, self.start_coord.lon,
                                                 self.end_coord.lat, self.end_coord.lon)


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
                            float(self.speed.text()), 0, 0)
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
            self.warship.update_solution(solution)
            [cpa_range, cpa_time] = cpa(self.ownship, self.warship)
            self.warship.solution.cpa_range = cpa_range
            self.warship.solution.cpa_time = cpa_time

            # now calculate the ellipse movement
            # get coordinates based on bearing and range
            (lat, lon) = bearing_and_range_to_coord(self.ownship, self.warship)
            self.warship.coord.lat = lat
            self.warship.coord.lon = lon

            global_pos = event.scenePos()

            dx = self.warship.coord.lat - global_pos.x() + 10
            dy = self.warship.coord.lon - global_pos.y() + 10

            self.course_lines[0].translate_line()

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

            self.course_lines[0].translate_line()

            super(ShipEllipse, self).mouseMoveEvent(event)

            self.warship.solution.rng = range_to_target(self.ownship, self.warship)
            self.warship.solution.bearing = bearing_to_target(self.ownship, self.warship)
            [cpa_range, cpa_time] = cpa(self.ownship, self.warship)
            self.warship.solution.cpa_range = cpa_range
            self.warship.solution.cpa_time = cpa_time

    def hoverMoveEvent(self, event):
        self.setToolTip(self.warship.tooltip())

    def bind_warship(self, warship):
        self.warship = warship
        self.course_lines.append(CourseLine(warship))

    def bind_ownship(self, ownship):
        self.ownship = ownship


class ManagerRectAnimation(QObject):
    rectChanged = pyqtSignal(QRectF)

    def __init__(self, parent=None):
        super(ManagerRectAnimation, self).__init__(parent)
        self._rect = QRectF()

        self._animation = QPropertyAnimation(self, targetObject=self, propertyName=b"rect", duration=6000)

    @property
    def animation(self):
        return self._animation

    def rect(self):
        return self._rect

    def setRect(self, r):
        self._rect = r
        self.rectChanged.emit(r)

    rect = pyqtProperty(QRectF, fget=rect, fset=setRect, notify=rectChanged)


class VehicleSummaryModel(QAbstractTableModel):

    def __init__(self, data, *args):
        QAbstractTableModel.__init__(self, *args)
        self.data = data
        self.header = ['ID', 'Desig', 'BRG', 'RNG', 'CRS', 'SPD', 'CPAr', 'CPAt']
        self.setDataList(data)
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateModel)
        self.timer.start(1000)

    def setDataList(self, data):
        self.data = data
        self.layoutAboutToBeChanged.emit()
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rowCount(0), self.columnCount(0)))
        self.layoutChanged.emit()

    def updateModel(self):
        self.layoutAboutToBeChanged.emit()
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rowCount(0), self.columnCount(0)))
        self.layoutChanged.emit()

    def data(self, index, role):
        if not index.isValid():
            return None
        if index.column() == 0: #id
            value = str(self.data[index.row()].id)
        elif index.column() == 1: #desig
            value = self.data[index.row()].desig
        elif index.column() == 2: #brg
            value = '{0}'.format(self.data[index.row()].solution.bearing)
        elif index.column() == 3: #rng
            value = str(self.data[index.row()].solution.rng)
        elif index.column() == 4: #course
            value = str(self.data[index.row()].solution.course)
        elif index.column() == 5: #speed
            value = str(self.data[index.row()].solution.speed)
        elif index.column() == 6: #cpar
            value = str(round(self.data[index.row()].solution.cpa_range))
        elif index.column() == 7: #cpat
            cpa_time = self.data[index.row()].solution.cpa_time
            minutes = cpa_time % 60
            seconds = (cpa_time * 60) % 60
            value = '{0}:{0}'.format(minutes, seconds)
        return value

    def setData(self, index, value):
        if not index.isValid():
            return False
        self.dataChanged.emit(index, index)
        return True

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None

    def rowCount(self, parent):
        return len(self.data)

    def columnCount(self, parent):
        return 8


class Window(QMainWindow):

    def __init__(self):
        super().__init__()

        self.title = "SubSkills"
        self.top = 0
        self.left = 0
        self.width = 1800
        self.height = 1000
        self.ownship = Ownship()
        self.warship1 = Warship(None, "A", None)
        self.warship2 = Warship(None, "B", None)

        self.scene = QGraphicsScene()
        self.blueBrush = QBrush(Qt.blue)
        self.redBrush = QBrush(Qt.red)
        self.cyanBrush = QBrush(Qt.cyan)

        self.whitePen = QPen(Qt.white)

        self.font = QFont('Times', 8)
        self.font.setBold(True)

        self.ship_database = ShipDatabase()
        self.ship_database.add([self.warship1, self.warship2])

        self.init_window()

    def init_window(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.create_graphic_view()

        self.show()

    def create_graphic_view(self):
        self.graphic_view = QGraphicsView(self.scene, self)
        self.graphic_view.setGeometry(0, 0, 1800, 1800)

        self.shapes()

    def shapes(self):
        ownship_ellipse = ShipEllipse(0, 0, 20, 20)
        self.ownship.coord.lat = 0
        self.ownship.coord.lon = 0
        ownship_ellipse.setPen(self.whitePen)
        ownship_ellipse.setBrush(self.cyanBrush)
        ownship_ellipse.setAcceptHoverEvents(True)
        ownship_ellipse.setToolTip("Ownship")
        solution = Solution(0, 0, 0, 3.5, 0, 0)
        self.ownship.set_solution(solution)
        ownship_ellipse.bind_warship(self.ownship)
        ownship_ellipse.bind_ownship(self.ownship)
        self.scene.addItem(ownship_ellipse)
        self.scene.addItem(ownship_ellipse.course_lines[0])
        self.scene.addItem(ownship_ellipse.course_lines[0].arrow_left)
        self.scene.addItem(ownship_ellipse.course_lines[0].arrow_right)
        self.scene.addItem(ownship_ellipse.course_lines[0].arrow_head)

        warship1_ellipse = ShipEllipse(-100, -600, 20, 20)
        self.warship1.ownship = self.ownship
        self.warship1.bind_ellipse(warship1_ellipse)
        self.warship1.coord.lat = -100
        self.warship1.coord.lon = -600
        solution = Solution(bearing_to_target(self.ownship, self.warship1),
                            range_to_target(self.ownship, self.warship1),
                            200, 27, 0, 0)
        self.warship1.set_solution(solution)
        warship1_ellipse.bind_warship(self.warship1)
        warship1_ellipse.bind_ownship(self.ownship)
        warship1_ellipse.setPen(self.whitePen)
        warship1_ellipse.setBrush(self.blueBrush)
        warship1_ellipse.setAcceptHoverEvents(True)
        warship1_ellipse.setToolTip("Warship {0}".format(self.warship1.desig))
        self.scene.addItem(warship1_ellipse)
        self.scene.addItem(warship1_ellipse.course_lines[0])
        self.scene.addItem(warship1_ellipse.course_lines[0].arrow_left)
        self.scene.addItem(warship1_ellipse.course_lines[0].arrow_right)
        self.scene.addItem(warship1_ellipse.course_lines[0].arrow_head)

        warship2_ellipse = ShipEllipse(100, -600, 20, 20)
        self.warship2.ownship = self.ownship
        self.warship2.bind_ellipse(warship2_ellipse)
        self.warship2.coord.lat = 100
        self.warship2.coord.lon = -600
        solution = Solution(bearing_to_target(self.ownship, self.warship2),
                            range_to_target(self.ownship, self.warship2),
                            160, 20, 0, 0)
        self.warship2.set_solution(solution)
        warship2_ellipse.bind_warship(self.warship2)
        warship2_ellipse.bind_ownship(self.ownship)
        warship2_ellipse.setPen(self.whitePen)
        warship2_ellipse.setBrush(self.redBrush)
        warship2_ellipse.setAcceptHoverEvents(True)
        warship2_ellipse.setToolTip("Warship {0}".format(self.warship2.desig))
        self.scene.addItem(warship2_ellipse)
        self.scene.addItem(warship2_ellipse.course_lines[0])
        self.scene.addItem(warship2_ellipse.course_lines[0].arrow_left)
        self.scene.addItem(warship2_ellipse.course_lines[0].arrow_right)
        self.scene.addItem(warship2_ellipse.course_lines[0].arrow_head)

        warship1_ellipse.setFlag(QGraphicsItem.ItemIsMovable)
        warship1_ellipse.course_lines[0].arrow_head.setFlag(QGraphicsItem.ItemIsMovable)

        warship2_ellipse.setFlag(QGraphicsItem.ItemIsMovable)
        warship2_ellipse.course_lines[0].arrow_head.setFlag(QGraphicsItem.ItemIsMovable)

        self.scene.setSceneRect(-900, -300, 1800, 1000)

        #manager_animation = ManagerRectAnimation(self.graphic_view)
        #manager_animation.rectChanged.connect(ownship_ellipse.setRect)
        #manager_animation.animation.setStartValue(QPointF(self.ownship.coord.lat, self.ownship.coord.lon))
        #manager_animation.animation.setEndValue(QPointF(self.ownship.coord.lat, self.ownship.coord.lon))
        #anager_animation.animation.start()

        self.vehicle_summary = VehicleSummaryModel([self.warship1, self.warship2])
        self.vehicle_table_view = QTableView()
        self.vehicle_table_view.setModel(self.vehicle_summary)
        self.vehicle_table_view.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.vehicle_table_view.resizeRowsToContents()
        self.vehicle_table_view.show()

        print(self.ownship)
        print(self.warship1)
        print(self.warship2)


def main():
    app = QApplication(sys.argv)
    window = Window()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
