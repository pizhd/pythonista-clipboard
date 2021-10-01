# coding: utf-8
import io
import os
import platform
from socket import *
from threading import Thread

_serverip_port = ('192.168.2.44', 2468)


# 装填器,cmd可以为str或bytes
# content可以为path、str、bytes、io.BytesIO
# 返回message+data格式的BytesIO()
class data_filler:
	def __init__(self, cmd, content):
		dataio = io.BytesIO()
		if isinstance(content, str):
			if os.path.isfile(content):
				with open(content, 'rb') as file:
					dataio.write(file.read())
			else:
				dataio.write(content.encode())
		elif isinstance(content, bytes):
			dataio.write(content)
		elif isinstance(content, io.BytesIO):
			dataio = content
		dataio.seek(0, 2)
		if isinstance(cmd, str):
			cmd = cmd.encode()
		cmd_bytes = cmd + b',' + str(dataio.tell()).encode()
		self.data = io.BytesIO()
		self.data.write(str(len(str(len(cmd_bytes)))).encode())
		self.data.write(str(len(cmd_bytes)).encode())
		self.data.write(cmd_bytes)
		self.data.write(dataio.getvalue())
		
		
# 接收器，接受装填器组合的数据
# func push_last_cache用来接受上一轮多余的BytesIO()
# push用来接受装填器组装的bytes数据，接收完后，多余读取的数据保存在earnings_bytesdata里，它是一个BytesIO()
# 接收完毕后可获取str类型的cmd命令信息和BytesIO()类型的bytesdata信息
class data_receiver:
	def __init__(self):
		self.cmd = ''
		self.bytesdata = io.BytesIO()
		self.earnings_bytesdata = io.BytesIO()
		self.finish = False
		self.__bytesdata_size = 0
		self.__bytesdata_progress = 0
		self.__receiver_active = False
		self.__truncate_cache = io.BytesIO()
		
	def push_last_cache(self, cache_bytesdata):
		self.__truncate_cache = io.BytesIO()
		self.__truncate_cache.write(cache_bytesdata.getvalue())
		self.__truncate_cache.seek(0, 2)
		
	def push(self, bytesdata):
		if self.finish:
			self.earnings_bytesdata.write(bytesdata)
			return
		if not self.__receiver_active:
			if self.__truncate_cache.tell() > 0:
				self.__truncate_cache.write(bytesdata)
				bytesdata = self.__truncate_cache
			else:
				bytesdata = io.BytesIO(bytesdata)
			bytesdata.seek(0, 2)
			if bytesdata.tell() > 1:
				bytesdata.seek(0)
				message_length_bit = int(bytesdata.read(1))
				bytesdata.seek(0, 2)
				if bytesdata.tell() - 1 > message_length_bit:
					bytesdata.seek(1)
					message_length = int(bytesdata.read(message_length_bit))
					bytesdata.seek(0, 2)
					if bytesdata.tell() >= message_length + message_length_bit + 1:
						bytesdata.seek(1 + message_length_bit)
						message = bytesdata.read(message_length).decode().split(',')
						self.cmd, self.__bytesdata_size = ','.join(message[:-1]), int(message[-1])
						self.__receiver_active = True
						nowseek = bytesdata.tell()
						bytesdata.seek(0, 2)
						if bytesdata.tell() - nowseek < self.__bytesdata_size:
							bytesdata.seek(nowseek)
							self.bytesdata.write(bytesdata.read())
							self.__bytesdata_progress = self.bytesdata.tell()
						else:
							bytesdata.seek(nowseek)
							self.bytesdata.write(bytesdata.read(self.__bytesdata_size))
							self.earnings_bytesdata.write(bytesdata.read())
							self.finish = True
					else:
						self.__truncate_cache = bytesdata
				else:
					self.__truncate_cache = bytesdata
			else:
				self.__truncate_cache = bytesdata
		else:
			bytesdata = io.BytesIO(bytesdata)
			bytesdata.seek(0, 2)
			self.bytesdata.seek(0, 2)
			if self.__bytesdata_progress + bytesdata.tell() < self.__bytesdata_size:
				self.bytesdata.write(bytesdata.getvalue())
				self.__bytesdata_progress += bytesdata.tell()
			else:
				bytesdata.seek(0)
				self.bytesdata.write(bytesdata.read(self.__bytesdata_size - self.__bytesdata_progress))
				self.__bytesdata_progress += bytesdata.tell()
				self.earnings_bytesdata.write(bytesdata.read())
				self.finish = True
				
				
class shortserver(Thread):
	clipboard = None
	
	def __init__(self):
		Thread.__init__(self)
		self.tcpSerSock = socket(AF_INET, SOCK_STREAM)
		self.tcpSerSock.bind(_serverip_port)
		self.tcpSerSock.listen(5)
		self.bufsiz = 1024 * 1024*20
		
	def run(self):
		if self.clipboard:
			self.__run()
			
	def __run(self):
		self.server_run = True
		while self.server_run:
			tcpCliSock, addr = self.tcpSerSock.accept()
			rd = data_receiver()
			while not rd.finish:
				data = tcpCliSock.recv(self.bufsiz)
				if not data:
					break
				rd.push(data)
			self.rec_msg(rd.cmd, rd.bytesdata, tcpCliSock)
			tcpCliSock.close()
		self.tcpSerSock.close()
		self.clipboard.stop()
		
	def rec_msg(self, cmd, bytesdata, tcpCliSock):
		recmd, redata = None, None
		if cmd == 'getclipboard':
			clip = self.getclipboard(cmd, bytesdata)
			if clip:
				recmd, redata = clip
		elif cmd == 'stop_clipboard_server':
			self.server_run = False
		else:
			clip = self.setclipboard(cmd, bytesdata)
			if clip:
				recmd, redata = clip
		if recmd:
			fd = data_filler(recmd, redata)
			tcpCliSock.sendall(fd.data.getvalue())
			
	def getclipboard(self, cmd, bytesdata):
		return self.clipboard.get()
		
	def setclipboard(self, cmd, bytesdata):
		return self.clipboard.set(cmd, bytesdata)
		
		
class shortclient:
	def __init__(self):
		self.tcp_client_socket = socket(AF_INET, SOCK_STREAM)
		self.tcp_client_socket.settimeout(20)
		self.bufsiz = 1024 * 1024*20
		
	def send(self, cmd, bytes=''):
		self.tcp_client_socket.connect(_serverip_port)
		rd = data_receiver()
		rf = data_filler(cmd, bytes)
		self.tcp_client_socket.sendall(rf.data.getvalue())
		while not rd.finish:
			data = self.tcp_client_socket.recv(self.bufsiz)
			if not data:
				break
			rd.push(data)
		self.tcp_client_socket.close()
		return [rd.cmd, rd.bytesdata.getvalue()]

