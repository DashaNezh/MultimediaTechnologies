from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QPushButton, QScrollArea, QSizePolicy, QGroupBox, QTabWidget
from PySide6.QtCore import Qt
from scene import SceneWidget
from letters import ShadingMode, DisplayMode, Vector3D, Matrix4x4
import math
from enum import Enum

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Визуализатор")
        self.setGeometry(100, 100, 1200, 900)
        
        # Создаем главный виджет и устанавливаем темный фон
        main_widget = QWidget()
        main_widget.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                border: 2px solid #3c3c3c;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #ff69b4;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
            QPushButton {
                background-color: #3c3c3c;
                border: 1px solid #ff69b4;
                border-radius: 4px;
                padding: 5px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #ff69b4;
            }
            QPushButton:checked {
                background-color: #ff69b4;
            }
            QSlider::groove:horizontal {
                border: 1px solid #ff69b4;
                height: 8px;
                background: #3c3c3c;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #ff69b4;
                border: 1px solid #ff69b4;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
            QLabel {
                color: #ffffff;
            }
        """)
        
        self.setCentralWidget(main_widget)
        
        # Создаем основной layout
        main_layout = QHBoxLayout(main_widget)
        
        # Левая панель с 3D сценой
        scene_container = QWidget()
        scene_layout = QVBoxLayout(scene_container)
        self.scene = SceneWidget()
        scene_layout.addWidget(self.scene)
        main_layout.addWidget(scene_container, stretch=3)
        
        # Правая панель с контролами
        controls_container = QWidget()
        controls_layout = QVBoxLayout(controls_container)
        controls_layout.setSpacing(15)
        controls_layout.setContentsMargins(10, 10, 10, 10)
        
        # Создаем вкладки для разных групп контролов
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3c3c3c;
                background: #2b2b2b;
            }
            QTabBar::tab {
                background: #3c3c3c;
                color: #ffffff;
                padding: 8px 12px;
                border: 1px solid #ff69b4;
            }
            QTabBar::tab:selected {
                background: #ff69b4;
            }
        """)
        
        # Вкладка "Буквы"
        letters_tab = QWidget()
        letters_layout = QVBoxLayout(letters_tab)
        self.create_letter_controls(letters_layout, "Буква Д", 'd')
        self.create_letter_controls(letters_layout, "Буква Н", 'n')
        tab_widget.addTab(letters_tab, "Буквы")
        
        # Вкладка "Вращение"
        rotation_tab = QWidget()
        rotation_layout = QVBoxLayout(rotation_tab)
        self.create_rotation_controls(rotation_layout, "Вращение буквы Д", 'd')
        self.create_rotation_controls(rotation_layout, "Вращение буквы Н", 'n')
        self.create_transform_controls(rotation_layout, "Управление камерой",
                                     self.rotate_camera, None)
        tab_widget.addTab(rotation_tab, "Вращение")
        
        # Вкладка "Заливка"
        shading_tab = QWidget()
        shading_layout = QVBoxLayout(shading_tab)
        self.create_shading_controls(shading_layout)
        tab_widget.addTab(shading_tab, "Заливка")
        
        # Вкладка "Освещение"
        light_tab = QWidget()
        light_layout = QVBoxLayout(light_tab)
        self.create_light_controls(light_layout)
        tab_widget.addTab(light_tab, "Освещение")
        
        controls_layout.addWidget(tab_widget)
        
        # Обернуть панель управления в QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidget(controls_container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumWidth(400)
        scroll_area.setStyleSheet("background: transparent;")

        # Кнопка сброса вне скролла
        reset_btn = QPushButton("Сбросить настройки")
        reset_btn.setMinimumHeight(40)
        reset_btn.clicked.connect(self.reset_view)
        # Обернем в отдельный layout для выравнивания по низу
        right_panel = QVBoxLayout()
        right_panel.addWidget(scroll_area)
        right_panel.addWidget(reset_btn)
        right_panel.setStretch(0, 1)
        right_panel.setStretch(1, 0)
        main_layout.addLayout(right_panel, stretch=1)

    def create_letter_controls(self, layout, title, prefix):
        group = QGroupBox(title)
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(8)

        for param, text in [('height', 'Высота'), ('width', 'Ширина'), ('depth', 'Глубина')]:
            slider = QSlider(Qt.Horizontal)
            slider.setRange(10, 200)
            slider.setValue(getattr(self.scene, f"{prefix}_letter").__dict__[param])
            slider.valueChanged.connect(lambda v, p=param, pr=prefix: self.update_letter_param(pr, p, v))

            label = QLabel(text)
            label.setAlignment(Qt.AlignCenter)

            group_layout.addWidget(label)
            group_layout.addWidget(slider)

        scale_slider = QSlider(Qt.Horizontal)
        scale_slider.setRange(50, 200)
        scale_slider.setValue(100)
        scale_slider.valueChanged.connect(lambda v, pr=prefix: self.update_letter_scale(pr, v))

        scale_label = QLabel("Масштаб")
        scale_label.setAlignment(Qt.AlignCenter)

        group_layout.addWidget(scale_label)
        group_layout.addWidget(scale_slider)

        layout.addWidget(group)

    def create_rotation_controls(self, layout, title, letter_prefix):
        group = QGroupBox(title)
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(10)

        for axis, text in [(0, "X"), (1, "Y"), (2, "Z")]:
            axis_group = QGroupBox(text)
            axis_layout = QHBoxLayout(axis_group)
            axis_layout.setSpacing(5)

            btn_plus = QPushButton("+")
            btn_plus.setMinimumSize(50, 30)
            btn_plus.clicked.connect(lambda _, a=axis, p=letter_prefix: self.rotate_letter(p, a, 10))

            btn_minus = QPushButton("-")
            btn_minus.setMinimumSize(50, 30)
            btn_minus.clicked.connect(lambda _, a=axis, p=letter_prefix: self.rotate_letter(p, a, -10))

            axis_layout.addWidget(btn_minus)
            axis_layout.addWidget(btn_plus)
            group_layout.addWidget(axis_group)

        layout.addWidget(group)

    def create_transform_controls(self, layout, title, rotate_cb, scale_cb):
        group = QGroupBox(title)
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(10)

        if rotate_cb:
            for axis, text in [(0, "X"), (1, "Y"), (2, "Z")]:
                axis_group = QGroupBox(text)
                axis_layout = QHBoxLayout(axis_group)
                axis_layout.setSpacing(5)

                btn_plus = QPushButton("+")
                btn_plus.setMinimumSize(50, 30)
                btn_plus.clicked.connect(lambda _, a=axis: rotate_cb(a, 10))

                btn_minus = QPushButton("-")
                btn_minus.setMinimumSize(50, 30)
                btn_minus.clicked.connect(lambda _, a=axis: rotate_cb(a, -10))

                axis_layout.addWidget(btn_minus)
                axis_layout.addWidget(btn_plus)
                group_layout.addWidget(axis_group)

        layout.addWidget(group)

    def create_mirror_controls(self, layout):
        group = QGroupBox("Зеркальное отображение")
        group_layout = QHBoxLayout(group)
        group_layout.setSpacing(10)

        for axis, text in [(0, "X"), (1, "Y")]:
            btn = QPushButton(f"Зеркало {text}")
            btn.setCheckable(True)
            btn.setMinimumSize(100, 30)
            btn.clicked.connect(lambda _, a=axis: self.scene.set_mirror(a))
            group_layout.addWidget(btn)

        layout.addWidget(group)

    def create_light_controls(self, layout):
        group = QGroupBox("Настройки освещения")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(10)

        for axis, text in [('x', 'X'), ('y', 'Y'), ('z', 'Z')]:
            axis_group = QGroupBox(f"Направление {text}")
            axis_layout = QVBoxLayout(axis_group)
            
            slider = QSlider(Qt.Horizontal)
            slider.setRange(-180, 180)
            slider.setValue(30 if axis == 'z' else 45 if axis == 'x' else 45)
            slider.valueChanged.connect(lambda v, a=axis: self.update_light(a, v))
            
            axis_layout.addWidget(slider)
            group_layout.addWidget(axis_group)

        layout.addWidget(group)

    def create_shading_controls(self, layout):
        group = QGroupBox("Метод закраски")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(8)
        for mode in ShadingMode:
            btn = QPushButton(mode.value)
            btn.setCheckable(True)
            btn.setMinimumHeight(35)
            btn.setChecked(mode == ShadingMode.PHONG)
            btn.clicked.connect(lambda _, m=mode: self.update_shading(m))
            group_layout.addWidget(btn)
        layout.addWidget(group)

    def update_letter_param(self, prefix, param, value):
        letter = getattr(self.scene, f"{prefix}_letter")
        setattr(letter, param, value)
        letter.update_geometry()
        self.scene.invalidate_cache()
        self.scene.update()

    def update_letter_scale(self, prefix, value):
        letter = getattr(self.scene, f"{prefix}_letter")
        scale_factor = value / 100.0
        self.scene.scale_letter(letter, scale_factor)

    def rotate_letter(self, letter_prefix, axis, angle):
        letter = getattr(self.scene, f"{letter_prefix}_letter")
        self.scene.rotate_letter(letter, axis, angle)

    def rotate_camera(self, axis, angle):
        self.scene.camera_rot[axis] += angle
        self.scene.invalidate_cache()
        self.scene.update()

    def update_light(self, axis, value):
        rad = math.radians(value)
        current = [self.scene.light_dir.x, self.scene.light_dir.y, self.scene.light_dir.z]

        if axis == 'x':
            current[0] = math.sin(rad) * 0.707 + 0.5
            current[1] = 0.5
            current[2] = -math.cos(rad) * 0.707 - 0.5
        elif axis == 'y':
            current[0] = 0.5
            current[1] = math.sin(rad) * 0.707 + 0.5
            current[2] = -math.cos(rad) * 0.707 - 0.5
        else:
            current[0] = math.cos(rad) * 0.5
            current[1] = math.sin(rad) * 0.5
            current[2] = -1

        self.scene.set_light_direction(current[0], current[1], current[2])

    def update_shading(self, mode):
        self.scene.set_shading_mode(mode)
        for btn in self.findChildren(QPushButton):
            if btn.text() in [m.value for m in ShadingMode]:
                btn.setChecked(btn.text() == mode.value)

    def reset_view(self):
        self.scene.camera_pos = Vector3D(0, 0, -400)
        self.scene.camera_rot = [0, 0, 0]
        self.scene.d_letter.transform = Matrix4x4.rotation_x(180)
        self.scene.d_letter.scale = 1.0
        self.scene.n_letter.transform = Matrix4x4.rotation_x(180)
        self.scene.n_letter.scale = 1.0
        self.scene.object_transform = Matrix4x4()
        self.scene.base_scale = 2.0
        self.scene.mirror_x = False
        self.scene.mirror_y = False
        self.scene.mirror_z = False
        self.scene.set_light_direction(0.5, 0.5, -1)
        self.scene.invalidate_cache()
        self.scene.update()