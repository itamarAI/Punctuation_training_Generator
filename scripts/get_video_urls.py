
from urllib.parse import urlparse, parse_qs
import scrapetube
import pandas as pd

def parse_youtube_url(url_list):
    url_parsed_list = []
    url_parse_error_list = []

    for url in url_list:
        if url.startswith(('youtu', 'www')):
            url = 'http://' + url
                
        query = urlparse(url)
        if (('youtube' in query.hostname) or ('youtu.be' in query.hostname)):
            #print(url, "\n", query)

            if (query.hostname == 'youtu.be'):
                url_parsed_list = url_parsed_list + [["video",url,query.path[1:]]]
            
            elif query.path == '/watch':
                url_parsed_list = url_parsed_list + [["video",url,parse_qs(query.query)['v'][0]]]
            
            elif query.path.startswith(('/embed/', '/v/')):
                if (len(query.path.split('/')) > 0): # 'http://www.youtube.com/v/_lOT2p_FCvA?version=3&amp;hl=en_US
                    url_parsed_list = url_parsed_list + [["video",url,query.path.split('/')[2]]]
                else: #http://www.youtube.com/embed/_lOT2p_FCvA
                    url_parsed_list = url_parsed_list + [["video",url,query.path]]
            
            elif query.path.startswith(('/playlist')):
                url_parsed_list = url_parsed_list + [["playlist",url,parse_qs(query.query)["list"][0]]]
            
            elif (query.path.startswith(('/channel/'))):
                CHANNEL_ID = query.path.split('/')[2]
                new_url = "https://www.youtube.com/channel/" + CHANNEL_ID
                url_parsed_list = url_parsed_list + [["channel", new_url,CHANNEL_ID]]
            
            elif (query.path.startswith(('/c/'))):
                CHANNEL_ID = query.path.split('/')[2]
                new_url = "https://www.youtube.com/c/" + CHANNEL_ID
                url_parsed_list = url_parsed_list + [["channel", new_url,CHANNEL_ID]]
            
            else:
                url_parse_error_list = url_parse_error_list + [url]
                print("No match found")
        
    df_url_parsed = pd.DataFrame(url_parsed_list,columns=["url_type","url","id"])
    if (len(url_parse_error_list) > 0):
        df_url_parse_error = pd.DataFrame(url_parse_error_list,columns=["url"])
    else:
        df_url_parse_error = pd.DataFrame()
        
    return([df_url_parsed,df_url_parse_error])

def get_videos_for_url(df_url_parsed):
    video_list = []
    for i,row in df_url_parsed.iterrows():
        print("Getting videos for url %s" % row["url"])
        if row["url_type"] == "channel":
            try:
                for video in scrapetube.get_channel(None,row["url"]):
                    video_title = video["title"]["runs"][0]["text"]
                    video_url = "https://www.youtube.com/watch?v="+ str(video['videoId'])
                    video_list = video_list + [[row["url"],video['videoId'], video_url, video_title]]
            except:
                print("error in channel url : %s" % row["url"])
                continue

        elif row["url_type"] == "playlist":
            try:
                for video in scrapetube.get_playlist(row["id"]):
                    video_title = video["title"]["runs"][0]["text"]
                    video_url = "https://www.youtube.com/watch?v="+ str(video['videoId'])
                    video_list = video_list + [[row["url"],video['videoId'], video_url, video_title]]
            except:
                print("error in playlist url : %s" % row["url"])
                continue

        elif row["url_type"] == "video":
                video_url = row["url"]
                video_id = row["id"]
                video_list = video_list + [[row["url"],video_id, video_url, ""]]
        else:
            try:
                for video in scrapetube.get_search(row["id"]):
                    video_title = video["title"]["runs"][0]["text"]
                    video_url = "https://www.youtube.com/watch?v="+ str(video['videoId'])
                    video_list = video_list + [[row["url"],video['videoId'], video_url, video_title]]
            except:
                print("error in other url : %s" % row["url"])
                continue


    df_video_list = pd.DataFrame(video_list, columns=["input_url","video_id","video_url","video_title"])
    return(df_video_list)

