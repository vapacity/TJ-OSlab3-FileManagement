import os
import pickle
from datetime import datetime

class Inode:
    def __init__(self, name, size, location):
        self.name = name
        self.size = size
        self.init_time = datetime.now()  # 创建时间
        self.revise_time = datetime.now()  # 修改时间
        self.type = "rw"  # 文件权限类型：r 只读, w 只写, a 只追加, rw 读写
        self.location = location  # 文件路径
        self.blocks = []
        self.parent = None

class Directory:
    def __init__(self, name, location, parent=None):
        self.name = name
        self.location = location  # 目录路径
        self.init_time = datetime.now()  # 创建时间 
        self.parent = parent
        self.files = {}
        self.subdirectories = {}

    def add_file(self, inode):
        self.files[inode.name] = inode

    def remove_file(self, file_name):
        if file_name in self.files:
            del self.files[file_name]

    def add_subdirectory(self, subdirectory):
        self.subdirectories[subdirectory.name] = subdirectory

    def remove_subdirectory(self, subdirectory_name):
        if subdirectory_name in self.subdirectories:
            del self.subdirectories[subdirectory_name]

    def list_contents(self):
        contents = []
        for file_name in self.files:
            contents.append(f"File: {file_name}")
        for subdir_name in self.subdirectories:
            contents.append(f"Subdirectory: {subdir_name}")
        return contents

    def get_subdirectory(self, name):
        return self.subdirectories.get(name)
    
    def output_attr(self):
        print("Name:",self.name)
        print("Location:",self.location)
        print("Files:",self.files)
        if self.parent:
            print("Parent:",self.parent.name)
        for sub in self.subdirectories:
            print("Sub Directory:",sub)
        print("Init Time:",self.init_time)

