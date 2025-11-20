# Spring 서버 stock_name 전달 확인 가이드

## 📋 확인 목적

Spring 서버에서 Python AI 서버로 `stock_name`(종목명)을 제대로 전달하는지 확인합니다.

---

## ✅ 수정해야 할 파일 체크리스트

### 1. DTO 수정 확인

#### `PortfolioStockDto.java` (또는 해당 DTO 파일)

**확인 사항**: `stockName` 필드가 있는지 확인

```java
package grit.stockIt.domain.stock.analysis.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record PortfolioStockDto(
    @JsonProperty("stock_code") String stockCode,
    @JsonProperty("stock_name") String stockName,  // ✅ 이 필드가 있어야 함!
    @JsonProperty("market_cap") Double marketCap,
    @JsonProperty("per") Double per,
    @JsonProperty("pbr") Double pbr,
    @JsonProperty("roe") Double roe,
    @JsonProperty("debt_ratio") Double debtRatio,
    @JsonProperty("dividend_yield") Double dividendYield,
    @JsonProperty("investment_amount") Double investmentAmount
) {}
```

**체크 포인트**:

- [ ] `stockName` 필드가 있음
- [ ] `@JsonProperty("stock_name")` 어노테이션이 있음
- [ ] 필드 타입이 `String`임

---

### 2. Service 수정 확인

#### `PortfolioAnalysisService.java` (또는 해당 Service 파일)

**확인 사항**: `stockName`을 설정하는 코드가 있는지 확인

```java
@Service
@RequiredArgsConstructor
public class PortfolioAnalysisService {

    // ... 기존 코드 ...

    private Mono<PortfolioStockDto> getStockDataForPortfolio(
            String stockCode,
            BigDecimal investmentAmount) {

        // ... KIS API 호출 로직 ...

        return Mono.zip(marketDataMono, financialDataMono, dividendDataMono)
            .map(tuple -> {
                MarketData marketData = tuple.getT1();
                FinancialData financialData = tuple.getT2();
                DividendData dividendData = tuple.getT3();

                // ✅ 여기서 stockName을 설정해야 함!
                String stockName = accountStock.getStock().getName();  // 또는 KIS API에서 받은 종목명

                return new PortfolioStockDto(
                    stockCode,
                    stockName,  // ✅ stockName 전달!
                    marketData.marketCap() != null
                        ? marketData.marketCap().doubleValue() : null,
                    marketData.per(),
                    marketData.pbr(),
                    financialData.roe(),
                    financialData.debtRatio(),
                    dividendData.dividendYield() != null
                        ? dividendData.dividendYield() : 0.0,
                    investmentAmount.doubleValue()
                );
            });
    }
}
```

**체크 포인트**:

- [ ] `stockName` 변수를 선언하고 값을 설정함
- [ ] `AccountStock.getStock().getName()` 또는 KIS API에서 종목명을 가져옴
- [ ] `PortfolioStockDto` 생성 시 `stockName`을 전달함

---

### 3. 종목명 가져오는 방법 확인

#### 방법 1: AccountStock에서 가져오기 (권장)

```java
// AccountStock 엔티티에서 Stock 엔티티를 통해 종목명 가져오기
String stockName = accountStock.getStock().getName();
```

**확인 사항**:

- [ ] `AccountStock`에 `getStock()` 메서드가 있음
- [ ] `Stock` 엔티티에 `getName()` 메서드가 있음
- [ ] `findByAccountIdWithStock()` 메서드로 JOIN FETCH를 사용하여 Stock을 함께 가져옴

#### 방법 2: KIS API에서 가져오기

```java
// KIS API 응답에서 종목명 가져오기
return stockDetailService.getStockDetail(stockCode)
    .map(stockDetail -> {
        String stockName = stockDetail.name();  // KIS API 응답의 종목명
        // ...
    });
```

**확인 사항**:

- [ ] KIS API 응답 DTO에 종목명 필드가 있음
- [ ] 종목명을 올바르게 추출함

---

## 🧪 테스트 방법

### 1. 로그 확인

#### Spring 서버 로그에 stockName이 포함되는지 확인

```java
// PortfolioAnalysisService.java
log.info("포트폴리오 분석 요청: stockCode={}, stockName={}", stockCode, stockName);
```

**예상 로그 출력**:

```
포트폴리오 분석 요청: stockCode=005930, stockName=삼성전자
포트폴리오 분석 요청: stockCode=000660, stockName=SK하이닉스
```

---

### 2. 요청 JSON 확인

#### Python AI 서버로 전송되는 요청 확인

```java
// PythonAnalysisClient.java 또는 PortfolioAnalysisService.java
log.debug("AI 서버 요청: {}", objectMapper.writeValueAsString(request));
```

**예상 JSON 형식**:

```json
{
  "stocks": [
    {
      "stock_code": "005930",
      "stock_name": "삼성전자", // ✅ 이 필드가 있어야 함!
      "market_cap": 6363611000000.0,
      "per": 21.72,
      "pbr": 1.86,
      "roe": 6.64,
      "debt_ratio": 26.36,
      "dividend_yield": 370.0,
      "investment_amount": 700000
    }
  ]
}
```

**체크 포인트**:

- [ ] `stock_name` 필드가 JSON에 포함됨
- [ ] `stock_name` 값이 null이 아님
- [ ] `stock_name` 값이 올바른 종목명임 (예: "삼성전자", "SK하이닉스")

---

### 3. Python AI 서버 응답 확인

#### Python AI 서버에서 stock_name을 제대로 받는지 확인

**테스트 요청**:

```bash
# AI 서버 포트 포워딩
kubectl port-forward deploy/stock-analyze-deployment 8000:8000

# 테스트 요청
curl -X POST http://localhost:8000/portfolio/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "stocks": [
      {
        "stock_code": "005930",
        "stock_name": "삼성전자",
        "market_cap": 6363611000000.0,
        "per": 21.72,
        "pbr": 1.86,
        "roe": 6.64,
        "debt_ratio": 26.36,
        "dividend_yield": 370.0,
        "investment_amount": 700000
      }
    ]
  }'
```

**예상 응답**:

```json
{
  "stock_details": [
    {
      "stock_code": "005930",
      "stock_name": "삼성전자",  // ✅ Spring에서 전달한 값이 그대로 반환됨
      "style_tag": "[초대형 우량주]",
      "description": "..."
    }
  ],
  ...
}
```

**체크 포인트**:

- [ ] 응답의 `stock_name`이 요청의 `stock_name`과 동일함
- [ ] `stock_name`이 "알 수 없는 종목"이 아님

---

### 4. 통합 테스트

#### Spring 서버 → Python AI 서버 전체 흐름 테스트

**Swagger UI에서 테스트**:

1. Spring 서버 Swagger UI 접속: `http://localhost:8080/swagger-ui/index.html`
2. `/api/portfolio/analyze` 엔드포인트 호출
3. 응답 확인:
   - `stock_details[].stock_name`이 올바른 종목명인지 확인
   - "알 수 없는 종목"이 없는지 확인

---

## 🔍 디버깅 방법

### 문제 1: stock_name이 null로 전달됨

**원인**:

- `AccountStock.getStock()`이 null
- `Stock.getName()`이 null
- JOIN FETCH가 제대로 작동하지 않음

**해결**:

```java
// AccountStock 조회 시 JOIN FETCH 확인
List<AccountStock> accountStocks = accountStockRepository
    .findByAccountIdWithStock(accountId);  // JOIN FETCH 사용

// null 체크 추가
String stockName = accountStock.getStock() != null
    ? accountStock.getStock().getName()
    : null;

if (stockName == null) {
    log.warn("종목명을 찾을 수 없습니다: stockCode={}", stockCode);
    // KIS API에서 종목명 가져오기 시도
}
```

---

### 문제 2: stock_name이 JSON에 포함되지 않음

**원인**:

- `@JsonProperty("stock_name")` 어노테이션 누락
- Jackson 직렬화 설정 문제

**해결**:

```java
// DTO 확인
public record PortfolioStockDto(
    @JsonProperty("stock_code") String stockCode,
    @JsonProperty("stock_name") String stockName,  // ✅ 어노테이션 확인
    // ...
) {}
```

---

### 문제 3: Python 서버에서 "알 수 없는 종목" 반환

**원인**:

- Spring 서버에서 `stock_name`을 전달하지 않음
- `stock_name`이 null로 전달됨

**해결**:

1. Spring 서버 로그에서 요청 JSON 확인
2. `stock_name` 필드가 있는지 확인
3. `stock_name` 값이 null이 아닌지 확인

---

## 📝 체크리스트 요약

### 코드 수정 확인

- [ ] `PortfolioStockDto`에 `stockName` 필드 추가됨
- [ ] `@JsonProperty("stock_name")` 어노테이션 추가됨
- [ ] `PortfolioAnalysisService`에서 `stockName` 설정됨
- [ ] `AccountStock.getStock().getName()` 또는 KIS API에서 종목명 가져옴

### 테스트 확인

- [ ] Spring 서버 로그에 `stockName`이 포함됨
- [ ] 요청 JSON에 `stock_name` 필드가 포함됨
- [ ] Python AI 서버 응답에 올바른 종목명이 포함됨
- [ ] "알 수 없는 종목"이 발생하지 않음

---

## 🎯 최종 확인 방법

### 1. Spring 서버 코드 검색

```bash
# stockName 필드가 있는지 확인
grep -r "stockName" src/main/java/grit/stockIt/domain/stock/analysis/

# PortfolioStockDto 확인
cat src/main/java/grit/stockIt/domain/stock/analysis/dto/PortfolioStockDto.java

# PortfolioAnalysisService에서 stockName 설정 확인
grep -A 5 "stockName" src/main/java/grit/stockIt/domain/stock/analysis/service/PortfolioAnalysisService.java
```

---

### 2. 실제 요청/응답 확인

**Spring 서버 로그에서 확인**:

```
DEBUG - AI 서버 요청: {"stocks":[{"stock_code":"005930","stock_name":"삼성전자",...}]}
```

**Python AI 서버 로그에서 확인**:

```
INFO - 포트폴리오 분석 요청: stocks=[Stock(stock_code='005930', stock_name='삼성전자', ...)]
```

---

## ✅ 성공 기준

다음 조건을 모두 만족하면 정상 작동:

1. ✅ Spring 서버에서 `stock_name` 필드를 포함한 JSON을 Python 서버로 전송
2. ✅ Python 서버가 `stock_name`을 받아서 사용
3. ✅ 응답의 `stock_name`이 "알 수 없는 종목"이 아님
4. ✅ 응답의 `stock_name`이 Spring 서버에서 전달한 값과 동일함

---

## 🚨 문제 발생 시

위 체크리스트를 순서대로 확인하고, 각 단계에서 문제가 있는 부분을 수정하세요.

특히 다음을 확인:

1. DTO에 `stockName` 필드가 있는가?
2. Service에서 `stockName`을 설정하는가?
3. 요청 JSON에 `stock_name`이 포함되는가?
4. Python 서버가 `stock_name`을 받는가?

---

**이 가이드를 Spring 서버 레포지토리에서 사용하여 stock_name 전달을 확인하세요!**
