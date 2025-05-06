import sys
import math
import numpy as np
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                               QLineEdit, QPushButton, QLabel, QHBoxLayout,
                               QMessageBox, QGroupBox, QScrollArea, QComboBox)
from PySide6.QtGui import QPainter, QPen, QColor, QPainterPath, QBrush, QFont
from PySide6.QtCore import Qt, QPointF, QSize

# Палитра
COLOR_PALETTE = [
    QColor("#4285F4"),  # Синий (Google)
    QColor("#EA4335"),  # Красный (Google)
    QColor("#FBBC05"),  # Желтый (Google)
    QColor("#34A853"),  # Зеленый (Google)
    QColor("#673AB7"),  # Фиолетовый (Material)
    QColor("#FF5722"),  # Оранжевый (Material)
    QColor("#009688"),  # Бирюзовый (Material)
    QColor("#795548")  # Коричневый (Material)
]


class ConesDataBase:
    """Класс для обработки данных и вычислений"""

    def __init__(self):
        self.functions = []
        # Список функций с описаниями
        self.available_functions = [
            ('-x/5', 'Линейная функция (-x/5)'),
            ('x', 'Линейная функция (x)'),
            ('math.exp(-x**2+math.cos(x))', 'Экспоненциальная с косинусом'),
            ('1/x', 'Гипербола (1/x)'),
            ('math.cos(x)/x', 'Синусоида'),
            ('math.sin(x)', 'Логарифм по основанию 2'),
            ('math.atan(math.exp(x)+7*x)', 'Арктангенс сложной функции'),
            ('(math.sin(x)/x', 'Функция sinc'),
            ('math.cosh(-0.5*x**3+math.log10(x))', 'Гиперболический косинус')
        ]

    def set_functions(self, funcs):
        """Установка активных функций"""
        self.functions = funcs.copy()

    def function_points(self, a, b, n):
        """
        - Для каждой функции из выбранных:
            - строит список из n точек на интервале [a, b]
            - каждая точка — это (x, f(x))
        - Защита от ошибок:
            - если значение функции слишком большое или случается ошибка (например, деление на 0),
              то значение заменяется на 0
        - Результат:
            - список списков точек: [[(x1, y1), (x2, y2), ...], [...], ...]
        """
        fvalues = []
        for function in self.functions:
            expr = function
            func = lambda x, e=expr: eval(e, {"math": math, "x": x})
            values = []
            np_args = np.linspace(a, b, num=n)
            args = np_args.tolist()
            for i in args:
                try:
                    if abs(func(i)) < 1e6:
                        values.append((i, func(i)))
                    else:
                        values.append((i, 0))
                except:
                    values.append((i, 0))
            fvalues.append(values.copy())
            values.clear()
        return fvalues

    def define_data(self, used_points):
        """
        - Принимает все точки функций [(x, f(x))] — список списков
        - Цель:
            - Собрать общие X (все одинаковые по сути)
            - Разделить значения функций на положительные и отрицательные
              (чтобы потом рисовать отдельно вверх и вниз)
        - Возвращает:
            - x — массив значений X
            - y_pos — сумма всех положительных значений функций в каждой точке X
            - y_neg — сумма всех отрицательных значений функций в каждой точке X
        """
        x = [];
        y_pos = [];
        y_neg = []
        for func_points in used_points:
            for i in range(0, len(func_points)):
                if i == len(x):
                    x.append(func_points[i][0])
                if i == len(y_neg):
                    y_pos.append(0)
                    y_neg.append(0)
                if func_points[i][1] > 0:
                    y_pos[i] += func_points[i][1]
                if func_points[i][1] < 0:
                    y_neg[i] += func_points[i][1]
        return x, y_pos, y_neg

    def graph_points(self, a, b, n):
        """
        - Похож на function_points, но:
            - Для каждой точки x собирает сразу значения ВСЕХ функций
        - Пример:
            - В точке x = 1: [(1, f1(1)), (1, f2(1)), (1, f3(1))]
        - Это нужно для отрисовки конусов — где на каждой координате x строятся все значения вместе
        """
        fvalues = []
        np_args = np.linspace(a, b, num=n)
        args = np_args.tolist()
        for i in args:
            values = []
            for function in self.functions:
                expr = function
                func = lambda x, e=expr: eval(e, {"math": math, "x": x})
                try:
                    if abs(func(i)) < 1e6:
                        values.append((i, func(i)))
                    else:
                        values.append((i, 0))
                except:
                    values.append((i, 0))
            fvalues.append(values.copy())
            values.clear()
        return fvalues

    def define_graph(self, used_points):
        """
        - Вход: результат из graph_points — список точек с несколькими функциями в каждой
        - Задача:
            - Подготовить данные по каждой точке x:
                - Список значений всех функций (высоты)
                - Сумма положительных значений (нужна для высоты вверх)
                - Сумма отрицательных значений (для вниз)
        - Результат:
            - список кортежей: (x, [f1, f2, ...], sum_pos, sum_neg)
        """
        cones = []
        try:
            for points in used_points:
                cones_height = []
                sum_neg = 0
                sum_pos = 0
                for point in points:
                    cones_height.append(point[1])
                    if point[1] >= 0:
                        sum_pos += point[1]
                    else:
                        sum_neg += point[1]
                cones.append((points[0][0], cones_height, sum_pos, sum_neg))
        finally:
            return cones

    def define_cones(self, points):
        """
        - Самое мясо. Из данных с суммами строит параметры 'конусов':
            - Высота каждой функции по порядку (наращивается в зависимости от предыдущих)
            - Радиус считается пропорционально её высоте
        - Как это работает:
            - Если функция положительная:
                - Она будет отложена вверх, над предыдущими положительными
            - Если отрицательная:
                - Она будет отложена вниз, под предыдущими отрицательными
        - Расчёт:
            - Сначала считается 'общая высота' (sum_pos или sum_neg)
            - Далее для каждой функции:
                - Считается, на какой высоте она начинается
                - Сколько занимает по высоте
                - Вычисляется радиус: чем выше — тем шире

        - Результат:
            - [(x, [(start, height, radius), (start, height, radius), ...]), ...]
            — т.е. для каждой точки по X массив конусов
        """
        cones_data = []
        digits_number = 3
        for group in points:
            arg = group[0]
            sum_pos = group[2]
            sum_neg = group[3]
            dots = group[1]
            cone_data = []
            for i in range(len(dots)):
                if dots[i] >= 0:
                    cone_height = sum_pos
                else:
                    cone_height = sum_neg
                height = 0
                radius = 0.5
                if cone_height != 0:
                    ratio = radius / cone_height
                else:
                    ratio = 1
                for j in range(i):
                    if dots[i] >= 0 and dots[j] >= 0:
                        height += dots[j]
                        cone_height -= dots[j]
                    if dots[i] < 0 and dots[j] < 0:
                        height += dots[j]
                        cone_height -= dots[j]
                radius = round(ratio * cone_height, digits_number)
                cone_data.append((round(height, digits_number),
                                  round(cone_height, digits_number),
                                  radius))
            cones_data.append((arg, cone_data))
        return cones_data


