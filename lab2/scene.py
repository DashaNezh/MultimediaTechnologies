from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPolygonF, QLinearGradient, QRadialGradient, QImage
from PySide6.QtCore import Qt, QPoint, QPointF
from letters import Letter3D, Vector3D, Matrix4x4, ShadingMode

class SceneWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor(35, 35, 35))
        self.setPalette(p)
        self.d_letter = Letter3D(100, 60, 30, offset_x=-60, letter_type='Д')
        self.n_letter = Letter3D(100, 60, 30, offset_x=60, letter_type='Н')
        self.camera_pos = Vector3D(0, 0, -400)
        self.camera_rot = [0, 0, 0]
        self.object_transform = Matrix4x4()
        self.scale = 1.0
        self.base_scale = 2.0
        self.auto_scale = True
        self.light_dir = Vector3D(0.5, 0.5, -1).normalized()
        self.light_pos = self.light_dir * 300
        self.shading_mode = ShadingMode.PHONG
        self.mirror_x = False
        self.mirror_y = False
        self.mirror_z = False
        self.cached_faces = None
        self.cache_valid = False

    def invalidate_cache(self):
        self.cache_valid = False

    def compute_phong_lighting(self, normal, position, inverse_transform):
        ambient_strength = 0.3
        diffuse_strength = 0.6
        specular_strength = 0.5
        shininess = 32

        light_dir = inverse_transform * self.light_dir
        light_dir = light_dir.normalized()

        world_pos = self.object_transform * position
        view_dir = (self.camera_pos - world_pos).normalized()

        if normal.dot(light_dir) <= 0:
            return ambient_strength

        diffuse = diffuse_strength * max(0, normal.dot(light_dir))
        reflect_dir = (light_dir - normal * (2 * normal.dot(light_dir))).normalized()
        specular = specular_strength * max(0, reflect_dir.dot(view_dir)) ** shininess

        intensity = ambient_strength + diffuse + specular
        return min(1.0, max(0.3, intensity))

    def clip_polygon_by_z0(self, vertices, normals, orig_vertices):
        # Sutherland-Hodgman clipping по z=0
        clipped_vertices = []
        clipped_normals = []
        clipped_orig = []
        n = len(vertices)
        for i in range(n):
            curr_v, curr_n, curr_o = vertices[i], normals[i], orig_vertices[i]
            prev_v, prev_n, prev_o = vertices[i-1], normals[i-1], orig_vertices[i-1]
            curr_in = curr_v.z > 0
            prev_in = prev_v.z > 0
            if curr_in:
                if not prev_in:
                    # Пересечение ребра с z=0
                    t = (0 - prev_v.z) / (curr_v.z - prev_v.z)
                    inter_v = Vector3D(
                        prev_v.x + t * (curr_v.x - prev_v.x),
                        prev_v.y + t * (curr_v.y - prev_v.y),
                        0
                    )
                    inter_n = Vector3D(
                        prev_n.x + t * (curr_n.x - prev_n.x),
                        prev_n.y + t * (curr_n.y - prev_n.y),
                        prev_n.z + t * (curr_n.z - prev_n.z)
                    )
                    inter_o = Vector3D(
                        prev_o.x + t * (curr_o.x - prev_o.x),
                        prev_o.y + t * (curr_o.y - prev_o.y),
                        prev_o.z + t * (curr_o.z - prev_o.z)
                    )
                    clipped_vertices.append(inter_v)
                    clipped_normals.append(inter_n)
                    clipped_orig.append(inter_o)
                clipped_vertices.append(curr_v)
                clipped_normals.append(curr_n)
                clipped_orig.append(curr_o)
            elif prev_in:
                # Пересечение ребра с z=0
                t = (0 - prev_v.z) / (curr_v.z - prev_v.z)
                inter_v = Vector3D(
                    prev_v.x + t * (curr_v.x - prev_v.x),
                    prev_v.y + t * (curr_v.y - prev_v.y),
                    0
                )
                inter_n = Vector3D(
                    prev_n.x + t * (curr_n.x - prev_n.x),
                    prev_n.y + t * (curr_n.y - prev_n.y),
                    prev_n.z + t * (curr_n.z - prev_n.z)
                )
                inter_o = Vector3D(
                    prev_o.x + t * (curr_o.x - prev_o.x),
                    prev_o.y + t * (curr_o.y - prev_o.y),
                    prev_o.z + t * (curr_o.z - prev_o.z)
                )
                clipped_vertices.append(inter_v)
                clipped_normals.append(inter_n)
                clipped_orig.append(inter_o)
        return clipped_vertices, clipped_normals, clipped_orig

    def compute_face_normal(self, vertices):
        # Пересчёт нормали для многоугольника (берём первые три точки)
        if len(vertices) < 3:
            return Vector3D(0, 0, 1)
        v1 = vertices[1] - vertices[0]
        v2 = vertices[2] - vertices[0]
        normal = Vector3D(
            v1.y * v2.z - v1.z * v2.y,
            v1.z * v2.x - v1.x * v2.z,
            v1.x * v2.y - v1.y * v2.x
        )
        return normal.normalized()

    def prepare_faces_cache(self):
        width, height = self.width(), self.height()
        self.cached_faces = []

        for letter in [self.d_letter, self.n_letter]:
            scale_matrix = Matrix4x4.scaling(letter.scale, letter.scale, letter.scale)
            letter_transform = self.object_transform * letter.transform * scale_matrix
            inverse_transform = letter_transform.inverse_rotation()

            transformed_vertices = []
            vertex_normals = []
            for v in letter.vertices:
                normal_sum = Vector3D(0, 0, 0)
                count = 0
                for face in letter.faces:
                    if v in face.vertices:
                        normal_sum += face.normal
                        count += 1
                vertex_normal = normal_sum.normalized() if count > 0 else Vector3D(0, 0, 1)

                v_transformed = letter_transform * v
                v_camera = self.apply_camera_transform(v_transformed)
                transformed_vertices.append(v_camera)
                vertex_normals.append(vertex_normal)

            for face in letter.faces:
                face_vertices = [transformed_vertices[letter.vertices.index(v)] for v in face.vertices]
                face_normals = [vertex_normals[letter.vertices.index(v)] for v in face.vertices]
                original_vertices = face.vertices

                # Грань отображается, если все вершины видимы
                if all(v.z > 0 for v in face_vertices) and len(face_vertices) >= 3:
                    screen_points = []
                    intensities = []
                    for i, v in enumerate(face_vertices):
                        factor = 300 / v.z
                        aspect = width / height
                        px = v.x * factor * self.base_scale * (1 / aspect if aspect > 1 else 1) + width / 2
                        py = v.y * factor * self.base_scale * (1 if aspect > 1 else aspect) + height / 2
                        screen_points.append(QPointF(px, py))
                        intensity = self.compute_phong_lighting(face_normals[i], original_vertices[i], inverse_transform)
                        intensities.append(intensity)
                    avg_depth = sum(v.z for v in face_vertices) / len(face_vertices)
                    self.cached_faces.append((avg_depth, face, screen_points, intensities))
        self.cached_faces.sort(reverse=True, key=lambda x: x[0])

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(35, 35, 35))

        if not self.cache_valid or self.cached_faces is None:
            self.prepare_faces_cache()
            self.cache_valid = True

        for depth, face, screen_points, intensities in self.cached_faces:
            polygon = QPolygonF(screen_points)

            # Выбор метода заливки
            if self.shading_mode == ShadingMode.MONOTONE:
                intensity = max(0.3, face.normal.dot(self.light_dir))
                color = QColor(
                    min(255, int(255 * intensity)),
                    min(255, int(105 * intensity)),
                    min(255, int(180 * intensity))
                )
                painter.setPen(QPen(color, 1))
                painter.setBrush(QBrush(color))
                painter.drawPolygon(polygon)
            elif self.shading_mode == ShadingMode.GOURAUD:
                gradient = QLinearGradient(screen_points[0], screen_points[2])
                base_color = QColor(255, 105, 180)  # Один базовый цвет
                for i, point in enumerate(screen_points):
                    intensity = intensities[i]
                    color = QColor(
                        min(255, int(base_color.red() * intensity)),
                        min(255, int(base_color.green() * intensity)),
                        min(255, int(base_color.blue() * intensity))
                    )
                    gradient.setColorAt(i / (len(screen_points) - 1), color)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(gradient))
                painter.drawPolygon(polygon)
            elif self.shading_mode == ShadingMode.PHONG:
                if screen_points:
                    x_sum = sum(p.x() for p in screen_points)
                    y_sum = sum(p.y() for p in screen_points)
                    count = len(screen_points)
                    center = QPointF(x_sum / count, y_sum / count)
                else:
                    center = QPointF(0, 0)

                gradient = QLinearGradient(center, screen_points[0])
                center_intensity = sum(intensities) / len(intensities)
                base_color = QColor(255, 105, 180)  # Один базовый цвет
                r = min(255, int(base_color.red() * center_intensity))
                g = min(255, int(base_color.green() * center_intensity))
                b = min(255, int(base_color.blue() * center_intensity))
                gradient.setColorAt(0, QColor(r, g, b))
                # Edge color (темнее)
                edge_r = int(r * 0.7)
                edge_g = int(g * 0.7)
                edge_b = int(b * 0.7)
                gradient.setColorAt(1, QColor(edge_r, edge_g, edge_b))
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(gradient))
                painter.drawPolygon(polygon)

        self.draw_light_source(painter)

    def draw_light_source(self, painter):
        light_pos = self.light_pos
        screen_pos = self.project_point_without_object_transform(light_pos)
        if screen_pos.x() != -1000 and screen_pos.y() != -1000:
            # Рисуем светящуюся точку
            painter.setPen(Qt.NoPen)
            radial_gradient = QRadialGradient(screen_pos, 10)
            radial_gradient.setColorAt(0, QColor(255, 255, 0, 200))
            radial_gradient.setColorAt(1, QColor(255, 255, 0, 0))
            painter.setBrush(QBrush(radial_gradient))
            painter.drawEllipse(screen_pos, 10, 10)
            
            # Рисуем контур
            painter.setPen(QPen(QColor(255, 255, 0), 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(screen_pos, 5, 5)
            
            # Подпись
            painter.setPen(QPen(QColor(255, 255, 0), 1))
            painter.drawText(screen_pos + QPoint(15, 5), "Источник света")

    def project_point(self, point):
        v_transformed = self.object_transform * point
        v_camera = self.apply_camera_transform(v_transformed)
        if v_camera.z > 0:
            factor = 300 / v_camera.z
            aspect_ratio = self.width() / self.height()
            px = v_camera.x * factor * self.base_scale * (
                1 / aspect_ratio if aspect_ratio > 1 else 1) + self.width() / 2
            py = v_camera.y * factor * self.base_scale * (1 if aspect_ratio > 1 else aspect_ratio) + self.height() / 2
            return QPoint(int(px), int(py))
        return QPoint(-1000, -1000)

    def project_point_without_object_transform(self, point):
        v_camera = self.apply_camera_transform(point)
        if v_camera.z > 0:
            factor = 300 / v_camera.z
            aspect_ratio = self.width() / self.height()
            px = v_camera.x * factor * self.base_scale * (
                1 / aspect_ratio if aspect_ratio > 1 else 1) + self.width() / 2
            py = v_camera.y * factor * self.base_scale * (1 if aspect_ratio > 1 else aspect_ratio) + self.height() / 2
            return QPoint(int(px), int(py))
        return QPoint(-1000, -1000)

    def apply_camera_transform(self, v):
        rot_x = Matrix4x4.rotation_x(self.camera_rot[0])
        rot_y = Matrix4x4.rotation_y(self.camera_rot[1])
        rot_z = Matrix4x4.rotation_z(self.camera_rot[2])
        rotation = rot_x * rot_y * rot_z
        translation = Matrix4x4.translation(-self.camera_pos.x, -self.camera_pos.y, -self.camera_pos.z)
        camera_transform = rotation * translation
        return camera_transform * v

    def auto_scale_view(self):
        if self.auto_scale:
            self.base_scale = min(self.width(), self.height()) / 600.0

    def resizeEvent(self, event):
        self.auto_scale_view()
        self.invalidate_cache()
        super().resizeEvent(event)

    def set_mirror(self, axis):
        if axis == 0:
            self.mirror_x = not self.mirror_x
        elif axis == 1:
            self.mirror_y = not self.mirror_y
        else:
            self.mirror_z = not self.mirror_z

        mirror_matrix = Matrix4x4.scaling(
            -1 if self.mirror_x else 1,
            -1 if self.mirror_y else 1,
            -1 if self.mirror_z else 1
        )
        self.object_transform = mirror_matrix
        self.invalidate_cache()
        self.update()

    def set_light_direction(self, x, y, z):
        self.light_dir = Vector3D(x, y, z).normalized()
        self.light_pos = self.light_dir * 300
        self.invalidate_cache()
        self.update()

    def rotate_letter(self, letter, axis, angle):
        letter.rotate(axis, angle)
        self.invalidate_cache()
        self.update()

    def scale_letter(self, letter, scale_factor):
        letter.set_scale(scale_factor)
        self.invalidate_cache()
        self.update()

    def set_shading_mode(self, mode):
        self.shading_mode = mode
        self.invalidate_cache()
        self.update()