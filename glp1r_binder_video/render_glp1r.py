import sys,http.server,threading,functools,os
from playwright.sync_api import sync_playwright
os.chdir(os.path.dirname(os.path.abspath(__file__)))
port=int(sys.argv[1]) if len(sys.argv)>1 else 8110
frames=[int(x) for x in sys.argv[2].split(',')] if len(sys.argv)>2 else list(range(600))
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
srv=http.server.ThreadingHTTPServer(('127.0.0.1',port),functools.partial(Q,directory='.'))
threading.Thread(target=srv.serve_forever,daemon=True).start()
out='fr_glp1r';os.makedirs(out,exist_ok=True)
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
    pg=b.new_page(viewport={'width':1080,'height':1350},device_scale_factor=1)
    pg.on('console',lambda m:print('console:',m.text) if m.type=='error' else None)
    pg.on('pageerror',lambda e:print('pageerror:',e))
    pg.goto(f'http://127.0.0.1:{port}/page_glp1r.html')
    pg.evaluate('window.ready');pg.wait_for_timeout(1500)
    if frames==[-1]:
        print(pg.evaluate('JSON.stringify(calibrate())'));sys.exit()
    for i in range(600):
        pg.evaluate(f'render({i},{"true" if (i in frames) else "false"})')
        import time as _t; _t0=_t.time()
        if i in frames:
            pg.screenshot(path=f'{out}/f{i:04d}.png',timeout=300000); print('frame',i,round(_t.time()-_t0,1),'s',flush=True)
        if i%100==0:print(i,flush=True)
    b.close()
