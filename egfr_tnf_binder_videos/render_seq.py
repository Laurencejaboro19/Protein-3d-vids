import sys,http.server,threading,functools,os
from playwright.sync_api import sync_playwright
os.chdir(os.path.dirname(os.path.abspath(__file__)))
key=sys.argv[1];port=int(sys.argv[2]);frames=[int(x) for x in sys.argv[3].split(',')] if len(sys.argv)>3 else list(range(600))
H=functools.partial(http.server.SimpleHTTPRequestHandler,directory='.')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
srv=http.server.ThreadingHTTPServer(('127.0.0.1',port),functools.partial(Q,directory='.'))
threading.Thread(target=srv.serve_forever,daemon=True).start()
out=f'fr_{key}_seq';os.makedirs(out,exist_ok=True)
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
    pg=b.new_page(viewport={'width':1080,'height':1350},device_scale_factor=1)
    pg.on('console',lambda m:print('console:',m.text) if m.type=='error' else None)
    pg.goto(f'http://127.0.0.1:{port}/page_seq.html?n={key}')
    pg.evaluate('window.ready');pg.wait_for_timeout(1500)
    done=0
    for i in range(600):
        # always advance state in order so rotation/opacity stay consistent
        pg.evaluate(f'render({i})')
        if i in frames: pg.screenshot(path=f'{out}/f{i:04d}.png')
        if i%100==0:print(key,i,flush=True)
    b.close()
