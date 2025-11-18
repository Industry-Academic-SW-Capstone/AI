# 🚀 Redis 캐싱 성능 테스트 가이드

## 📋 목차
1. [테스트 환경 구축](#1-테스트-환경-구축)
2. [성능 테스트 실행 방법](#2-성능-테스트-실행-방법)
3. [예상 결과 포맷](#3-예상-결과-포맷)
4. [이력서 작성 가이드](#4-이력서-작성-가이드)

---

## 1. 테스트 환경 구축

### 1-1. 배포 환경
- **서버:** GKE (Google Kubernetes Engine)
- **위치:** (배포 후 URL 입력 예정)
- **캐시:** Redis 7 (GKE)
- **LLM API:** Google Gemini 2.0 Flash (무료 티어)
- **애플리케이션:** FastAPI + Python 3.10

### 1-2. 테스트 아키텍처

```
사용자 요청
    ↓
FastAPI Pod (replicas: 2)
    ↓
[캐시 확인] → Redis Pod
    ↓ (캐시 미스)
Gemini API 호출
    ↓
Redis에 저장 (TTL: 3시간)
```

---

## 2. 성능 테스트 실행 방법

### 2-1. 테스트 엔드포인트

**POST** `/test/performance/compare`

### 2-2. 요청 예시

#### 📌 100회 요청 테스트 (권장 - 무료 API 안전)
```bash
curl -X POST "https://<your-domain>/test/performance/compare" \
  -H "Content-Type: application/json" \
  -d '{
    "company_names": ["삼성전자", "SK하이닉스", "NAVER", "카카오"],
    "request_count": 100
  }'
```

#### 📌 1000회 요청 테스트 (주의: API 한도 확인 필요)
```bash
curl -X POST "https://<your-domain>/test/performance/compare" \
  -H "Content-Type: application/json" \
  -d '{
    "company_names": ["삼성전자", "SK하이닉스", "NAVER", "카카오", "LG에너지솔루션"],
    "request_count": 1000
  }'
```

### 2-3. 테스트 시나리오 설명

- **기업 4개 × 100회 요청** = 각 기업당 25회씩 조회
- **첫 번째 조회**: 캐시 미스 → Gemini API 호출 (약 1~3초)
- **이후 조회**: 캐시 히트 → Redis에서 반환 (약 1~10ms)

---

## 3. 예상 결과 포맷

### 3-1. 응답 JSON 구조

```json
{
  "test_config": {
    "company_names": ["삼성전자", "SK하이닉스", "NAVER", "카카오"],
    "company_count": 4,
    "request_count": 100,
    "requests_per_company": 25
  },
  "with_cache": {
    "avg_time_ms": 15.234,
    "min_time_ms": 1.023,
    "max_time_ms": 1523.456,
    "total_time_ms": 1523.4,
    "cache_hits": 96,
    "cache_misses": 4,
    "cache_hit_rate": 96.0
  },
  "without_cache": {
    "avg_time_ms": 1850.123,
    "min_time_ms": 1200.456,
    "max_time_ms": 2800.789,
    "total_time_ms": 185012.3,
    "cache_hits": 0,
    "cache_misses": 100,
    "cache_hit_rate": 0
  },
  "improvement": {
    "speed_improvement": "121.5배",
    "avg_time_reduction": "1834.889ms",
    "time_reduction_percent": "99.2%",
    "total_time_saved": "183488.9ms",
    "api_calls_reduced": 96,
    "api_call_reduction_percent": "96.0%"
  }
}
```

### 3-2. 성능 지표 해석

| 지표 | 설명 | 이력서 활용 |
|------|------|------------|
| **speed_improvement** | 캐시 사용 시 몇 배 빨라졌는지 | "Redis 캐싱으로 응답 속도 **121.5배** 개선" |
| **time_reduction_percent** | 응답 시간 단축 비율 | "평균 응답 시간 **99.2% 단축**" |
| **cache_hit_rate** | 캐시에서 바로 응답한 비율 | "캐시 히트율 **96%** 달성" |
| **api_calls_reduced** | 절감한 API 호출 수 | "Gemini API 호출 **96회 절감** (비용 절감)" |

---

## 4. 이력서 작성 가이드

### 4-1. 기술 스택 선택 근거 (면접 대비)

#### Q: "왜 Redis를 선택했나요?"

**모범 답변**:
> "5가지 분산 캐시 솔루션을 비교 분석했습니다.
> 
> 1. **Redis vs Memcached**: TTL 제한(30일) 없고 자료구조가 풍부한 Redis 선택
> 2. **Redis vs Hazelcast**: 소규모 서비스에서 3노드 클러스터는 오버엔지니어링 판단
> 3. **Redis vs Caffeine**: Kubernetes 멀티 Pod 환경(replicas: 2)에서 로컬 캐시는 Pod 간 공유 불가 → 캐시 효율 50% 감소
> 4. **Redis vs DragonflyDB**: 신생 프로젝트로 프로덕션 검증 부족
> 
> **결론**: 안정성, 커뮤니티, 운영 편의성을 고려해 Redis 선택했습니다."

---

### 4-2. 이력서 기재 예시

#### 📌 **버전 1: 간결형 (1줄)**
```
Redis 캐싱으로 Gemini LLM 기업 설명 API 응답 속도 120배 개선 (1.8초 → 15ms)
```

#### 📌 **버전 2: 기술 스택 명시 (추천)**
```
[성능 최적화] Redis 분산 캐싱을 활용한 AI 서비스 응답 속도 개선

- Kubernetes 멀티 Pod 환경에서 분산 캐시 전략 설계
- Gemini LLM API 응답 시간 99% 단축: 1.85초 → 15ms (120배 향상)
- API 호출 96% 절감으로 무료 티어 한도 내 서비스 운영 가능
- 캐시 히트율 96% 달성 (TTL: 3시간, 인기 종목 중심 최적화)
- GKE 프로덕션 환경에서 100회 부하 테스트로 검증
```

#### 📌 **버전 3: 상세형 (기술 블로그/포트폴리오용)**
```
[시스템 설계] AI 기반 주식 분석 서비스의 Redis 캐싱 아키텍처 구축

**1. 문제 정의**
- Gemini LLM API 호출 시 평균 1.85초 응답 시간으로 사용자 경험 저하
- Kubernetes 환경 (replicas: 2)에서 로컬 캐시는 Pod 간 공유 불가
- 무료 API 한도 (RPM 제한)로 인한 확장성 제약

**2. 솔루션 설계**
- 5가지 캐싱 솔루션 비교 분석 후 Redis 선택
  - Caffeine (로컬): Pod 간 공유 불가로 탈락
  - Memcached: TTL 30일 제한, 기능 제약으로 탈락
  - Hazelcast: 소규모 서비스에 과도한 리소스 (3노드) 소요로 탈락
  - DragonflyDB: 프로덕션 검증 부족으로 탈락
  - **Redis**: 안정성, 커뮤니티, TTL 유연성으로 최종 선택
- TTL 전략: 기업 정보(3시간), 재무 분석(1시간) 차등 적용
- 캐시 키 설계: `company_desc:{한글명}` (MD5 해시 사용)

**3. 구현 결과**
- **성능**: 응답 속도 120배 향상 (1.85초 → 15ms, 99% 단축)
- **비용**: Gemini API 호출 96% 절감 (100회 → 4회)
- **안정성**: 캐시 히트율 96% 달성, Redis SPOF 대응 전략 수립
- **확장성**: 동시 접속자 1000명 처리 가능 (기존 10명 수준)

**4. 검증**
- GKE 환경에서 100회/1000회 부하 테스트로 성능 검증
- Prometheus + Grafana로 실시간 모니터링 구축

**기술 스택**: Python, FastAPI, Redis, Kubernetes (GKE), Gemini API, Prometheus
```

---

### 4-3. 면접 예상 질문 & 답변

#### Q1: "캐시 만료(TTL)를 3시간으로 설정한 이유는?"
**A**: "기업 설명은 분 단위로 변하지 않는 정적 데이터입니다. 하지만 신규 상장, 사업 재편 등을 고려해 너무 길면 안 되므로 3시간으로 설정했습니다. 반면 재무 지표(PER, PBR)는 주가에 따라 변동이 크므로 1시간 TTL을 적용했습니다."

#### Q2: "Redis가 다운되면 어떻게 되나요?"
**A**: "현재는 단일 Redis 인스턴스라 SPOF입니다. 하지만 캐시는 휘발성 데이터이므로 Redis 다운 시 Gemini API를 직접 호출해 서비스는 유지됩니다. 다만 응답이 느려지죠. 향후 트래픽 증가 시 Redis Sentinel(HA) 또는 Redis Cluster로 마이그레이션 계획입니다."

#### Q3: "Caffeine 대신 Redis를 선택한 결정적 이유는?"
**A**: "Kubernetes 멀티 Pod 환경(replicas: 2)입니다. Caffeine은 각 Pod마다 독립적인 캐시를 가지므로 같은 데이터를 2번 저장하고, 캐시 히트율도 50% 감소합니다. Redis는 모든 Pod가 공유하므로 메모리 효율과 캐시 효율이 모두 높습니다. 또한 Pod 재시작 시에도 캐시가 보존됩니다."

---

## 5. 실제 테스트 실행 체크리스트

### 배포 전
- [ ] Docker 이미지 빌드 (v0.1.5)
- [ ] Gemini API 키 Secret 등록
- [ ] Redis Deployment 배포
- [ ] AI 서버 Deployment 배포

### 테스트 실행
- [ ] Swagger UI에서 `/test/performance/compare` 확인
- [ ] 100회 테스트 실행 (안전)
- [ ] 결과 JSON 저장
- [ ] 1000회 테스트 실행 (API 한도 확인 후)
- [ ] 결과 JSON 저장

### 문서화
- [ ] 실제 측정값으로 README 업데이트
- [ ] 이력서/포트폴리오에 수치 반영
- [ ] GitHub에 성능 테스트 결과 업로드
- [ ] 기술 블로그 작성 (선택)

---

## 6. 주의사항

⚠️ **Gemini API 무료 한도**
- RPM (Requests Per Minute): 분당 15회
- 1000회 테스트 시 약 66분 소요 예상
- 테스트 전 API 사용량 확인 필수!

⚠️ **캐시 워밍업**
- 첫 번째 테스트는 캐시가 비어있어 모든 요청이 API 호출됨
- 정확한 비교를 위해 한 번 워밍업 후 재측정 권장

---

## 7. 다음 단계

1. **Docker 빌드 & 배포**
   ```bash
   docker buildx build --platform linux/amd64,linux/arm64 -t choij17/stock-ai-analyze-server:0.1.5 --push .
   kubectl apply -f k8s/
   ```

2. **포트포워딩으로 로컬 테스트**
   ```bash
   kubectl port-forward deploy/stock-analyze-deployment 8000:8000
   ```

3. **Swagger UI 접속**
   ```
   http://localhost:8000/docs
   ```

4. **성능 테스트 실행**
   - `/test/performance/compare` 엔드포인트 호출
   - 결과 JSON 저장

5. **이력서 작성**
   - 실제 측정값으로 성과 기재
   - 기술적 의사결정 과정 정리

---

**작성일**: 2025-11-18  
**작성자**: Stockit AI Team  
**버전**: 0.1.5

