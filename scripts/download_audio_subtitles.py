import yt_dlp
from yt_dlp.utils import DownloadError
import requests
import os
import json

def list_formats(link):
    ydl_opts = {'listformats': True, 'skip_download': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print(ydl.download(link))
        
class FilenameCollectorPP(yt_dlp.postprocessor.common.PostProcessor):
    def __init__(self):
        super(FilenameCollectorPP, self).__init__(None)
        self.filenames = []

    def run(self, information):
        self.filenames.append(information['filepath'])
        return [], information


def download_audio_subtitles(link):

        # 'postprocessors': [{
        #     'key': 'FFmpegExtractAudio',
        #     'preferredcodec': 'mp3',
        #     'preferredquality': '192',
        # }],


    ydl_opts = {
        'outtmpl': '../output/audio/%(id)s.%(ext)s',
        'format': 'bestaudio/best[asr=16000]',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitle': '--write-sub --sub-lang en'
    }
    ydl = yt_dlp.YoutubeDL(ydl_opts)
    
    filename_collector = FilenameCollectorPP()
    ydl.add_post_processor(filename_collector)
    
    try:
        ydl.download([link])
    except Exception as e:
            if isinstance(e, DownloadError):
                pass
            elif hasattr(e, 'message'):
                if "Command returned error code 23" in e.message:
                    pass
                else:
                    raise(e)
            else:
                raise(e)      
    return filename_collector.filenames[0]

# if __name__=="__main__":

#     youtube_link = "https://youtu.be/syXplPKQb_o"
#     filename = download_audio(youtube_link)
#     print(filename)