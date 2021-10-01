# coding: utf-8
import ui
import os
import io
import tcp
import time
import clipboard
from PIL import Image
from objc_util import *
import sys

def find_view_by_name(subviews, name):
	for view in subviews:
		if view.name == name:
			return view
			
			
def label_state(view, statestr):
	view.text = time.strftime('%H:%M:%S ' + statestr, time.localtime())
	
	
global_cmd, global_bytesdata = None, None

def NSItemProvider(type, data, filename=None):
	if type == 'str':
		uti = 'public.utf8-plain-text'
		fdata = data.decode('utf-8')
		filename = 'text'
	elif type == 'img':
		uti = 'public.png'
		fdata = ui.Image.from_data(data, 2.0)
		filename = type
	else:
		uti='Url'
		fdata=data
		filename=type
	if type=='str' or type=='img':
		nsitem_provider = ObjCClass('NSItemProvider').alloc().initWithItem_typeIdentifier_(None, uti)
		nsitem_provider.registerObject_visibility_(fdata, 0)
		nsitem_provider.setSuggestedName_(filename)
		return [nsitem_provider]
	else:
		nsitem_provider=ObjCClass('NSItemProvider').alloc().initWithContentsOfURL_(nsurl(fdata))
		nsitem_provider.setSuggestedName_(filename)
		return [nsitem_provider]
		
		
def NSUIDragItem(nsdrag_list):
	nsui_drag_item = []
	for nsdrag in nsdrag_list:
		nsui_drag_item.append(ObjCClass('UIDragItem').alloc().initWithItemProvider(nsdrag))
	return nsui_drag_item
	
	
def Set_Drage(type, data, view):
	NSUIDragitems = NSUIDragItem(NSItemProvider(type, data))
	
	def dragInteraction_itemsForBeginningSession_(_m, _c, interaction, session):
		return ns(NSUIDragitems).ptr
		
	draginter = create_objc_class('dragDelegate', methods=[dragInteraction_itemsForBeginningSession_],
	protocols=['UIDragInteractionDelegate'])
	delegate = draginter.alloc().init()
	obj_draginter = ObjCClass('UIDragInteraction').alloc().initWithDelegate(delegate)
	obj_draginter.setEnabled(True)
	view.objc_instance.addInteraction(obj_draginter)
	
	
def winTOios(sender):
	global global_cmd, global_bytesdata
	msgview = find_view_by_name(sender.superview.superview.subviews, 'msglabel')
	dragview = find_view_by_name(find_view_by_name(sender.superview.superview.subviews, 'dropdragview').subviews,
	'dragview')
	dragview_text = find_view_by_name(dragview.subviews, 'textcopy')
	dragview_image = find_view_by_name(dragview.subviews, 'imagecopy')
	ccb = tcp.shortclient()
	cmd, data = ccb.send('getclipboard')
	global_cmd, global_bytesdata = cmd, data
	if cmd == 'str' or cmd == 'img':
		if cmd == 'str':
			dragview_text.hidden = False
			dragview_image.hidden = True
			dragview_text.text = data.decode()
		else:
			dragview_text.hidden = True
			dragview_image.hidden = False
			dragview_image.image = ui.Image.from_data(data, 2.0)
		Set_Drage(cmd, data, dragview)
		find_view_by_name(sender.superview.superview.subviews, 'copyToClipboard').enabled = True
	else:
		dragview_text.hidden = False
		dragview_image.hidden = True
		if not os.path.exists('files'):
			os.mkdir('files')
		filename='files/'+str(time.time())+cmd
		with open(filename,'wb')as file:
			file.write(data)
		dragview_text.text = cmd
		Set_Drage(cmd, filename, dragview)
		find_view_by_name(sender.superview.superview.subviews, 'copyToClipboard').enabled = False
	label_state(msgview, 'ToIOS Succeed')
	find_view_by_name(find_view_by_name(sender.superview.superview.subviews, 'dropdragview').subviews,
	'dragview').alpha = 1
	
	
def iosTOwin(sender):
	msgview = find_view_by_name(sender.superview.superview.subviews, 'msglabel')
	ccb = tcp.shortclient()
	text, img, cmd, databytes, rmsg = clipboard.get(), clipboard.get_image(), None, None, None
	if len(text) != 0:
		rmsg, rdata = ccb.send('set_text_to_clipboard', text)
	else:
		bimg = io.BytesIO()
		img.save(bimg, 'png')
		rmsg, rdata = ccb.send('set_img_to_clipboard', bimg)
	if rmsg == 'Successfully':
		label_state(msgview, 'ToWin Succeed')
		find_view_by_name(sender.superview.superview.subviews, 'copyToClipboard').enabled = False
		find_view_by_name(find_view_by_name(sender.superview.superview.subviews, 'dropdragview').subviews,
		'dragview').alpha = 0
	else:
		label_state(msgview, 'ToWin Failed')
		
		
def copyTOclipboard(sender):
	global global_cmd, global_bytesdata
	msgview = find_view_by_name(sender.superview.subviews, 'msglabel')
	if global_cmd == 'str':
		clipboard.set(global_bytesdata.decode())
		label_state(msgview, 'CopyToClipboard Succeed')
	elif global_cmd == 'img':
		clipboard.set_image(Image.open(io.BytesIO(global_bytesdata)), jpeg_quality=1)
		label_state(msgview, 'CopyToClipboard Succeed')
	else:
	
		label_state(msgview, 'CopyToClipboard Succeed')
		
if(len(sys.argv)>1):
	v = ui.load_view()
	v.present(sys.argv[1])
else:	
	v= ui.load_view()
	v.present("fullscreen")
