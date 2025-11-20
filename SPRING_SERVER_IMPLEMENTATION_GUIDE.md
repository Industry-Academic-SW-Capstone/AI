# Spring 서버 포트폴리오 분석 구현 가이드

## 📋 프로젝트 상황

### 프로젝트 개요

- **메인 서버**: Spring Boot (이 레포지토리)
- **AI 서버**: FastAPI (Python) - 별도 레포지토리
- **배포 환경**: Kubernetes (GKE)
- **도메인**: https://www.stockit.live

### 현재 완료된 부분

#### ✅ AI 서버 (Python)

- **엔드포인트**: `/portfolio/analyze` (POST)
- **상태**: 구현 완료 및 배포 완료
- **Kubernetes Service**: `stock-analyze-svc:8000`
- **CORS**: 설정 완료 (모든 origin 허용)
- **DTO**: 영문 필드명 지원 (`stock_code`, `market_cap`, `investment_amount` 등)

#### ✅ Spring 서버 (기존 구현)

- **단일 종목 분석**: `/api/stocks/{stockCode}/analyze` (POST) - PR #73에서 구현 완료
- **PythonAnalysisClient**: `analyze()` 메서드 구현 완료
- **StockAnalysisService**: KIS API 호출 및 Python 서버 연동 로직 완료
- **Redis 캐싱**: KIS API 결과 캐싱 (시장: 5분, 재무/배당: 24시간)

#### ❌ 아직 구현 필요한 부분

- **포트폴리오 분석**: `/api/portfolio/analyze` (GET 또는 POST)
- **PortfolioAnalysisService**: AccountStock 조회 → 재무 데이터 수집 → AI 서버 호출
- **PythonAnalysisClient**: `analyzePortfolio()` 메서드 추가
- **PortfolioAnalysisController**: 엔드포인트 추가

---

## 🎯 구현 목표

사용자의 main 계좌에 보유한 모든 주식을 분석하여:

1. 각 종목별 AI 스타일 분석
2. 전체 포트폴리오의 투자 스타일 비중
3. 페르소나 매칭 (워렌 버핏, 피터 린치 등과의 유사도)

---

## 📊 데이터 흐름

```
1. 프론트엔드
   └─> GET /api/portfolio/analyze (JWT 포함)
       ↓
2. Spring 서버 Controller
   └─> PortfolioAnalysisService.analyzePortfolio(accountId)
       ↓
3. Spring 서버 Service
   ├─> JWT에서 사용자 ID 추출
   ├─> main 계좌 조회 (is_default = true)
   ├─> AccountStock 조회 (보유 종목 목록)
   └─> 각 종목별 재무 데이터 조회 (KIS API 3개, 병렬 처리)
       ↓
4. Spring 서버 PythonClient
   └─> POST http://stock-analyze-svc:8000/portfolio/analyze
       {
         "stocks": [
           {
             "stock_code": "005930",
             "market_cap": 6363611000000.0,
             "per": 21.72,
             "pbr": 1.86,
             "roe": 6.64,
             "debt_ratio": 26.36,
             "dividend_yield": 370.0,
             "investment_amount": 700000  // quantity * averagePrice
           }
         ]
       }
       ↓
5. AI 서버
   ├─> 각 종목별 스타일 분석 (K-means 모델)
   ├─> 투자금액 비중으로 사용자 스타일 벡터 계산
   ├─> 페르소나 매칭 (유사도 계산)
   └─> 결과 반환
       ↓
6. Spring 서버
   └─> 프론트엔드로 응답 전달
```

---

## 🔌 AI 서버 API 스펙

### 요청 형식 (POST `/portfolio/analyze`)

```json
{
  "stocks": [
    {
      "stock_code": "005930",
      "market_cap": 6363611000000.0,
      "per": 21.72,
      "pbr": 1.86,
      "roe": 6.64,
      "debt_ratio": 26.36,
      "dividend_yield": 370.0,
      "investment_amount": 700000
    },
    {
      "stock_code": "000660",
      "market_cap": 4069533000000.0,
      "per": 20.57,
      "pbr": 5.35,
      "roe": 37.52,
      "debt_ratio": 48.13,
      "dividend_yield": 7.5,
      "investment_amount": 600000
    }
  ]
}
```