class PlotWidget(QWidget):
    """Виджет для отображения графиков"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale_x, self.scale_y = None, None
        self.vert_lines = 9
        self.cones_db = ConesDataBase()
        self.functions = []
        self.color_index = 0

        self.funcs = None
        self.masses = None
        self.arg_funcs = None
        self.cones_params = None
        self.cones = None
        self.cell_height = 15
        self.cell_width = 20
        self.razmetka = 16

        # Настройки внешнего вида
        self.setStyleSheet("""
            background-color: #FFFFFF;
            border: 1px solid #E0E0E0;
            border-radius: 4px;
        """)

    def update_data(self, functions, a, b, n):
        """Обновляет данные графика:
        - принимает выбранные функции и параметры (a, b, n)
        - вызывает все нужные методы из ConesDataBase
        - обновляет масштаб и перерисовывает виджет"""
        self.functions = functions
        self.cones_db.set_functions(functions)

        # Вычисление данных
        self.funcs = self.cones_db.function_points(a, b, n)
        self.masses = self.cones_db.define_data(self.funcs)
        self.arg_funcs = self.cones_db.graph_points(a, b, n)
        self.cones_params = self.cones_db.define_graph(self.arg_funcs)
        self.cones = self.cones_db.define_cones(self.cones_params)

        # Настройка масштаба
        self.cell_height = n + 1
        self.cell_width = self.vert_lines + 1
        self.scale_x = 480 / self.cell_height
        self.scale_y = 640 / self.cell_width

        self.update()

    def paintEvent(self, event):
        """Отрисовка виджета"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if len(self.functions) > 0:
            try:
                self.draw_grid(painter)
                self.draw_axes(painter)
                self.draw_cones(painter, self.cones)
                self.draw_legend(painter, self.cones)
            except Exception as e:
                QMessageBox.warning(self, "Ошибка отрисовки", f"Произошла ошибка: {str(e)}")

    def crosses_line(self):
        """Вычисление положения нулевой линии"""
        minw = min(min(self.masses[2]), 0)
        maxw = max(max(self.masses[1]), 0)
        cross_y = ((0 - minw) / (maxw - minw)) * (640 - 2 * self.scale_y) + self.scale_y
        return cross_y

    def draw_grid(self, painter):
        """Отрисовка сетки"""
        scale_x, scale_y = self.scale_x, self.scale_y
        if scale_y < self.razmetka:
            scale_y = self.razmetka
        if scale_x < self.razmetka:
            scale_x = self.razmetka

        w_width, w_height = 640, 480

        # Сетка
        painter.setPen(QPen(QColor("#F0F0F0"), 1, Qt.DotLine))
        px = 0
        while px <= 640:
            painter.drawLine(px, 0, px, w_height)
            px += scale_y

        py = 0
        while py <= 480:
            painter.drawLine(0, py, w_width, py)
            py += scale_x

        # Границы
        painter.setPen(QPen(QColor("#E0E0E0"), 1.5, Qt.SolidLine))
        painter.drawLine(640, 0, 640, 480)
        painter.drawLine(0, 480, 640, 480)
        painter.drawLine(0, 0, 0, 480)
        painter.drawLine(0, 0, 640, 0)

    def draw_axes(self, painter):
        """Отрисовка осей"""
        scale_x, scale_y = self.scale_x, self.scale_y
        crosses = self.crosses_line()

        minw = min(min(self.masses[2]), 0)
        maxw = max(max(self.masses[1]), 0)
        used_width = 640 - 2 * scale_y

        minh = min(self.masses[0])
        maxh = max(self.masses[0])
        used_height = 480 - 1 * scale_x

        cross_y = crosses

        # Ось Y
        painter.setPen(QPen(Qt.black, 2))
        painter.drawLine(cross_y, 0, cross_y, 480)

        # Подписи оси Y
        nps_y = np.linspace(minw, maxw, num=self.vert_lines)
        cells_y = nps_y.tolist()

        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)

        painter.setPen(QPen(QColor("#FFFFFF"), 1))

        for i in range(len(cells_y)):
            py = scale_y * (1 + i)
            y = cells_y[i]
            painter.drawText(py - 7, 490, f"{round(y, 2)}")

        # Подписи оси X
        cell_scale_x = len(self.masses[0])
        npx_s = np.linspace(minh, maxh, num=cell_scale_x)
        x_s = npx_s.tolist()

        for i in range(len(x_s)):
            px = used_height - scale_x * i
            x = x_s[i]
            painter.drawText(650, px + 3, f"{round(x, 2)}")

    def draw_cones(self, painter, cones_data):
        """
            Отрисовывает псевдо-3D конусы для каждой точки X и каждой функции
            Как работает:
            1. Считаем, где находится "ось X" (cross_y) — это базовая линия, от которой идут конусы вверх/вниз.
            2. Для каждой точки X:
               - рассчитываем вертикальное положение на экране (px)
               - для каждой функции:
                   • определяем цвет
                   • считаем вершину и основание конуса (apex, base)
                   • рассчитываем радиус и направление (вверх или вниз)
                   • рисуем треугольный/круглый конус с помощью Bezier-кривых
            3. Если функция "уходит вниз" — рисуем вогнутую часть основания
            4. Добавляем контуры (черные линии) по краям, чтобы конус смотрелся объёмнее
            """
        scale_x, scale_y = self.scale_x, self.scale_y
        crosses = self.crosses_line()
        cross_y = crosses

        minw_minus = min(min(self.masses[2]), 0)
        maxw_minus = 0
        maxw_plus = max(max(self.masses[1]), 0)
        minw_plus = 0

        used_height = 480 - 1 * scale_x
        curve_scale = 30

        for i in range(len(cones_data)):
            cones = cones_data[i]
            px = used_height - i * scale_x
            color_num = 0

            first_below_zero = True
            is_there_above_zero = False
            for cone in cones[1]:
                if cone[0] + cone[1] > 0:
                    is_there_above_zero = True

            for cone in cones[1]:
                color = COLOR_PALETTE[color_num % len(COLOR_PALETTE)]
                painter.setPen(QPen(color, 1))

                height = cone[0];
                cone_height = cone[1];
                radius = cone[2]
                direction = 1 if (height + cone_height) > 0 else -1

                y_h = height
                y_ch = height + cone_height

                if direction < 0:
                    try:
                        h = ((y_h - maxw_minus) / (minw_minus - maxw_minus)) * (cross_y - scale_y) * direction
                        ch = ((y_ch - maxw_minus) / (minw_minus - maxw_minus)) * (cross_y - scale_y) * direction
                    except:
                        h = 0;
                        ch = 0
                else:
                    try:
                        h = ((y_h - minw_plus) / (maxw_plus - minw_plus)) * (640 - scale_y - cross_y)
                        ch = ((y_ch - minw_plus) / (maxw_plus - minw_plus)) * (640 - scale_y - cross_y)
                    except:
                        h = 0;
                        ch = 0

                apex_y = cross_y + ch
                apex_x = px
                base_center_y = cross_y + h
                base_left_x = px - radius * scale_x
                base_right_x = px + radius * scale_x
                control_y = base_center_y + radius * direction * curve_scale

                path = QPainterPath()
                path.moveTo(apex_y, apex_x)
                path.lineTo(base_center_y, base_left_x)
                path.quadTo(control_y, px, base_center_y, base_right_x)
                path.closeSubpath()

                brush = QBrush(color)
                painter.fillPath(path, brush)

                painter.setPen(QPen(Qt.black, 1))
                painter.drawLine(apex_y, apex_x, base_center_y, base_left_x)
                painter.drawLine(apex_y, apex_x, base_center_y, base_right_x)

                if cone_height < 0:
                    painter.drawPath(path)
                if cone_height >= 0 or (first_below_zero and not is_there_above_zero):
                    control_y_neg = base_center_y + radius * direction * (-curve_scale)
                    painter.setPen(QPen(color, 1))

                    path = QPainterPath()
                    path.moveTo(base_center_y, base_left_x)
                    path.quadTo(control_y, px, base_center_y, base_left_x)
                    painter.drawPath(path)

                    path = QPainterPath()
                    path.moveTo(base_center_y, base_left_x)
                    path.quadTo(control_y, px, base_center_y, base_right_x)
                    path.quadTo(control_y_neg, px, base_center_y, base_left_x)
                    path.closeSubpath()
                    painter.fillPath(path, brush)

                    path = QPainterPath()
                    path.moveTo(base_center_y, base_left_x)
                    path.quadTo(control_y_neg, px, base_center_y, base_right_x)
                    painter.setPen(QPen(Qt.black, 1))
                    painter.drawPath(path)

                if first_below_zero and cone_height < 0:
                    first_below_zero = False
                color_num += 1

    def draw_legend(self, painter, cones_data):
        """Отрисовка легенды"""
        if not self.functions or not cones_data:
            return

        legend_width, legend_height = 700, 50
        color_num = 0

        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)

        # Рамка легенды
        painter.setPen(QPen(QColor("#E0E0E0"), 1))
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
        painter.drawRoundedRect(legend_width - 10, legend_height - 20,
                                250, 20 + len(self.functions) * 20, 5, 5)

        for i, function in enumerate(self.functions):
            color = COLOR_PALETTE[color_num % len(COLOR_PALETTE)]
            painter.setPen(QPen(color, 3))
            painter.drawLine(legend_width, legend_height, legend_width + 20, legend_height)

            # Поиск описания функции
            func_desc = next((desc for expr, desc in self.cones_db.available_functions
                              if expr == function), function)

            painter.setPen(QPen(Qt.black, 1))
            painter.drawText(legend_width + 30, legend_height + 5, func_desc)
            legend_height += 20
            color_num += 1


