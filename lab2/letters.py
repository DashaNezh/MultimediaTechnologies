import math
from PySide6.QtGui import QColor
from enum import Enum


class ShadingMode(Enum):
    MONOTONE = "Монотонное"
    GOURAUD = "Градиент Гуро"
    PHONG = "Градиент Фонга"


class Vector3D:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other):
        return Vector3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector3D(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar):
        return Vector3D(self.x * scalar, self.y * scalar, self.z * scalar)

    def length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def normalized(self):
        length = self.length()
        if length == 0:
            return Vector3D(0, 0, 0)
        return Vector3D(self.x / length, self.y / length, self.z / length)

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z


class Matrix4x4:
    def __init__(self):
        self.m = [[0] * 4 for _ in range(4)]
        self.m[0][0] = 1
        self.m[1][1] = 1
        self.m[2][2] = 1
        self.m[3][3] = 1

    def __mul__(self, other):
        if isinstance(other, Vector3D):
            x = self.m[0][0] * other.x + self.m[0][1] * other.y + self.m[0][2] * other.z + self.m[0][3]
            y = self.m[1][0] * other.x + self.m[1][1] * other.y + self.m[1][2] * other.z + self.m[1][3]
            z = self.m[2][0] * other.x + self.m[2][1] * other.y + self.m[2][2] * other.z + self.m[2][3]
            w = self.m[3][0] * other.x + self.m[3][1] * other.y + self.m[3][2] * other.z + self.m[3][3]
            if w != 0:
                x /= w
                y /= w
                z /= w
            return Vector3D(x, y, z)
        elif isinstance(other, Matrix4x4):
            result = Matrix4x4()
            for i in range(4):
                for j in range(4):
                    result.m[i][j] = sum(self.m[i][k] * other.m[k][j] for k in range(4))
            return result

    @staticmethod
    def translation(x, y, z):
        mat = Matrix4x4()
        mat.m[0][3] = x
        mat.m[1][3] = y
        mat.m[2][3] = z
        return mat

    @staticmethod
    def rotation_x(angle):
        mat = Matrix4x4()
        rad = math.radians(angle)
        mat.m[1][1] = math.cos(rad)
        mat.m[1][2] = -math.sin(rad)
        mat.m[2][1] = math.sin(rad)
        mat.m[2][2] = math.cos(rad)
        return mat

    @staticmethod
    def rotation_y(angle):
        mat = Matrix4x4()
        rad = math.radians(angle)
        mat.m[0][0] = math.cos(rad)
        mat.m[0][2] = math.sin(rad)
        mat.m[2][0] = -math.sin(rad)
        mat.m[2][2] = math.cos(rad)
        return mat

    @staticmethod
    def rotation_z(angle):
        mat = Matrix4x4()
        rad = math.radians(angle)
        mat.m[0][0] = math.cos(rad)
        mat.m[0][1] = -math.sin(rad)
        mat.m[1][0] = math.sin(rad)
        mat.m[1][1] = math.cos(rad)
        return mat

    @staticmethod
    def scaling(sx, sy, sz):
        mat = Matrix4x4()
        mat.m[0][0] = sx
        mat.m[1][1] = sy
        mat.m[2][2] = sz
        return mat

    def inverse_rotation(self):
        result = Matrix4x4()
        for i in range(3):
            for j in range(3):
                result.m[i][j] = self.m[j][i]
        return result


class Face:
    def __init__(self, vertices, color):
        self.vertices = vertices
        self.color = color
        self.normal = self.calculate_normal()
        self.center = self.calculate_center()

    def calculate_normal(self):
        if len(self.vertices) < 3:
            return Vector3D(0, 0, 0)
        v1 = self.vertices[1] - self.vertices[0]
        v2 = self.vertices[2] - self.vertices[0]
        normal = Vector3D(
            v1.y * v2.z - v1.z * v2.y,
            v1.z * v2.x - v1.x * v2.z,
            v1.x * v2.y - v1.y * v2.x
        )
        return normal.normalized()

    def calculate_center(self):
        if not self.vertices:
            return Vector3D(0, 0, 0)
        x = sum(v.x for v in self.vertices) / len(self.vertices)
        y = sum(v.y for v in self.vertices) / len(self.vertices)
        z = sum(v.z for v in self.vertices) / len(self.vertices)
        return Vector3D(x, y, z)