**필드 설명**:

- `stock_code`: 종목 코드 (String) - 필수
- `market_cap`: 시가총액 (Double) - 필수
- `per`: PER (Double) - 필수
- `pbr`: PBR (Double) - 필수
- `roe`: ROE (Double) - 필수
- `debt_ratio`: 부채비율 (Double) - 필수
- `dividend_yield`: 배당수익률 (Double) - 필수
- `investment_amount`: 투자금액 (Double) - 필수 (quantity \* averagePrice)

### 응답 형식

```json
{
  "stock_details": [
    {
      "stock_code": "005930",
      "stock_name": "삼성전자",
      "style_tag": "[초대형 우량주]",
      "description": "대한민국 대표 우량주: 시가총액이 가장 커요..."
    },
    {
      "stock_code": "000660",
      "stock_name": "SK하이닉스",
      "style_tag": "[고성장 기대주]",
      "description": "미래를 꿈꾸는 성장주: PER이 엄청나게 높아요..."
    }
  ],
  "summary": {
    "market_cap": 5216781500000.0,
    "per": 21.145,
    "pbr": 3.605,
    "roe": 22.08,
    "debt_ratio": 37.245,
    "dividend_yield": 188.75
  },
  "style_breakdown": [
    {
      "style_tag": "[고성장 기대주]",
      "percentage": 51.7
    },
    {
      "style_tag": "[초대형 우량주]",
      "percentage": 48.3
    }
  ],
  "persona_match": [
    {
      "name": "피터 린치",
      "percentage": 68.0,
      "philosophy": "[근거: ...] 피터 린치는..."
    },
    {
      "name": "워렌 버핏",
      "percentage": 42.0,
      "philosophy": "[근거: ...] 워렌 버핏은..."
    }
  ]
}
```

**응답 필드 설명**:

- `stock_details`: 각 종목별 분석 결과 (List)
- `summary`: 포트폴리오 종합 성향 (가중 평균, Map<String, Double>)
- `style_breakdown`: 스타일 태그별 비중 (List, 내림차순 정렬)
- `persona_match`: 페르소나 일치율 (List, 내림차순 정렬)

---

## 💻 구현해야 할 코드

### 1. DTO 생성

#### PortfolioStockDto.java (요청용)

```java
package grit.stockIt.domain.stock.analysis.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record PortfolioStockDto(
    @JsonProperty("stock_code") String stockCode,
    @JsonProperty("market_cap") Double marketCap,
    @JsonProperty("per") Double per,
    @JsonProperty("pbr") Double pbr,
    @JsonProperty("roe") Double roe,
    @JsonProperty("debt_ratio") Double debtRatio,
    @JsonProperty("dividend_yield") Double dividendYield,
    @JsonProperty("investment_amount") Double investmentAmount
) {}
```

#### PortfolioAnalysisRequest.java

```java
package grit.stockIt.domain.stock.analysis.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public record PortfolioAnalysisRequest(
    @JsonProperty("stocks") List<PortfolioStockDto> stocks
) {}
```

#### StockDetail.java (응답용)

```java
package grit.stockIt.domain.stock.analysis.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record StockDetail(
    @JsonProperty("stock_code") String stockCode,
    @JsonProperty("stock_name") String stockName,
    @JsonProperty("style_tag") String styleTag,
    @JsonProperty("description") String description
) {}
```

#### StyleBreakdown.java (응답용)

```java
package grit.stockIt.domain.stock.analysis.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record StyleBreakdown(
    @JsonProperty("style_tag") String styleTag,
    @JsonProperty("percentage") Double percentage
) {}
```

#### PersonaMatch.java (응답용)

```java
package grit.stockIt.domain.stock.analysis.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record PersonaMatch(
    @JsonProperty("name") String name,
    @JsonProperty("percentage") Double percentage,
    @JsonProperty("philosophy") String philosophy
) {}
```

#### PortfolioAnalysisResponse.java (응답용)

```java
package grit.stockIt.domain.stock.analysis.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import java.util.Map;

public record PortfolioAnalysisResponse(
    @JsonProperty("stock_details") List<StockDetail> stockDetails,
    @JsonProperty("summary") Map<String, Double> summary,
    @JsonProperty("style_breakdown") List<StyleBreakdown> styleBreakdown,
    @JsonProperty("persona_match") List<PersonaMatch> personaMatch
) {}
```

