import os, shutil
import requests
from bs4 import BeautifulSoup as bs
from PIL import Image
from fpdf import FPDF
from flask import Flask, render_template, url_for, request

app = Flask(__name__)

@app.route('/')
def home():
	return render_template('index.html')

@app.route('/article', methods=['POST'])
def article():
	url = request.form['url']

	result = scrape_data(url)
	pdf_filename = create_pdf(result)
	return render_template('article.html', result=result,pdf_filename=pdf_filename)


url = 'https://www.livescience.com/3945-history-dinosaurs.html'
def scrape_data(url):
	data = []

	headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0'}
	response = requests.get(url, headers=headers)

	soup = bs(response.content, 'html.parser')
	article = soup.find('article', {'class':'news-article'})

	title = article.find('h1').get_text().strip()
	data.append({'title':title})

	author_tags = article.find_all('span', {'class':'by-author'})
	authors = ''
	for author in author_tags:
		authors += author.get_text().strip() + ' '
	data.append({'authors':authors})

	intro = article.find('p', {'class':'strapline'}).get_text().strip()
	data.append({'intro':intro})

	try:
		img = article.find('img', {'class':'hero-image'})['data-original-mos']
		data.append({'img':img})
	except:
		pass

	article_body = article.find('div', {'id':'article-body'})
	tags = article_body.find_all(['p','h3','img','li'])

	for tag in tags:
		if tag.name == 'p':
			p_text = tag.get_text().strip()
			if(len(p_text) > 0 and not p_text.startswith('Related')):
				if ','.join(tag.parent['class']).find('fancy') == -1:
					data.append({'p':p_text})					
		elif tag.name == 'h3':
			data.append({'h3': tag.get_text().strip()})			
		elif tag.name == 'li':
			data.append({'li':tag.get_text().strip()})			
		elif tag.name == 'img':
			data.append({'img':tag['data-original-mos']})

	return data

def download_images(data, folder_name):
	urls = []

	# get all urls
	for item in data:
		if item.get('img'):
			urls.append(item.get('img'))

	# create folder for images
	if not os.path.exists(folder_name):
		os.makedirs(folder_name)

	# download images in folder
	for url in urls:
		response = requests.get(url)
		img_name = url.split('/')[-1]
		with open(os.path.join(folder_name,img_name), 'wb') as file:
			file.write(response.content)

def create_pdf(data):
	folder_name = 'images'
	download_images(data, folder_name)

	pdf = FPDF(orientation='P', unit='pt', format='A4')
	pdf.add_font('Helvetica', style='', fname='fonts/Helvetica.ttf', uni=True)
	pdf.add_font('Helvetica', style='B', fname='fonts/Helvetica-Bold.ttf', uni=True)
	pdf.add_font('Helvetica', style='I', fname='fonts/Helvetica-Oblique.ttf', uni=True)
	pdf.add_font('Helvetica', style='BI', fname='fonts/Helvetica-BoldOblique.ttf', uni=True)

	pdf.add_page()

	for item in data:
		if item.get('title'):
			pdf.set_text_color(249, 174, 59)
			pdf.set_font(family='Helvetica', style='B', size=34)
			pdf.multi_cell(w=0, h=50, txt=item.get('title'), align='C')
		elif item.get('authors'):
			pdf.set_text_color(0,0,0)
			pdf.set_font(family='Helvetica', style='B',size=14)
			pdf.cell(w=0, h=50, txt='By ' + item.get('authors'), align='C',ln=1)
		elif item.get('intro'):
			pdf.set_text_color(2, 56, 83)
			pdf.set_font(family='Helvetica', style='B', size=14)
			pdf.multi_cell(w=500, h=20, txt=item.get('intro'), align='C')
			pdf.cell(w=0,h=20,txt='',ln=1)
		elif item.get('p'):
			pdf.set_text_color(0,0,0)
			pdf.set_font(family='Helvetica', size=12)
			pdf.multi_cell(w=0, h=15, txt=item.get('p'))
			pdf.cell(w=0,h=20,txt='',ln=1)
		elif item.get('h3'):
			pdf.set_text_color(46, 169, 223)
			pdf.set_font(family='Helvetica', style='B', size=16)
			pdf.multi_cell(w=0, h=15, txt=item.get('h3'))
			pdf.cell(w=0,h=20,txt='',ln=1)
		elif item.get('li'):
			pdf.set_text_color(0,0,0)
			pdf.set_font(family='Helvetica', size=12)
			pdf.multi_cell(w=0, h=15, txt='\u2022' + item.get('li'))
			pdf.cell(w=0,h=20,txt='',ln=1)
		elif item.get('img'):
			img_name = item.get('img').split('/')[-1]
			img = Image.open(os.path.join(folder_name,img_name))
			img.close()
			img_width = img.width if img.width <= 400 else 400
			img_x = (pdf.w - img_width) // 2
			pdf.image(os.path.join(folder_name,img_name), w=img_width, x=img_x)
			pdf.cell(w=0,h=20,txt='',ln=1)

	pdf_filename = 'static/' + data[0]['title'].lower().replace(' ', '_').replace('?','') + '.pdf'
	pdf.output(pdf_filename)

	# delete images folder
	shutil.rmtree(folder_name)

	return data[0]['title'].lower().replace(' ', '_').replace('?','') + '.pdf'

if __name__ == "__main__":
	app.run(debug=True)