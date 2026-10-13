-- 한 행에 한 종목의 하루 가격 정보를 저장합니다.
-- PostgreSQL에서 실행하면 테이블을 만듭니다. 지금은 파일만 저장합니다.
CREATE TABLE prices (
    -- 종목코드의 앞자리 0을 보존합니다.
    stock_code TEXT NOT NULL,
    market TEXT NOT NULL,
    date DATE NOT NULL,

    -- 이번 자료의 가격은 원 단위 정수이며 양수만 허용합니다.
    open BIGINT NOT NULL CHECK (open > 0),
    high BIGINT NOT NULL CHECK (high > 0),
    low BIGINT NOT NULL CHECK (low > 0),
    close BIGINT NOT NULL CHECK (close > 0),

    -- 거래량은 누락과 음수를 금지하고 0은 허용합니다.
    volume BIGINT NOT NULL CHECK (volume >= 0),

    -- 같은 종목의 같은 날짜 자료가 중복되지 않도록 합니다.
    PRIMARY KEY (stock_code, date)
);