from PIL import Image, ImageQt
import os
import sys
import h5py
import codecs

from PyQt6.QtCore import Qt
from PyQt6.QtGui import (QAction, QStandardItemModel, QStandardItem, QFont, QPixmap, QIntValidator)
from PyQt6.QtWidgets import (QApplication, QMenu, QMainWindow, QWidget, QFileDialog, QTreeView, 
                            QHBoxLayout, QVBoxLayout, QPushButton, QTabWidget, QTableWidget, QAbstractItemView,
                            QTableWidgetItem, QHeaderView, QGroupBox, QLineEdit, QLabel)
from numpy import ndarray

class FileTreeItem(QStandardItem):
    depth = 0
    path = "/"

    def __init__(self, text):
        super().__init__(text)


class MainWindow(QMainWindow):
    full_filename = ""

    def __init__(self):
        super().__init__()
        self.resize(800, 600)
        self.setWindowTitle('HDF Viewer')

        # create menu bar
        menu_bar = self.menuBar()
        file_menu = QMenu('File', self)
        edit_menu = QMenu('Edit', self)
        settings_menu = QMenu('Settings', self)
        help_menu = QMenu('Help', self)
        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(edit_menu)
        menu_bar.addMenu(settings_menu)
        menu_bar.addMenu(help_menu)
        self.setMenuBar(menu_bar)

        o_file = QAction('Open', self)
        c_file = QAction('Close', self)
        o_file.setShortcut('Ctrl+O')
        file_menu.addActions([o_file, c_file])

        # create attributes area
        layout = QHBoxLayout()
        struct_opened_file = QTreeView()
        struct_opened_file.setHeaderHidden(True)
        struct_opened_file.setMaximumWidth(250)
        struct_opened_file.setMinimumWidth(150)
        model = QStandardItemModel()
        struct_opened_file.setModel(model)
        root_item = model.invisibleRootItem()

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(['Name','Type','Array Size','Value'])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setFont(QFont(QFont().defaultFamily(),12,QFont.Weight.Bold, False))
        table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        table.setFont(QFont(QFont().defaultFamily(),12,1,False))
        table.verticalHeader().hide()

        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(table, "Attribute Info")
        self.tab_widget.addTab(QWidget(), "Other")
        self.tab_widget.hide()

        layout_for_item_info = QHBoxLayout()
        layout_for_item_info.addWidget(self.tab_widget)
        layout_for_item_info.setContentsMargins(2,2,2,2)

        container_for_item_info = QGroupBox()
        container_for_item_info.setLayout(layout_for_item_info)

        layout.addWidget(struct_opened_file)
        layout.addWidget(container_for_item_info)
        layout.setStretch(0, 1)
        layout.setStretch(1, 3)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)


        struct_opened_file.clicked.connect(lambda: self.display_info_about_item(
            model.itemFromIndex(struct_opened_file.currentIndex()), self.tab_widget))
        struct_opened_file.doubleClicked.connect(lambda: self.show_window_data(
            model.itemFromIndex(struct_opened_file.currentIndex())))

        o_file.triggered.connect(lambda: self.open_file(root_item))
        c_file.triggered.connect(lambda: self.close_file(root_item, self.tab_widget))

    def open_file(self, root_item:QStandardItem):
        self.full_filename = QFileDialog.getOpenFileName(self,
                    'Select file',
                    os.getcwd(),
                    'HDF (*.h5 *.he5 *.hdf5 *.h4 *.he4 *.hdf4 *.hdf)')
        if self.full_filename[0]:
            with h5py.File(self.full_filename[0]) as file:
                filename = FileTreeItem(os.path.basename(self.full_filename[0]))
                filename.setFont(QFont(QFont().defaultFamily(),12,QFont.Weight.Medium,True))
                filename.setEditable(False)
                root_item.appendRow(filename)

                self.create_tree_file(file, filename)


    def create_tree_file(self, parent_element:h5py.File, parent_item:FileTreeItem, i=0):
        i = i + 1
        keys = list(parent_element.keys())
        if (keys != []):
            for item in parent_element.items():

                hdf_item = FileTreeItem(item[0])
                hdf_item.setEditable(False)
                hdf_item.depth = i
                parent_item.appendRow(hdf_item)

                if (isinstance(item[1], h5py.Group)):
                    hdf_item.setFont(QFont(QFont().defaultFamily(),12,1,False))
                    hdf_item.path = parent_item.path + item[0] + "/"
                    self.create_tree_file(parent_element[item[0]], hdf_item, i)
                else:
                    hdf_item.setFont(QFont(QFont().defaultFamily(),12,1,False))
                    hdf_item.path = parent_item.path + item[0]

    def display_info_about_item(self, selected_item:FileTreeItem, tab_widget:QTabWidget):
        tab_widget.show()
        table: QTableWidget = tab_widget.widget(0)
        table.clearContents()
        table.setRowCount(0)

        with h5py.File(self.full_filename[0]) as file:
            current_item = file
            path = selected_item.path.split("/")

            if (selected_item.depth != 0):
                for i in range(1, selected_item.depth + 1):
                    for item in current_item.items():
                        if (item[0] == path[i]):
                            current_item = current_item[item[0]]
                            break
                            
            attrs = current_item.attrs
            keys_attrs = list(attrs.keys())
            table.setRowCount(len(keys_attrs))
            for i in range(len(keys_attrs)):
                value = attrs.__getitem__(keys_attrs[i])
                table.setItem(i,0,QTableWidgetItem(keys_attrs[i]))
                if (isinstance(value, ndarray)):
                    result_str = ""
                    for j in range(len(value)):
                        if (isinstance(value[j], bytes)):
                            result_str += str(value[j].decode('utf-8'))
                        else:
                            result_str += str(value[j])
                        if j+1 != len(value):
                            result_str += ", "
                    table.setItem(i,3,QTableWidgetItem(result_str))
                    table.setItem(i,2,QTableWidgetItem(str(len(value))))
                else:
                    if (isinstance(value, bytes)):
                        table.setItem(i, 3, QTableWidgetItem(str(value.decode('utf-8'))))
                    else:
                        table.setItem(i, 3, QTableWidgetItem(str(value)))
                    table.setItem(i,2,QTableWidgetItem(str(1)))


    def close_file(self, root_item:QStandardItem, tab_widget:QTabWidget):
        root_item.removeRows(0, root_item.rowCount())
        tab_widget.hide()
        tab_widget.widget(0).clearContents()

    def show_window_data(self, selected_item:FileTreeItem):
        with h5py.File(self.full_filename[0]) as file:
            current_item = file
            path = selected_item.path.split("/")

            if (selected_item.depth != 0):
                for i in range(1, selected_item.depth + 1):
                    for item in current_item.items():
                        if (item[0] == path[i]):
                            current_item = current_item[item[0]]
                            break

            if (isinstance(current_item, h5py.Dataset)):
                items = list(current_item.attrs.items())
                if len(items) > 0:
                    value = items[0][1]
                    if not isinstance(value, bytes):
                        value = value[0]

                self.data_win = DataWindow()

                if len(items) >= 1 and items[0][0] == "CLASS" and value.decode('utf-8') == "IMAGE":
                    self.data_win.create_image(current_item)
                else:
                    self.data_win.create_table(len(current_item.maxshape), current_item.maxshape, current_item)
                self.data_win.show()


class DataWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(600, 450)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        container = QWidget()
        self.page_switcher = QWidget()
        layout_for_page_switcher = QHBoxLayout()
        prev_page = QPushButton("Prev Frame")
        self.current_page = QLineEdit()
        self.total_page = QLineEdit()
        next_page = QPushButton("Next Frame")

        prev_page.setFixedSize(80, 24)
        self.current_page.setFixedSize(48, 24)
        self.total_page.setFixedSize(48, 24)
        next_page.setFixedSize(80, 24)


        layout_for_page_switcher.addWidget(prev_page)
        layout_for_page_switcher.addWidget(self.current_page)
        layout_for_page_switcher.addWidget(self.total_page)
        layout_for_page_switcher.addWidget(next_page)
        layout_for_page_switcher.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.page_switcher.setLayout(layout_for_page_switcher)
        self.page_switcher.hide()
        layout.addWidget(self.page_switcher)

        container.setLayout(layout)
        self.setCentralWidget(container)

        prev_page.clicked.connect(lambda: self.change_page(-1))
        next_page.clicked.connect(lambda: self.change_page(1))
        self.current_page.returnPressed.connect(lambda: self.go_to_the_page())


    def create_table(self, dimension:int, size, data:h5py.Dataset, height=0, width=1, depth=2):
        self.dimension = dimension
        self.height = height
        self.width = width
        self.depth = depth
        self.size = size
        instruction = "self.data = data["
        for i in range(dimension):
            if i in {height, width, depth}:
                instruction += ":"
            else:
                instruction += "0"
            if i != dimension:
                instruction += ","
        instruction += "]"
        exec(instruction)

        menu_bar = self.menuBar()
        table_menu = QMenu('Table', self)
        menu_bar.addMenu(table_menu)
        self.setMenuBar(menu_bar)

        table = QTableWidget()
        table.setItemDelegate
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        if (dimension > 2):
            self.page_switcher.show()
        if (dimension == 1):
            table.setRowCount(size[0])
            table.setColumnCount(1)

            for i in range(size[0]):
                table.setItem(i,0, QTableWidgetItem(str(data[i])))
        elif (dimension == 2):
            table.setRowCount(size[0])
            table.setColumnCount(size[1])

            for i in range(size[0]):
                for j in range(size[1]):
                    table.setItem(i, j, QTableWidgetItem(str(data[i,j])))
        else:
            table.setRowCount(size[height])
            table.setColumnCount(size[width])
            self.current_page.setText("0")
            self.current_page.setValidator(QIntValidator(0, size[depth] - 1, self))
            self.total_page.setText(str(size[depth] - 1))
            self.total_page.setEnabled(False)

            str_data = "table.setItem(i, j, QTableWidgetItem(str(data["
            for i in range(size[height]):
                for j in range(size[width]):
                    for d in range(dimension):
                        if d == height:
                            str_data += str(i)
                        elif d == width:
                            str_data += str(j)
                        else:
                            str_data += "0"
                        if (d+1 != dimension):
                            str_data += ","
                    str_data += "])))"
                    exec(str_data)
                    str_data = "table.setItem(i, j, QTableWidgetItem(str(data["



        self.centralWidget().layout().addWidget(table)

    def change_page(self, changes):
        if (int(self.current_page.text()) + changes != -1 and 
            int(self.current_page.text()) + changes != self.size[self.depth]):
            table:QTableWidget = self.centralWidget().layout().itemAt(1).widget()
            table.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
            str_data = "table.setItem(i, j, QTableWidgetItem(str(self.data["
            for i in range(self.size[self.height]):
                for j in range(self.size[self.width]):
                    for d in range(self.dimension):
                        if d == self.height:
                            str_data += str(i)
                        elif d == self.width:
                            str_data += str(j)
                        elif d == self.depth:
                            str_data += str(int(self.current_page.text()) + changes)
                        if (d in {self.height, self.width, self.depth} and d+1 != self.dimension):
                            str_data += ","
                    str_data += "])))"
                    exec(str_data)
                    str_data = "table.setItem(i, j, QTableWidgetItem(str(self.data["
            self.current_page.setText(str(int(self.current_page.text()) + changes))
            table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def go_to_the_page(self):
        page = int(self.current_page.text())
        if (page >= 0 and page <= int(self.total_page.text())):
            table:QTableWidget = self.centralWidget().layout().itemAt(1).widget()
            table.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
            str_data = "table.setItem(i, j, QTableWidgetItem(str(self.data["
            for i in range(self.size[self.height]):
                for j in range(self.size[self.width]):
                    for d in range(self.dimension):
                        if d == self.height:
                            str_data += str(i)
                        elif d == self.width:
                            str_data += str(j)
                        elif d == self.depth:
                            str_data += str(page)
                        if (d in {self.height, self.width, self.depth} and d+1 != self.dimension):
                            str_data += ","
                    str_data += "])))"
                    exec(str_data)
                    str_data = "table.setItem(i, j, QTableWidgetItem(str(self.data["
            table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def create_image(self, data:h5py.Dataset):
        menu_bar = self.menuBar()
        image_menu = QMenu('Image', self)
        menu_bar.addMenu(image_menu)
        self.setMenuBar(menu_bar)
        
        image = QLabel()
        img = Image.fromarray(data[:])
        qt_img = ImageQt.ImageQt(img)

        image.setPixmap(QPixmap.fromImage(qt_img).scaled(600, 450, Qt.AspectRatioMode.KeepAspectRatio))
        self.centralWidget().layout().addWidget(image)
        image.show()




app = QApplication(sys.argv)
window = MainWindow()
window.show()

app.exec()