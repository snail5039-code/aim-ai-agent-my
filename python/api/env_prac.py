import os

# 환경변수 설정
os.environ['SERVICE_KEY'] = 'abcd1234'

# 환경변수 조회 (Key가 없을 경우 KeyError 발생)
port = os.environ['SERVICE_KEY']

# get 메서드를 이용한 조회 (Key가 없을 경우 None 반환 및 기본값 설정 가능)
db_host = os.environ.get('DB_HOST', 'localhost')

print(f"PORT: {port}, HOST: {db_host}")

