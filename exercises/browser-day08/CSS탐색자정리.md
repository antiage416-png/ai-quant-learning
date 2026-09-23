# HTML 관계와 CSS 선택자 한눈에 보기

1주차에 BeautifulSoup으로 찾았던 HTML 요소를 CSS 선택자로 표현해 보는 2주차 8일차 참고 자료입니다.

**선택자는 원하는 요소를 찾는 조건입니다.** 요소를 찾은 뒤에는 글자나 속성값을 따로 꺼냅니다.

## 1. 가장 헷갈리는 선택자 비교

| 선택자 | 읽는 방법 | 핵심 구분 |
|---|---|---|
| `p a` | p 안에 있는 a 태그 | 공백: 모든 깊이의 자손 |
| `p > a` | p 바로 아래에 있는 a 태그 | `>`: 직접 자식만 |
| `p.a` | a라는 클래스를 가진 p 태그 | 점: 클래스, 같은 요소에 조건 적용 |
| `p .a` | p 안에 있는 a 클래스의 요소 | 공백과 점: 자손 중 클래스 검색 |
| `a[href]` | href 속성이 있는 a 태그 | 대괄호: 속성 조건 |

> `p.a`의 a는 **클래스 이름**, `p a`의 a는 **태그 이름**입니다.

## 2. 공통 예제 HTML

아래 표의 결과는 이 예제를 기준으로 합니다. 현재 example.com의 원문을 그대로 옮긴 것이 아니라, 관계를 비교하기 위한 학습용 예제입니다.

```html
<div id="news">
  <p class="headline">
    <a href="/article/1">첫 번째 기사</a>
    <span>
      <a href="/article/2">두 번째 기사</a>
    </span>
  </p>

  <p class="summary">기사 요약</p>

  <a class="headline external" href="https://example.com" target="_blank">
    외부 기사
  </a>
</div>
```

```text
div#news
├── p.headline
│   ├── a                  첫 번째 기사
│   └── span
│       └── a              두 번째 기사
├── p.summary              기사 요약
└── a.headline.external    외부 기사
```

## 3. 부모·자식·조상·자손·형제

| 관계 | 뜻 | 공통 예제에서의 관계 |
|---|---|---|
| 부모 | 바로 한 단계 위 요소 | 첫 번째 기사 a의 부모는 p |
| 자식 | 바로 한 단계 아래 요소 | p.headline의 자식은 첫 a와 span |
| 조상 | 부모를 포함해 위쪽의 요소들 | 두 번째 기사 a의 조상에 span, p, div가 포함됨 |
| 자손 | 자식을 포함해 아래쪽 모든 깊이의 요소들 | p.headline의 자손은 첫 a, span, 두 번째 a |
| 형제 | 같은 부모를 가진 요소들 | 두 p와 외부 기사 a는 같은 div의 자식 |

**자식은 바로 아래, 자손은 아래의 모든 깊이입니다.**

## 4. 기본 선택자: 태그·클래스·ID

| 선택자 | 의미 | 공통 예제에서 선택되는 요소 |
|---|---|---|
| `p` | 태그 이름이 p | 두 p |
| `.headline` | headline 클래스를 가진 요소 | 첫 p와 외부 기사 a |
| `p.headline` | p이면서 headline 클래스인 요소 | 첫 p |
| `a.headline` | a이면서 headline 클래스인 요소 | 외부 기사 a |
| `.headline.external` | 두 클래스를 모두 가진 요소 | 외부 기사 a |
| `#news` | id가 news인 요소 | 바깥 div |
| `div#news` | div이면서 id가 news인 요소 | 바깥 div |

| HTML 표기 | 의미 | 대응 선택자 |
|---|---|---|
| `class="headline"` | 여러 요소에 같은 클래스를 붙일 수 있음 | `.headline` |
| `class="headline external"` | 한 요소에 클래스 두 개 | `.headline.external` |
| `id="news"` | 문서 안에서 고유하게 지정해야 하는 식별자 | `#news` |

## 5. 관계 선택자: 공백·>·+·~

| 선택자 | 관계 | 공통 예제에서 선택되는 요소 |
|---|---|---|
| `p a` | p의 자손인 a | 첫 번째·두 번째 기사 a |
| `p > a` | p의 직접 자식인 a | 첫 번째 기사 a만 |
| `p.headline + p` | 바로 다음 형제 요소가 p이면 선택 | 요약 p |
| `p.headline + a` | 바로 다음 형제 요소가 a이면 선택 | 없음: 바로 다음은 p |
| `p.headline ~ a` | 뒤쪽 형제 중 a를 모두 선택 | 외부 기사 a |

`+`와 `~`는 같은 부모를 가진 **뒤쪽 형제**를 찾습니다. 공백·줄바꿈은 형제 요소로 세지 않습니다.

## 6. p a·p.a·p .a 전용 비교 예제

```html
<p class="a">첫 번째 문장</p>
<p>
  <a href="/hello">링크</a>
  <span class="a">두 번째 문장</span>
</p>
```

| 선택자 | 선택되는 요소 | 이유 |
|---|---|---|
| `p.a` | `<p class="a">` | p 자체의 클래스가 a |
| `p a` | `<a href="/hello">` | p 안에 있는 a 태그 |
| `p .a` | `<span class="a">` | p 안에 있고 클래스가 a |

## 7. 속성 선택자

