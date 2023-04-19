#libraries
from pdf2image import convert_from_path
import cv2, pytesseract, re, img2pdf, os, glob
from PIL import Image 
from transformers import pipeline

Image.MAX_IMAGE_PIXELS = 100000000000


#convert pdf to jpgs
def make_pics(filename):
	print(filename)
	pages = convert_from_path(filename, 300)   
	i = 1
	for page in pages:
		print('page: ', page)
		image_name = 'Page_' + str(i) + '.jpg'  
		page.save(image_name, 'JPEG')
		i = i+1
	return i  

def ocr_test(image):
	stuff = ''
	pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'
	data = pytesseract.image_to_data(image, output_type = 'dict', config='--psm 6')
	return data

def filter_spaces(data):
	k = len(data['level']) 
	x = 0 
	while x !=k:
		try:
			if data['text'][x] != '':
				x +=1
			else:
				del data['text'][x]
				del data['block_num'][x]
				del data['par_num'][x]
				del data['line_num'][x]
				del data['word_num'][x]
				del data['left'][x]
				del data['top'][x]
				del data['width'][x]
				del data['height'][x]
				del data['conf'][x]  
		except:
			break
	return data


#remove the word from the jpg
def blur_func(imagename, data, to_erase):
	image = cv2.imread(imagename)
	sentence = ' '.join(data['text']).upper()
	sentence_words = sentence.split()
	counter = 0 
	
	for z in range(len(to_erase)):
		if to_erase[z]['word'].upper() in sentence:
			for i, word in enumerate(sentence_words):
				if word.startswith(to_erase[z]['word'].upper()):
					counter += 1
					(x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
					cv2.rectangle(image, (x, y), (x + w, y + h), (255, 255, 255), -1)
					sentence_words[i] = "@@@@"
					sentence = str()
					sentence = ' '.join(sentence_words)
					break
	
	print("words erased: ", counter)
	return image

#convert back to pdf 
def make_pdf(imagepath):
	images = glob.glob('*.jpg')
	with open(imagepath,'wb') as f:
		f.write(img2pdf.convert(images))


#remove jpg from the directory 
def remove_jpgs():

	filestotal = glob.glob('*.jpg')
	for file in filestotal:
		os.remove(file)

def model1(words):
	path = "models/stanford-deidentifier-base"
	classifier = pipeline('token-classification', path)
	data_string = " ".join(words['text'])
	filtered = classifier(data_string)
	return filtered

def model2(words):
	path = "models/stanford-deidentifier-with-radiology-reports-and-i2b2"
	classifier = pipeline('token-classification', path)
	data_string = " ".join(words['text'])
	filtered = classifier(data_string)
	return filtered


def compare_lists(words_first_model, words_second_model):
	i = j = 1
	while not i >= len(words_first_model):
		if words_first_model[i]['start'] == words_first_model[i-1]['end']:
			words_first_model[i]['word'] = (words_first_model[i-1]['word'] + words_first_model[i]['word']).replace("#", "")
			words_first_model[i]['start'] = words_first_model[i-1]['start']
			
			words_first_model[i]['index'] -= 1

			words_first_model.pop(i-1)
			i -= 1
		else:
			i +=1

	while not j >= len(words_second_model):
		if words_second_model[j]['start'] == words_second_model[j-1]['end']:
			words_second_model[j]['word'] = (words_second_model[j-1]['word'] + words_second_model[j]['word']).replace("#", "")
			words_second_model[j]['start'] = words_second_model[j-1]['start']

			words_first_model[j]['index'] -= 1

			words_second_model.pop(j-1)
			j -= 1
		else:
			j +=1
	
	for i in range(len(words_first_model)):
		for j in range(len(words_second_model)):
			if (words_second_model[j]['word'] != words_first_model[i]['word']) and j==len(words_first_model):
				words_first_model.append(words_second_model[j])
	
	return words_first_model

def words_to_erase(words_first_model, words_second_model):
	final_list = []
	
	for i in range(len(words_first_model)):
		del words_first_model[i]['entity']
		del words_first_model[i]['score']
	
	for i in range(len(words_second_model)):
		del words_second_model[i]['entity']
		del words_second_model[i]['score']
	
	final_list = compare_lists(words_first_model, words_second_model)
	return(final_list)
	  
def main(fileinput, fileoutput):
	inputs = glob.glob(fileinput+'*.pdf')
	print("inputs: ", inputs)
	for filename in inputs:
		i = 1
		#create pictures and get the counter for them as jpgtotal
		jpgtotal = make_pics(filename)
		print("\n\njpgtotal: ", jpgtotal-1)
		while i != jpgtotal:
			#get data from the first page, put in a loop later, for now hard coded
			page_loc = 'Page_' + str(i) + '.jpg'

			#get the data 
			data = ocr_test(page_loc)

			data = filter_spaces(data)

			#get new image after erasing the word from the specific page 
			words_first_model = model1(data)
			words_second_model = model2(data) 
			
			final_list = words_to_erase(words_first_model, words_second_model)

			#comp_str = string_erased(final_list, data)
			
			image = blur_func(page_loc, data, final_list)

			#save the new image with the old name so it replaces
			cv2.imwrite(page_loc, image)
			i += 1
		#remove the images from directory

		#replace the input directory in the name with the output
		filenamed = filename.replace(fileinput[:len(fileinput)-1], fileoutput[:len(fileoutput)-1])
		#combine all the jpgs and output the pdf in the output folder
		print("filename:", filenamed)
		make_pdf(filenamed)
		#remove the jpgs
		remove_jpgs()


if __name__ == '__main__':
	main('input/', 'output/')