---

### 2. PythonAnalysisClient에 메서드 추가

```java
// PythonAnalysisClient.java
public Mono<PortfolioAnalysisResponse> analyzePortfolio(PortfolioAnalysisRequest request) {
    return webClient.post()
        .uri(pythonServerUrl + "/portfolio/analyze")  // AI 서버 엔드포인트
        .bodyValue(request)
        .retrieve()
        .bodyToMono(PortfolioAnalysisResponse.class)
        .onErrorResume(e -> {
            log.error("포트폴리오 분석 API 호출 실패", e);
            return Mono.error(new RuntimeException("AI 서버 분석 실패", e));
        });
}
```

---

### 3. PortfolioAnalysisService 생성

```java
package grit.stockIt.domain.stock.analysis.service;

import grit.stockIt.domain.account.entity.Account;
import grit.stockIt.domain.account.entity.AccountStock;
import grit.stockIt.domain.account.repository.AccountRepository;
import grit.stockIt.domain.account.repository.AccountStockRepository;
import grit.stockIt.domain.stock.analysis.dto.*;
import grit.stockIt.global.exception.BadRequestException;
import grit.stockIt.global.exception.ForbiddenException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class PortfolioAnalysisService {

    private final AccountRepository accountRepository;
    private final AccountStockRepository accountStockRepository;
    private final StockAnalysisService stockAnalysisService;  // 기존 Service 재사용
    private final PythonAnalysisClient pythonAnalysisClient;

    @Transactional(readOnly = true)
    public Mono<PortfolioAnalysisResponse> analyzePortfolio(Long accountId) {
        // 1. Account 조회 및 권한 확인
        Account account = accountRepository.findById(accountId)
            .orElseThrow(() -> new BadRequestException("계좌를 찾을 수 없습니다."));

        ensureAccountOwner(account);

        // 2. AccountStock에서 보유 종목 조회
        List<AccountStock> accountStocks = accountStockRepository
            .findByAccountIdWithStock(accountId);

        if (accountStocks.isEmpty()) {
            log.info("보유종목이 없습니다: accountId={}", accountId);
            return Mono.just(createEmptyResponse());
        }

        // 3. 각 종목의 재무 데이터 조회 (병렬 처리)
        // StockAnalysisService의 getMarketData, getFinancialData, getDividendData를 재사용
        List<Mono<PortfolioStockDto>> stockMonoList = accountStocks.stream()
            .map(accountStock -> {
                String stockCode = accountStock.getStock().getCode();

                // 투자금액 계산
                BigDecimal investmentAmount = accountStock.getAveragePrice()
                    .multiply(BigDecimal.valueOf(accountStock.getQuantity()));

                // KIS API 3개 호출 (병렬 처리, 캐시 우선)
                // StockAnalysisService의 private 메서드를 사용하려면 리팩토링이 필요합니다.
                // 여기서는 직접 호출 가능한 public 메서드가 있다고 가정합니다.

                // 방법 1: StockAnalysisService의 analyzeStock을 호출하고 응답에서 재무 데이터 추출
                // 방법 2: StockAnalysisService에 public 메서드 추가 (getMarketData, getFinancialData, getDividendData)
                // 방법 3: 여기서 직접 KIS API 호출 (중복 코드)

                // 여기서는 방법 1을 사용 (간단하지만 비효율적)
                // 실제로는 방법 2를 권장 (StockAnalysisService 리팩토링 필요)

                return getStockDataForPortfolio(stockCode, investmentAmount);
            })
            .toList();

        // 4. 모든 종목 데이터 수집
        return Flux.merge(stockMonoList)
            .collectList()
            .flatMap(stocks -> {
                // 5. Python AI 서버로 POST 요청
                PortfolioAnalysisRequest request = new PortfolioAnalysisRequest(stocks);
                return pythonAnalysisClient.analyzePortfolio(request);
            })
            .onErrorResume(e -> {
                log.error("포트폴리오 분석 실패: accountId={}", accountId, e);
                return Mono.just(createEmptyResponse());
            });
    }

    // 각 종목의 재무 데이터를 조회하는 헬퍼 메서드
    // 주의: StockAnalysisService에 public 메서드가 있다면 그것을 사용하세요
    private Mono<PortfolioStockDto> getStockDataForPortfolio(
            String stockCode,
            BigDecimal investmentAmount) {

        // StockAnalysisService의 analyzeStock을 호출하고
        // 응답이 아닌 중간 데이터를 가져와야 합니다.
        // 실제로는 StockAnalysisService에 다음과 같은 public 메서드가 필요합니다:
        // - Mono<MarketData> getMarketData(String stockCode)
        // - Mono<FinancialData> getFinancialData(String stockCode)
        // - Mono<DividendData> getDividendData(String stockCode)

        // 임시 구현 (StockAnalysisService를 리팩토링해야 함)
        // 여기서는 기존 analyzeStock을 호출하지만, 이는 AI 분석까지 수행하므로 비효율적입니다.
        // 실제 구현 시 StockAnalysisService를 리팩토링하여 재무 데이터만 조회하는 메서드를 public으로 만들어야 합니다.

        // 임시로 KIS API를 직접 호출하는 로직 (StockAnalysisService 코드 참고)
        // 실제로는 StockAnalysisService의 private 메서드를 public으로 변경하거나
        // 별도의 Service를 만들어야 합니다.

        // 여기서는 예시 코드만 제공합니다.
        return Mono.just(new PortfolioStockDto(
            stockCode,
            null, // marketCap - StockAnalysisService에서 가져와야 함
            null, // per
            null, // pbr
            null, // roe
            null, // debtRatio
            null, // dividendYield
            investmentAmount.doubleValue()
        ));
    }

    // 계좌 소유자 확인
    private void ensureAccountOwner(Account account) {
        String memberEmail = getAuthenticatedEmail();
        if (!account.getMember().getEmail().equals(memberEmail)) {
            throw new ForbiddenException("해당 계좌에 대한 권한이 없습니다.");
        }
    }

    // 인증된 사용자 이메일 조회
    private String getAuthenticatedEmail() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || !authentication.isAuthenticated()
                || "anonymousUser".equals(authentication.getPrincipal())) {
            throw new ForbiddenException("로그인이 필요합니다.");
        }
        return authentication.getName();
    }

    // 빈 응답 생성
    private PortfolioAnalysisResponse createEmptyResponse() {
        return new PortfolioAnalysisResponse(
            List.of(),
            Map.of(),
            List.of(),
            List.of()
        );
    }
}
```