class Letter3D:
    def __init__(self, height, width, depth, offset_x=0, letter_type='Д'):
        self.height = height
        self.width = width
        self.depth = depth
        self.offset_x = offset_x
        self.letter_type = letter_type
        self.vertices = []
        self.faces = []
        self.transform = Matrix4x4.rotation_x(180)
        self.scale = 1.0
        self.update_geometry()

    def update_geometry(self):
        self.vertices = []
        self.faces = []
        h, w, d, ox = self.height, self.width, self.depth, self.offset_x
        bar_thickness = h * 0.1  # Толщина перекладин и стоек

        if self.letter_type == 'Д':
            self.create_letter_D(h, w, d, ox, bar_thickness)
        else:
            self.create_letter_N(h, w, d, ox, bar_thickness)

    def create_letter_D(self, h, w, d, ox, bar_thickness):
        hw = w / 2
        hd = d / 2
        top_y = h
        bottom_y = 0
        # Перекладина почти в самом низу
        crossbar_y = bottom_y + bar_thickness / 2 + 1
        crossbar_bottom = crossbar_y - bar_thickness / 2
        # Верхние точки совпадают
        top_x = ox
        left_bottom_x = ox - hw
        right_bottom_x = ox + hw

        # Левая стойка (наклонная)
        front_left_leg = [
            Vector3D(left_bottom_x, crossbar_y + bar_thickness / 2, -hd),
            Vector3D(left_bottom_x + bar_thickness, crossbar_y + bar_thickness / 2, -hd),
            Vector3D(top_x + bar_thickness / 2, top_y, -hd),
            Vector3D(top_x - bar_thickness / 2, top_y, -hd)
        ]
        back_left_leg = [
            Vector3D(left_bottom_x, crossbar_y + bar_thickness / 2, hd),
            Vector3D(left_bottom_x + bar_thickness, crossbar_y + bar_thickness / 2, hd),
            Vector3D(top_x + bar_thickness / 2, top_y, hd),
            Vector3D(top_x - bar_thickness / 2, top_y, hd)
        ]

        # Правая стойка (наклонная)
        front_right_leg = [
            Vector3D(right_bottom_x - bar_thickness, crossbar_y + bar_thickness / 2, -hd),
            Vector3D(right_bottom_x, crossbar_y + bar_thickness / 2, -hd),
            Vector3D(top_x + bar_thickness / 2, top_y, -hd),
            Vector3D(top_x - bar_thickness / 2, top_y, -hd)
        ]
        back_right_leg = [
            Vector3D(right_bottom_x - bar_thickness, crossbar_y + bar_thickness / 2, hd),
            Vector3D(right_bottom_x, crossbar_y + bar_thickness / 2, hd),
            Vector3D(top_x + bar_thickness / 2, top_y, hd),
            Vector3D(top_x - bar_thickness / 2, top_y, hd)
        ]

        # Нижняя перекладина еще длиннее
        crossbar_extension = bar_thickness * 3.5
        crossbar_left = left_bottom_x + bar_thickness - crossbar_extension
        crossbar_right = right_bottom_x - bar_thickness + crossbar_extension
        front_crossbar = [
            Vector3D(crossbar_left, crossbar_y + bar_thickness / 2, -hd),
            Vector3D(crossbar_right, crossbar_y + bar_thickness / 2, -hd),
            Vector3D(crossbar_right, crossbar_y - bar_thickness / 2, -hd),
            Vector3D(crossbar_left, crossbar_y - bar_thickness / 2, -hd)
        ]
        back_crossbar = [
            Vector3D(crossbar_left, crossbar_y + bar_thickness / 2, hd),
            Vector3D(crossbar_right, crossbar_y + bar_thickness / 2, hd),
            Vector3D(crossbar_right, crossbar_y - bar_thickness / 2, hd),
            Vector3D(crossbar_left, crossbar_y - bar_thickness / 2, hd)
        ]

        # Ножки под концами перекладины (верх совпадает с низом перекладины)
        leg_height = h * 0.18
        # Левая ножка
        front_left_foot = [
            Vector3D(crossbar_left, crossbar_bottom, -hd),
            Vector3D(crossbar_left + bar_thickness, crossbar_bottom, -hd),
            Vector3D(crossbar_left + bar_thickness, crossbar_bottom - leg_height, -hd),
            Vector3D(crossbar_left, crossbar_bottom - leg_height, -hd)
        ]
        back_left_foot = [
            Vector3D(crossbar_left, crossbar_bottom, hd),
            Vector3D(crossbar_left + bar_thickness, crossbar_bottom, hd),
            Vector3D(crossbar_left + bar_thickness, crossbar_bottom - leg_height, hd),
            Vector3D(crossbar_left, crossbar_bottom - leg_height, hd)
        ]
        # Правая ножка
        front_right_foot = [
            Vector3D(crossbar_right - bar_thickness, crossbar_bottom, -hd),
            Vector3D(crossbar_right, crossbar_bottom, -hd),
            Vector3D(crossbar_right, crossbar_bottom - leg_height, -hd),
            Vector3D(crossbar_right - bar_thickness, crossbar_bottom - leg_height, -hd)
        ]
        back_right_foot = [
            Vector3D(crossbar_right - bar_thickness, crossbar_bottom, hd),
            Vector3D(crossbar_right, crossbar_bottom, hd),
            Vector3D(crossbar_right, crossbar_bottom - leg_height, hd),
            Vector3D(crossbar_right - bar_thickness, crossbar_bottom - leg_height, hd)
        ]

        self.vertices = (
                front_left_leg + back_left_leg + front_right_leg + back_right_leg +
                front_crossbar + back_crossbar +
                front_left_foot + back_left_foot + front_right_foot + back_right_foot
        )
        main_color = QColor(255, 105, 180)  # Один цвет для всех граней
        side_color = main_color
        top_color = main_color

        self._create_faces_for_part(front_left_leg, back_left_leg)
        self._create_faces_for_part(front_right_leg, back_right_leg)
        self._create_faces_for_part(front_crossbar, back_crossbar)
        self._create_faces_for_part(front_left_foot, back_left_foot)
        self._create_faces_for_part(front_right_foot, back_right_foot)

    def create_letter_N(self, h, w, d, ox, bar_thickness):
        # Остаётся без изменений
        hw = w / 2
        hd = d / 2
        hh = h / 2

        front_left = [
            Vector3D(ox - hw, h, -hd),
            Vector3D(ox - hw + bar_thickness, h, -hd),
            Vector3D(ox - hw + bar_thickness, 0, -hd),
            Vector3D(ox - hw, 0, -hd)
        ]
        back_left = [
            Vector3D(ox - hw, h, hd),
            Vector3D(ox - hw + bar_thickness, h, hd),
            Vector3D(ox - hw + bar_thickness, 0, hd),
            Vector3D(ox - hw, 0, hd)
        ]
        front_right = [
            Vector3D(ox + hw - bar_thickness, h, -hd),
            Vector3D(ox + hw, h, -hd),
            Vector3D(ox + hw, 0, -hd),
            Vector3D(ox + hw - bar_thickness, 0, -hd)
        ]
        back_right = [
            Vector3D(ox + hw - bar_thickness, h, hd),
            Vector3D(ox + hw, h, hd),
            Vector3D(ox + hw, 0, hd),
            Vector3D(ox + hw - bar_thickness, 0, hd)
        ]
        front_bar = [
            Vector3D(ox - hw + bar_thickness, hh + bar_thickness / 2, -hd),
            Vector3D(ox + hw - bar_thickness, hh + bar_thickness / 2, -hd),
            Vector3D(ox + hw - bar_thickness, hh - bar_thickness / 2, -hd),
            Vector3D(ox - hw + bar_thickness, hh - bar_thickness / 2, -hd)
        ]
        back_bar = [
            Vector3D(ox - hw + bar_thickness, hh + bar_thickness / 2, hd),
            Vector3D(ox + hw - bar_thickness, hh + bar_thickness / 2, hd),
            Vector3D(ox + hw - bar_thickness, hh - bar_thickness / 2, hd),
            Vector3D(ox - hw + bar_thickness, hh - bar_thickness / 2, hd)
        ]

        self.vertices = front_left + back_left + front_right + back_right + front_bar + back_bar
        main_color = QColor(255, 105, 180)  # Один цвет для всех граней
        side_color = main_color
        top_color = main_color

        self._create_faces_for_part(front_left, back_left)
        self._create_faces_for_part(front_right, back_right)
        self._create_faces_for_part(front_bar, back_bar)

        # Используем основной цвет для дополнительных граней
        self.faces.append(Face([front_left[1], front_bar[0], back_bar[0], back_left[1]], main_color))
        self.faces.append(Face([back_left[1], back_bar[0], front_bar[0], front_left[1]], main_color))
        self.faces.append(Face([front_left[2], front_bar[3], back_bar[3], back_left[2]], main_color))
        self.faces.append(Face([back_left[2], back_bar[3], front_bar[3], front_left[2]], main_color))
        self.faces.append(Face([front_right[0], front_bar[1], back_bar[1], back_right[0]], main_color))
        self.faces.append(Face([back_right[0], back_bar[1], front_bar[1], front_right[0]], main_color))
        self.faces.append(Face([front_right[3], front_bar[2], back_bar[2], back_right[3]], main_color))
        self.faces.append(Face([back_right[3], back_bar[2], front_bar[2], back_right[3]], main_color))

    def _create_faces_for_part(self, front_vertices, back_vertices):
        main_color = QColor(255, 105, 180)  # Один цвет для всех граней
        side_color = main_color
        top_color = main_color

        # Передняя и задняя грани
        self.faces.append(
            Face([front_vertices[0], front_vertices[1], front_vertices[2], front_vertices[3]], main_color))
        self.faces.append(Face([back_vertices[0], back_vertices[3], back_vertices[2], back_vertices[1]], main_color))

        # Боковые грани
        for i in range(len(front_vertices)):
            next_i = (i + 1) % len(front_vertices)
            side_face = [
                front_vertices[i],
                back_vertices[i],
                back_vertices[next_i],
                front_vertices[next_i]
            ]
            v1 = side_face[1] - side_face[0]
            v2 = side_face[2] - side_face[0]
            normal = Vector3D(
                v1.y * v2.z - v1.z * v2.y,
                v1.z * v2.x - v1.x * v2.z,
                v1.x * v2.y - v1.y * v2.x
            ).normalized()
            center = Vector3D(
                sum(v.x for v in side_face) / 4,
                sum(v.y for v in side_face) / 4,
                sum(v.z for v in side_face) / 4
            )
            to_center = center * (-1)
            if normal.dot(to_center) < 0:
                side_face = [front_vertices[i], front_vertices[next_i], back_vertices[next_i], back_vertices[i]]
            self.faces.append(Face(side_face, side_color))

        # Верхняя и нижняя грани (если есть)
        if len(front_vertices) >= 4:
            top_face = [front_vertices[0], front_vertices[1], back_vertices[1], back_vertices[0]]
            bottom_face = [front_vertices[3], front_vertices[2], back_vertices[2], back_vertices[3]]
            self.faces.append(Face(top_face, top_color))
            self.faces.append(Face(bottom_face, top_color))

    def rotate(self, axis, angle):
        if axis == 0:
            rot = Matrix4x4.rotation_x(angle)
        elif axis == 1:
            rot = Matrix4x4.rotation_y(angle)
        else:
            rot = Matrix4x4.rotation_z(angle)
        self.transform = rot * self.transform

    def set_scale(self, scale_factor):
        self.scale = scale_factor
