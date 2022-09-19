import subprocess
import os
from pydub import AudioSegment
from pydub.silence import split_on_silence
from pathlib import Path



def convert_chunks_to_sample_rate(chunk_filename, folder_name):

    output_filename = os.path.join(folder_name,Path(chunk_filename).stem + ".aac")
    return_code = subprocess.call(['ffmpeg','-loglevel','error','-y','-i',chunk_filename, "-acodec", "aac", "-ac", "1", "-ar", "16000", output_filename])

    return



# a function that splits the audio file into chunks

def chunk_large_audio(audio_filename, chunks_root_dir):

    #Create name of folder where chunks will be stored
    folder_name = os.path.join(chunks_root_dir,Path(audio_filename).stem)
    file_suffix = str(Path(audio_filename).suffix)

    print("Starting AudioSegment review")
    try:
        sound = AudioSegment.from_file(audio_filename, file_suffix)
    except:
        print("*** Error in processing audi0 file - AudioSegment not recognized %s" % audio_filename)
        return("*** Error")

    # split audio sound where silence is 500 miliseconds or more and get chunks
    chunks = split_on_silence(sound,
        min_silence_len = 500,
        silence_thresh = sound.dBFS-15,
        keep_silence=500,
    )
    print("Completed AudioSegment review")
    
    # create a directory to store the audio chunks
    if not os.path.isdir(folder_name):
        os.mkdir(folder_name)

    # process each chunk 
    chunk_counter = 0
    chunk_file = AudioSegment.empty()
    duration_counter = 0

    for i, audio_chunk in enumerate(chunks, start=1):
        flag = False
        duration_counter = duration_counter + audio_chunk.duration_seconds
        chunk_file = chunk_file + audio_chunk

        if (duration_counter >= 30):
            # export audio chunk and save it in the `folder_name` directory.
            chunk_counter = chunk_counter + 1
            chunk_filename = os.path.join(folder_name, f"chunk{str(chunk_counter).zfill(5)}.wav")
            print("exporting %s" % chunk_filename)
            chunk_file.export(chunk_filename, format="wav")
            duration_counter = 0
            flag = True
            chunk_file = AudioSegment.empty()
            #convert chunk file to teh right asmple rate and format
            convert_chunks_to_sample_rate(chunk_filename, folder_name)

        
    #Export the last chunk before returning
    if (flag == False):
        chunk_counter = chunk_counter + 1
        chunk_filename = os.path.join(folder_name, f"chunk{chunk_counter}.wav")
        print("exporting %s" % chunk_filename)
        chunk_file.export(chunk_filename, format="wav")
        convert_chunks_to_sample_rate(chunk_filename, folder_name)

    
    return(folder_name)

