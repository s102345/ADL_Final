import requests
from bs4 import BeautifulSoup
import pandas as pd
import random
from tqdm import tqdm
import requests

def scrape_youtube_comments(video_url):
    google_key = 'AIzaSyBceYE5XDdU4WSN9Er8znoOtKjEU12HWf8'
    video_id = video_url.split("v=")[1]
    api_url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&key={google_key}"
    response = requests.get(api_url)
    data = response.json()
    comments = []
    if "items" in data:
        for item in data["items"]:
            comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            comments.append(comment)
        
        while "nextPageToken" in data and len(comments) < 500:
            next_page_token = data["nextPageToken"]
            api_url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&key={google_key}&pageToken={next_page_token}"
            response = requests.get(api_url)
            data = response.json()
            if "items" in data:
                for item in data["items"]:
                    comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                    comments.append(comment)
    
    random.shuffle(comments)
    return comments[:200]

if __name__ == "__main__":
    data = pd.read_csv('./video_links_1.csv')
    names = data['Name']
    links = data['Link']
    df_out = pd.DataFrame({
            'Name':[],
            'Comment':[]
        })
    for i in tqdm(range(len(links))):
        # print(names[i])
        comments = scrape_youtube_comments(links[i])
        df_next = pd.DataFrame({
            'Name':[names[i]] * len(comments),
            'Comment':comments
        })
        df_out = pd.concat([df_out, df_next],axis=0)

    df_out.to_csv('./comment_list.csv')
        # for i, comment in enumerate(comments, 1):
        #     print(f"Comment {i}: {comment}")


