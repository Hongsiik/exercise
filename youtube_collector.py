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

# 채널 ID (확인 후 교체 필요)
CHANNELS = {
    'KBS': 'UCDIB1DOwPPe58M2fHPyVVDA',
    'JTBC': 'UCTdZyOFVzontd9MZOJDg8Qw'
}

CHANNEL_KEYWORDS = {
    'KBS': '[3분 HL]',
    'JTBC': '[3분 하이라이트]'
}

def get_channel_videos(channel_id):
    """48시간 이내 업로드된 영상 최대 50개 최신순으로 가져오기"""
    published_after = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'key': YOUTUBE_API_KEY,
        'channelId': channel_id,
        'part': 'snippet',
        'order': 'date',
        'maxResults': 50,
        'type': 'video',
        'publishedAfter': published_after
    }
    response = requests.get(url, params=params)
    
    # 디버깅 로그 추가
    print(f"API 응답 코드: {response.status_code}")
    print(f"API 응답 내용: {response.json()}")
    
    return response.json().get('items', [])

def get_view_count(video_id):
    """조회수 가져오기"""
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
    """업로드 후 24시간 지났는지 확인"""
    published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
    return datetime.now(timezone.utc) - published_at >= timedelta(hours=24)

def already_collected(video_id):
    """이미 수집 완료된 영상인지 확인"""
    result = supabase.table('raw_youtube_views')\
        .select('id')\
        .eq('video_id', video_id)\
        .eq('is_24h_passed', True)\
        .execute()
    return len(result.data) > 0

def extract_match_name(title, keyword):
    """제목에서 팀명만 추출 → raw_match_results match_name과 매칭되도록"""
    match_part = title.split(keyword)[1].strip()
    match_part = match_part.split('|')[0].strip()

    # vs / VS 기준으로 팀명만 추출
    normalized = match_part.replace(' VS ', ' vs ').replace(' Vs ', ' vs ')
    if ' vs ' in normalized.lower():
        parts = normalized.lower().split(' vs ')
        team_a = parts[0].split()[-1]  # 마지막 단어 = 팀명
        team_b = parts[1].split()[0]   # 첫 단어 = 팀명
        return f"{team_a} vs {team_b}"
    return match_part

def collect_youtube_views():
    print(f'[{datetime.now()}] 유튜브 조회수 수집 시작...')
    collected = 0

    for channel_name, channel_id in CHANNELS.items():
        keyword = CHANNEL_KEYWORDS[channel_name]
        videos = get_channel_videos(channel_id)
        print(f'[{channel_name}] 최근 48시간 영상 {len(videos)}개 스캔')

        for item in videos:
            video_id = item['id']['videoId']
            title = item['snippet']['title']
            published_at = item['snippet']['publishedAt']

            # 키워드 필터링
            if keyword not in title:
                continue

            # 이미 수집 완료된 영상 스킵
            if already_collected(video_id):
                print(f'  이미 수집됨: {title}')
                continue

            # 24시간 안 된 것 스킵
            if not is_24h_passed(published_at):
                print(f'  대기중 (24시간 미경과): {title}')
                continue

            # 조회수 수집
            view_count = get_view_count(video_id)
            match_name = extract_match_name(title, keyword)
            print(f'  수집: {title} → {match_name} → {view_count:,}회')

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
            collected += 1

    print(f'[{datetime.now()}] 완료! {collected}개 수집')

if __name__ == "__main__":
    collect_youtube_views()