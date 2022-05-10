import sys
from modules.General import *
from PyQt5.QtWidgets import QApplication, QMainWindow
from UI.UI_MapAppMainWindow import Ui_MapAppMainWindow
from PyQt5.Qt import QPixmap, QImage, Qt
# from Modules.EasyThreadsQt import queue_thread_qt


START_SCALE = 13
START_POS = [37.588392, 55.734036]

MAP_TYPES = ['map', 'sat']
GO_NAMES_TYPE = 'skl'  # GO - geographic objects
TRAFFIC_JAMS_TYPE = 'trf'

ERROR_STYLESHEET = '*{color:red;}'
INFO_LABEL_STYLESHEET = '*{color:black;}'

TOPONYM_NOT_FOUND_ERROR_MSG = 'Объект не найден'
BAD_RESPONSE_ERROR = 'Нет ответа от сервера'


class MapApp(Ui_MapAppMainWindow, QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Назначаем функции на элементы UI
        self.map_type_box.currentIndexChanged.connect(self.update_map_type)
        self.post_address_box.currentIndexChanged.connect(self.update_address)
        self.go_names_btn.clicked.connect(self.update_map_type)
        self.traffic_jams_btn.clicked.connect(self.update_map_type)
        self.find_obj_btn.clicked.connect(self.get_object)
        self.reset_result_btn.clicked.connect(self.reset_result)

        # Пусть карта позиционируется на Москве, дабы было понятно что
        # программа работает
        self.map_pos = START_POS  # Параметр ll
        self.map_type = 'map'     # Параметр l
        self.scale = START_SCALE  # Параметр z
        self.tags = []            # Параметр pt
        self.address = None
        self.post_address = None
        self.toponym = None

        self.pix_maps = {}  # Словарь с уже загруженными ранее картинками

        self.override_map_params()

    def reset_result(self):
        self.map_pos = START_POS
        self.tags = []
        self.address = None
        self.post_address = None
        self.address_label.setText('')
        self.toponym = None
        self.override_map_params()

    def get_pix_map(self, map_type=None, map_pos=None, scale=None, tags=None):
        """Получение изображения карты."""

        # Если в метод не переданы какие-либо параметры, используем текущие
        # параметры карты
        if map_type is None:
            map_type = self.map_type
        if map_pos is None:
            map_pos = self.map_pos
        if scale is None:
            scale = self.scale
        if tags is None:
            tags = self.tags

        map_params = {
            "l": map_type,
            'll': ','.join(map(str, map_pos)),
            'z': str(scale),
            'pt': '~'.join(map(str, tags))
        }
        key = tuple(map_params.values())
        pix_map = self.pix_maps.get(key)
        if pix_map is None:
            response = perform_request(MAP_API_SERVER, params=map_params)
            image = QImage().fromData(response.content)
            pix_map = QPixmap().fromImage(image)
            self.pix_maps[key] = pix_map
        return pix_map

    def override_map_params(self):
        """Изменение параметров карты."""
        self.map_label.setPixmap(self.get_pix_map())

    def keyPressEvent(self, *args, **kwargs):
        key = args[0].key()
        if key == Qt.Key_PageUp:
            if self.scale < 17:
                self.scale += 1
            self.override_map_params()
        elif key == Qt.Key_PageDown:
            if self.scale > 0:
                self.scale -= 1
            self.override_map_params()

    def update_map_type(self):
        map_type = [MAP_TYPES[self.map_type_box.currentIndex()]]
        if self.go_names_btn.isChecked():
            map_type += [GO_NAMES_TYPE]
        if self.traffic_jams_btn.isChecked():
            map_type += [TRAFFIC_JAMS_TYPE]
        self.map_type = ','.join(map_type)
        self.override_map_params()

    def update_address(self):
        if self.post_address_box.currentIndex():
            self.set_address_label()
        else:
            self.set_address_label(self.post_address)

    def get_object(self):
        try:
            toponyms = get_toponyms(self.object_input.text())
            if len(toponyms) == 0:
                self.print_error(TOPONYM_NOT_FOUND_ERROR_MSG)
            else:
                self.toponym = toponyms[0]
                self.map_pos = get_pos_by_toponym(self.toponym)
                self.tags.append(f'{",".join(map(str, self.map_pos))},comma')
                self.address = get_address_by_toponym(self.toponym)
                self.post_address = get_post_address_by_toponym(self.toponym)
                self.set_address_label(self.post_address)
                self.clear_info_label()
                self.override_map_params()
        except RequestError:
            self.print_error(BAD_RESPONSE_ERROR)

    def print_error(self, msg):
        self.info_label.setStyleSheet(ERROR_STYLESHEET)
        self.info_label.setText(msg)

    def clear_info_label(self):
        self.info_label.setStyleSheet(INFO_LABEL_STYLESHEET)
        self.info_label.setText('')

    def set_address_label(self, post_address=None):
        if post_address and not self.post_address_box.currentIndex():
            self.address_label.setText(f'{self.address}, почтовый адрес:'
                                       f' {self.post_address}')
        else:
            self.address_label.setText(self.address)


app = QApplication(sys.argv)
map_app = MapApp()
map_app.show()
sys.exit(app.exec_())