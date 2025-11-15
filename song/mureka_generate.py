import requests
import time
import os
from dotenv import load_dotenv
from langchain.tools import tool

load_dotenv() 

MUREKA_API_KEY = os.environ.get("MUREKA_API_KEY")
MUREKA_API_URL_BASE = os.environ.get("MUREKA_API_URL")


if not MUREKA_API_KEY:
    raise ValueError("MUREKA_API_KEY가 .env 파일에 설정되지 않았습니다.")
if not MUREKA_API_URL_BASE:
    raise ValueError("MUREKA_API_URL이 .env 파일에 설정되지 않았습니다.")

MUREKA_API_URL = MUREKA_API_URL_BASE.rstrip('/') 

HEADERS = {
    "Authorization": f"Bearer {MUREKA_API_KEY}",
    "Content-Type": "application/json"
}

@tool
def generate_song_via_api(lyrics: str, prompt: str = "kpop") -> str:
    """
    Mureka API를 사용하여 주어진 가사와 장르 프롬프트를 기반으로 노래를 생성합니다.
    이 툴은 노래 생성을 요청하고, 작업이 완료될 때까지 폴링(polling)한 후,
    최종적으로 생성된 노래의 MP3 URL을 반환합니다.

    Args:
        lyrics (str): 노래를 만드는 데 사용할 가사. (필수)
        prompt (str): 노래의 장르나 스타일을 지정하는 프롬프트. 
                       (선택 사항, 기본값 'kpop')
                       예: "kpop", "sad ballad", "fast rock"
                       
    Returns:
        str: 생성된 노래의 MP3 URL. 오류 발생 시 오류 메시지를 반환합니다.
    """
    
    generation_url = f"{MUREKA_API_URL}/v1/song/generate"
    query_url_base = f"{MUREKA_API_URL}/v1/song/query"
    
    print(f"🎵 (Tool) 1. Mureka API에 노래 생성을 요청합니다...")
    print(f"   (호출 주소: {generation_url})")
    
    payload = {
        "lyrics": lyrics,
        "model": "auto",
        "prompt": prompt
    }
    
    try:
        response = requests.post(generation_url, headers=HEADERS, json=payload)
        response.raise_for_status() 
        data = response.json()
        task_id = data.get('id') 
        
        if not task_id:
            return f"오류: 응답에서 'id'를 받지 못했습니다. 응답: {data}"
            
        print(f"✅ (Tool) 1-1. 작업 ID 수신: {task_id}")

    except requests.exceptions.HTTPError as e:
        return f"오류: 노래 생성 요청 실패. {e} \n서버 응답: {e.response.text}"
    except Exception as e:
        return f"오류: 노래 생성 요청 실패. {e}"

    # 폴링
    print(f"⏳ (Tool) 2. 노래가 완성될 때까지 10초마다 확인합니다...")
    while True:
        try:
            polling_url = f"{query_url_base}/{task_id}" 
            response = requests.get(polling_url, headers=HEADERS) 
            response.raise_for_status()
            
            data = response.json()
            status = data.get('status')
            
            if status == "succeeded":
                print("✅ (Tool) 2-1. 노래 생성 성공!")
                
                choices_list = data.get('choices')
                
                if choices_list and isinstance(choices_list, list) and len(choices_list) > 0:
                    first_choice = choices_list[0]
                    mp3_url = first_choice.get('url')
                    
                    if mp3_url:
                        return mp3_url # 👈 성공!
                    else:
                        return "오류: 'choices[0]' 안에 'url' 키가 없습니다."
                else:
                    return f"오류: 'status'는 SUCCESS지만 'choices' 배열이 없거나 비어있습니다. 응답: {data}"
                
            elif status == "FAILED":
                return f"오류: 노래 생성 실패. {data.get('error_message')}"
                
            else: 
                print(f"   ...(Tool) 아직 처리 중 (상태: {status})")
                time.sleep(10) 

        except Exception as e:
            return f"오류: 작업 상태 확인 실패. {e}"

# test 실행 부분
if __name__ == "__main__":
    test_lyrics = "[Verse 1] 데이터 언덕 위,\n오차(Loss) 찾기,\n최소로,\n가야 할 곳.\n\n[Chorus] 경사 하강,\nStep by Step.\n가장 가파른 길,\n내려가,\n학습률,\n속도 조절,\n정답을 찾아.\n\n[Outro] 머신러닝,\n기본 원리,\n경사 하강법!"
    test_prompt = "kpop, 1 min"
    
    mp3_url = generate_song_via_api(test_lyrics, test_prompt)
    
    print("\n--- 최종 결과 ---")
    print(mp3_url)