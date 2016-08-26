from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTLine, LTFigure, LTImage, LTChar, LTRect, LTCurve

#PDF to HTML converter class
class Pdf2Html:
	"""docstring for Pdf2Html"""
	def __init__(self):
		# self.arg = arg
		self.f = open('index.html','wb')
		pass

	def make_html(self,pages):
		f = self.f
		self.header_tag(f)
		for lt_obj in pages:
			if lt_obj[1]=='p':
				self.page_tag(f,lt_obj[0])
			elif isinstance(lt_obj[2], LTTextBox) or isinstance(lt_obj[2], LTTextLine):
				self.text_tag(f,lt_obj[0],lt_obj[1])
			elif isinstance(lt_obj[2], LTImage):
				self.image_tag(f,lt_obj[0],lt_obj[1])
			elif isinstance(lt_obj[6], LTRect) or isinstance(lt_obj[6], LTLine):
				self.rect_tag(f,lt_obj[1], lt_obj[2], lt_obj[3], lt_obj[4],lt_obj[5])

		self.footer_tag(f)
		f.close()
		f = None
		self.f = None
		pages = None

	def header_tag(self,f):
		f.write('<!DOCTYPE html>\n<html>\n<head>\n<title></title>\n<link rel="stylesheet" type="text/css" href="css/mystyle.css">\n</head>\n<body>\n')

	def footer_tag(self,f):
		f.write('</body></html>\n')

	def page_tag(self,f,pgnum):
	    f.write('<span style="position:absolute; border: black 0.5px solid; '
	               'left:20px; top:%dpx; width:1030px; height:%dpx;"></span>\n' %
	               (
	                pgnum*100 + (pgnum-1)*1300,
	                1300,
	                ))

	def text_tag(self,f,idd,text):
		f.write('<SPAN id="id_%s">%s</SPAN>\n' %(idd,text.replace('\n','<br>')))

	def image_tag(self,f,idd,path):#, item, borderwidth, x, y, w, h):
		f.write('<SPAN id="id_%s"><img src="%s" ></SPAN>\n' %(idd,path))

	def rect_tag(self,f, x, y, w, h,pgnum):
	    f.write('<span style="position:absolute; border: black 1px solid; '
	               'left:%dpx; top:%dpx; width:%dpx; height:%dpx;"></span>\n' %
	               (
	                x*1.8, 1.5*(936*pgnum-y),
	                w*1.8, h*1.5))
