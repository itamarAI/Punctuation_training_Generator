import pandas as pd
import nltk
#nltk.download('punkt')
import string
from collections import OrderedDict
import re
import difflib
from nltk.util import ngrams
import codecs
import random
import os
from cdifflib import CSequenceMatcher
import glob
from pathlib import Path

from functools import wraps
import time
from diff_match_patch import diff_match_patch

def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        #print(f'Function {func.__name__}{args} {kwargs} Took {total_time:.4f} seconds')
        print(f'Function {func.__name__} Took {total_time:.4f} seconds')

        return result
    return timeit_wrapper


#@timeit
def find_sentences(inp_text):
    sentences= nltk.sent_tokenize(inp_text)
    words_count = [ len(nltk.word_tokenize(x)) for x in sentences]
    return([sentences,words_count])

#Create a dictionary that has the standardized sentence as key, and sentence with punctuations as value
#@timeit
def create_dict_sentences(sentences_list):
    sentence_dict = OrderedDict()

    translator = str.maketrans(string.punctuation, ' '*len(string.punctuation))
    for sentence in sentences_list:
        #Single quotes should be replaced by a null string
        sentence_dict[sentence.lower().replace("'","").translate(translator)] = sentence
        #sentence_dict[sentence.lower().translate(str.maketrans('', '', string.punctuation))] = sentence
    
    return(sentence_dict)


#Match a sentence to the text
#@timeit
# def match_sentence_to_audio_text(sentence_key,sentence_value,audio_text):

#     #Use the C version of SequenceMatcher
#     difflib.SequenceMatcher = CSequenceMatcher

#     #Check 1 - if substring in string
#     query_string = sentence_key
#     large_string = audio_text

#     search_output = re.search(query_string, audio_text)
#     if search_output is not None:
#         match_type = "exact match"
#         match_similarity = 1.0
#         match_sentence = sentence_value
#         match_query = query_string
#         match_audio_text_interim = search_output.group(0)
#         match_audio_text_final = search_output.group(0)
#         match_start = search_output.start
#         match_end = search_output.end
#         #print("exact found ", 1.0, "\n", sentence_value, "\n", search_output.group(0), "\n")
#     else:
#         # Check 2 - Uses ngrams to find longest match
#         query_string_length  = len(query_string.split())
#         max_sim_val    = 0
#         max_sim_string = u""

#         for ngram in ngrams(large_string.split(), query_string_length + int(0*query_string_length)):
#             hay_ngram = u" ".join(ngram)
#             similarity = difflib.SequenceMatcher(None, hay_ngram, query_string).ratio()

#             if similarity > max_sim_val:
#                 max_sim_val = similarity
#                 max_sim_string = hay_ngram

#                 #print("fuzzy found", max_sim_val, "\n", sentence_value, "\n", query_string, "\n", max_sim_string, "\n", max_sim_string, "\n",)
#                 match_type = "fuzzy_1iter_found"
#                 match_similarity = max_sim_val
#                 match_sentence = sentence_value
#                 match_query = query_string
#                 match_audio_text_interim = max_sim_string
#                 match_audio_text_final = max_sim_string

#     return([match_type,match_similarity,match_sentence, match_query,match_audio_text_interim,match_audio_text_final])

def match_sentence_to_audio_text(sentence_key,sentence_value,audio_text, location):
    dmp = diff_match_patch()
    #dmp.Match_Distance
    dmp.Match_Threshold = 0.5

    diffs = dmp.match_main(audio_text,sentence_key,location)
    if (diffs == -1):
        #print("No match found for %s", sentence_value)
        return(None)
    else:
        match_type = "diff_match_patch"
        match_similarity = dmp.Match_Threshold
        match_sentence = sentence_value
        match_query = sentence_key
        match_audio_text_interim = audio_text[diffs:diffs+len(sentence_value)]
        match_audio_text_final = audio_text[diffs:diffs+len(sentence_value)]
        similarity_ratio = difflib.SequenceMatcher(None, match_query,match_audio_text_interim).ratio()

        #Patch the sudit text to remove additional words etc
        sub_text = re.sub("\s\s+" , " ",match_sentence.lower().strip().translate(str.maketrans('', '', string.punctuation)))
        tran_text = re.sub("\s\s+" , " ", match_audio_text_final.lower().strip().translate(str.maketrans('', '', string.punctuation)))
        dmp_patch = diff_match_patch()
        diffs_patch = dmp_patch.patch_make(tran_text,sub_text)
        patches_tuple = dmp.patch_apply(diffs_patch,tran_text)
        if (patches_tuple):
            match_audio_text_final = patches_tuple[0]
        else:
            print("No patch %s /n %s" % match_sentence, match_audio_text_final)





    return([match_type,match_similarity,match_sentence, match_query,match_audio_text_interim,match_audio_text_final,similarity_ratio,diffs])



