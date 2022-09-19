
import requests
import json

def speech_transcript_api(chunk_filename):
        multipart_form_data = {
                'file': (chunk_filename, open(chunk_filename, 'rb')),
        }
        
        response = requests.post('http://35.194.20.242:8080/predict',
                                files=multipart_form_data)
        
        if (response.status_code == 200):
                return(json.loads(response.text)["text"])
        else:
                return("*** Error transcripting file %s" % chunk_filename)

