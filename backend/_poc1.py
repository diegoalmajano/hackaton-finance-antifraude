import time, uuid
from antifraude.analysis import ingest, rules, text
from antifraude.intel import urls
def t(name, f):
    s=time.perf_counter(); 
    try: r=f()
    except Exception as e: r=repr(e)[:80]
    print(f"{name}: {time.perf_counter()-s:.2f}s", str(r)[:60])
N=100_000
U=uuid.uuid4()
t("urlre a.a.a.", lambda: len(list(ingest._URL_RE.finditer("a."*50000))))
t("urlre a-a.", lambda: len(list(ingest._URL_RE.finditer("a-"*50000))))
t("urlre a.a. no slash", lambda: len(list(ingest._URL_RE.finditer(("a"*50+".")*2000))))
t("urlre 'a.b' x", lambda: len(list(ingest._URL_RE.finditer("a.b "*25000))))
t("iban", lambda: text.minimize("ES12"+" 1234"*25000))
t("iban2", lambda: text.minimize("AB12"+"A"*100000))
t("card", lambda: text.minimize("1 "*50000))
t("card digits", lambda: text.minimize("1"*100000))
t("card dash", lambda: text.minimize("1-"*50000))
t("code ctx", lambda: text.minimize("pin"+" "*100000))
t("code ctx2", lambda: text.minimize("pin a"*20000))
t("pwd", lambda: text.minimize("clave "*20000))
t("clean", lambda: text.clean_text(" "*100000+"x"))
d=__import__("antifraude.intel.entities",fromlist=["x"]).EntityDirectory.load_default()
def scr(s):
    r=ingest.from_manual_text(s,U); return rules.screen(r.message,d)
for name,s in {
 "verb spam":"introduce "*10000,
 "verb spam2":"introduce"+" x"*50000,
 "verb nodot":"introduzca "+"a"*100000,
 "verb x many":("introduzca "+"a"*69+" ")*1500,
 "negation":"nunca "+"a "*50000,
 "negation2":"ni "*30000,
 "unrec":("si no ha sido usted "+"a"*79)*1000,
 "unrec2":"si no reconoce "+"a"*100000,
 "otp":("introduce codigo "+"a"*39+" ")*3000,
 "family":("mama "+"a"*59)*1500,
 "payment":("envia "+"a"*39+" ")*3000,
 "spaces":"a "*50000,
}.items():
    t("screen "+name, lambda: scr(s))
t("mentioned", lambda: rules.mentioned_entities("a "*50000, d))
t("pipeline-ish url analyze", lambda: [urls.analyze_url(u,d,None) for u in scr(" ".join("http://"+"a"*50+str(i)+".com/x" for i in range(200)))[0].urls])
