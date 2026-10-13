-- SK하이닉스의 지정 기간 종가를 날짜순으로 조회합니다.
SELECT stock_code, date, close
FROM prices
WHERE stock_code = '000660'
  AND date BETWEEN '2025-01-02' AND '2025-01-06'
ORDER BY date;