#Cleanup punctuations in audio text - sometimes audio text comes with it and leads to mismatches
#@timeit
def pre_match_audio_text_cleanup(text):
    translator = str.maketrans(string.punctuation, ' '*len(string.punctuation))
    #Single quotes should be replaced by a null string
    text = text.lower().replace("'","").translate(translator)
    return text

## Clean up audio text - remove duplicates, check words etc
#@timeit
def clean_up_audio_text_block(text):

    # Print repeated words
    dups_list = re.findall(r'\b(\w+)( \1\b)+', text)
    # if (len(dups_list) > 0):
    #     print("Duplicates = ", re.findall(r'\b(\w+)( \1\b)+', text))
    #     pass

    # Remove repeated words
    re_output = re.sub(r'\b(\w+)( \1\b)+', r'\1', text)
    return re_output

#@timeit
def clean_up_subtitle_text_block(text):
    # Renove wrods like PROFESSOR:, AUDIENCE:, CLAMORING or text in brackets
    text1 = re.sub(r'PROFESSOR:', ' ', text)
    text2 = re.sub(r'AUDIENCE:', ' ', text1)
    text3 = re.sub("\[.*?\]"," ",text2)
    #text4 = re.sub("[A-Z]+[0-9]+:$"," ",text3)
    return text3


## Combine lines to get the size between 500-800 words
#@timeit
def combine_sentences(df_match_input, min_para_size = 500, max_para_size = 800):

    # Choose a random number between 500 and 800
    #random.seed(3) [This is for testing]
    count_limit = random.randint(min_para_size, max_para_size)
    counter = 0
    subtitle_text_list = []
    audio_text_list = []
    subtitle_text = ''
    audio_text = ''
    subtitle_text_list = []
    audio_text_list = []
    #print(df_match_input.shape[0])
    flag = False

    for i, row in df_match_input.iterrows():
        counter = counter + row["sentence_word_count"]
        subtitle_text = subtitle_text + " " + row["match_sentence"]
        audio_text = audio_text + " " + row["match_audit_text_final"]
        #print("count limit ", count_limit, " row ", i, "counter = ", counter)

        if ((counter >= count_limit)): #or (i >= df_match_input.shape[0]-1)):
                flag = True
                #print("added row %s; counter %s; count_limit %s" % (i,counter,count_limit))
                audio_text_list = audio_text_list + [audio_text]
                subtitle_text_list = subtitle_text_list + [subtitle_text]
                count_limit = random.randint(min_para_size, max_para_size)
                subtitle_text = ''
                audio_text = ''
                counter = 0

    if (flag == False):
                flag = True
                #print("in true; added row %s; counter %s; count_limit %s" % (i,counter,count_limit))
                audio_text_list = audio_text_list + [audio_text]
                subtitle_text_list = subtitle_text_list + [subtitle_text]
  
    return([subtitle_text_list,audio_text_list])



def get_available_pairs(transcription_audio_dir, subtitles_dir):

    #Get all transcriptions available in directory
    transcript_list = [Path(x).stem for x in glob.glob(transcription_audio_dir+"*.txt")]
    #Get subtitlrs available in directory
    subtitles_list = [Path(x).stem for x in glob.glob(subtitles_dir+"*.txt")]

    transcript_subtitles_list = list(set(transcript_list) & set(subtitles_list))

    return(sorted(transcript_subtitles_list))


