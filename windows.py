# coding: utf-8
import tcp
import os
import io
import zipfile
import shutil
import ctypes
import pythoncom
import win32clipboard
import win32con
import win32gui
from PIL import BmpImagePlugin, Image
from ctypes.wintypes import DWORD, POINT, BOOL


class clipboard():
	clipboardFormat = [
	win32clipboard.CF_UNICODETEXT,
	win32clipboard.CF_DIB,
	win32clipboard.CF_HDROP
	]
	clipboard = None
	
	def __init__(self):
		wc = win32gui.WNDCLASS()
		wc.lpszClassName = 'Clipboard_Window'
		wc.hbrBackground = win32con.COLOR_BTNFACE + 1
		wc.lpfnWndProc = self.__wndProc
		class_atom = win32gui.RegisterClass(wc)
		self.__hwnd = win32gui.CreateWindow(
		class_atom, 'Clipboard_Window', win32con.WS_OVERLAPPEDWINDOW,
		win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT,
		win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT,
		0, 0, 0, None)
		
	def __setclipboarddata(self, datatype, bytesdata):
	
		# print('here_setdata_size'+str(len(data)))
		win32clipboard.SetClipboardData(datatype, bytesdata.getvalue().decode())
		
	def set(self, setcmd_str, bytesdata):
		ret, data = None, None
		win32clipboard.OpenClipboard()
		win32clipboard.EmptyClipboard()
		try:
			if setcmd_str == 'set_img_to_clipboard':
				img = io.BytesIO()
				Image.open(io.BytesIO(bytesdata.getvalue())).save(img, 'BMP')
				win32clipboard.SetClipboardData(win32clipboard.CF_DIB, img.getvalue()[14:])
			elif setcmd_str == 'set_text_to_clipboard':
				win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, bytesdata.getvalue().decode())
			elif setcmd_str == 'set_files_to_clipboard':
				class DROPFILES(ctypes.Structure):
					_fields_ = (('pFiles', DWORD),
					('pt', POINT),
					('fNC', BOOL),
					('fWide', BOOL))
					
				tmp_dir = os.path.join(os.getenv('TEMP'), 'clip_tmp_dir')
				if not os.path.exists(tmp_dir):
					os.makedirs(tmp_dir)
				for old in os.listdir(tmp_dir):
					file_path = os.path.join(tmp_dir, old)
					if os.path.isfile(file_path):
						os.remove(file_path)
					elif os.path.isdir(file_path):
						shutil.rmtree(file_path)
				zip_file = zipfile.ZipFile(io.BytesIO(bytesdata.getvalue()), 'r')
				zip_file.extractall(tmp_dir)
				zip_file.close()
				temp_file_paths = [os.path.join(tmp_dir, i) for i in os.listdir(tmp_dir)]
				offset = ctypes.sizeof(DROPFILES)
				length = sum(len(p) + 1 for p in temp_file_paths) + 1
				size = offset + length * ctypes.sizeof(ctypes.c_wchar)
				buf = (ctypes.c_char * size)()
				df = DROPFILES.from_buffer(buf)
				df.pFiles, df.fWide = offset, True
				for path in temp_file_paths:
					array_t = ctypes.c_wchar * (len(path) + 1)
					path_buf = array_t.from_buffer(buf, offset)
					path_buf.value = path
					offset += ctypes.sizeof(path_buf)
				stg = pythoncom.STGMEDIUM()
				stg.set(pythoncom.TYMED_HGLOBAL, buf)
				win32clipboard.SetClipboardData(win32clipboard.CF_HDROP, stg.data)
			ret, data = 'Successfully', b''
		except:
			ret, data = 'Failed', b''
		win32clipboard.CloseClipboard()
		return ret, data
		
	def get(self):
		if self.clipboardtype == win32clipboard.CF_DIB:
			cb = io.BytesIO()
			BmpImagePlugin.DibImageFile(io.BytesIO(self.__clipboarddata)).save(cb, 'PNG')
			return 'img', cb
		elif self.clipboardtype == win32clipboard.CF_UNICODETEXT:
			cb = io.BytesIO(self.__clipboarddata.encode())
			return 'str', cb
		elif self.clipboardtype == win32clipboard.CF_HDROP:
			cb = None
			if len(self.__clipboarddata) == 1 and not os.path.isdir(self.__clipboarddata[0]):
				path = self.__clipboarddata[0]
				if os.path.exists(path) and (os.path.splitext(path)[-1]).lower() in ['.jpg', '.png', '.bmp']:
					cb = io.BytesIO()
					Image.open(path).save(cb, 'PNG')
					return 'img', cb
				else:
					try:
						with open(path, 'rb')as file:
							return os.path.basename(path), io.BytesIO(file.read())
					except Exception as error :
						return 'error.log',str(error).encode('utf-8')
			elif len(self.__clipboarddata) > 0:
				cb = io.BytesIO()
				file_list = []
				fdir_list = []
				
				def listdir(path):
					if (len(fdir_list) == 0):
						fdir_list.append(os.path.dirname(path))
					if not os.path.isdir(path):
						file_list.append(path)
					else:
						for cpath in os.listdir(path):
							listdir(os.path.join(path, cpath))
							
				for tpath in self.__clipboarddata:
					listdir(tpath)
					
				def appendfile(file_path):
					f = open(file_path, 'rb')
					file_contents = f.read()
					zf = zipfile.ZipFile(cb, 'a', zipfile.ZIP_STORED)
					zf.writestr(file_path.replace(fdir_list[0], ""), file_contents)
					for zfile in zf.filelist:
						zfile.create_system = 0
						f.close()
						
				for file_path_ in file_list:
					try:
						appendfile(file_path_)
					except:
						pass
				cb.seek(0)
				nstr = str(len(file_list)) + 'files'
				return nstr + '.zip', cb
				
	def __listen_clipboard(self):
		clipboard_format = win32clipboard.GetPriorityClipboardFormat(self.clipboardFormat)
		if clipboard_format in self.clipboardFormat:
			win32clipboard.OpenClipboard()
			self.__clipboarddata = win32clipboard.GetClipboardData(clipboard_format)
			win32clipboard.CloseClipboard()
			self.clipboardtype = clipboard_format
		else:
			self.clipboardtype = None
			
	def __wndProc(self, hwnd, msg, wParam, lParam):
		if msg == win32con.WM_DESTROY:
			win32gui.PostQuitMessage(0)
		if msg == win32con.WM_DRAWCLIPBOARD:
			self.__listen_clipboard()
		return win32gui.DefWindowProc(hwnd, msg, wParam, lParam)
		
	def __run(self):
		win32clipboard.SetClipboardViewer(self.__hwnd)
		win32gui.PumpMessages()
		
	def stop(self):
		os._exit(0)
		
	def run(self):
		tcpserver = tcp.shortserver()
		tcpserver.clipboard = self
		tcpserver.setDaemon(True)
		tcpserver.start()
		self.__run()

