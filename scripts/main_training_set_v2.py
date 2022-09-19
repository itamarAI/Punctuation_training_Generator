
import pandas as pd
import os
import time
import glob
from pathlib import Path
import json
import csv
import time

import get_video_urls
import download_audio_subtitles
import chunk_audio_file
import speech_transcript_api
import parse_subtitles
import transcript_subtitles_matching

if __name__=="__main__":

    # Input filename
    inp_dir = "../data"
    inp_file = "input_urls.xlsx"
    input_fname = os.path.join(inp_dir,inp_file)

    # Output
    out_dir = "../output"
    out_video_list_file = "video_list_urls.xlsx"
    out_audio_dir = "../output/audio/*"
    chunks_root_dir = "../output/audio"
    transcription_audio_dir = "../output/transcript/"
    subtitles_dir = "../output/subtitles/"
    match_results_dir = "../output/match_results/"

    #steps_to_run = ['step1']
    steps_to_run = ['step1','step2','step3','step4','step5','step6']
    video_start_row = 0
    video_end_row = 50



########################### Step 1 - Videos for input urls ######################################## 
    if ('step1' in steps_to_run):
        print("Processing Step 1 - get videoids for input urls")
        df_inp = pd.read_excel(input_fname)
        df_url_parsed, df_url_parse_error = get_video_urls.parse_youtube_url(df_inp["URL"].to_list())
        #print(df_url_parsed)
        df_videos = get_video_urls.get_videos_for_url(df_url_parsed)
        #print(df_videos)


        writer = pd.ExcelWriter(os.path.join(out_dir,out_video_list_file), engine='xlsxwriter')

        df_inp.to_excel(writer, sheet_name="input_urls", index=False)
        df_url_parsed.to_excel(writer, sheet_name="parsed_urls", index=False)
        if (df_url_parse_error.shape[0] >0):
            df_url_parse_error.to_excel(writer, sheet_name="urls_parse_error", index=False)
        df_videos.to_excel(writer,sheet_name="videos_urls", index=False)

        writer.save()
########################### Videos for input urls ########################################    

    if ('step2' in steps_to_run):
        print("Processing Step 2 - videos for input urls")

        df_videos = pd.read_excel(os.path.join(out_dir,out_video_list_file), sheet_name="videos_urls")

########################## Step 2 - Download audio files and subtitles associated with the videos ########################################    

        for i,row in df_videos[video_start_row:video_end_row].iterrows():
            print("downloading file %s", row["video_url"])
            download_audio_subtitles.download_audio_subtitles(row["video_url"])
            time.sleep(5)
########################## Download audio files and subtitles associated with the videos ########################################    


########################### Step 3 - Chunk the audio files ########################################

    if ('step3' in steps_to_run):
        print("Processing Step 3 - chunk the audio file")

        # Get list of audio files downloaded
        audio_list = [x for x in glob.glob(out_audio_dir) if os.path.isfile(x) and Path(x).suffix != ".vtt"] 

        print("list of videos for which ")
        for audio_filename in audio_list:
            
            #Check if audio file has already been processed
            audio_chunk_dir = os.path.join(chunks_root_dir,Path(Path(audio_filename).name).stem)
            
            
            if ((Path(audio_chunk_dir).is_dir()) and len(os.listdir(audio_chunk_dir)) > 0):
                print("***Bypassing Audio file %s as chunks already exist" % audio_filename)
            else:
                #Create ~30 second chunks and convert to .aac format with 16K sample rate
                folder_name = chunk_audio_file.chunk_large_audio(audio_filename, chunks_root_dir)
########################### Chunk the audio files ########################################
    
########################### Step 4 - Call speech transcript api for each chunk and save the text in a csv file ########################################

    if ('step4' in steps_to_run):

        print("Processing Step 4 - call speech transcription")

        #Get list of all directories with chunk files
        all_chunk_directory_list = [x for x in glob.glob(out_audio_dir) if os.path.isdir(x)]
        tic = time.perf_counter()
        for audio_chunk_dir in all_chunk_directory_list:
            print("Speech transcription for %s" % audio_chunk_dir)
            transcription_error_list = []
            transcription_text_list = []
            transcription_text = ""
            for chunk_filename in sorted(glob.glob(audio_chunk_dir + "/*.aac")):
                print("processing speech transcription %s" % chunk_filename)
                response_out = speech_transcript_api.speech_transcript_api(chunk_filename)
                if (response_out.startswith("*** Error transcripting file")):
                    transcription_error_list = transcription_error_list + [chunk_filename]
                else:
                    transcription_text_list = transcription_text_list + [response_out]
            
            transcription_text = ' '.join(transcription_text_list)

            with open(os.path.join(transcription_audio_dir, str(Path(audio_chunk_dir).name) + ".txt"), 'w', encoding='UTF8') as f:
                f.write(transcription_text)
        toc = time.perf_counter()
        print(f"speech to text in {toc - tic:0.4f} seconds")
        #print(transcription_error_list)

# ########################### Step 4 - Call speech transcript api for each chunk and save the text in a csv file ########################################


# ########################### Step 5 - Parse subtitles and save the text in a csv file ########################################

    if ('step5' in steps_to_run):
        print("Processing Step 5 - parsing subtitles")

        # # Get list of vtt files downloaded
        vtt_list = [x for x in glob.glob(out_audio_dir) if os.path.isfile(x) and Path(x).suffix == ".vtt"] 

        for fname in vtt_list:
            filename_prefix = Path(Path(fname).name).stem
            #get the video id from the filename
            subtitle_output_fname = os.path.join(subtitles_dir,filename_prefix.split('.en-')[0] + ".txt")

            subtitle_text = parse_subtitles.vtt_to_linear_text(fname)

            #clean up subtitles before writing

            with open(subtitle_output_fname, 'w', encoding='UTF8') as f:
                f.write(subtitle_text)

# ########################### Step 5 - Parse subtitles and save the text in a csv file ########################################


########################### Step 6 - Matching ########################################

    if ('step6' in steps_to_run):

        #Get available pairs of subtitles and audio transcripts
        pairs_list = transcript_subtitles_matching.get_available_pairs(transcription_audio_dir, subtitles_dir)

        for item in pairs_list:
            print("Processing Step 6 - matching subtitles to transcript - %s" % item)

            fname_transcript = os.path.join(transcription_audio_dir, item + ".txt")
            fname_subtitle = os.path.join(subtitles_dir, item + ".txt")

            with open(fname_transcript, 'r') as f1:
                transcript_text = f1.read()

            with open(fname_subtitle, 'r') as f2:
                subtitle_text = f2.read()

            transcript_subtitles_matching.match_transcript_subtitles(item,subtitle_text, transcript_text,match_results_dir)

########################### Step 6 - Matching ########################################
