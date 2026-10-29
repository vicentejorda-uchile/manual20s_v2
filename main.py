import json
import math
import os
import time
import uuid
from datetime import date, timedelta

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex as hx

BG, CARD, EL, EL2 = hx("#000000"), hx("#1C1C1E"), hx("#2C2C2E"), hx("#3A3A3C")
TX, SEC, AC, OK, BAD = hx("#F5F5F7"), hx("#8E8E93"), hx("#0A84FF"), hx("#30D158"), hx("#FF453A")
PAL = ["#0A84FF", "#BF5AF2", "#30D158", "#FF9F0A", "#FF453A", "#64D2FF", "#FFD60A", "#FF6482"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
DS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def num(t, d=None):
    t = str(t).strip().replace(",", ".")
    if not t:
        return d
    try:
        v = float(t)
    except ValueError:
        return None
    return v if math.isfinite(v) and v >= 0 else None


def dur(s):
    s = max(0, int(s))
    h, m = s // 3600, s % 3600 // 60
    return f"{h}h {m:02d}m" if h else (f"{m}m" if m else f"{s}s")


def clk(s):
    s = max(0, int(s))
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def per():
    h = date.today()
    return h.isoformat(), (h - timedelta(days=h.weekday())).isoformat(), f"{h.year}-01-01"


class L(Label):
    def __init__(s, t, sz=15, col=TX, b=False, h="left", **kw):
        super().__init__(text=t, font_size=sp(sz), color=col, bold=b, size_hint_y=None, halign=h, valign="middle", **kw)
        s.bind(width=lambda *a: setattr(s, "text_size", (s.width, None)))
        s.bind(texture_size=lambda *a: setattr(s, "height", s.texture_size[1] + dp(6)))


def B(t, cb, col=EL, tc=TX, w=None, h=dp(44)):
    b = Button(text=t, background_normal="", background_down="", background_color=col, color=tc, bold=True,
               font_size=sp(14), size_hint_y=None, height=h)
    if w:
        b.size_hint_x = None
        b.width = w
    b.bind(on_release=lambda *a: cb())
    return b


def I(t="", hint="", **kw):
    return TextInput(text=t, hint_text=hint, multiline=False, size_hint_y=None, height=dp(44), background_normal="",
                     background_active="", background_color=EL, foreground_color=TX, hint_text_color=SEC,
                     cursor_color=AC, padding=[dp(12), dp(12)], font_size=sp(16), **kw)


def Sp(vals, t):
    return Spinner(text=t, values=vals, size_hint_y=None, height=dp(44), background_normal="", background_color=EL,
                   color=TX, font_size=sp(15))


def row(*ws, h=dp(44), sp_=dp(8)):
    r = BoxLayout(size_hint_y=None, height=h, spacing=sp_)
    for w in ws:
        r.add_widget(w)
    return r


class Card(BoxLayout):
    def __init__(s, fill=False):
        super().__init__(orientation="vertical", size_hint_y=1 if fill else None, padding=dp(14), spacing=dp(6))
        if not fill:
            s.bind(minimum_height=s.setter("height"))
        s.bind(pos=s.bg, size=s.bg)

    def bg(s, *a):
        s.canvas.before.clear()
        with s.canvas.before:
            Color(*CARD)
            RoundedRectangle(pos=s.pos, size=s.size, radius=[dp(16)])


class Dot(Widget):
    def __init__(s, col):
        super().__init__(size_hint=(None, None), size=(dp(14), dp(14)))
        s.col = col
        s.bind(pos=s.d, size=s.d)

    def d(s, *a):
        s.canvas.clear()
        with s.canvas:
            Color(*s.col)
            Ellipse(pos=s.pos, size=s.size)


class Bar(Widget):
    def __init__(s, v, col):
        super().__init__(size_hint_y=None, height=dp(8))
        s.v, s.col = v, col
        s.bind(pos=s.d, size=s.d)

    def set(s, v):
        s.v = v
        s.d()

    def d(s, *a):
        s.canvas.clear()
        with s.canvas:
            Color(*EL)
            RoundedRectangle(pos=s.pos, size=s.size, radius=[dp(4)])
            if s.v > 0:
                Color(*s.col)
                RoundedRectangle(pos=s.pos, size=(max(dp(8), s.width * min(1, s.v)), s.height), radius=[dp(4)])


class Chart(Widget):
    def __init__(s, ser):
        super().__init__(size_hint_y=None, height=dp(130))
        s.ser = ser
        s.bind(pos=s.d, size=s.d)

    def d(s, *a):
        s.canvas.clear()
        mx = max([v for _, v in s.ser] + [3600])
        w = s.width / len(s.ser)
        with s.canvas:
            for i, (dd, v) in enumerate(s.ser):
                Color(*(AC if dd == date.today() else EL2))
                hh = (s.height - dp(4)) * v / mx
                RoundedRectangle(pos=(s.x + i * w + w * .2, s.y), size=(w * .6, max(hh, dp(3) if v else 0)), radius=[dp(5)])


class Store:
    def __init__(s, path):
        s.p, s.d = path, None
        try:
            with open(path, encoding="utf-8") as f:
                s.d = json.load(f)
        except Exception:
            pass
        if not isinstance(s.d, dict) or not isinstance(s.d.get("asignaturas"), list) or not isinstance(s.d.get("sesiones"), list):
            s.d = {"asignaturas": [s.nueva("Mecánica", PAL[0], 1.5, 8, 300), s.nueva("Cálculo Avanzado", PAL[1], 2, 10, 400)], "sesiones": []}
        s.save()

    @staticmethod
    def nueva(n, c, md, ms, ma):
        return {"id": uuid.uuid4().hex[:10], "nombre": n, "color": c, "meta_diaria": md, "meta_semanal": ms, "meta_anual": ma}

    def save(self):
        tmp = self.p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.d, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.p)

    @property
    def asigs(s):
        return s.d["asignaturas"]

    @property
    def ses(s):
        return s.d["sesiones"]

    @property
    def t(s):
        return s.d.setdefault("crono", {"aid": None, "acum": 0.0, "ini": None, "obj": None})

    def reset(s):
        s.d["crono"] = {"aid": None, "acum": 0.0, "ini": None, "obj": None}
        s.save()

    def el(s):
        c = s.t
        return c["acum"] + (time.time() - c["ini"] if c["ini"] else 0)

    def active(s):
        return s.el() > 0 or bool(s.t["ini"])

    def asig(s, i):
        return next((a for a in s.asigs if a["id"] == i), None)

    def add(s, aid, seg, fecha, origen):
        s.ses.append({"id": uuid.uuid4().hex[:12], "asignatura_id": aid, "fecha": fecha, "segundos": int(seg), "origen": origen})
        s.save()

    def sec(s, aid=None, d=None, h=None):
        return sum(x["segundos"] for x in s.ses if (not aid or x["asignatura_id"] == aid) and (not d or x["fecha"] >= d) and (not h or x["fecha"] <= h))

    def por_dia(s):
        hoy = date.today()
        out = []
        for i in range(6, -1, -1):
            d = hoy - timedelta(days=i)
            out.append((d, s.sec(None, d.isoformat(), d.isoformat())))
        return out

    def racha(s):
        f = {x["fecha"] for x in s.ses if x["segundos"] > 0}
        d = date.today()
        if d.isoformat() not in f:
            d -= timedelta(days=1)
        n = 0
        while d.isoformat() in f:
            n += 1
            d -= timedelta(days=1)
        return n


