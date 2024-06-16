# OS lab3——文件管理系统

## 一、项目简介

1. ##### 项目目的

   - 理解文件存储空间的管理；
   - 掌握文件的物理结构、目录结构和文件操作；
   - 实现简单文件系统管理；
   - 加深文件系统实现过程的理解；

2. ##### 项目内容

   文件存储空间管理可采取链接结构（如FAT文件系统中的显式链接等）或者其他学过的方法；空闲空间管理可采用位图或者其他方法；文件目录采用多级目录结构，目录项目中应包含：文件名、物理地址、长度等信息。文件系统提供的操作：格式化、创建子目录、删除子目录、显示目录、更改当前目录、创建文件、打开文件、关闭文件、写文件、读文件、删除文件...

3. ##### 开发环境

   系统：Windows11

   IDE：VScode

   requirements: python3.8，PyQt5

4. ##### 运行方法

   确保 `pip install PyQt5`

   在根目录执行 `python main.py`


## 二、系统架构

1. ### 类的设计

   | 类                   | 作用                                                         |
   | -------------------- | :----------------------------------------------------------- |
   | Inode                | `Inode` 类表示文件的元数据，包括文件名、大小、创建时间、修改时间、文件权限类型、文件路径和存储数据块的列表，即FCB块。 |
   | Directory            | `Directory` 类表示目录，包含子目录和文件的字典，并提供添加、移除和列出目录内容的功能。 |
   | IndexedFileSystem    | `IndexedFileSystem` 类表示文件系统，包含所有目录和文件的管理，提供文件系统的格式化、目录切换、文件和目录的创建、删除、复制和移动功能。 |
   | FileManagementSystem | 继承自QMainWindow，包含了整个系统的Qt样式和交互              |

2. ### 文件系统设计

   1. ##### 文件系统架构

      - 文件存储空间管理：使用了索引存储的方式
      - 空闲空间管理：采用了集合set的方式，存储了所有当前空闲的内存块
      - 文件目录：采用了树形目录。文件系统根目录为 `/root`，可以包含文件和子目录。文件和目录的层级结构可以任意嵌套。
      - 文件系统大小：文件系统的大小为 1 MB，每个数据块的大小为 512 字节，总共有 2048 个数据块。

   2. ##### 文件系统功能

      - 格式化：初始化文件系统，清空所有数据块和目录结构。
      - 目录管理：支持创建、删除和切换目录。
      - 文件管理：支持创建、读取、写入、删除、复制和移动文件。
      - 持久化：支持将文件系统保存到磁盘，并从磁盘加载文件系统。

## 三、功能实现

1. ##### 格式化

   格式化功能通过 `IndexedFileSystem` 类中的 `format` 方法实现。此方法会清空所有数据块，重置空闲块集合，重新初始化根目录，并重置当前目录为根目录。 执行格式化后，文件系统恢复到初始状态，所有存储的数据和目录结构将被清除，空闲块集合重新填满。

2. ##### 创建子目录

   创建子目录功能通过 `IndexedFileSystem` 类中的 `create_directory` 方法实现。此方法接收一个目录名称作为参数，创建一个新的 `Directory` 对象，并将其添加到当前目录的子目录字典中。 在当前目录下成功创建新的子目录，并在目录结构中添加该子目录的元数据。

3. ##### 删除子目录

   删除子目录功能通过 `Directory` 类中的 `remove_subdirectory` 方法实现。此方法接收一个子目录名称作为参数，从当前目录的子目录字典中删除该子目录。指定的子目录及其内容将被删除，目录结构中不再包含该子目录的信息。

4. ##### 显示目录

   显示目录内容通过 `IndexedFileSystem` 类中的 `list_directory` 方法实现。此方法调用当前目录的 `list_contents` 方法，列出所有文件和子目录的名称。用户可以查看当前目录下的所有文件和子目录的名称，以便进行进一步的操作。同时，系统会根据当前进入的文件夹自动在左侧目录栏展开到当前文件及部分，