| 선택자 | 의미 | 일치하는 속성값 예시 |
|---|---|---|
| `a[href]` | href 속성이 있는 a | `href="/article/1"` |
| `a[target="_blank"]` | target 값이 정확히 일치 | `target="_blank"` |
| `a[href^="https://"]` | href가 지정 문자열로 시작 | `https://example.com` |
| `a[href$=".pdf"]` | href가 지정 문자열로 끝남 | `/files/report.pdf` |
| `a[href*="article"]` | href에 지정 문자열이 포함됨 | `/article/1` |

| 기호 | 기억할 의미 |
|---|---|
| `[속성]` | 존재 |
| `=` | 정확히 일치 |
| `^=` | 시작 |
| `$=` | 끝 |
| `*=` | 포함 |

- `a[href]`는 주소의 유효성을 검사하지 않습니다. `href=""`인 요소도 선택합니다.
- `[href$=".pdf"]`는 문자열의 끝을 검사합니다. `report.pdf?download=1`은 이 조건에 맞지 않습니다.
- 속성 선택자는 HTML에 적힌 값을 검사합니다. `/article/1`을 자동으로 전체 URL로 바꾸지는 않습니다.

## 8. 조건 결합과 여러 선택자

| 선택자 | 의미 |
|---|---|
| `#news p.headline > a[href]` | news 안의 headline 클래스 p 바로 아래에서 href가 있는 a |
| `h1, h2` | h1 또는 h2인 요소들 |
| `h1 h2` | h1 안에 있는 h2 |
| `a.headline.external` | a이면서 headline과 external 클래스를 모두 가진 요소 |

복합 선택자 `#news p.headline > a[href]`는 공통 예제에서 **첫 번째 기사 a**를 선택합니다.

## 9. BeautifulSoup에 적용하기

| 목적 | 코드 | 반환 결과 |
|---|---|---|
| 일치하는 모든 요소 찾기 | `soup.select("a[href]")` | 리스트 형태의 결과, 없으면 빈 리스트 |
| 첫 번째 일치 요소 찾기 | `soup.select_one("a[href]")` | Tag 객체 하나, 없으면 None |
| 태그 안의 글자 가져오기 | `link.get_text(strip=True)` | 문자열 |
| 속성값 가져오기 | `link["href"]` | 속성이 없으면 KeyError |
| 속성값을 안전하게 조회 | `link.get("href")` | 속성이 없으면 None |

```python
# CSS 선택자로 href 속성이 있는 모든 a 태그를 찾습니다.
links = soup.select("a[href]")

# 찾은 요소에서 글자와 주소를 꺼냅니다.
for link in links:
    print(link.get_text(strip=True))
    print(link["href"])
```

| 기존에 사용한 방법 | CSS 선택자를 사용한 방법 |
|---|---|
| `soup.find_all("a", href=True)` | `soup.select("a[href]")` |
| `soup.find("title")` | `soup.select_one("title")` |

`"a[href]"`는 **검색 조건 문자열**입니다. `link["href"]`는 **이미 찾은 Tag 객체에서 속성값을 꺼내는 Python 표현식**입니다.

`get_text(strip=True)`는 텍스트 조각마다 앞뒤 공백을 제거합니다. 중첩 태그 사이에 구분 공백이 필요하면 `get_text(" ", strip=True)`처럼 구분자를 지정할 수 있습니다.

## 10. 브라우저에서 확인하는 방법

1. Chrome 또는 Edge에서 연습 페이지를 엽니다.
2. 원하는 글자를 우클릭하고 **검사**를 선택합니다.
3. 개발자 도구의 **Elements(요소)** 내부를 클릭합니다.
4. **Ctrl+F**를 누르고 선택자를 입력합니다.
5. 검색된 요소와 일치 개수를 확인합니다.

Elements 검색창은 CSS 선택자뿐 아니라 텍스트와 XPath 검색도 지원하므로, 검색 결과에서 실제 선택된 요소를 함께 확인합니다.

| example.com에서 확인할 선택자 | 기대되는 대상 |
|---|---|
| `h1` | Example Domain 제목 |
| `p a` | Learn more 링크 |
| `p > a` | Learn more 링크 |
| `a[href]` | Learn more 링크 |

현재 실습 페이지에서는 링크가 p의 직접 자식이어서 `p a`와 `p > a`의 결과가 같습니다. 중간에 span 같은 요소가 들어가면 결과가 달라질 수 있습니다.

브라우저의 Elements는 **현재 DOM 구조**를 보여주고, BeautifulSoup은 **전달받은 HTML**을 분석합니다. JavaScript로 구조가 바뀐 페이지에서는 두 결과가 다를 수 있습니다.

## 11. 이해도 확인

| 질문 | 답 |
|---|---|
| p 바로 아래의 a만 찾으려면? | `p > a` |
| p 안의 a를 깊이에 관계없이 찾으려면? | `p a` |
| summary 클래스인 p를 찾으려면? | `p.summary` |
| p 안에서 summary 클래스의 요소를 찾으려면? | `p .summary` |
| href가 있는 a를 찾으려면? | `a[href]` |
| 찾은 링크의 주소를 Python에서 꺼내려면? | `link["href"]` |
| h1과 h2를 함께 찾으려면? | `h1, h2` |

다음 학습: Network에서 요청 주소·요청 방식·응답 상태와 본문을 관찰합니다.
