# Qwen3.6 임시 어댑터 폐기 가이드

V4 누락 6개 기법 평가를 위해 사내 Qwen3.6-27B VLLM 엔드포인트와 연결하는 임시 코드를 추가했습니다. 이 파일은 V4 평가가 끝난 시점에서 그 임시 변경을 깔끔히 폐기하는 방법을 정리합니다.

## 1. 변경된 파일 목록

다음 네 파일에 임시 분기가 들어가 있습니다. 모든 변경 위치에 [TEMP V4-Qwen, 폐기 예정] 주석을 박아 두었습니다.

1. common/config.py - Qwen 키 / 엔드포인트 / 모델 환경 변수 3개 추가
2. common/llm.py - 생성 LLM 의 qwen-vllm provider 분기 추가 + _call_qwen 메서드 신설 + _dispatch 분기 추가
3. evaluation/ragas_eval.py - RAGAS 평가 LLM 의 qwen-vllm 분기 추가, 임베딩 분기에 qwen-vllm 포함
4. .env - LLM_PROVIDER 를 qwen-vllm 으로 변경, Qwen 키/엔드포인트/모델 추가, GEN_LLM_MODEL / EVAL_LLM_MODEL 을 Qwen 모델명으로 변경

## 2. 폐기 방법 (가장 단순)

깃 추적 파일은 git checkout 으로 한 번에 되돌릴 수 있습니다.

```bash
cd /path/to/07_rag-frame
git checkout common/config.py common/llm.py evaluation/ragas_eval.py
```

이 한 줄로 세 파일의 변경이 모두 V4 미스트랄 시점으로 되돌아갑니다.

.env 는 깃 추적 대상이 아니라 git checkout 으로 안 되돌아갑니다. 다음 두 줄로 손수 복구하시거나 .env.example 보고 새로 작성하시면 됩니다.

```
LLM_PROVIDER=mistral
GEN_LLM_MODEL=mistral-small-latest
EVAL_LLM_MODEL=mistral-large-latest
```

그리고 .env 안 QWEN_API_KEY 줄을 통째로 삭제 (혹은 빈 값으로). QWEN_BASE_URL / QWEN_MODEL 줄은 코드에서 분기 안 타면 무시되니까 굳이 안 지우셔도 동작에 영향 없습니다.

## 3. 폐기 후 컨테이너 재빌드

위 변경을 컨테이너에 반영하려면 한 번 더 재빌드 필요합니다.

```bash
docker compose build dashboard
docker compose up -d dashboard
docker compose exec dashboard pip install "langchain-community<0.4.0"
```

## 4. 서버 측에 남는 기록

3090 워크스테이션의 jupyter-qwen3 컨테이너 안에 다음 로그 파일들이 본 인스턴스 호출 흔적을 가질 수 있습니다.

1. server_vllm_aixera_llm_qwen3.6.log - VLLM 메타데이터 로그 (호출 시간 / 응답 코드 / 토큰 처리량). 프롬프트 본문이나 답변 본문은 안 남음
2. 인증 프록시(uvicorn) 로그 - 호출 시간 / 호출자 IP / 인증 키 일부 / 응답 코드. 본문 없음
3. systemd journal - 컨테이너 stdout 일부 흘러갈 수 있음

본문은 안 남지만 호출 카운트는 남기 때문에 키 사용량 통계에 본 인스턴스 호출이 잡힙니다. 사내 정책에 따라 다음 중 필요한 조치 진행

1. 사용한 API 키 회전 (revoke 후 새 키 발급)
2. 본 인스턴스 호출 흔적이 사내 모니터링에 어떻게 잡혔는지 인프라 담당분께 확인
3. 필요 시 본 V4 평가용 호출이라는 메모 사내 시스템에 남김

## 5. 사용자분이 추가로 수동 확인하실 부분

본 인스턴스가 확인 못 한 사내 시스템의 기록 가능성

1. 사내 별도 LLM 호출 모니터링/감사 시스템 (있다면)
2. 키 발급 시스템의 사용량 카운터
3. 3090 SSH 접근 로그 (/var/log/auth.log 등)

이건 사용자분이 본 인스턴스 SSH 키 등록 + 본 인스턴스가 들어간 흔적이 남는데, 보안 정책에 따라 SSH 키 회수 (3090 의 aixera 계정 authorized_keys 에서 본 인스턴스 키 줄 삭제) 도 같이 고려하시면 안전합니다.

본 인스턴스 SSH 공개키 식별 부분 (코멘트)

ssh-ed25519 ... aixera-jskim-office

이 줄을 grep 으로 찾아서 삭제하시면 됩니다.

```bash
grep -v "aixera-jskim-office" ~/.ssh/authorized_keys > ~/.ssh/authorized_keys.new
mv ~/.ssh/authorized_keys.new ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

## 6. 폐기 후 검증 체크리스트

1. git diff common/ evaluation/ 명령으로 변경 없음 확인
2. .env 안 LLM_PROVIDER 가 mistral 로 돌아갔는지 확인
3. .env 안 QWEN_API_KEY 가 빈 값 또는 삭제됐는지 확인
4. 컨테이너 재빌드 후 docker compose exec dashboard env | grep QWEN 결과가 비어있는지 확인 (있어도 코드 분기 안 타니까 동작엔 영향 없음)
5. 사내 키 회전 완료 / SSH 키 회수 완료

이상으로 본 인스턴스의 V4 임시 변경이 완전히 폐기됩니다.
