# Airflow S3 Tutorial

Apache Airflow 환경에서 S3를 활용한 DAG 관리 및 AWS 서비스 통합 예제 프로젝트입니다.

## 주요 기능

- **S3 DAG 동기화**: S3 버킷에서 DAG 파일을 자동으로 동기화
- **AWS Secrets Manager 통합**: 안전한 자격 증명 관리
- **RDS 연동**: AWS RDS MySQL 데이터베이스 쿼리 실행
- **Docker Compose 기반**: 간편한 로컬 개발 환경 구성

## 아키텍처

```
┌─────────────┐
│   S3 Bucket │ ──┐
│  (DAG 저장소) │   │  60초마다 동기화
└─────────────┘   │
                  ▼
┌────────────────────────────────────────┐
│         Airflow Docker Environment      │
│  ┌──────────┐  ┌──────────┐           │
│  │ Scheduler│  │  Worker  │           │
│  └──────────┘  └──────────┘           │
│  ┌──────────┐  ┌──────────┐           │
│  │  WebUI   │  │  Redis   │           │
│  └──────────┘  └──────────┘           │
└────────────────────────────────────────┘
         │                    │
         │                    │
    ┌────▼───────┐     ┌─────▼────────┐
    │  AWS RDS   │     │AWS Secrets   │
    │  (MySQL)   │     │  Manager     │
    └────────────┘     └──────────────┘
```

## 프로젝트 구조

```
airflow-s3-tutorial/
├── dags/                          # Airflow DAG 파일 (S3에서 동기화됨)
│   ├── s3_sync_test_dag.py       # S3 동기화 테스트 DAG
│   └── rds_secrets_manager_test_dag.py  # RDS 쿼리 DAG
├── config/                        # Airflow 설정 파일
│   └── airflow.cfg
├── plugins/                       # Airflow 플러그인
├── logs/                          # Airflow 로그
├── test/                          # 테스트 및 개발용 DAG
├── docker-compose.yaml            # Docker Compose 설정
├── .env                           # 환경 변수 (gitignore)
├── .env.example                   # 환경 변수 템플릿
└── README.md                      # 프로젝트 문서
```

## 사전 요구사항

- Docker Desktop (Mac/Windows) 또는 Docker Engine (Linux)
- Docker Compose v2.0+
- AWS CLI (선택사항)
- 최소 4GB RAM, 2 CPU

## 설치 및 설정

### 1. 저장소 클론

```bash
git clone <repository-url>
cd airflow-s3-tutorial
```

### 2. 환경 변수 설정

`.env.example` 파일을 복사하여 `.env` 파일을 생성합니다:

```bash
cp .env.example .env
```

`.env` 파일을 편집하여 필요한 값을 입력합니다:

```bash
# Airflow 기본 설정
AIRFLOW_UID=50000
_AIRFLOW_WWW_USER_USERNAME=airflow
_AIRFLOW_WWW_USER_PASSWORD=airflow

# AWS 자격 증명
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=ap-northeast-2

# S3 DAG 동기화 설정
S3_DAG_BUCKET=your-dag-bucket-name
S3_DAG_PREFIX=dags/
SYNC_INTERVAL=300

# RDS 설정 (선택사항)
RDS_HOST=your-rds-endpoint.region.rds.amazonaws.com
RDS_PORT=3306
RDS_DATABASE=your_database_name
RDS_SECRET_NAME=your-secrets-manager-secret-name
```

### 3. Airflow 시작

```bash
# 컨테이너 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 4. Airflow UI 접속

브라우저에서 http://localhost:8080 접속

- **Username**: airflow (또는 `.env`에 설정한 값)
- **Password**: airflow (또는 `.env`에 설정한 값)

## DAG 설명

### 1. S3 Sync Test DAG (`s3_sync_test`)

S3에서 DAG가 정상적으로 동기화되는지 확인하는 테스트 DAG입니다.

- **Schedule**: 매 5분마다 실행
- **기능**: 현재 시간 출력 및 S3 동기화 확인

### 2. RDS Secrets Manager Test DAG (`rds_secrets_manager_test`)

AWS Secrets Manager를 사용하여 RDS MySQL 데이터베이스에 연결하고 쿼리를 실행합니다.

- **Schedule**: 수동 실행 (Manual trigger)
- **기능**:
  1. AWS Secrets Manager에서 DB 자격 증명 가져오기
  2. RDS MySQL에 연결
  3. `airbyte_test_users` 테이블에서 1개 레코드 조회
  4. 결과를 로그에 출력

**환경 변수 요구사항**:
- `RDS_HOST`: RDS 엔드포인트
- `RDS_PORT`: RDS 포트 (기본값: 3306)
- `RDS_DATABASE`: 데이터베이스 이름
- `RDS_SECRET_NAME`: Secrets Manager 시크릿 이름

## S3 DAG 동기화

### 동작 원리

`s3-dag-sync` 서비스가 백그라운드에서 실행되며:
1. 설정된 `SYNC_INTERVAL`(기본 300초)마다
2. S3 버킷 `s3://${S3_DAG_BUCKET}/${S3_DAG_PREFIX}`에서
3. 로컬 `./dags/` 디렉토리로 DAG 파일을 동기화합니다

### S3에 DAG 업로드