class IndexedFileSystem:
    def __init__(self, size, block_size):
        self.size = size
        self.block_size = block_size
        self.total_blocks = size // block_size
        self.data_blocks = [None] * self.total_blocks
        self.free_blocks = set(range(self.total_blocks))
        self.root = Directory("root", "/root")
        self.current_directory = self.root
        self.inodes = {}

    def format(self):
        """格式化文件系统"""
        self.data_blocks = [None] * self.total_blocks
        self.free_blocks = set(range(self.total_blocks))
        self.root = Directory("root", "/root")
        self.current_directory = self.root
        self.inodes = {}

    def find_free_blocks(self, num_blocks):
        """查找空闲块"""
        if len(self.free_blocks) < num_blocks:
            return None
        free_blocks = list(self.free_blocks)[:num_blocks]
        return free_blocks

    def create_directory(self, dir_name):
        """创建新目录"""
        new_dir = Directory(name=dir_name, location=self.get_current_path() + "/" + dir_name, parent=self.current_directory)
        self.current_directory.add_subdirectory(new_dir)

    def change_directory(self, path):
        """更改当前目录"""
        if path.startswith("/"):
            current_dir = self.root
            path_parts = path.strip("/").split("/")[1:] # 由于/已经进入root目录，首元素root路径应该被舍去
        else:
            current_dir = self.current_directory
            path_parts = path.split("/")

        for part in path_parts:
            if part == "..":
                if current_dir.parent:
                    current_dir = current_dir.parent
            elif part == "." or part == "":
                continue
            else:
                next_dir = current_dir.get_subdirectory(part)
                if next_dir:
                    current_dir = next_dir
                else:
                    print(f"Directory '{part}' not found.")
                    return

        self.current_directory = current_dir
        print(f"Changed directory to: {self.get_current_path()}")

    def get_current_path(self):
        """获取当前目录路径"""
        parts = []
        current_dir = self.current_directory
        while current_dir:
            parts.append(current_dir.name)
            current_dir = current_dir.parent 
        return "/" + "/".join(reversed(parts))

    def list_directory(self):
        """列出当前目录内容"""
        contents = self.current_directory.list_contents()
        for item in contents:
            print(item)

    def allocate_file(self, file_name, file_data, file_type="rw"):
        """分配文件"""
        required_blocks = (len(file_data) + self.block_size - 1) // self.block_size
        free_blocks = self.find_free_blocks(required_blocks)
        
        if free_blocks is None:
            print("Not enough free space to allocate the file.")
            return

        inode = Inode(file_name, len(file_data), self.get_current_path() + "/" + file_name)
        inode.type = file_type  # 设置文件权限
        for i in range(required_blocks):
            block_index = free_blocks[i]
            self.data_blocks[block_index] = file_data[i * self.block_size:(i + 1) * self.block_size]
            inode.blocks.append(block_index)
            self.free_blocks.remove(block_index)

        self.current_directory.add_file(inode)
        inode.parent = self.current_directory
        print(f"File '{file_name}' allocated with blocks: {inode.blocks}")

    def read_file(self, file_name):
        """读取文件"""
        if file_name not in self.current_directory.files:
            print(f"File '{file_name}' not found.")
            return None

        inode = self.current_directory.files[file_name]
        file_data = b""
        for block_index in inode.blocks:
            file_data += self.data_blocks[block_index]
        return file_data[:inode.size]  # Trim to the exact file size

    def write_file(self, file_name, new_data):
        """写入文件，覆盖原有内容并重新分配内存块"""
        if file_name not in self.current_directory.files:
            print(f"File '{file_name}' not found.")
            return

        inode = self.current_directory.files[file_name]
        if 'r' in inode.type and 'w' not in inode.type:
            print(f"File '{file_name}' is read-only.")
            return

        # 计算新内容所需的块
        required_blocks = (len(new_data) + self.block_size - 1) // self.block_size
        current_blocks = len(inode.blocks)

        # 如果需要更多的块，查找空闲块并分配
        if required_blocks > current_blocks:
            additional_blocks = self.find_free_blocks(required_blocks - current_blocks)
            if additional_blocks is None:
                print("Not enough free space to extend the file.")
                return
            inode.blocks.extend(additional_blocks)
            for block_index in additional_blocks:
                self.free_blocks.remove(block_index)
        # 如果需要更少的块，释放多余的块
        elif required_blocks < current_blocks:
            for block_index in inode.blocks[required_blocks:]:
                self.data_blocks[block_index] = None
                self.free_blocks.add(block_index)
            inode.blocks = inode.blocks[:required_blocks]

        inode.size = len(new_data)
        inode.revise_time = datetime.now()  # 更新修改时间
        for i in range(required_blocks):
            block_index = inode.blocks[i]
            self.data_blocks[block_index] = new_data[i * self.block_size:(i + 1) * self.block_size]

        print(f"File '{file_name}' written with new data. Blocks: {inode.blocks}")
    
    def delete_file(self, file_name):
        """删除文件"""
        if file_name not in self.current_directory.files:
            print(f"File '{file_name}' not found.")
            return

        inode = self.current_directory.files[file_name]
        for block_index in inode.blocks:
            self.data_blocks[block_index] = None
            self.free_blocks.add(block_index)

        self.current_directory.remove_file(file_name)
        print(f"File '{file_name}' deleted.")

    def delete_directory(self, dir_name):
        """递归删除目录及其内容"""
        if dir_name not in self.current_directory.subdirectories:
            print(f"Directory '{dir_name}' not found.")
            return

        dir_to_delete = self.current_directory.subdirectories[dir_name]
        self.recursive_delete_directory(dir_to_delete)
        self.current_directory.remove_subdirectory(dir_name)
        print(f"Directory '{dir_name}' and its contents deleted.")

    def recursive_delete_directory(self, directory):
        """递归删除目录中的文件和子目录"""
        for file_name in list(directory.files.keys()):
            inode = directory.files[file_name]
            for block_index in inode.blocks:
                self.data_blocks[block_index] = None
                self.free_blocks.add(block_index)
            del directory.files[file_name]

        for subdir_name in list(directory.subdirectories.keys()):
            self.recursive_delete_directory(directory.subdirectories[subdir_name])
            del directory.subdirectories[subdir_name]

    def copy_file(self, source_path, dest_path):
        """复制文件"""
        source_dir, source_file = os.path.split(source_path)
        dest_dir = dest_path
        self.change_directory(source_dir)
        file_data = self.read_file(source_file)
        if file_data is None:
            return
        self.change_directory(dest_dir)
        new_file_name = source_file if dest_dir != source_dir else self.generate_new_name(source_file, self.current_directory.files)
        self.allocate_file(new_file_name, file_data)
    
    def generate_new_name(self, name, existing_names):
        """生成不重名的新名称"""
        base, ext = os.path.splitext(name)
        count = 1
        new_name = f"{base}_copy{count}{ext}"
        while new_name in existing_names:
            count += 1
            new_name = f"{base}_copy{count}{ext}"
        return new_name

    def copy_directory(self, source_dir, dest_dir, new_name=None):
        """复制目录"""
        if new_name is None:
            new_name = source_dir.name if dest_dir != source_dir.parent else self.generate_new_name(source_dir.name, dest_dir.subdirectories)
        new_dir = Directory(name=new_name, location=dest_dir.location + "/" + new_name, parent=dest_dir)
        dest_dir.add_subdirectory(new_dir)
        self.recursive_copy_directory(source_dir, new_dir)

    def recursive_copy_directory(self, src_dir, dst_dir):
        for file_name, file_inode in src_dir.files.items():
            file_data = self.read_file(file_inode.name)
            new_file_name = file_name
            new_file_inode = Inode(name=new_file_name, size=file_inode.size, location=dst_dir.location + "/" + new_file_name)
            new_file_inode.blocks = file_inode.blocks.copy()  # 复制块信息
            dst_dir.add_file(new_file_inode)
            self.inodes[new_file_inode.name] = new_file_inode
        
        for subdir_name, subdir in src_dir.subdirectories.items():
            new_subdir_name = subdir_name if subdir_name not in dst_dir.subdirectories else self.generate_new_name(subdir_name, dst_dir.subdirectories)
            new_subdir = Directory(name=new_subdir_name, location=dst_dir.location + "/" + new_subdir_name, parent=dst_dir)
            dst_dir.add_subdirectory(new_subdir)
            self.recursive_copy_directory(subdir, new_subdir)

    def move_file(self, source_path, dest_path):
        """移动文件"""
        source_dir, source_file = os.path.split(source_path)
        dest_dir, dest_file = os.path.split(dest_path)
        self.change_directory(source_dir)
        file_data = self.read_file(source_file)
        if file_data is None:
            return
        self.delete_file(source_file)
        self.change_directory(dest_dir)
        self.allocate_file(dest_file, file_data)

    def change_file_type(self, file_name, new_type):
        """更改文件权限类型"""
        if file_name not in self.current_directory.files:
            print(f"File '{file_name}' not found.")
            return
        inode = self.current_directory.files[file_name]
        inode.type = new_type
        inode.revise_time = datetime.now()  # 更新修改时间
        print(f"File '{file_name}' type changed to {new_type}.")

    def save_to_disk(self, filename):
        """保存文件系统到磁盘"""
        with open(filename, 'wb') as f:
            pickle.dump(self, f)

    @staticmethod
    def load_from_disk(filename):
        """从磁盘加载文件系统"""
        with open(filename, 'rb') as f:
            return pickle.load(f)

