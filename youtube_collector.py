import os
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

CHANNELS = {
    'KBS': 'UCDIB1DOwPPe58M2fHPyVVDA',
    'JTBC': 'UCTdZyOFVzontd9MZOJDg8Qw'
}

CHANNEL_KEYWORDS = {
    'KBS': '[3분 HL]',
    'JTBC': '[3분 하이라이트]'
}

def get_upload_playlist_id(channel_id):
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        'key': YOUTUBE_API_KEY,
        'id': channel_id,
        'part': 'contentDetails'
    }
    response = requests.get(url, params=params)
    return response.json()['items'][0]['contentDetails']['relatedPlaylists']['uploads']

def get_channel_videos(channel_id):
    playlist_id = get_upload_playlist_id(channel_id)
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        'key': YOUTUBE_API_KEY,
        'playlistId': playlist_id,
        'part': 'snippet',
        'maxResults': 50
    }
    response = requests.get(url, params=params)
    return response.json().get('items', [])

def get_view_count(video_id):
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        'key': YOUTUBE_API_KEY,
        'id': video_id,
        'part': 'statistics'
    }
    response = requests.get(url, params=params)
    items = response.json().get('items', [])
    return int(items[0]['statistics'].get('viewCount', 0)) if items else None

def is_24h_passed(published_at_str):
    published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
    return datetime.now(timezone.utc) - published_at >= timedelta(hours=24)

def already_collected(video_id):
    result = supabase.table('raw_youtube_views')\
        .select('id')\
        .eq('video_id', video_id)\
        .eq('is_24h_passed', True)\
        .execute()
    return len(result.data) > 0

def extract_match_name(title, keyword):
    match_part = title.split(keyword)[1].strip()
    match_part = match_part.split('|')[0].strip()
    normalized = match_part.replace(' VS ', ' vs ').replace(' Vs ', ' vs ')
    if ' vs ' in normalized.lower():
        parts = normalized.lower().split(' vs ')
        team_a = parts[0].split()[-1]
        team_b = parts[1].split()[0]
        return f"{team_a} vs {team_b}"
    return match_part

def collect_youtube_views():
    print(f'[{datetime.now()}] 유튜브 조회수 수집 시작...')
    collected = 0

    for channel_name, channel_id in CHANNELS.items():
        keyword = CHANNEL_KEYWORDS[channel_name]
        videos = get_channel_videos(channel_id)
        print(f'[{channel_name}] {len(videos)}개 영상 스캔')

        for item in videos:
            video_id = item['snippet']['resourceId']['videoId']
            title = item['snippet']['title']
            published_at = item['snippet']['publishedAt']

            if keyword not in title:
                continue

            print(f'  키워드 매칭: {title}')
            print(f'  24시간 경과: {is_24h_passed(published_at)} / 업로드: {published_at}')
            print(f'  이미 수집됨: {already_collected(video_id)}')
if __name__ == "__main__":
    collect_youtube_views()