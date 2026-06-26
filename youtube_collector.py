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
    print(f'  [get_upload_playlist_id] channel_id={channel_id}')
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        'key': YOUTUBE_API_KEY,
        'id': channel_id,
        'part': 'contentDetails'
    }
    response = requests.get(url, params=params)
    print(f'  [get_upload_playlist_id] 응답 코드: {response.status_code}')
    data = response.json()
    playlist_id = data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    print(f'  [get_upload_playlist_id] playlist_id={playlist_id}')
    return playlist_id

def get_channel_videos(channel_id):
    print(f'  [get_channel_videos] channel_id={channel_id}')
    playlist_id = get_upload_playlist_id(channel_id)
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        'key': YOUTUBE_API_KEY,
        'playlistId': playlist_id,
        'part': 'snippet',
        'maxResults': 50
    }
    response = requests.get(url, params=params)
    print(f'  [get_channel_videos] 응답 코드: {response.status_code}')
    items = response.json().get('items', [])
    print(f'  [get_channel_videos] 가져온 영상 수: {len(items)}개')
    return items

def get_view_count(video_id):
    print(f'  [get_view_count] video_id={video_id}')
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        'key': YOUTUBE_API_KEY,
        'id': video_id,
        'part': 'statistics'
    }
    response = requests.get(url, params=params)
    print(f'  [get_view_count] 응답 코드: {response.status_code}')
    items = response.json().get('items', [])
    view_count = int(items[0]['statistics'].get('viewCount', 0)) if items else None
    print(f'  [get_view_count] 조회수: {view_count}')
    return view_count

def is_24h_passed(published_at_str):
    published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    diff = now - published_at
    passed = diff >= timedelta(hours=24)
    print(f'  [is_24h_passed] 업로드: {published_at_str} / 경과: {diff} / 24시간 초과: {passed}')
    return passed

def already_collected(video_id):
    result = supabase.table('raw_youtube_views')\
        .select('id')\
        .eq('video_id', video_id)\
        .eq('is_24h_passed', True)\
        .execute()
    collected = len(result.data) > 0
    print(f'  [already_collected] video_id={video_id} / 이미 수집됨: {collected}')
    return collected

def extract_match_name(title, keyword):
    print(f'  [extract_match_name] title={title}')
    match_part = title.split(keyword)[1].strip()
    match_part = match_part.split('|')[0].strip()
    normalized = match_part.replace(' VS ', ' vs ').replace(' Vs ', ' vs ')
    if ' vs ' in normalized.lower():
        parts = normalized.lower().split(' vs ')
        team_a = parts[0].split()[-1]
        team_b = parts[1].split()[0]
        result = f"{team_a} vs {team_b}"
        print(f'  [extract_match_name] 추출된 경기명: {result}')
        return result
    return match_part

def collect_youtube_views():
    print(f'[{datetime.now()}] 유튜브 조회수 수집 시작...')
    collected = 0

    for channel_name, channel_id in CHANNELS.items():
        print(f'\n=== {channel_name} 채널 처리 시작 ===')
        keyword = CHANNEL_KEYWORDS[channel_name]
        videos = get_channel_videos(channel_id)

        for item in videos:
            video_id = item['snippet']['resourceId']['videoId']
            title = item['snippet']['title']
            published_at = item['snippet']['publishedAt']

            if keyword not in title:
                continue

            print(f'\n  키워드 매칭: {title}')

            if already_collected(video_id):
                print(f'  → 이미 수집됨. 스킵')
                continue

            if not is_24h_passed(published_at):
                print(f'  → 24시간 미경과. 스킵')
                continue

            view_count = get_view_count(video_id)
            match_name = extract_match_name(title, keyword)

            print(f'  → Supabase 저장 시도: {match_name} / {view_count:,}회')
            supabase.table('raw_youtube_views').upsert({
                'video_id': video_id,
                'channel': channel_name,
                'title': title,
                'published_at': published_at,
                'collected_at': datetime.now(timezone.utc).isoformat(),
                'view_count': view_count,
                'match_name': match_name,
                'is_24h_passed': True
            }).execute()
            print(f'  → 저장 완료!')
            collected += 1

    print(f'\n[{datetime.now()}] 완료! 총 {collected}개 수집')

if __name__ == "__main__":
    collect_youtube_views()