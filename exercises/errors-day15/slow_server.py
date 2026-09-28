from http.server import BaseHTTPRequestHandler, HTTPServer
import time


class SlowHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print("요청을 받았습니다. 3초 후 응답합니다.", flush=True)
        time.sleep(3)

        try:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Hello")
        except (BrokenPipeError, ConnectionResetError):
            # 요청한 쪽이 먼저 기다리기를 끝내면 발생할 수 있습니다.
            print("클라이언트가 먼저 연결을 종료했습니다.")


# 이 컴퓨터 내부에서만 접근하는 연습용 서버입니다.
with HTTPServer(("127.0.0.1", 8765), SlowHandler) as server:
    # 요청이 오지 않으면 최대 60초 대기 후 종료합니다.
    server.timeout = 60

    print("서버 준비: http://127.0.0.1:8765/", flush=True)

    # 요청 한 번을 처리한 뒤 서버를 종료합니다.
    server.handle_request()