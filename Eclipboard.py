# coding: utf-8
from tcp import shortclient
from PIL import Image
import os,io,clipboard,datetime,zipfile,editor

client = shortclient()
home=os.path.join(os.path.expanduser('~'),"Documents")

def img(bytes):
	name=str(datetime.datetime.now())+'.png'
	with open(name,"wb") as img:
		img.write(bytes)

def file(name,bytes):
	with open(name,"wb")as file:
		file.write(bytes)

def text(bytes):
	clipboard.set(bytes.decode())
	
def send(content,sendtype="str"):
	if sendtype=="img":
		client.send("set_img_to_clipboard",content)
	elif sendtype=="path":
		if type(content)==io.BytesIO:
			client.send("set_files_to_clipboard",content)
		else:
			cb=io.BytesIO()
			zf = zipfile.ZipFile(cb, 'a',zipfile.ZIP_STORED)
			if type(content) ==str:
				zf.write(content,content.split("/")[-1])
			elif type(content)==list:
				for f in content:
					zf.write(f,f.split("/")[-1])
			zf.close()
			send(cb,sendtype)
			
	else:
		client.send("set_text_to_clipboard",str(content))
		
def get():
	data=client.send("getclipboard")
	if data[0]=="str":
		text(data[1])
	elif data[0]=="img":
		img(data[1])
	else:
		if len(data)>1:
			file(data[0],data[1])
			
def copy():
	open_file=editor.get_path()
	if open_file!=None:
		sel_start, sel_end = editor.get_selection()
		if sel_start==sel_end:
			if sel_start==0:
				send(str(open_file),"path")
			else:
				send(clipboard.get())
		else:
			send(editor.get_text()[sel_start:sel_end])
	else:
		if clipboard.get():
			send(clipboard.get())
		elif clipboard.get_image():
			bimg = io.BytesIO()
			clipboard.get_image().save(bimg, 'png')
			send(bimg,"img")
			
def paste():
	get()


def img(bytes):
	name=os.path.join(home,str(datetime.datetime.now())+'.png')
	with open(name,"wb") as img:
		img.write(bytes)
	clipboard.set_image(Image.open(io.BytesIO(bytes)), jpeg_quality=1)
def file(name,bytes):
	if ".zip" in name:
		zip_file = zipfile.ZipFile(io.BytesIO(bytes), 'r')
		zip_file.extractall(os.path.join(home,str(datetime.datetime.now())))
		zip_file.close()
	else:
		with open(os.path.join(home,name),"wb")as file:
			file.write(bytes)
