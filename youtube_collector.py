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

TEAM_NAME_MAP = {
    '콩고민주공화국': '콩고',
    '남아프리카공화국': '남아공',
    '보스니아헤르체고비나': '보스니아',
}

def normalize_team_name(name):
    return TEAM_NAME_MAP.get(name.strip(), name.strip())

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
    all_items = []
    next_page_token = None

    while True:
        params = {
            'key': YOUTUBE_API_KEY,
            'playlistId': playlist_id,
            'part': 'snippet',
            'maxResults': 50,
            'pageToken': next_page_token
        }
        response = requests.get(url, params=params)
        data = response.json()
        items = data.get('items', [])
        all_items.extend(items)

        if items:
            oldest = items[-1]['snippet']['publishedAt']
            oldest_dt = datetime.fromisoformat(oldest.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) - oldest_dt > timedelta(hours=25):
                break

        next_page_token = data.get('nextPageToken')
        if not next_page_token:
            break

    return all_items

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
    match_part = match_part.split('|')[0].split('｜')[0].strip()
    normalized = match_part.replace(' VS ', ' vs ').replace(' Vs ', ' vs ')
    if ' vs ' in normalized.lower():
        parts = normalized.lower().split(' vs ')
        team_a = normalize_team_name(parts[0].split()[-1])
        team_b = normalize_team_name(parts[1].split()[0])
        return f"{team_a} vs {team_b}"
    return match_part

def update_match_results(match_name, channel, view_count, collected_at):
    collected_date = collected_at[:10]

    if channel == 'KBS':
        # kbs_views가 이미 있으면 스킵
        existing = supabase.table('raw_match_results')\
            .select('kbs_views')\
            .eq('match_name', match_name)\
            .execute()
        
        if existing.data and existing.data[0]['kbs_views'] is not None:
            print(f'  KBS 조회수 이미 존재. 스킵: {match_name}')
            return

        supabase.table('raw_match_results').update({
            'kbs_views': view_count,
            'views_measured_at': collected_date,
            'days_elapsed': 1,
            'measure_type': '일평균'
        }).eq('match_name', match_name).execute()

    elif channel == 'JTBC':
        # jtbc_views가 이미 있으면 스킵
        existing = supabase.table('raw_match_results')\
            .select('jtbc_views')\
            .eq('match_name', match_name)\
            .execute()
        
        if existing.data and existing.data[0]['jtbc_views'] is not None:
            print(f'  JTBC 조회수 이미 존재. 스킵: {match_name}')
            return

        supabase.table('raw_match_results').update({
            'jtbc_views': view_count,
            'views_measured_at': collected_date,
            'days_elapsed': 1,
            'measure_type': '일평균'
        }).eq('match_name', match_name).execute()

def collect_youtube_views():
    print(f'[{datetime.now()}] 유튜브 조회수 수집 시작...')
    collected = 0

    for channel_name, channel_id in CHANNELS.items():
        keyword = CHANNEL_KEYWORDS[channel_name]
        videos = get_channel_videos(channel_id)

        for item in videos:
            video_id = item['snippet']['resourceId']['videoId']
            title = item['snippet']['title']
            published_at = item['snippet']['publishedAt']

            if keyword not in title:
                continue
            if already_collected(video_id):
                continue
            if not is_24h_passed(published_at):
                continue

            view_count = get_view_count(video_id)
            match_name = extract_match_name(title, keyword)
            collected_at = datetime.now(timezone.utc).isoformat()

            supabase.table('raw_youtube_views').upsert({
                'video_id': video_id,
                'channel': channel_name,
                'title': title,
                'published_at': published_at,
                'collected_at': collected_at,
                'view_count': view_count,
                'match_name': match_name,
                'is_24h_passed': True
            }).execute()

            update_match_results(match_name, channel_name, view_count, collected_at)

            collected += 1
            print(f'  수집: [{channel_name}] {match_name} → {view_count:,}회')

    print(f'[{datetime.now()}] 완료! 총 {collected}개 수집')

if __name__ == "__main__":
    collect_youtube_views()