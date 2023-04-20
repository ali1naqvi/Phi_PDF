# Medical Document PHI Filter

## Project Description 
- A filter for PDFS containing PHI. The PDF was first converted to images and then scanned using OCR to extract the text. OCR was used primarily because the location of the text is given whereas other libraries/wrappers do not account for this. Next I used two stanford BERT Deidentifaction models to scan the text and give back words it considered PHI. From the results, I cleaned up the outputs as these models don't give exact words and are split up. The two different set of outputs that were given from the models were then compared and merged just in case one of the model missed words. The words were searched in the string and using OpenCV, the image was recreated with the text covered. Finally, the images are merged and the PDF is outputted in the output folder

## Built with 
- Python

## Steps to run the Project
1. pip install necessary libraries 
2. The pdfs that are to be used should go inside the input folder
3. run PhiPdf.py

Sample inputs are given in the input folder with fake patient information (created using CHATGPT). 