**⚠️ 중요**: `StockAnalysisService`의 `getMarketData()`, `getFinancialData()`, `getDividendData()` 메서드가 `private`이므로, 이를 `public`으로 변경하거나 별도의 `StockDataService`를 만들어야 합니다.

---

### 4. StockAnalysisService 리팩토링 (선택사항, 권장)

기존 `StockAnalysisService`의 private 메서드를 public으로 변경:

```java
// StockAnalysisService.java
// 기존 private 메서드를 public으로 변경

public Mono<MarketData> getMarketData(String stockCode) {
    // 기존 private getMarketData 로직
    // ...
}

public Mono<FinancialData> getFinancialData(String stockCode) {
    // 기존 private getFinancialData 로직
    // ...
}

public Mono<DividendData> getDividendData(String stockCode) {
    // 기존 private getDividendData 로직
    // ...
}
```

그러면 `PortfolioAnalysisService`에서:

```java
private Mono<PortfolioStockDto> getStockDataForPortfolio(
        String stockCode,
        BigDecimal investmentAmount) {

    Mono<MarketData> marketDataMono = stockAnalysisService.getMarketData(stockCode);
    Mono<FinancialData> financialDataMono = stockAnalysisService.getFinancialData(stockCode);
    Mono<DividendData> dividendDataMono = stockAnalysisService.getDividendData(stockCode);

    return Mono.zip(marketDataMono, financialDataMono, dividendDataMono)
        .map(tuple -> {
            MarketData marketData = tuple.getT1();
            FinancialData financialData = tuple.getT2();
            DividendData dividendData = tuple.getT3();

            return new PortfolioStockDto(
                stockCode,
                marketData.marketCap() != null ? marketData.marketCap().doubleValue() : null,
                marketData.per(),
                marketData.pbr(),
                financialData.roe(),
                financialData.debtRatio(),
                dividendData.dividendYield() != null ? dividendData.dividendYield() : 0.0,
                investmentAmount.doubleValue()
            );
        });
}
```

