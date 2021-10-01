# coding: utf-8
import os

if (os.name == 'nt'):
	def steup(runpy='wsteup.py', runbat='Python_Pad_Clipboard_Auto_Run.bat'):
		trycount = 5
		while trycount:
			try:
				import PIL
				import win32clipboard
				break
			except:
				if (trycount == 0):
					os._exit(0)
				os.system(
				'pip install pywin32 -i http://mirrors.aliyun.com/pypi/simple  --trusted-host mirrors.aliyun.com')
				os.system(
				'pip install Pillow -i http://mirrors.aliyun.com/pypi/simple  --trusted-host mirrors.aliyun.com')
				trycount -= 1
		startup_path = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'Microsoft', 'Windows', 'Start Menu',
		'Programs', 'Startup')
		with open(runbat, 'w') as file:
			file.write('@echo off' + os.linesep)
			file.write('if "%1" == "h" goto begin' + os.linesep)
			file.write('mshta vbscript:createobject("wscript.shell").run("%~nx0 h",0)(window.close)&&exit' + os.linesep)
			file.write(':begin' + os.linesep)
			file.write('python "' + os.path.realpath(runpy) +'"'+ os.linesep)
			file.write('exit' + os.linesep)
		import pythoncom
		from win32com.shell import shell
		from win32com.shell import shellcon
		shortcut = pythoncom.CoCreateInstance(shell.CLSID_ShellLink, None, pythoncom.CLSCTX_INPROC_SERVER,
		shell.IID_IShellLink)
		shortcut.SetPath(os.path.realpath(runbat))
		shortcut.SetWorkingDirectory(os.path.abspath('.'))
		shortcut.QueryInterface(pythoncom.IID_IPersistFile).Save(os.path.join(startup_path, runbat + '.lnk'), 0)
		
		
	if (not os.path.exists('Python_Pad_Clipboard_Auto_Run.bat')):
		steup()
	import windows
	
	cb = windows.clipboard()
	with open("pid.txt","w") as file:
		file.write(str(os.getpid()))
	cb.run()

