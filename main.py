import os
import shutil
import layout_scanner
from Pdf2Html import Pdf2Html

#Make folder named with current time 'now'
now = raw_input("Please enter the name of the pdf file (e.g. test.pdf)\n")


# print(os.path.isfile(os.getcwd()+'/test/'+now))
if os.path.isfile(os.getcwd()+'/test/'+now):
	now = now[0:len(now)-4]
	if(os.path.exists(str(os.getcwd())+'/'+now)):
		shutil.rmtree(os.getcwd()+'/'+now)

	os.makedirs(now)
	os.makedirs(now+'/css')
	os.makedirs(now+'/img')
	os.chdir(os.getcwd()+'/'+now)

	# print(os.getcwd())
	# print(os.pardir+'/test/'+now+'.pdf')
	# print(os.path.isfile(os.pardir+'/test/'+now+'.pdf'))

	#Call the PDFminer parser, returns tree of PDF components.
	myparser=layout_scanner.get_pages(os.pardir+'/test/'+now+'.pdf')

	#Instantiate object from my converter Pdf2Html class
	converterObj = Pdf2Html()

	#Create html file 'index.html'
	converterObj.make_html(myparser)
