const e = document.querySelector(".navbar-collapse"),
    t = document.querySelector("#toggleNav"),
    n = document.querySelector("#closeNav"),
    o = document.querySelector(".dimmer");

function s() {
    e.classList.remove("show"), o.style.opacity = "0", setTimeout((() => {
        o.style.visibility = "hidden", o.style.display = "none"
    }), 300)
}
t.addEventListener("click", (function() {
    e.classList.contains("show") ? s() : (o.style.display = "block", e.classList.add("show"), o.style.visibility = "visible", o.style.opacity = "1")
})), n.addEventListener("click", s), o.addEventListener("click", s);
const i = document.getElementById("searchInput");
if (i) {
    i.addEventListener("keyup", (function() {
        let e, t, n, o, s, a;
        for (e = i.value.toUpperCase(), t = document.getElementById("searchList"), n = t.getElementsByTagName("li"), s = 0; s < n.length; s++) o = n[s].getElementsByTagName("a")[0], a = o.textContent || o.innerText, a.toUpperCase().indexOf(e) > -1 ? n[s].style.display = "" : n[s].style.display = "none"
    }))
}
if ((() => {
        const e = document.querySelectorAll(".needs-validation");
        Array.from(e).forEach((e => {
            e.addEventListener("submit", (t => {
                e.checkValidity() || (t.preventDefault(), t.stopPropagation()), e.classList.add("was-validated")
            }), !1)
        }))
    })(), document.querySelector("#specialDiscountModal")) {
    new bootstrap.Modal("#specialDiscountModal", {}).show()
}
window.onscroll = function() {
    window.pageYOffset >= 100 ? (a.classList.add("sticky"), e.style.top = "0") : (a.classList.remove("sticky"), e.removeAttribute("style"))
};
const a = document.querySelector("header");
document.addEventListener("DOMContentLoaded", (function() {
    var e = document.querySelectorAll("img.lazy");
    if (e && "IntersectionObserver" in window) {
        let t = new IntersectionObserver((function(e, n) {
            e.forEach((function(e) {
                if (e.isIntersecting) {
                    let o = e.target;

                    function n() {
                        o.src = o.getAttribute("data-src"), o.classList.remove("lazy"), t.unobserve(o)
                    }
                    navigator.onLine ? n() : caches.match(o.getAttribute("data-src")).then((e => {
                        e && e.ok && 200 === e.status && n()
                    }))
                }
            }))
        }));
        e.forEach((function(e) {
            t.observe(e)
        }))
    }
}));
const r = document.querySelectorAll("#bookmarkCourse"),
    c = document.querySelectorAll("#likeCourse");
r && r.forEach((e => {
    e.addEventListener("click", (function() {
        const e = this.querySelector("svg");
        "" !== e.style.fill ? e.style.fill = "" : e.style.fill = "#146da5"
    }))
})), c && c.forEach((e => {
    e.addEventListener("click", (function() {
        const e = this.querySelector("svg");
        "transparent" !== e.style.fill ? e.style.fill = "transparent" : e.style.fill = "#ff0000"
    }))
})), "serviceWorker" in navigator && window.addEventListener("load", (() => {
    navigator.serviceWorker.register("/sw.js", {
        scope: "/"
    }).then((e => {
        setInterval((() => {
            e.update()
        }), 36e5)
    }))
}));
const l = document.querySelector(".install-app"),
    d = document.getElementById("installPwaBtn"),
    u = document.querySelector(".not-support"),
    f = document.querySelector(".support"),
    y = document.getElementById("hideInstallApp");
let m = null;

function p(e, t) {
    const n = new Date;
    n.setTime(n.getTime() + 24 * t * 60 * 60 * 1e3);
    const o = "expires=" + n.toUTCString();
    document.cookie = e + "=true;" + o + ";path=/"
}

function g(e) {
    const t = e + "=",
        n = document.cookie.split(";");
    for (let e = 0; e < n.length; e++) {
        let o = n[e];
        for (;
            " " === o.charAt(0);) o = o.substring(1, o.length);
        if (0 === o.indexOf(t)) return o.substring(t.length, o.length)
    }
    return null
}

function v(t) {
    if (l.classList.replace("d-block", "d-none"), e.classList.remove("has-banner"), t) {
        "BUTTON" === t.currentTarget.tagName && p("hideInstallApp", 3)
    }
}
g("hideInstallApp") && v(), window.addEventListener("beforeinstallprompt", (async e => {
    e.preventDefault(), m = e, u.classList.add("d-none"), f.classList.replace("d-none", "d-block")
})), d.addEventListener("click", (async () => {
    if (!m) return;
    "accepted" === (await m.prompt()).outcome && v()
})), window.matchMedia("(display-mode: standalone)").matches && v(), y.addEventListener("click", v);
let h = !1;
if (!navigator.onLine) {
    const e = document.getElementById("offlineToast");
    h = !0, new bootstrap.Toast(e).show()
}
const w = document.getElementById("getNotificationPermissionBtn"),
    L = document.getElementById("getNotificationPermissionToast"),
    E = L.querySelector(".btn-close"),
    k = new bootstrap.Toast(L);
const b = function() {
    const e = new Date,
        t = e.getDate(),
        n = e.getMonth() + 1;
    return `${e.getFullYear()}-${n<10?"0"+n:n}-${t<10?"0"+t:t}`
}();
const I = await async function() {
    try {
        const e = await fetch("./notification.json");
        if (!e.ok) throw new Error(`Response status: ${e.status}`);
        return await e.json()
    } catch (e) {
        console.error(e.message)
    }
}();
let S;
if (I) {
    S = I.filter((e => e.date === b));
    (function(e) {
        const t = [],
            n = e.toLowerCase();
        for (let e = 0; e < localStorage.length; e++) {
            const o = localStorage.key(e);
            o && o.toLowerCase().startsWith(n) && t.push({
                key: o,
                value: localStorage.getItem(o)
            })
        }
        return t
    })("UUID-").forEach((e => {
        const t = e.value;
        S = S.filter((e => e.UUID !== t))
    }))
}
let q = !1;
"granted" === Notification.permission && (q = !0);
const T = async () => {
        Notification.requestPermission().then((e => {
            if (k.hide(), "granted" === e) return (async () => {
                "serviceWorker" in navigator && navigator.serviceWorker.ready.then((e => {
                    S && S.forEach((t => {
                        e.showNotification(t.title, {
                            body: t.text,
                            icon: t.iconLink,
                            data: {
                                url: t.redirectUrl
                            }
                        }), localStorage.setItem(`UUID-${t.id}`, t.UUID)
                    }))
                }))
            })(), q = !0
        }))
    },
    N = g("HideToastNotification");
q ? T() : "default" !== Notification.permission || N || (h ? setTimeout((() => {
    k.show()
}), 1e4) : k.show()), w.addEventListener("click", T), E.addEventListener("click", (function() {
    p("HideToastNotification", 3)
}));