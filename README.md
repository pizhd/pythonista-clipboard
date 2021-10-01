# Pclipboard
用于windows系统和ios系统下pythonista与editorial应用的互传文本、图片和文件。

## 使用之前:
修改tcp.py
```python
_serverip_port = ('192.168.2.44', 2468)
# 改为自己windows电脑的IP与服务要使用的端口
```

## windows安装:
1. windows系统安装python环境
2. 将文件夹复制到合适的目录
3. 点击wsteup.py

## pythonista使用:
1. windows系统使用右键复制文件或文本
2. 运行Pclipboard.py,点击winTOios
3. 将文本或文件拖动到目标app下
4. 或点击copyTOclipboard,将文本复制到ios的剪切板
5. 仅能复制文本或图片到windows系统,在ios拷贝图片或文字后,点击iosTOwin,在windows系统下使用ctrl+v粘贴.注意图片和文字仅存在windows剪切板里

## editorial使用:
1. Eclipboard.py文件内置函数get()、copy()函数
2. get()->从windows获取剪切板数据，包括文本、图片、文件
3. copy()->从ios复制文件、文本、图片到windows
4. 通过ios的快捷指令和editorial内置功能workflow灵活使用
