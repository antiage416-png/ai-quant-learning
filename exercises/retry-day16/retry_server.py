from http.server import BaseHTTPRequestHandler, HTTPServer


class RetryHandler(BaseHTTPRequestHandler):
    # 서버가 받은 요청 수를 기록합니다.
    request_count = 0

    def do_GET(self):
        RetryHandler.request_count += 1
        count = RetryHandler.request_count

        if count <= 10:
            # 첫 요청에는 연습용 429 응답을 보냅니다.
            self.send_response(429)
            self.send_header("Retry-After", "2")
            self.end_headers()
            self.wfile.write(b"Please retry after 2 seconds.")
        else:
            # 두 번째 요청부터는 성공 응답을 보냅니다.
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Success!")


# 이 컴퓨터 내부에서만 접근하는 연습 서버입니다.
with HTTPServer(("127.0.0.1", 8766), RetryHandler) as server:
    print("서버 준비: http://127.0.0.1:8766/", flush=True)
    print("종료하려면 이 터미널에서 Ctrl+C를 누르세요.", flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n서버를 종료합니다.")