5. ##### 创建文件

   创建文件功能通过 `IndexedFileSystem` 类中的 `allocate_file` 方法实现。此方法接收文件名称和文件数据作为参数，计算所需的数据块，查找空闲块，将数据写入数据块，并在当前目录中添加新的 `Inode`。 在当前目录下成功创建新的文件，分配所需的数据块并存储文件数据，文件元数据被记录在目录中。

6. ##### 读文件

   读取文件功能通过 `IndexedFileSystem` 类中的 `read_file` 方法实现。此方法接收文件名称作为参数，找到对应的 `Inode`，读取其数据块中的内容，并返回文件数据。 用户可以读取并获取指定文件的数据内容，以便进行查看或进一步处理。

7. ##### 写文件

   写入文件功能通过 `IndexedFileSystem` 类中的 `write_file` 方法实现。此方法接收文件名称和新数据作为参数，重新计算所需数据块，更新文件数据块，释放多余的块，并更新文件元数据。指定文件的内容将被新数据覆盖，文件的数据块可能会重新分配，文件元数据中的修改时

8. ##### 删除文件

   删除文件功能通过 `IndexedFileSystem` 类中的 `delete_file` 方法实现。此方法接收文件名称作为参数，找到对应的 `Inode`，释放其所有数据块，从当前目录中移除该文件。 指定文件及其数据块将被删除，文件系统中不再包含该文件的信息，数据块将重新变为空闲状态。

9. ##### 复制文件

   复制文件功能通过 `IndexedFileSystem` 类中的 `copy_file` 方法实现，通过`copy_item`方法进行。获取源文件的路径和名称，读取源文件的数据块，确定目标路径，如果目标路径与源路径相同，生成一个不重名的新文件名，最后在目标目录中分配新的文件节点并复制数据块。在执行复制文件操作后，指定的文件将在目标目录中创建一个副本，副本文件的内容与原文件完全一致，如果在同一目录下会生成一个带有_copy后缀的新文件。

10. ##### 粘贴文件

    粘贴文件功能在 `FileManagementSystem` 类中实现，通过 `paste_item` 方法进行。检查是否存在复制的文件节点。如果是文件节点，调用 `copy_file` 方法复制文件到当前目录。如果是目录节点，调用 `copy_directory` 方法递归复制目录及其内容。更新文件视图和目录树视图。当用户粘贴文件时，系统会根据先前复制的文件或目录信息，在当前目录中创建一个副本。如果目标目录是源目录的子目录，会弹出警告窗口，防止无限递归复制。

11. ##### 属性显示

    显示文件或目录属性功能通过 `show_inode_properties` 方法实现。此方法接收 `Inode` 对象作为参数，创建一个对话框显示文件或目录的各种属性信息。 用户可以查看指定文件或目录的详细属性信息，包括名称、路径、大小、创建时间、修改时间和类型等。

12. ##### 操作写入磁盘

    将操作写入磁盘功能通过 `IndexedFileSystem` 类中的 `save_to_disk` 方法实现。此方法接收文件名作为参数，将整个文件系统对象序列化并保存到指定文件中。文件系统的当前状态将被保存到磁盘文件中，确保所有操作结果被持久化存储，以便在下次启动时恢复文件系统的状态。

## 四、用户界面设计

1. #### 整体界面

