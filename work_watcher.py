import os
import time
import datetime

# 실행 중인 프로세스를 확인하는 함수
def check_process(process_name):
    cmd = "ps ax | grep " + process_name + " | grep -v grep"
    result = os.popen(cmd).read()
    return result != ""

def remove_old_logs(log_folder, days=100):
    """
    지정된 log_folder 내에 있는 파일 중,
    마지막 수정 시각이 현재로부터 100일(기본값) 이상 지난 경우 삭제합니다.
    """
    if not os.path.isdir(log_folder):
        return  # 폴더가 없으면 아무 것도 하지 않음

    now = time.time()
    cutoff = now - days * 24 * 60 * 60  # 100일(초단위)
    
    for file_name in os.listdir(log_folder):
        file_path = os.path.join(log_folder, file_name)
        
        # 파일만 대상으로 처리
        if os.path.isfile(file_path):
            file_mtime = os.path.getmtime(file_path)
            if file_mtime < cutoff:
                try:
                    os.remove(file_path)
                    print(f"[INFO] 오래된 로그 파일 삭제: {file_path}")
                except Exception as e:
                    print(f"[ERROR] 로그 파일 삭제 중 문제 발생: {file_path}, {e}")

# 실행할 스크립트 파일명
script_file = "work_notice.py"

# 감시 주기 (초)
watch_interval = 60  # 예시로 1분마다 확인

# 로그 폴더 경로 (필요에 맞게 수정)
LOG_FOLDER_PATH = "log"

while True:
    # 스크립트가 실행 중인지 확인
    if not check_process(script_file):
        print(f"{script_file}가 실행 중이지 않습니다. 다시 실행합니다.")
        os.system(f"nohup python3 {script_file} &")
    else:
        print(f"{script_file}가 실행 중입니다.")
    
    # 로그 폴더에서 100일 지난 파일 삭제
    remove_old_logs(LOG_FOLDER_PATH, days=100)

    # 일정 간격으로 감시
    time.sleep(watch_interval)
