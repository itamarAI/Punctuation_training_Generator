
# Training Set creation

Script to match audio transcripts with subtitles in Youtube videos
DO NOT USE MASTER, MAKE A COPY FOR NEW SCRIPT RUNS.
DO NOT UPLOAD USED SCRIPT SET TO GITHUB REPO (Or you'll accidentally upload many many gigabytes of random audio)

For consolidating all matched results see bottom of document.


Project structure:

```
├── data
│   ├── input_urls.xlsx                     <- List of urls for which videos need to be downloaded and processed
│
├── output                                  <- Output where results are saved.
│   └── video_list_urls.xlsx                <- Videos identified for the input urls
│   └── audio                               <- Folder where audio files (webm, aac) and subtitles are stored
│       └── <video_id>                      <- Folder for each video where chunks are stored for processing
│   └── subtitles                           <- Folder where text associated with subtitles are stored - one file for each videoid
│   └── transcript                          <- Folder where text associated with transcripts are stored - one file for each videoid
│   └── match_results                       <- Folder with Excel file for each video. Tab Matched_blocks contains the matched sentences
│
├── scripts                    
│   └── main_training_set_v2.py             <- Main script.
│   └── get_videos_url.py                   <- Get all videos associated with a list of urls
│   └── download_audio_subtitles.py         <- Downlload audio file and subtitles file for a video 
│   └── chunk_audio_file.py                 <- Split audio file into chunks by first splitting on silence and then combining to get 30 secs audio files
│   └── speech_transcript_api.py            <- Calls audio file to transcript api
│   └── parse_subtitlrs.py                  <- Parse the suntitles file to extract text 
│   └── transcript_subtitles_matching.py    <- Matches text in subtitle file with corresponding text in transcript file
│
├── README.md                               <- The top-level README for developers using this. 


Prerequisites:
---------------
1) Install required packages
    cdifflib
    nltk
    pandas
    pydub
    requests
    scrapetube
    unicode_slugify
    webvtt_py
    youtube_dl
    youtube_transcript_api
    yt_dlp
    diff-match-patch

2) Create the directory ./output, ./output/audio, ./output/subtitles, ./output/transcript, ./match_results
3) Create directory ./data
4) Create and store input_urls.xlsx in the ./data folder


Code structure
--------------
Six steps
1. Step 1 - Identify urls of Videos for each of the input urls
2. Step 2 - Download audio files and subtitles associated with the video
3. Step 3 - Chunk the audio files
4. Step 4 - Call speech transcript api for each chunk and save the text in a csv file
5. Step 5 - Parse subtitles and save the text in a csv file
6. Step 6 - Match subtitles and transcript for each video

Running the script:
---------------
1) Change diretory to ./scripts
2) python main_training_set_v2.py

Output
------
Matching output is stored in ./output/match_results
A Excel file is created for each videoid.


Running the script in stages:
-----------------------------

It is possiblle to run each of the steps separately. Of course for Step 2 to run, Step 1 output should be available.
Include steps to run in the steps_to_run list definition on line 34 of main_training_set_v2.py

Step 2 - audio file and subtitles file download takes a long time. You can split the runs by specifying video_start_row and video_end_row in lines 36 & 37

Step 3 - Audio files chunks are created only if directory with videoid is not created in ./output/audio

Step 4 - Speech transcript is callled for all videoids for which folder with chunk has been created i.e in ./output/audio/*

Step 5 - Parse subtitles is called for all videoids for all vtt files i.e in ./output/audio/*

Step 6 - Matching is run for those videoids for which a subtitles and transcript file can be found in ./output/subtitles and ./output/transcript respectively

Notes
-----
Step 3 - File chunking step takes long time as it does AudioSegmentReview for silence
Step 6 - Matching takes about 10 mins on a laptop for transcript with 500 sentences




To consolidate all matched results into a single csv at end of collection please follow these instructions:

- the file 'main_create_consolidated_training_set.py' is placed in the script directory. 
- pip install openpypxl has been done for mac.
- To run, cd into script directory and run the script. 
- All excel files with "matched_blocks" tab in ./output/match_results are read.
- Consolidated output is appended to the consolidated.csv file. If a previous file exists then it appends to it. 






Troubleshooting:
- If step 2 isn't applying the correct URLs try deleting the video_list_urls.xlsx. If there isn't one, it will be generated. 
- If no steps are operating correctly, try deleing all output files and starting with a fresh fileset. Never use master.