```bash
# AWS CLI를 사용하여 DAG 업로드
aws s3 cp dags/my_dag.py s3://your-bucket/dags/my_dag.py

# 또는 전체 디렉토리 동기화
aws s3 sync dags/ s3://your-bucket/dags/
```

### 수동 동기화

```bash
# S3에서 즉시 동기화
docker-compose exec s3-dag-sync \
  aws s3 sync s3://${S3_DAG_BUCKET}/${S3_DAG_PREFIX} /local/dags/
```

## 환경 변수 변경 시 주의사항

`.env` 파일을 수정한 후에는 **반드시 컨테이너를 재생성**해야 합니다:

```bash
# ❌ 잘못된 방법 - 환경 변수가 적용되지 않음
docker-compose restart

# ✅ 올바른 방법 - 컨테이너 재생성
docker-compose up -d

# 또는 완전 재시작
docker-compose down && docker-compose up -d
```

## 유용한 명령어

### 로그 확인

```bash
# 전체 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f airflow-scheduler
docker-compose logs -f airflow-worker
docker-compose logs -f s3-dag-sync

# DAG processor 에러 확인
docker-compose logs airflow-dag-processor | grep -i error
```

### DAG 관리

```bash
# DAG 목록 확인
docker-compose exec airflow-scheduler airflow dags list

# DAG import 에러 확인
docker-compose exec airflow-dag-processor airflow dags list-import-errors

# DAG 수동 실행
docker-compose exec airflow-scheduler airflow dags trigger <dag_id>

# DAG 일시 정지/해제
docker-compose exec airflow-scheduler airflow dags pause <dag_id>
docker-compose exec airflow-scheduler airflow dags unpause <dag_id>
```

### 컨테이너 관리

```bash
# 컨테이너 상태 확인
docker-compose ps

# 컨테이너 중지
docker-compose down

# 볼륨까지 삭제 (완전 초기화)
docker-compose down -v

# 특정 서비스만 재시작 (환경 변수 변경 시 사용하지 말 것!)
docker-compose restart airflow-scheduler
```

### Python 패키지 설치

추가 Python 패키지가 필요한 경우:

```bash
# 임시 설치 (재시작 시 사라짐)
docker-compose exec airflow-worker pip install <package-name>

# 영구 설치를 위해서는 Dockerfile 수정 필요
```

## AWS 서비스 설정

### IAM 권한

Airflow가 사용하는 IAM 사용자/역할에 다음 권한이 필요합니다:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::your-dag-bucket/*",
        "arn:aws:s3:::your-dag-bucket"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:region:account-id:secret:your-secret-name*"
      ]
    }
  ]
}
```

### RDS 네트워크 설정

RDS에 연결하려면:
1. RDS 보안 그룹에서 Airflow가 실행되는 IP 허용
2. 퍼블릭 액세스 활성화 (개발 환경) 또는 VPN/VPC 설정 (프로덕션)

## 트러블슈팅

### DAG가 UI에 표시되지 않음

1. **DAG import 에러 확인**:
   ```bash
   docker-compose exec airflow-dag-processor airflow dags list-import-errors
   ```

2. **S3 동기화 확인**:
   ```bash
   docker-compose logs s3-dag-sync
   ls -la dags/
   ```

3. **Python 캐시 삭제**:
   ```bash
   find dags/ -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
   docker-compose restart airflow-dag-processor
   ```

### RDS 연결 실패

1. **환경 변수 확인**:
   ```bash
   docker-compose exec airflow-worker printenv | grep RDS_
   ```

2. **네트워크 연결 테스트**:
   ```bash
   docker-compose exec airflow-worker \
     python3 -c "import pymysql; pymysql.connect(host='${RDS_HOST}', port=${RDS_PORT}, user='admin', password='...')"
   ```

3. **Secrets Manager 확인**:
   ```bash
   aws secretsmanager get-secret-value --secret-id ${RDS_SECRET_NAME} --region ${AWS_DEFAULT_REGION}
   ```

### 메모리 부족

```bash
# Docker Desktop의 리소스 할당 확인 및 증가
# Settings > Resources > Memory를 최소 4GB로 설정
```

## 보안 주의사항

1. **`.env` 파일을 절대 Git에 커밋하지 마세요**
   - `.gitignore`에 포함되어 있는지 확인

2. **AWS 자격 증명 관리**
   - 가능하면 IAM 역할 사용
   - Access Key는 최소 권한 원칙 적용

3. **Secrets Manager 사용**
   - 민감한 정보는 코드에 하드코딩하지 말고 Secrets Manager 사용

4. **프로덕션 환경**
   - 기본 비밀번호 변경
   - HTTPS 사용
   - 방화벽 및 네트워크 보안 설정

## 참고 자료

- [Apache Airflow 공식 문서](https://airflow.apache.org/docs/)
- [Airflow Docker 가이드](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html)
- [AWS Secrets Manager 문서](https://docs.aws.amazon.com/secretsmanager/)
- [S3 CLI 명령어](https://docs.aws.amazon.com/cli/latest/reference/s3/)

## 라이선스

이 프로젝트는 학습 및 개발 목적으로 제공됩니다.

## 기여

이슈 및 풀 리퀘스트를 환영합니다!
