#libraries
from pdf2image import convert_from_path
import cv2, pytesseract, re, img2pdf, os, glob, philter_lite
from PIL import Image 
from transformers import AutoTokenizer, AutoModel, pipeline
from copy import deepcopy


from numpy import save, load, asarray

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


#get ocr to create data, data is with dictionary to make faster
def ocr_test(image):
    stuff = ''
    pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'
    # convert the image to black and white for better OCR
    #gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    data = pytesseract.image_to_data(image, output_type = 'dict', config='--psm 6')
    #write string into a text file
    return data

#remove the word from the jpg
def blur_func(imagename, data, to_erase):
    print(data['text'])
    print(to_erase)
    image = cv2.imread(imagename)
    boxes = len(data['level'])
    for z in range(len(to_erase)):
        for i in range(boxes):
            if int(data['conf'][i]) > 60:
    	        if to_erase[z]['word'].upper() ==  data['text'][i].upper() :
                    (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
                    image = cv2.rectangle(image, (x, y), (x + w, y + h), (255, 255, 255), -1)
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
    print("STRING GOING IN ------------------------", data_string)
    filtered = classifier(data_string)
    print(filtered)
    print("FIRST---------------------")
    return filtered

def model2(words):
    path = "models/stanford-deidentifier-with-radiology-reports-and-i2b2"
    classifier = pipeline('token-classification', path)
    data_string = " ".join(words['text'])
    filtered = classifier(data_string)
    print("STRING GOING IN ------------------------", data_string)
    print(filtered)
    print("SECOND---------------------")
    return filtered


def compare_lists(words_first_model, words_second_model):
    i = j = 1
    while i != len(words_first_model):
        if words_first_model[i]['start'] == words_first_model[i-1]['end']:
            words_first_model[i]['word'] = (words_first_model[i-1]['word'] + words_first_model[i]['word']).replace("#", "")
            words_first_model[i]['start'] = words_first_model[i-1]['start']
            words_first_model.pop(i-1)
            i -= 1
        else:
            i +=1

    while j != len(words_second_model):
        if words_second_model[j]['start'] == words_second_model[j-1]['end']:
            words_second_model[j]['word'] = (words_second_model[j-1]['word'] + words_second_model[j]['word']).replace("#", "")
            words_second_model[j]['start'] = words_second_model[j-1]['start']
            words_second_model.pop(j-1)
            j -= 1
        else:
            j +=1
    
    for i in range(len(words_first_model)):
        for j in range(len(words_second_model)):
            if words_second_model[j]['word'] != words_first_model[i]['word'] and j==len(words_first_model):
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
        print("jpgtotal: ", jpgtotal-1)
        while i != jpgtotal:
            #get data from the first page, put in a loop later, for now hard coded
            page_loc = 'Page_' + str(i) + '.jpg'

            #get the data 
            data = ocr_test(page_loc)

            #get new image after erasing the word from the specific page 
            words_first_model = model1(data)
            words_second_model = model2(data) 
            
            final_list = words_to_erase(words_first_model, words_second_model)
            
            image = blur_func(page_loc, data, final_list) 
            


            #save the new image with the old name so it replaces
            cv2.imwrite(page_loc, image)
            i += 1
        #remove the images from directory

        #replace the input directory in the name with the output
        filename = re.sub('input', 'output', filename)
        #combine all the jpgs and output the pdf in the output folder
        print("filename:", filename)
        make_pdf(filename)
        #remove the jpgs
        remove_jpgs()


if __name__ == '__main__':
    main('input/', 'output/')