@timeit
def match_transcript_subtitles(video_name,subtitles_text, audio_to_text,match_results_dir):
    
    #clean up subtitles text
    subtitles_text = clean_up_subtitle_text_block(subtitles_text)

    # Match Code
    subtitle_text_sentences, subtitle_text_words_count = find_sentences(subtitles_text)

    #Create a dictionary for all sentences in Subtitles - key is the standardized query for the sentence, item is the original sentence
    sentence_dict = create_dict_sentences(subtitle_text_sentences)
    print("Number of sentences = %s" % len(sentence_dict.keys()))

    count = 0
    match_type_list = []
    match_similarity_list = []
    match_sentence_list = []
    match_query_list = []
    match_audio_text_interim_list = []
    match_audio_text_final_list = []
    similarity_ratio_list = []

    # Perform pre-match cleanup of audio text
    audio_to_text = pre_match_audio_text_cleanup(audio_to_text)
    location = 0

    for key,value in sentence_dict.items():
        
        #print("*** processing sentence number %s" % count)
        # Perform pre-match cleanup of audio text
        audio_to_text = pre_match_audio_text_cleanup(audio_to_text)

        #Find a match for the standardized query related to sentence with the subtitle text
        output = match_sentence_to_audio_text(key,value,audio_to_text,location)
        #print(output)
        if (output):
            match_type,match_similarity,match_sentence, match_query,match_audio_text_interim,match_audio_text_final, similarity_ratio, location = match_sentence_to_audio_text(key,value,audio_to_text,location)

            #print(match_query)
            #print("before ",match_audio_text_final)
            #print("\n")

            #Clean up audio text blocks (remove repeated words)
            match_audio_text_final = clean_up_audio_text_block(match_audio_text_final)
            #print("after ",match_audio_text_final)
            
            #Clean up subtitle text box to remove subtitle conditioning
            #match_sentence = clean_up_subtitle_text_block(match_sentence)

            match_type_list = match_type_list + [match_type]
            match_similarity_list = match_similarity_list + [match_similarity]
            match_sentence_list = match_sentence_list + [match_sentence]
            match_query_list = match_query_list + [match_query]
            match_audio_text_interim_list = match_audio_text_interim_list + [match_audio_text_interim]
            match_audio_text_final_list = match_audio_text_final_list + [match_audio_text_final]
            similarity_ratio_list = similarity_ratio_list + [similarity_ratio]

            count = count + 1

    #print(len(match_sentence_list))
    #print(len(match_audio_text_final_list))
        
    df_match = pd.DataFrame(list(zip(match_type_list,match_similarity_list,match_sentence_list,match_query_list,match_audio_text_interim_list,match_audio_text_final_list, similarity_ratio_list)),
                columns = ["match_type","match_similarity","match_sentence","match_query","match_audi_text_interim","match_audit_text_final", "similarity_ratio"])

    df_match["sentence_word_count"] = df_match["match_sentence"].map(lambda x: len(x.split()))

    print("Number of sentences processed = ", count)


    ## Filter out sentences with similarity less than 0.9
    df_match_filtered = df_match #.loc[df_match["match_similarity"] > 0.9]

    ## Read sentence matches file and build blocks
    subtitle_text_list,audio_text_list = combine_sentences(df_match_filtered, min_para_size = 500, max_para_size = 800)

    df_matched_blocks = pd.DataFrame(list(zip(subtitle_text_list, audio_text_list)), columns = ["subtitle_text","audio_text"])
    df_matched_blocks["subtitle_word_count"] = df_matched_blocks["subtitle_text"].map(lambda x: len(x.split()))

    writer = pd.ExcelWriter(os.path.join(match_results_dir,video_name+".xlsx"), engine='xlsxwriter')

    df_match_filtered.to_excel(writer, sheet_name = "Match_input",index=False)
    df_matched_blocks.to_excel(writer, sheet_name = "Matched_blocks",index=False)

    writer.close()