![Image text](https://github.com/vapacity/TJ-OSlab3-FileManagement/blob/main/imgs/整体.png)

3. #### 界面功能点

   1. ##### 创建文件

      ![Image text](https://github.com/vapacity/TJ-OSlab3-FileManagement/blob/main/imgs/创建文件.png)

      右键点击空白处创建

      ![Image text](https://github.com/vapacity/TJ-OSlab3-FileManagement/blob/main/imgs/创建文件2.png)

   3. ##### 打开文件

      ![Image text](https://github.com/vapacity/TJ-OSlab3-FileManagement/blob/main/imgs/打开文件.png)

   5. ##### 写文件

      ![Image text](https://github.com/vapacity/TJ-OSlab3-FileManagement/blob/main/imgs/写文件.png)

   7. ##### 复制文件

      支持ctrl+C的快捷键

      ![Image text](https://github.com/vapacity/TJ-OSlab3-FileManagement/blob/main/imgs/复制文件.png)

   9. ##### 粘贴文件

      支持ctrl+V的快捷键

      粘贴在同一目录下如果有相同名字会增加"_copy"后缀

      ![Image text](https://github.com/vapacity/TJ-OSlab3-FileManagement/blob/main/imgs/粘贴文件.png)

   11. ##### 文件重命名

      ![Image text](https://github.com/vapacity/TJ-OSlab3-FileManagement/blob/main/imgs/文件重命名.png)

   11. ##### 查看文件属性

      文件类型尚未开发

      ![Image text](https://github.com/vapacity/TJ-OSlab3-FileManagement/blob/main/imgs/查看属性.png)

   11. ##### 删除文件

      支持delete快捷键

      ![Image text](https://github.com/vapacity/TJ-OSlab3-FileManagement/blob/main/imgs/删除文件.png)

   11. ##### 创建文件夹

      ![Image text](https://github.com/vapacity/TJ-OSlab3-FileManagement/blob/main/imgs/创建文件夹.png)

   11. ##### 打开文件夹

       ![Image text](https://github.com/vapacity/TJ-OSlab3-FileManagement/blob/main/imgs/打开文件夹.png)

   13. ##### 复制文件夹

       ![Image text](https://github.com/vapacity/TJ-OSlab3-FileManagement/blob/main/imgs/复制文件夹.png)

   15. ##### 粘贴文件夹

       递归复制文件夹内所有内容，同目录下重名更名规则与文件一致

       ![Image text](https://github.com/vapacity/TJ-OSlab3-FileManagement/blob/main/imgs/粘贴文件夹2.png)

   17. ##### 文件夹重命名

       ![Image text](https://github.com/vapacity/TJ-OSlab3-FileManagement/blob/main/imgs/文件夹重命名.png)

   19. ##### 文件夹属性

       文件夹的size尚未开发

       ![Image text](https://github.com/vapacity/TJ-OSlab3-FileManagement/blob/main/imgs/文件夹属性.png)

   21. ##### 删除文件夹

       递归删除文件夹内所有内容

       ![Image text](https://github.com/vapacity/TJ-OSlab3-FileManagement/blob/main/imgs/删除文件夹.png)

   23. ##### 目录显示

       ![Image text](https://github.com/vapacity/TJ-OSlab3-FileManagement/blob/main/imgs/目录显示.png)

       右键点击可选择展开/合拢文件夹

       ![Image text](https://github.com/vapacity/TJ-OSlab3-FileManagement/blob/main/imgs/目录显示2.png)

   25. ##### 目录跳转

       1. ###### 快速访问

          ![Image text](https://github.com/vapacity/TJ-OSlab3-FileManagement/blob/main/imgs/双击跳转.png)

       2. ###### 地址跳转

          可以键入绝对路径跳转到对应目录下

          ![Image text](https://github.com/vapacity/TJ-OSlab3-FileManagement/blob/main/imgs/地址跳转.png)

## 五、总结

1. ##### 心得体会

   文件系统是我在操作系统中最喜欢的章节，在实操写代码的过程中，更深刻的理解了文件系统的一些工作原理，对文件存储空间管理、空闲空间管理以及多级目录结构等概念有了更深的理解。

   在此过程中我提升了自己的编程技巧和编程习惯。

   但是代码的规范性和整洁程度不够完善，在此次项目中没有事先做好项目架构，对前端的类的划分很模糊，在之后有时间会进一步完善。

2. ##### 改进方向

   将代码重构，拆分成更多的类便于维护。

   UI界面改进，增强其可交互性。

   补充功能，包括剪切、查看方式、撤销等等，尽可能与实际操作系统的文件系统靠拢。

   