class FunctionSelector(QGroupBox):
    """Виджет для выбора функций"""

    def __init__(self, cones_db, parent=None):
        super().__init__("Выберите функции", parent)
        self.cones_db = cones_db
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)

        self.checkboxes = []
        for i, (expr, desc) in enumerate(self.cones_db.available_functions):
            checkbox = QPushButton(desc)
            checkbox.setCheckable(True)
            checkbox.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 5px;
                    border: 1px solid #E0E0E0;
                    border-radius: 3px;
                    background-color: #FFFFFF;
                    color: #000000;
                }
                QPushButton:checked {
                    background-color: #2196F3;
                    border: 1px solid #1976D2;
                    color: white;
                }
            """)
            self.checkboxes.append(checkbox)
            self.scroll_layout.addWidget(checkbox)

        self.scroll.setWidget(self.scroll_widget)
        self.layout.addWidget(self.scroll)

    def get_selected_functions(self):
        """Получение выбранных функций"""
        selected = []
        for i, checkbox in enumerate(self.checkboxes):
            if checkbox.isChecked():
                selected.append(self.cones_db.available_functions[i][0])
        return selected


class MainWindow(QMainWindow):
    """Главное окно приложения"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Графический анализатор функций")
        self.setMinimumSize(1200, 800)

        # Центральный виджет и основной layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Виджет для выбора функций
        self.cones_db = ConesDataBase()
        self.function_selector = FunctionSelector(self.cones_db)
        self.function_selector.setFixedWidth(300)
        main_layout.addWidget(self.function_selector)

        # Правая часть (график + управление)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Виджет для рисования
        self.plot_widget = PlotWidget()
        right_layout.addWidget(self.plot_widget, stretch=1)

        # Панель управления
        control_group = QGroupBox("Параметры построения")
        control_layout = QHBoxLayout(control_group)

        # Поля ввода
        self.a_input = QLineEdit()
        self.a_input.setPlaceholderText("Начало интервала")
        self.a_input.setText("-5")
        self.a_input.setStyleSheet("padding: 5px;")

        self.b_input = QLineEdit()
        self.b_input.setPlaceholderText("Конец интервала")
        self.b_input.setText("5")
        self.b_input.setStyleSheet("padding: 5px;")

        self.n_input = QLineEdit()
        self.n_input.setPlaceholderText("Количество точек")
        self.n_input.setText("20")
        self.n_input.setStyleSheet("padding: 5px;")

        # Кнопка построения
        btn_draw = QPushButton("Построить график")
        btn_draw.setStyleSheet("""
            QPushButton {
                background-color: #4285F4;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3367D6;
            }
        """)
        btn_draw.clicked.connect(self.update_diagram)

        # Добавление элементов на панель управления
        control_layout.addWidget(QLabel("От:"))
        control_layout.addWidget(self.a_input)
        control_layout.addWidget(QLabel("До:"))
        control_layout.addWidget(self.b_input)
        control_layout.addWidget(QLabel("Точек:"))
        control_layout.addWidget(self.n_input)
        control_layout.addWidget(btn_draw)

        right_layout.addWidget(control_group)
        main_layout.addWidget(right_panel, stretch=1)

    def update_diagram(self):
        """Обновление диаграммы"""
        try:
            functions = self.function_selector.get_selected_functions()
            if not functions:
                QMessageBox.warning(self, "Ошибка", "Не выбрано ни одной функции!")
                return

            a = float(self.a_input.text())
            b = float(self.b_input.text())
            n = int(self.n_input.text())

            if a >= b:
                QMessageBox.warning(self, "Ошибка", "Начало интервала должно быть меньше конца!")
                return

            if n <= 1:
                QMessageBox.warning(self, "Ошибка", "Количество точек должно быть больше 1!")
                return

            self.plot_widget.update_data(functions, a, b, n)
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите корректные числовые значения!")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Произошла ошибка: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Установка стиля для всего приложения
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())