---

### 5. PortfolioAnalysisController 생성

```java
package grit.stockIt.domain.stock.analysis.controller;

import grit.stockIt.domain.stock.analysis.dto.PortfolioAnalysisResponse;
import grit.stockIt.domain.stock.analysis.service.PortfolioAnalysisService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@Slf4j
@RestController
@RequestMapping("/api/portfolio")
@Tag(name = "portfolio-analysis", description = "포트폴리오 분석 API")
@RequiredArgsConstructor
public class PortfolioAnalysisController {

    private final PortfolioAnalysisService portfolioAnalysisService;

    @Operation(summary = "포트폴리오 분석", description = "사용자의 보유 종목을 분석하여 투자 스타일과 페르소나를 매칭합니다.")
    @GetMapping("/analyze")
    public Mono<PortfolioAnalysisResponse> analyzePortfolio(
        @RequestParam Long accountId
    ) {
        log.info("포트폴리오 분석 요청: accountId={}", accountId);
        return portfolioAnalysisService.analyzePortfolio(accountId);
    }
}
```

---

## 🔧 설정 확인

### application.yml

```yaml
python:
  analysis:
    url: http://stock-analyze-svc:8000 # Kubernetes 내부 Service 이름
```

또는 로컬 테스트용:

```yaml
python:
  analysis:
    url: http://localhost:8000 # 포트 포워딩 사용 시
```

---

## 📝 구현 체크리스트

- [ ] DTO 생성 (PortfolioStockDto, PortfolioAnalysisRequest, PortfolioAnalysisResponse 등)
- [ ] PythonAnalysisClient에 `analyzePortfolio()` 메서드 추가
- [ ] StockAnalysisService 리팩토링 (선택사항, 권장)
- [ ] PortfolioAnalysisService 생성
- [ ] PortfolioAnalysisController 생성
- [ ] application.yml 설정 확인
- [ ] 테스트 작성
- [ ] API 문서 업데이트 (Swagger)

---

## 🧪 테스트 방법

### 1. 로컬 테스트

```bash
# AI 서버 포트 포워딩
kubectl port-forward deploy/stock-analyze-deployment 8000:8000

# Spring 서버 실행
# application.yml에서 python.analysis.url을 http://localhost:8000으로 설정

# Swagger UI에서 테스트
# GET http://localhost:8080/api/portfolio/analyze?accountId=1
```

### 2. Kubernetes 환경 테스트

```bash
# AI 서버 Service 확인
kubectl get svc stock-analyze-svc

# Spring 서버 Pod에서 테스트
kubectl exec -it <spring-pod-name> -- curl http://stock-analyze-svc:8000/
```

---

## ⚠️ 주의사항

1. **StockAnalysisService 리팩토링**: 기존 private 메서드를 public으로 변경하거나 별도 Service를 만들어야 합니다.
2. **에러 처리**: AI 서버 호출 실패 시 빈 응답을 반환하거나 적절한 에러 처리 필요
3. **권한 확인**: Account 소유자 확인 로직 필수
4. **캐싱**: StockAnalysisService의 Redis 캐싱이 자동으로 적용됩니다
5. **병렬 처리**: Flux.merge를 사용하여 여러 종목의 재무 데이터를 병렬로 조회

---

## 📚 참고 자료

- **기존 코드**: `StockAnalysisService`, `StockAnalysisController` (PR #73)
- **AI 서버**: `http://stock-analyze-svc:8000/docs` (Swagger UI)
- **엔티티**: `Account`, `AccountStock`, `Stock`

---

## 🎉 완료 후 확인 사항

1. Swagger UI에서 `/api/portfolio/analyze` 엔드포인트가 보이는지
2. 실제 호출 시 AI 서버로 요청이 전달되는지 (로그 확인)
3. AI 서버로부터 올바른 응답을 받는지
4. 프론트엔드에서 정상적으로 데이터가 표시되는지

---

**이 문서를 Spring 서버 레포지토리에 복사하여 사용하세요!**
