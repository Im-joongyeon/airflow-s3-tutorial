# S3 DAG 동기화 설정 가이드

## 개요
이 설정은 AWS S3 버킷에서 Airflow DAG 파일을 자동으로 동기화합니다.
`s3-dag-sync` 서비스가 주기적으로 S3에서 DAG 파일을 가져옵니다.

## 1. AWS 인증 정보 설정

### .env 파일 생성
```bash
cp .env.example .env
```

### .env 파일 편집
`.env` 파일을 열어서 다음 정보를 입력하세요:

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=AKIA...           # AWS Access Key
AWS_SECRET_ACCESS_KEY=your_secret   # AWS Secret Key
AWS_DEFAULT_REGION=ap-northeast-2   # AWS Region (서울)

# S3 Configuration
S3_DAG_BUCKET=my-airflow-dags       # S3 버킷 이름
S3_DAG_PREFIX=dags/                 # S3 버킷 내 DAG 파일 경로
SYNC_INTERVAL=60                    # 동기화 주기 (초)
```

### AWS Credentials 얻는 방법
1. AWS Console → IAM → Users → Security credentials
2. "Create access key" 클릭
3. Access Key ID와 Secret Access Key 복사

### 필요한 IAM 권한
S3 버킷 읽기 권한이 필요합니다:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket-name/*",
        "arn:aws:s3:::your-bucket-name"
      ]
    }
  ]
}
```

## 2. S3 버킷 준비

### S3 버킷 생성 (없는 경우)
```bash
aws s3 mb s3://my-airflow-dags --region ap-northeast-2
```

### 테스트용 DAG 파일 업로드
```bash
# 예시 DAG 파일을 S3에 업로드
aws s3 cp dags/example_s3_dag.py s3://my-airflow-dags/dags/

# 또는 폴더 전체 업로드
aws s3 sync ./dags s3://my-airflow-dags/dags/
```

### S3 버킷 구조 예시
```
s3://my-airflow-dags/
└── dags/
    ├── example_s3_dag.py
    ├── etl_pipeline.py
    └── data_processing.py
```

## 3. Docker Compose 실행

### 초기 실행
```bash
# Airflow 초기화 및 모든 서비스 시작
docker-compose up -d
```

### S3 동기화 서비스만 시작
```bash
docker-compose up -d s3-dag-sync
```

### 동기화 로그 확인
```bash
# 실시간 로그 확인
docker-compose logs -f s3-dag-sync

# 출력 예시:
# [2024-01-15 10:30:00] Syncing DAGs from S3...
# download: s3://my-airflow-dags/dags/example_s3_dag.py to dags/example_s3_dag.py
# [2024-01-15 10:30:01] Sync completed successfully
```

## 4. 동작 확인

### DAG 파일 확인
```bash
# 로컬 dags 폴더 확인
ls -la dags/

# S3에서 동기화된 파일이 있어야 합니다
```

### Airflow UI 확인
1. 브라우저에서 `http://localhost:8080` 접속
2. 로그인: airflow / airflow
3. DAGs 페이지에서 `example_s3_sync_dag` 확인

### 동기화 테스트
```bash
# 1. S3에 새 DAG 파일 추가
echo "# Test DAG" > test_dag.py
aws s3 cp test_dag.py s3://my-airflow-dags/dags/

# 2. 60초 후 (또는 설정한 SYNC_INTERVAL 후) 로컬에 파일 생성 확인
ls -la dags/test_dag.py

# 3. Airflow UI 새로고침하여 새 DAG 확인
```

## 5. 트러블슈팅

### 동기화가 안 되는 경우

1. **AWS 인증 오류**
   ```bash
   # s3-dag-sync 컨테이너 접속하여 확인
   docker-compose exec s3-dag-sync sh
   aws s3 ls s3://my-airflow-dags/dags/
   ```

2. **권한 문제**
   ```bash
   # dags 폴더 권한 확인
   ls -la dags/

   # 필요시 권한 변경
   chmod -R 755 dags/
   ```

3. **S3 버킷 접근 불가**
   - IAM 권한 확인
   - 버킷 정책 확인
   - 리전 설정 확인

### 로그 확인
```bash
# 모든 서비스 로그
docker-compose logs

# 특정 서비스 로그
docker-compose logs s3-dag-sync
docker-compose logs airflow-scheduler
```

## 6. 프로덕션 고려사항

### 보안
- `.env` 파일을 `.gitignore`에 추가
- AWS IAM 역할 사용 (EC2/ECS 환경)
- S3 버킷 암호화 활성화

### 성능
- `SYNC_INTERVAL` 적절히 조정 (너무 짧으면 불필요한 API 호출)
- 큰 DAG 파일의 경우 증분 동기화 고려
- CloudWatch를 통한 모니터링

### 비용
- S3 API 호출 비용 고려
- 동기화 주기 최적화

## 7. 서비스 관리

### 서비스 중지
```bash
docker-compose stop s3-dag-sync
```

### 서비스 재시작
```bash
docker-compose restart s3-dag-sync
```

### 전체 종료
```bash
docker-compose down
```

### 환경변수 변경 후 재시작
```bash
docker-compose up -d --force-recreate s3-dag-sync
```
