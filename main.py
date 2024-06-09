import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, QPushButton,
                             QTreeWidget, QTreeWidgetItem, QMenu, QAction, QSplitter, QInputDialog,
                             QGridLayout, QLabel, QScrollArea, QFrame, QDialog, QFormLayout, QToolButton, QPlainTextEdit,QMessageBox)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QFontDatabase, QFont,QIcon
from fileManagement import Inode, Directory, IndexedFileSystem
import pickle

import os

def get_resource_path(relative_path):
    """获取资源文件的绝对路径，考虑 PyInstaller 打包后的情况"""
    try:
        # PyInstaller 创建临时文件夹，并将路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# 示例使用
file_path = get_resource_path("file.png")
dir_path = get_resource_path("dir.png")
filesystem_path = get_resource_path("filesystem.pkl")

# 确保在使用这些路径时正确处理

class CustomFileView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setLayout(QGridLayout())
        self.setContextMenuPolicy(Qt.CustomContextMenu)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.parent.selected_frame:
                self.parent.selected_frame.setStyleSheet("")
                self.parent.selected_frame = None
        elif event.button() == Qt.RightButton:
            if self.parent.selected_frame:
                self.parent.selected_frame.setStyleSheet("")
                self.parent.selected_frame = None
            self.parent.show_context_menu(event.globalPos())

class FileManagementSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_frame = None
        self.initUI()
        self.file_system_path = "filesystem.pkl"  # 保存文件系统的路径
        
        # 尝试加载文件系统
        try:
            self.file_system = IndexedFileSystem.load_from_disk(self.file_system_path)
            print("文件系统加载成功")
        except (FileNotFoundError, EOFError, pickle.UnpicklingError):
            print("加载文件系统失败，初始化新文件系统")
            self.file_system = IndexedFileSystem(1024 * 1024, 512)  # 初始化文件系统
            self.file_system.format()
        
        self.update_tree_view()
        self.update_file_view()
        self.path_edit.setText('/root')  # 初始化路径为/root
        self.history = []
        self.history_index = -1

    def initUI(self):
        self.setWindowTitle('File Management System @2253896 张文健')
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon('dir.png'))
        # 加载字体
        QFontDatabase.addApplicationFont("path/to/SimSun.ttf")  # 请确保宋体字体文件在指定路径
        QFontDatabase.addApplicationFont("path/to/Frutiger.ttf")  # 请确保Frutiger字体文件在指定路径
        
        font_chinese = QFont("SimSun", 12)
        font_english = QFont("Frutiger", 12)
        
        self.setFont(font_chinese)  # 默认字体设为宋体

        # 创建主布局
        main_layout = QVBoxLayout()
        
        # 路径输入和控制按钮
        path_layout = QHBoxLayout()
        
        self.left_button = QPushButton('<')
        self.left_button.clicked.connect(self.go_up_directory)
        self.left_button.setFont(font_english)
        path_layout.addWidget(self.left_button)
        
        self.right_button = QPushButton('>')
        self.right_button.clicked.connect(self.go_down_directory)
        self.right_button.setFont(font_english)
        path_layout.addWidget(self.right_button)
        
        self.path_edit = QLineEdit()
        self.path_edit.setText('/root')  # 初始化路径为/root
        self.path_edit.returnPressed.connect(self.change_directory)
        self.path_edit.setFont(font_english)
        path_layout.addWidget(self.path_edit)
        
        main_layout.addLayout(path_layout)
        
        # 操作按钮
        operation_layout = QHBoxLayout()

        # 创建展开按钮
        operation_menu = QMenu()
        add_file_action = operation_menu.addAction("Add File")
        add_file_action.triggered.connect(self.add_file)
        add_folder_action = operation_menu.addAction("Add Folder")
        add_folder_action.triggered.connect(self.add_folder)
        
        operation_button = QToolButton()
        operation_button.setText("Add")
        operation_button.setMenu(operation_menu)
        operation_button.setPopupMode(QToolButton.InstantPopup)
        operation_button.setFont(font_english)
        operation_layout.addWidget(operation_button)
        
        copy_button = QPushButton('Copy')
        copy_button.clicked.connect(self.copy_item)
        copy_button.setFont(font_english)
        operation_layout.addWidget(copy_button)

        paste_button = QPushButton('Paste')
        paste_button.clicked.connect(self.paste_item)
        paste_button.setFont(font_english)
        operation_layout.addWidget(paste_button)
        
        delete_button = QPushButton('Delete')
        delete_button.clicked.connect(self.delete_item)
        delete_button.setFont(font_english)
        operation_layout.addWidget(delete_button)
        
        format_button = QPushButton('Format')
        format_button.clicked.connect(self.format_system)
        format_button.setFont(font_english)
        operation_layout.addWidget(format_button)

        details_button = QPushButton('Details')
        details_button.clicked.connect(self.show_properties)
        details_button.setFont(font_english)
        operation_layout.addWidget(details_button)

        main_layout.addLayout(operation_layout)
        
        # 目录树和文件视图
        splitter = QSplitter(Qt.Horizontal)
        
        self.tree_view = QTreeWidget()
        self.tree_view.setHeaderLabel('快速访问')
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_tree_context_menu)
        self.tree_view.itemDoubleClicked.connect(self.tree_item_double_clicked)
        self.tree_view.setFont(font_english)
        splitter.addWidget(self.tree_view)
        
        self.file_view = CustomFileView(self)  # 使用自定义的 CustomFileView 类
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.file_view)
        splitter.addWidget(scroll_area)
        
        splitter.setSizes([300, 700])  # 设置左右比例为3:7
        
        main_layout.addWidget(splitter)
        
        # 创建主窗口部件
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.show()

    def closeEvent(self, event):
        """在关闭窗口时保存文件系统"""
        self.file_system.save_to_disk(self.file_system_path)
        print("文件系统已保存")
        event.accept()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.delete_item()
        elif event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
            self.copy_item()
        elif event.key() == Qt.Key_V and event.modifiers() == Qt.ControlModifier:
            self.paste_item()
        else:
            super().keyPressEvent(event)
    
    def update_tree_view(self):
        expanded_items = self.get_expanded_items(self.tree_view.invisibleRootItem())
        self.tree_view.clear()
        self.add_tree_items(self.tree_view.invisibleRootItem(), self.file_system.root)
        self.set_expanded_items(self.tree_view.invisibleRootItem(), expanded_items)
        self.expand_current_directory()
    
    def add_tree_items(self, parent_item, directory):
        is_current_path = (self.file_system.current_directory == directory)
        dir_name = f"📂 {directory.name}" if is_current_path else f"📁 {directory.name}"
        dir_item = QTreeWidgetItem(parent_item, [dir_name])
        dir_item.setData(0, Qt.UserRole, directory)
        
        if is_current_path:
            dir_item.setExpanded(True)  # 展开当前目录
        
        for subdir in directory.subdirectories.values():
            self.add_tree_items(dir_item, subdir)
        '''
        for file in directory.files.values():
            file_name = f"📁 {file.name}"
            file_item = QTreeWidgetItem(dir_item, [file_name])
            file_item.setData(0, Qt.UserRole, file)
        '''
    
    def expand_current_directory(self):
        root = self.tree_view.invisibleRootItem()
        self.expand_directory(root)

    def expand_directory(self, parent_item):
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            directory = child.data(0, Qt.UserRole)
            if isinstance(directory, Directory) and self.file_system.current_directory == directory:
                child.setExpanded(True)  # 展开当前目录
                self.expand_directory(child)  # 递归展开子目录

    def get_expanded_items(self, item):
        expanded = []
        for i in range(item.childCount()):
            child = item.child(i)
            if child.isExpanded():
                expanded.append(child.data(0, Qt.UserRole).name)
                expanded.extend(self.get_expanded_items(child))
        return expanded

    def set_expanded_items(self, item, expanded):
        for i in range(item.childCount()):
            child = item.child(i)
            if child.data(0, Qt.UserRole).name in expanded:
                child.setExpanded(True)
                self.set_expanded_items(child, expanded)
    
    def update_file_view(self):
        # 清空网格布局
        for i in reversed(range(self.file_view.layout().count())):
            widget_to_remove = self.file_view.layout().itemAt(i).widget()
            if widget_to_remove is not None:
                self.file_view.layout().removeWidget(widget_to_remove)
                widget_to_remove.setParent(None)
        
        # 设置网格布局的行和列
        rows = 4
        cols = 4
        
        # 初始化行列位置
        row = 0
        col = 0
        
        items = list(self.file_system.current_directory.files.values()) + list(self.file_system.current_directory.subdirectories.values())
        
        for item in items:
            if col >= cols:
                col = 0
                row += 1
            self.add_file_view_item(item, row, col, is_dir=isinstance(item, Directory))
            col += 1
        
        # 填充空白区域
        for r in range(rows):
            for c in range(cols):
                if self.file_view.layout().itemAtPosition(r, c) is None:
                    spacer = QLabel()
                    spacer.setFixedSize(100, 100)
                    self.file_view.layout().addWidget(spacer, r, c)

    def add_file_view_item(self, inode, row, col, is_dir=False):
        icon = QLabel()
        pixmap = QPixmap("dir.png" if is_dir else "file.png")
        icon.setPixmap(pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon.setAlignment(Qt.AlignCenter)
        
        name = QLabel(inode.name)
        name.setAlignment(Qt.AlignCenter)
        name.setFont(QFont("SimSun", 8))

        container = QVBoxLayout()
        container.addWidget(icon)
        container.addWidget(name)
        
        frame = QFrame()
        frame.setLayout(container)
        frame.setFixedSize(100, 100)  # 固定每个格子的大小
        frame.setFrameShape(QFrame.NoFrame)  # 移除外框
        frame.setContextMenuPolicy(Qt.CustomContextMenu)
        frame.mousePressEvent = lambda event: self.select_frame(frame, event)
        frame.mouseDoubleClickEvent = lambda event: self.double_click_frame(frame)

        self.file_view.layout().addWidget(frame, row, col)

        # 将 inode 存储在 frame 的 UserRole 中，便于后续操作
        frame.setProperty('inode', inode)

    def select_frame(self, frame, event):
        if event.button() == Qt.LeftButton:
            if self.selected_frame:
                self.selected_frame.setStyleSheet("")
            self.selected_frame = frame
            frame.setStyleSheet("background-color: lightblue;")
        elif event.button() == Qt.RightButton:
            self.selected_frame = frame
            self.selected_frame.setStyleSheet("background-color: lightblue;")
            self.show_context_menu(event.globalPos())

    def change_directory(self):
        path = self.path_edit.text()
        self.file_system.change_directory(path)
        self.path_edit.setText(self.file_system.get_current_path())
        self.update_file_view()
        self.update_tree_view()  # 更新树视图
        self.history.append(path)
        self.history_index += 1
    
    def go_up_directory(self):
        self.file_system.change_directory('..')
        self.path_edit.setText(self.file_system.get_current_path())
        self.update_file_view()
        self.update_tree_view()  # 更新树视图
        self.history.append(self.file_system.get_current_path())
        self.history_index += 1
    
    def go_down_directory(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.file_system.change_directory(self.history[self.history_index])
            self.path_edit.setText(self.file_system.get_current_path())
            self.update_file_view()
            self.update_tree_view()
    
    def add_file(self):
        file_name, ok = QInputDialog.getText(self, 'Add File', 'Enter file name:')
        if ok and file_name:
            if file_name in self.file_system.current_directory.files:
                QMessageBox.warning(self, 'Error', 'A file with the same name already exists.')
                return
            self.file_system.allocate_file(file_name, b'')
            self.update_file_view()
            self.update_tree_view()  # 更新树视图
    
    def add_folder(self):
        folder_name, ok = QInputDialog.getText(self, 'Add Folder', 'Enter folder name:')
        if ok and folder_name:
            if folder_name in self.file_system.current_directory.subdirectories:
                QMessageBox.warning(self, 'Error', 'A folder with the same name already exists.')
                return
            self.file_system.create_directory(folder_name)
            self.update_tree_view()
            self.update_file_view()
    
    def delete_item(self):
        if self.selected_frame:
            inode = self.selected_frame.property('inode')
            if isinstance(inode, Inode):
                self.file_system.delete_file(inode.name)
            elif isinstance(inode, Directory):
                self.file_system.delete_directory(inode.name)
            self.update_tree_view()
            self.update_file_view()

    def format_system(self):
        if self.file_system:
            self.file_system.format()
        self.update_tree_view()
        self.update_file_view()    

    def rename_item(self):
        if self.selected_frame:
            inode = self.selected_frame.property('inode')
            new_name, ok = QInputDialog.getText(self, 'Rename', 'Enter new name:')
            if ok and new_name:
                if isinstance(inode, Inode):
                    self.file_system.current_directory.files[new_name] = self.file_system.current_directory.files.pop(inode.name)
                    inode.name = new_name
                elif isinstance(inode, Directory):
                    self.file_system.current_directory.subdirectories[new_name] = self.file_system.current_directory.subdirectories.pop(inode.name)
                    inode.name = new_name
                self.update_tree_view()
                self.update_file_view()

    def tree_item_double_clicked(self, item, column):
        inode = item.data(0, Qt.UserRole)
        if isinstance(inode, Directory):
            self.file_system.change_directory(inode.location)
            self.path_edit.setText(self.file_system.get_current_path())
            self.update_file_view()
            self.update_tree_view()
    
    def show_context_menu(self, pos):
        context_menu = QMenu(self)
        if self.selected_frame and self.selected_frame.property('inode') is not None:
            open_action = QAction('Open', self)
            open_action.triggered.connect(self.open_item)
            context_menu.addAction(open_action)
            
            copy_action = QAction('Copy', self)
            copy_action.triggered.connect(self.copy_item)
            context_menu.addAction(copy_action)

            rename_action = QAction('Rename', self)
            rename_action.triggered.connect(self.rename_item)
            context_menu.addAction(rename_action)

            delete_action = QAction('Delete', self)
            delete_action.triggered.connect(self.delete_item)
            context_menu.addAction(delete_action)
            
            properties_action = QAction('Settings', self)
            properties_action.triggered.connect(self.show_properties)
            context_menu.addAction(properties_action)
        else:
            paste_action = QAction('Paste', self)
            paste_action.triggered.connect(self.paste_item)
            context_menu.addAction(paste_action)

            add_file_action = QAction('Add File', self)
            add_file_action.triggered.connect(self.add_file)
            context_menu.addAction(add_file_action)
            
            add_folder_action = QAction('Add Folder', self)
            add_folder_action.triggered.connect(self.add_folder)
            context_menu.addAction(add_folder_action)

            back_action = QAction('Go Back', self)
            back_action.triggered.connect(self.go_up_directory)
            context_menu.addAction(back_action)
        
        context_menu.exec_(pos)
    
    def show_tree_context_menu(self, pos):
        item = self.tree_view.itemAt(pos)
        if item:
            context_menu = QMenu(self)
            
            unfold_action = QAction('Unfold Directory', self)
            unfold_action.triggered.connect(lambda: self.unfold_item(item))
            context_menu.addAction(unfold_action)

            fold_action = QAction('Fold Directory', self)
            fold_action.triggered.connect(lambda: self.fold_item(item))
            context_menu.addAction(fold_action)
            
            context_menu.exec_(self.tree_view.mapToGlobal(pos))
    
    def unfold_item(self, item):
        item.setExpanded(True)
        self.expand_all_children(item)
    
    def expand_all_children(self, item):
        for i in range(item.childCount()):
            child = item.child(i)
            child.setExpanded(True)
            self.expand_all_children(child)

    def fold_item(self, item):
        item.setExpanded(False)
        self.collapse_all_children(item)
    
    def collapse_all_children(self, item):
        for i in range(item.childCount()):
            child = item.child(i)
            child.setExpanded(False)
            self.collapse_all_children(child)

    def double_click_frame(self, frame):
        inode = frame.property('inode')
        if isinstance(inode, Directory):
            self.file_system.change_directory(inode.location)
            self.path_edit.setText(self.file_system.get_current_path())
            self.update_file_view()
            self.update_tree_view()
        elif isinstance(inode, Inode):
            file_data = self.file_system.read_file(inode.name)
            if file_data is not None:
                try:
                    content = file_data.decode('utf-8')
                except UnicodeDecodeError:
                    content = file_data.decode('latin1')  # 尝试使用另一种编码进行解码
                self.show_file_editor(inode.name, content)
    
    def show_file_editor(self, file_name, file_content):
        content_dialog = QDialog(self)
        content_dialog.setWindowTitle(file_name)
        layout = QVBoxLayout(content_dialog)
        content_editor = QPlainTextEdit(file_content)
        content_editor.setFixedHeight(300)  # 设置高度为15行
        layout.addWidget(content_editor)
        button_box = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(lambda: self.save_file_content(file_name, content_editor.toPlainText(), content_dialog))
        button_box.addWidget(save_button)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(content_dialog.reject)
        button_box.addWidget(cancel_button)
        layout.addLayout(button_box)
        content_dialog.exec_()

    def save_file_content(self, file_name, file_content, dialog):
        self.file_system.write_file(file_name, file_content.encode('utf-8'))
        dialog.accept()

    def open_item(self):
        if self.selected_frame:
            inode = self.selected_frame.property('inode')
            if isinstance(inode, Directory):
                self.file_system.change_directory(inode.location)
                self.path_edit.setText(self.file_system.get_current_path())
                self.update_file_view()
                self.update_tree_view()  # 更新树视图
            elif isinstance(inode, Inode):
                file_data = self.file_system.read_file(inode.name)
                if file_data is not None:
                    try:
                        content = file_data.decode('utf-8')
                    except UnicodeDecodeError:
                        content = file_data.decode('latin1')  # 尝试使用另一种编码进行解码
                    self.show_file_editor(inode.name, content)
    
    def copy_item(self):
        if self.selected_frame:
            inode = self.selected_frame.property('inode')
            self.copy_file = inode

    def paste_item(self):
        if hasattr(self, 'copy_file'):
            copy_inode = self.copy_file
            copy_file_path = copy_inode.location
            if isinstance(copy_inode, Inode):
                self.file_system.copy_file(copy_file_path, self.file_system.current_directory.location)
            elif isinstance(copy_inode, Directory):
                # 检查目标目录是否为源目录的子目录
                current_path = self.file_system.get_current_path()
                if current_path.startswith(copy_inode.location):
                    QMessageBox.warning(self, 'Error', 'Cannot copy a directory into its own subdirectory.')
                    return
                self.file_system.copy_directory(copy_inode, self.file_system.current_directory)
            self.update_file_view()
            self.update_tree_view()

    def move_item(self):
        # Implement move functionality
        pass
    
    def show_properties(self):
        if self.selected_frame:
            inode = self.selected_frame.property('inode')
            self.show_inode_properties(inode)
    
    def show_inode_properties(self, inode):
        properties_dialog = QDialog(self)
        properties_dialog.setWindowTitle('Settings')
        layout = QFormLayout(properties_dialog)
        
        font_english = QFont("Frutiger", 12)
        font_chinese = QFont("SimSun", 12)
        
        name_label = QLabel(inode.name)
        name_label.setFont(font_chinese)
        location_label = QLabel(inode.location)
        location_label.setFont(font_chinese)
        size_label = QLabel(str(inode.size)+"B" if hasattr(inode, 'size') else 'N/A')
        size_label.setFont(font_english)
        init_time_label = QLabel(inode.init_time.strftime('%Y-%m-%d %H:%M:%S'))
        init_time_label.setFont(font_english)
        if hasattr(inode, 'revise_time'):
            revise_time_label = QLabel(inode.revise_time.strftime('%Y-%m-%d %H:%M:%S')) 
            revise_time_label.setFont(font_english)
        if hasattr(inode, 'type_label'):
            type_label = QLabel(inode.type)
            type_label.setFont(font_english)
        
        name_text_label = QLabel('Name:')
        name_text_label.setFont(font_english)
        location_text_label = QLabel('Location:')
        location_text_label.setFont(font_english)
        size_text_label = QLabel('Size:')
        size_text_label.setFont(font_english)
        init_time_text_label = QLabel('Init Time:')
        init_time_text_label.setFont(font_english)
        if hasattr(inode, 'revise_time'):
            revise_time_text_label = QLabel('Revise Time:') if revise_time_label else None
        if hasattr(inode, 'type_label'):
            type_text_label = QLabel('Type:') if type_label else None

        if hasattr(inode, 'revise_time'):
            revise_time_text_label.setFont(font_english)
        if hasattr(inode, 'type_label'):
            type_text_label.setFont(font_english)
        
        layout.addRow(name_text_label, name_label)
        layout.addRow(location_text_label, location_label)
        layout.addRow(size_text_label, size_label)
        layout.addRow(init_time_text_label, init_time_label)
        if hasattr(inode, 'revise_time'):
            layout.addRow(revise_time_text_label, revise_time_label)
        if hasattr(inode, 'type_label'):
            layout.addRow(type_text_label, type_label)
        
        properties_dialog.exec_()




if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FileManagementSystem()
    sys.exit(app.exec_())