class Manual(App):
    def build(s):
        Window.clearcolor = BG
        Window.softinput_mode = "below_target"
        s.st = Store(os.path.join(s.user_data_dir, "datos_estudio.json"))
        s.tab, s.modo, s.mins, s.sel, s.msg, s.msgc, s.pend = "panel", "l", "25", None, "", OK, None
        s.clkl = s.msgl = None
        s.foco, s.flen, s.anim_in = False, 0, False
        root = BoxLayout(orientation="vertical", padding=[0, dp(28), 0, 0])
        s.cont = BoxLayout()
        s.mini = Button(background_normal="", background_color=EL, color=TX, size_hint_y=None, height=0, opacity=0,
                        font_size=sp(13), bold=True)
        s.mini.bind(on_release=lambda *a: s.go("crono"))
        nav = BoxLayout(size_hint_y=None, height=dp(56))
        s.tabs = {}
        for k, t in [("panel", "Panel"), ("crono", "Cronómetro"), ("reg", "Registrar"), ("asig", "Asignaturas")]:
            b = Button(text=t, background_normal="", background_color=BG, color=SEC, font_size=sp(13))
            b.bind(on_release=lambda w, k=k: s.go(k))
            nav.add_widget(b)
            s.tabs[k] = b
        for w in (s.cont, s.mini, nav):
            root.add_widget(w)
        s.go("panel")
        Clock.schedule_interval(s.tick, .25)
        return root

    def go(s, k):
        s.tab, s.msg, s.pend = k, "", None
        s.render()

    def render(s):
        s.clkl = s.msgl = None
        s.foco = False
        for k, b in s.tabs.items():
            b.background_color = EL if k == s.tab else BG
            b.color = TX if k == s.tab else SEC
        getattr(s, "v_" + s.tab)()
        s.tick()

    def page(s, title, sub=""):
        sv = ScrollView(do_scroll_x=False)
        col = BoxLayout(orientation="vertical", size_hint_y=None, padding=[dp(16), dp(8)], spacing=dp(12))
        col.bind(minimum_height=col.setter("height"))
        sv.add_widget(col)
        s.cont.clear_widgets()
        s.cont.add_widget(sv)
        col.add_widget(L(title, 28, TX, True))
        if sub:
            col.add_widget(L(sub, 13, SEC))
        return col

    def setmsg(s, t, c=OK):
        s.msg, s.msgc = t, c
        if s.msgl:
            s.msgl.text, s.msgl.color = t, c

    def ids(s):
        return {a["nombre"]: a["id"] for a in s.st.asigs}

    def prog(s, card, nombre, hecho, meta, col):
        f = hecho / (meta * 3600) if meta > 0 else 0
        t = f"{nombre}: {dur(hecho)}" + (f" de {meta:g} h · {int(f * 100)}%" if meta > 0 else " · sin meta")
        card.add_widget(L(t, 12, OK if f >= 1 else SEC))
        card.add_widget(Bar(f, col))

    def v_panel(s):
        st = s.st
        hy, lu, an = per()
        r = st.racha()
        hoy = date.today()
        c = s.page("Panel", f"{DIAS[hoy.weekday()].capitalize()}, {hoy.day} de {MESES[hoy.month - 1]}  ·  " +
                   (f"racha de {r} día{'s' if r != 1 else ''}" if r else "sin racha, empieza hoy"))
        g = GridLayout(cols=2, spacing=dp(12), size_hint_y=None)
        g.bind(minimum_height=g.setter("height"))
        for k, v in [("Horas totales", f"{st.sec() / 3600:.1f} h"), ("Hoy", dur(st.sec(None, hy, hy))),
                     ("Esta semana", dur(st.sec(None, lu))), ("Este año", dur(st.sec(None, an)))]:
            cd = Card()
            cd.add_widget(L(k, 12, SEC))
            cd.add_widget(L(v, 22, TX, True))
            g.add_widget(cd)
        c.add_widget(g)
        c.add_widget(L("Últimos 7 días", 18, TX, True))
        ser = st.por_dia()
        c.add_widget(Chart(ser))
        lr = BoxLayout(size_hint_y=None, height=dp(36))
        for d, v in ser:
            lr.add_widget(Label(text=f"{DS[d.weekday()]}\n{v / 3600:.1f}h", font_size=sp(11), color=TX if d == hoy else SEC, halign="center"))
        c.add_widget(lr)
        c.add_widget(L("Asignaturas", 18, TX, True))
        if not st.asigs:
            c.add_widget(L("Crea tu primera asignatura en la pestaña Asignaturas.", 14, SEC))
        for a in st.asigs:
            cd = Card()
            ib = Button(text="Iniciar", background_normal="", background_color=EL, color=TX, size_hint=(None, None),
                        size=(dp(80), dp(34)), font_size=sp(13))
            ib.bind(on_release=lambda w, i=a["id"]: s.start_on(i))
            dot = Dot(hx(a["color"]))
            nm = L(a["nombre"], 17, TX, True)
            cd.add_widget(row(dot, nm, L(f"{st.sec(a['id']) / 3600:.1f} h", 13, SEC, h="right", size_hint_x=None, width=dp(60)), ib, h=dp(36)))
            s.prog(cd, "Hoy", st.sec(a["id"], hy, hy), a["meta_diaria"], hx(a["color"]))
            s.prog(cd, "Semana", st.sec(a["id"], lu), a["meta_semanal"], hx(a["color"]))
            s.prog(cd, "Año", st.sec(a["id"], an), a["meta_anual"], hx(a["color"]))
            c.add_widget(cd)

    def start_on(s, aid):
        if s.st.active() and s.st.t["aid"] != aid:
            s.go("crono")
            s.setmsg("Ya hay una sesión activa con otra asignatura.", BAD)
            return
        s.sel = aid
        s.go("crono")

    def ftxt(s, x):
        x = max(0, int(x))
        return f"{x // 60:02d}:{x % 60:02d}" if s.foco and x < 3600 else clk(x)

    def v_foco(s):
        st = s.st
        c = st.t
        a = st.asig(c["aid"])
        col = hx(a["color"]) if a else AC
        s.foco = True
        animar, s.anim_in = s.anim_in, False
        box = BoxLayout(orientation="vertical", padding=[dp(16), dp(12), dp(16), dp(12)])
        s.cont.clear_widgets()
        s.cont.add_widget(box)
        cd = Card(fill=True)
        cd.padding = dp(18)
        cd.spacing = dp(10)
        if animar:
            cd.size_hint_y = .6
            cd.opacity = 0
        box.add_widget(cd)
        cd.add_widget(L(a["nombre"] if a else "", 20, TX, True, h="center"))
        cd.add_widget(L(f"Pomodoro · {c['obj'] / 60:g} min" if c["obj"] else "Modo libre", 13, SEC, h="center"))
        s.clkl = Label(text="", font_size=sp(52), bold=True, font_name="RobotoMono-Regular", color=TX)
        cd.add_widget(s.clkl)
        cd.add_widget(L("En curso" if c["ini"] else "En pausa", 14, OK if c["ini"] else SEC, h="center"))
        s.bar = Bar(0, col)
        s.bar.height = dp(10)
        cd.add_widget(s.bar)
        s.inf = L("", 13, SEC, h="center")
        cd.add_widget(s.inf)
        cd.add_widget(row(B("Pausar" if c["ini"] else "Reanudar", s.pause if c["ini"] else s.start, AC, TX, h=dp(54)), h=dp(54)))
        cd.add_widget(row(B("Guardar", s.fin, OK, BG), B("Descartar", s.disc)))
        s.msgl = L(s.msg, 14, s.msgc, h="center")
        cd.add_widget(s.msgl)
        s.flen = 5
        if animar:
            Animation(size_hint_y=1, opacity=1, d=.5, t="out_cubic").start(cd)
            Animation(font_size=sp(88), d=.7, t="out_back").start(s.clkl)
        else:
            s.clkl.font_size = sp(88)

    def v_crono(s):
        st = s.st
        c = st.t
        if st.active():
            return s.v_foco()
        lock = False
        names = list(s.ids())
        a = st.asig(c["aid"] or s.sel)
        cur = a["nombre"] if a else (names[0] if names else "Sin asignaturas")
        pg = s.page("Cronómetro", "Registra tu tiempo de estudio en vivo.")
        cd = Card()
        pg.add_widget(cd)
        s.spn = Sp(names or ["Sin asignaturas"], cur)
        s.spn.disabled = lock
        s.spn.bind(text=lambda w, t: setattr(s, "sel", s.ids().get(t)))
        cd.add_widget(s.spn)
        mb = row(B("Libre", lambda: s.setmodo("l"), AC if s.modo == "l" else EL), B("Pomodoro", lambda: s.setmodo("p"), AC if s.modo == "p" else EL))
        for b in mb.children:
            b.disabled = lock
        cd.add_widget(mb)
        if s.modo == "p":
            mn = I(s.mins, "Minutos")
            mn.disabled = lock
            mn.bind(text=lambda w, t: setattr(s, "mins", t))
            cd.add_widget(mn)
        s.clkl = Label(text="00:00:00", font_size=sp(52), bold=True, font_name="RobotoMono-Regular", color=TX, size_hint_y=None, height=dp(110))
        cd.add_widget(s.clkl)
        s.bar = Bar(0, hx(a["color"]) if a else AC)
        cd.add_widget(s.bar)
        s.inf = L("", 13, SEC, h="center")
        cd.add_widget(s.inf)
        t = "Pausar" if c["ini"] else ("Reanudar" if lock else "Iniciar")
        cd.add_widget(row(B(t, s.pause if c["ini"] else s.start, AC, TX), B("Guardar", s.fin, OK, BG), B("Descartar", s.disc)))
        s.msgl = L(s.msg, 14, s.msgc, h="center")
        cd.add_widget(s.msgl)

    def setmodo(s, m):
        s.modo = m
        s.render()

    def start(s):
        st, c = s.st, s.st.t
        if not st.active():
            aid = s.ids().get(s.spn.text)
            if not aid:
                return s.setmsg("Crea una asignatura primero.", BAD)
            if s.modo == "p":
                m = num(s.mins)
                if m is None or not 1 <= m <= 600:
                    return s.setmsg("Ingresa entre 1 y 600 minutos.", BAD)
                c["obj"] = m * 60
            else:
                c["obj"] = None
            c["aid"] = aid
        s.anim_in = not st.active()
        c["ini"] = time.time()
        st.save()
        s.msg = ""
        s.render()

    def pause(s):
        c = s.st.t
        c["acum"] = s.st.el()
        c["ini"] = None
        s.st.save()
        s.render()

    def fin(s):
        st = s.st
        seg = int(st.el())
        if seg < 1:
            return s.setmsg("Aún no hay tiempo para guardar.", SEC)
        a = st.asig(st.t["aid"])
        if a:
            st.add(a["id"], seg, date.today().isoformat(), "cronometro")
            s.msg, s.msgc = f"Sesión guardada: {dur(seg)} en {a['nombre']}.", OK
        else:
            s.msg, s.msgc = "La asignatura ya no existe; sesión descartada.", BAD
        st.reset()
        s.render()

    def disc(s):
        if not s.st.active():
            return
        if s.pend != "disc":
            s.pend = "disc"
            return s.setmsg("Toca Descartar otra vez para confirmar.", BAD)
        s.pend = None
        s.st.reset()
        s.msg = ""
        s.render()

    def tick(s, *a):
        st = s.st
        c = st.t
        t = st.el()
        if c["ini"] and c["obj"] and t >= c["obj"]:
            seg, aid = int(c["obj"]), c["aid"]
            if st.asig(aid):
                st.add(aid, seg, date.today().isoformat(), "cronometro")
            st.reset()
            s.msg, s.msgc = f"Pomodoro completado: {dur(seg)} guardados.", OK
            s.render()
            return
        act = st.active()
        s.mini.height = dp(36) if act and s.tab != "crono" else 0
        s.mini.opacity = 1 if act and s.tab != "crono" else 0
        if act:
            x = st.asig(c["aid"])
            s.mini.text = ("En curso " if c["ini"] else "En pausa ") + clk(math.ceil(c["obj"] - t) if c["obj"] else t) + "  ·  " + (x["nombre"] if x else "")
        if s.tab != "crono" or not s.clkl:
            return
        x = st.asig(c["aid"]) or st.asig(s.sel) or (None if s.foco else st.asig(s.ids().get(s.spn.text)))
        hy = date.today().isoformat()
        base = st.sec(x["id"], hy, hy) if x else 0
        ob = c["obj"] or (num(s.mins, 25) * 60 if s.modo == "p" else 0)
        if ob:
            s.clkl.text = s.ftxt(math.ceil(max(0, ob - t)))
            f = t / ob
        else:
            s.clkl.text = s.ftxt(t)
            f = (base + t) / (x["meta_diaria"] * 3600) if x and x["meta_diaria"] > 0 else 0
        if s.foco and len(s.clkl.text) != s.flen:
            s.flen = len(s.clkl.text)
            Animation.cancel_all(s.clkl, "font_size")
            s.clkl.font_size = sp(88) if s.flen <= 5 else sp(60)
        s.bar.set(f)
        s.inf.text = f"Hoy en {x['nombre']}: {dur(base + (t if c['aid'] else 0))}" + (f" de {x['meta_diaria']:g} h" if x["meta_diaria"] > 0 else "") if x else "Crea una asignatura para empezar"

    def v_reg(s):
        st = s.st
        names = list(s.ids())
        a = st.asig(s.sel)
        pg = s.page("Registrar horas", "Añade tiempo estudiado manualmente.")
        cd = Card()
        pg.add_widget(cd)
        s.rs = Sp(names or ["Sin asignaturas"], a["nombre"] if a else (names[0] if names else "Sin asignaturas"))
        s.rf = I(date.today().isoformat(), "AAAA-MM-DD")
        s.rh, s.rm = I("", "Horas"), I("", "Minutos")
        for w in (L("Asignatura", 12, SEC), s.rs, L("Fecha (AAAA-MM-DD)", 12, SEC), s.rf, row(s.rh, s.rm), B("Guardar horas", s.add_reg, AC)):
            cd.add_widget(w)
        s.msgl = L(s.msg, 14, s.msgc, h="center")
        cd.add_widget(s.msgl)
        pg.add_widget(L("Historial reciente", 18, TX, True))
        orden = sorted(enumerate(st.ses), key=lambda p: (p[1]["fecha"], p[0]), reverse=True)[:40]
        if not orden:
            pg.add_widget(L("Todavía no hay sesiones registradas.", 14, SEC))
        for _, x in orden:
            ax = st.asig(x["asignatura_id"])
            h = Card()
            bt = Button(text="Confirmar" if s.pend == x["id"] else "Eliminar", background_normal="", background_color=EL, color=BAD,
                        size_hint=(None, None), size=(dp(90), dp(34)), font_size=sp(13))
            bt.bind(on_release=lambda w, i=x["id"]: s.del_ses(i))
            h.add_widget(row(Dot(hx(ax["color"]) if ax else SEC), L(f"{ax['nombre'] if ax else 'Eliminada'}\n{x['fecha']} · {'Cronómetro' if x.get('origen') == 'cronometro' else 'Manual'}", 13, TX),
                             L(dur(x["segundos"]), 14, TX, True, h="right", size_hint_x=None, width=dp(70)), bt, h=dp(48)))
            pg.add_widget(h)

    def add_reg(s):
        st = s.st
        aid = s.ids().get(s.rs.text)
        if not aid:
            return s.setmsg("Crea una asignatura primero.", BAD)
        try:
            f = date.fromisoformat(s.rf.text.strip())
        except ValueError:
            return s.setmsg("Fecha inválida. Usa AAAA-MM-DD.", BAD)
        if f > date.today():
            return s.setmsg("La fecha no puede ser futura.", BAD)
        h, m = num(s.rh.text, 0.0), num(s.rm.text, 0.0)
        if h is None or m is None:
            return s.setmsg("Horas y minutos deben ser números positivos.", BAD)
        seg = int(round(h * 3600 + m * 60))
        if seg <= 0:
            return s.setmsg("Ingresa al menos un minuto.", BAD)
        if seg > 86400:
            return s.setmsg("Un registro no puede superar 24 horas.", BAD)
        st.add(aid, seg, f.isoformat(), "manual")
        s.sel = aid
        s.msg, s.msgc = f"Guardado: {dur(seg)} en {st.asig(aid)['nombre']}.", OK
        s.render()

    def del_ses(s, i):
        if s.pend != i:
            s.pend = i
        else:
            s.pend = None
            s.st.d["sesiones"] = [x for x in s.st.ses if x["id"] != i]
            s.st.save()
        s.render()

    def v_asig(s):
        st = s.st
        pg = s.page("Asignaturas", "Define tus metas en horas.")
        pg.add_widget(B("Nueva asignatura", lambda: s.form(None), AC))
        if not st.asigs:
            pg.add_widget(L("No hay asignaturas. Crea la primera.", 14, SEC))
        for a in st.asigs:
            n = sum(1 for x in st.ses if x["asignatura_id"] == a["id"])
            cd = Card()
            cd.add_widget(row(Dot(hx(a["color"])), L(a["nombre"], 17, TX, True), h=dp(32)))
            cd.add_widget(L(f"Meta diaria {a['meta_diaria']:g} h · semanal {a['meta_semanal']:g} h · anual {a['meta_anual']:g} h\n"
                            f"{st.sec(a['id']) / 3600:.1f} h en {n} sesión{'es' if n != 1 else ''}", 12, SEC))
            cd.add_widget(row(B("Editar", lambda a=a: s.form(a), h=dp(38)),
                              B("Confirmar" if s.pend == a["id"] else "Eliminar", lambda i=a["id"]: s.del_asig(i), EL, BAD, h=dp(38)), h=dp(38)))
            pg.add_widget(cd)

    def del_asig(s, i):
        if s.pend != i:
            s.pend = i
        else:
            s.pend = None
            if s.st.t["aid"] == i:
                s.st.reset()
            s.st.d["asignaturas"] = [a for a in s.st.asigs if a["id"] != i]
            s.st.d["sesiones"] = [x for x in s.st.ses if x["asignatura_id"] != i]
            s.st.save()
        s.render()

    def form(s, a):
        st = s.st
        s.fc = a["color"] if a else PAL[len(st.asigs) % len(PAL)]
        bx = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8), padding=dp(6))
        bx.bind(minimum_height=bx.setter("height"))
        sv = ScrollView()
        sv.add_widget(bx)
        pop = Popup(title="Editar asignatura" if a else "Nueva asignatura", content=sv, size_hint=(.94, .9), background="",
                    background_color=CARD, title_size=sp(18), separator_color=CARD)
        nm = I(a["nombre"] if a else "", "Nombre")
        md = I(f"{a['meta_diaria']:g}" if a else "1", "Horas")
        ms = I(f"{a['meta_semanal']:g}" if a else "7", "Horas")
        ma = I(f"{a['meta_anual']:g}" if a else "250", "Horas")
        er = L("", 13, BAD)
        cols = []

        def pick(c):
            s.fc = c
            for b, k in cols:
                b.text = "OK" if k == c else ""

        cr = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        for k in PAL:
            b = Button(text="", background_normal="", background_color=hx(k), color=BG, bold=True, font_size=sp(11))
            b.bind(on_release=lambda w, k=k: pick(k))
            cols.append((b, k))
            cr.add_widget(b)
        pick(s.fc)

        def guardar():
            n = nm.text.strip()
            if not n:
                er.text = "Escribe un nombre."
                return
            if any(x["nombre"].lower() == n.lower() and (not a or x["id"] != a["id"]) for x in st.asigs):
                er.text = "Ya existe una asignatura con ese nombre."
                return
            v = [num(md.text, 0.0), num(ms.text, 0.0), num(ma.text, 0.0)]
            if None in v:
                er.text = "Las metas deben ser números positivos."
                return
            if v[0] > 24 or v[1] > 168 or v[2] > 8784:
                er.text = "Alguna meta supera el máximo posible."
                return
            if a:
                a.update(nombre=n, color=s.fc, meta_diaria=v[0], meta_semanal=v[1], meta_anual=v[2])
            else:
                st.asigs.append(st.nueva(n, s.fc, *v))
            st.save()
            pop.dismiss()
            s.render()

        for w in (L("Nombre", 12, SEC), nm, L("Color", 12, SEC), cr, L("Meta diaria (horas)", 12, SEC), md,
                  L("Meta semanal (horas)", 12, SEC), ms, L("Meta anual (horas)", 12, SEC), ma, er,
                  row(B("Cancelar", pop.dismiss), B("Guardar", guardar, AC))):
            bx.add_widget(w)
        pop.open()


if __name__ == "__main__":
    Manual().run()
