"use strict";

function createVideoPlayer(e) {
    var t = document.querySelector(e),
        n = t.querySelector(".video"),
        $ = t.querySelector("#screenshot"),
        r = t.querySelector("#grayVideoToggle"),
        i = t.querySelector("#playPause"),
        a = t.querySelector("#setPlaybackRate"),
        o = t.querySelector("#pictureInPicture"),
        _ = t.querySelector(".controllers"),
        l = t.querySelector(".progress-video"),
        c = t.querySelector(".progress-hidden"),
        s = t.querySelector("#progressMarker"),
        d = t.querySelector("#timeProgress"),
        u = t.querySelector("#plusSecond"),
        v = t.querySelector("#minusSecond"),
        p = t.querySelector("#fullscreen"),
        f = t.querySelector("#volumeRange"),
        h = t.querySelector("#volumeContainer"),
        g = t.querySelector("#volumeBtn"),
        y = t.querySelector(".loading"),
        m = t.querySelector(".user-information"),
        L = t.querySelector(".buffered"),
        E = t.querySelector(".times"),
        q = t.querySelector(".current-time"),
        S = t.querySelector(".duration"),
        b = t.querySelector(".setting-panel"),
        w = t.querySelector("#setting"),
        k = t.querySelector("#closeSetting"),
        x = t.querySelectorAll(".control"),
        M = t.querySelector(".alarm"),
        T = t.querySelector(".alarm-text"),
        R = t.querySelector("#zoom");

    function C(e) {
        T.innerHTML = e, M.style.opacity = "1", M.style.right = "25px", setTimeout(() => {
            M.style.opacity = "0", M.style.right = "-100%"
        }, 5e3)
    }
    let z = !1,
        H = navigator.connection.effectiveType,
        P = "slow-2g" === H || "2g" === H;

    function A(e, $) {
        var r = document.createElement("canvas");
        r.width = n.videoWidth, r.height = n.videoHeight, r.getContext("2d").drawImage(n, 0, 0, r.width, r.height);
        var i = r.toDataURL();
        if (e) {
            var a = document.createElement("a");
            a.href = i, a.download = "screenshot.png", a.click()
        }
        if ($) {
            let o = document.createElement("section");
            o.classList.add("zoomist-section"), o.dir = "ltr";
            let _ = document.createElement("div");
            _.classList.add("zoomist-container");
            let l = document.createElement("div");
            l.classList.add("zoomist-wrapper");
            let c = document.createElement("div");
            c.classList.add("zoomist-image");
            let s = document.createElement("img");
            s.src = i;
            let d = document.createElement("div");
            d.classList.add("zoomist-dimmer");
            let u = document.createElement("button");
            u.classList.add("btn", "rounded-circle", "d-flex", "align-items-center", "justify-content-center", "p-0", "w-h-25", "position-relative", "closeZoomistBtn"), u.innerHTML = `
      <svg width="20px" height="30px" viewBox="0 0 1024 1024">
        <path fill="#333" d="M195.2 195.2a64 64 0 0 1 90.496 0L512 421.504 738.304 195.2a64 64 0 0 1 90.496 90.496L602.496 512 828.8 738.304a64 64 0 0 1-90.496 90.496L512 602.496 285.696 828.8a64 64 0 0 1-90.496-90.496L421.504 512 195.2 285.696a64 64 0 0 1 0-90.496z">
        </path>
      </svg>
      `, c.appendChild(s), l.appendChild(c), _.appendChild(l), o.appendChild(_), o.appendChild(u), document.body.appendChild(o), document.body.appendChild(d);
            let v = new Event("zoomistContainerAdded");
            document.dispatchEvent(v), document.body.scrollIntoView({
                behavior: "smooth",
                block: "start"
            }), u.addEventListener("click", () => {
                o.remove(), d.remove(), t.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                })
            })
        }
    }
    M && n.addEventListener("error", e => {
        switch (e.target.error.code) {
            case e.target.error.MEDIA_ERR_ABORTED:
                C("شما پخش ویدئو را متوقف کردید.");
                break;
            case e.target.error.MEDIA_ERR_NETWORK:
                C("یک خطای شبکه باعث شد تا بارگیری ویدئو تا حدی با شکست مواجه شود.");
                break;
            case e.target.error.MEDIA_ERR_DECODE:
                C("پخش ویدیو به دلیل مکشل یااینکه ویدیو از ویژگی هایی استفاده می کرد که مرورگر شما پشتیبانی نمی کند متوقف شد.");
                break;
            case e.target.error.MEDIA_ERR_SRC_NOT_SUPPORTED:
                C("ویدیو بارگیری نشد، یا به دلیل خرابی سرور یا شبکه یا به دلیل پشتیبانی نشدن قالب");
                break;
            default:
                C("خطای ناشناخته ، به پشتیبانی کدنا مراجعه کنید.")
        }
    }), $ && $.addEventListener("click", function() {
        I && A(!0, !1)
    });
    var B = !1;
    r && r.addEventListener("click", function() {
        B ? (n.style.filter = "grayscale(0)", B = !1) : (n.style.filter = "grayscale(1)", B = !0)
    });
    var D = !1,
        I = !1;
    i && i.addEventListener("click", function() {
        n.currentTime >= n.duration ? n.play() : D ? n.pause() : n.play()
    }), n.addEventListener("play", function(e) {
        i.innerHTML = '\n                                            <svg fill="#fff" width="21px" height="21px" viewBox="0 0 32 32">\n                                                <path d="M5.92 24.096q0 0.832 0.576 1.408t1.44 0.608h4.032q0.832 0 1.44-0.608t0.576-1.408v-16.16q0-0.832-0.576-1.44t-1.44-0.576h-4.032q-0.832 0-1.44 0.576t-0.576 1.44v16.16zM18.016 24.096q0 0.832 0.608 1.408t1.408 0.608h4.032q0.832 0 1.44-0.608t0.576-1.408v-16.16q0-0.832-0.576-1.44t-1.44-0.576h-4.032q-0.832 0-1.408 0.576t-0.608 1.44v16.16z"></path>\n                                            </svg>\n                                            <span class="control-tooltip">پخش (K)</span>', !z && P && (C("سرعت اینترنت شما ضعیف است. ممکن است در پخش با مشکل مواجه شوید."), z = !0), D = !0, I = !0
    }), n.addEventListener("pause", function() {
        i.innerHTML = '\n                                            <svg width="21px" height="21px" viewBox="0 0 11 14">\n                                                <g stroke="none" stroke-width="1" fill="none" fill-rule="evenodd">\n                                                    <g transform="translate(-753.000000, -955.000000)">\n                                                        <g transform="translate(100.000000, 852.000000)">\n                                                            <g transform="translate(646.000000, 98.000000)">\n                                                                <g>\n                                                                    <rect x="0" y="0" width="24" height="24"></rect>\n                                                                    <path d="M7,6.82 L7,17.18 C7,17.97 7.87,18.45 8.54,18.02 L16.68,12.84 C17.3,12.45 17.3,11.55 16.68,11.15 L8.54,5.98 C7.87,5.55 7,6.03 7,6.82 Z" fill="#fff"></path>\n                                                                </g>\n                                                            </g>\n                                                        </g>\n                                                     </g>\n                                                </g>\n                                            </svg>\n                                            <span class="control-tooltip">پخش (K)</span>', D = !1
    }), t && t.addEventListener("click", function(e) {
        e.target.classList.contains("controllers") && _.classList.toggle("show")
    }), a && a.addEventListener("click", function(e) {
        1 === n.playbackRate ? (n.playbackRate = 1.5, e.target.innerHTML = "<span>1.5</span>سرعت پخش") : 1.5 === n.playbackRate ? (n.playbackRate = 2, e.target.innerHTML = "<span>2</span>سرعت پخش") : 2 === n.playbackRate ? (n.playbackRate = .5, e.target.innerHTML = "<span>0.5</span>سرعت پخش") : .5 === n.playbackRate && (n.playbackRate = 1, e.target.innerHTML = "<span>1</span>سرعت پخش")
    }), o && (-1 != navigator.userAgent.indexOf("Firefox") ? o.remove() : o.addEventListener("click", function() {
        document.pictureInPictureElement ? document.exitPictureInPicture().then(function() {}).catch(function(e) {
            return console.error(e)
        }) : n.requestPictureInPicture()
    })), l && (l.addEventListener("click", function(e) {
        var t, $, r = (t = e, $ = c.getBoundingClientRect(), (t.clientX - $.left) / c.offsetWidth);
        n.currentTime = r * n.duration, s.style.width = r * c.offsetWidth + "px", I = !0
    }), l.addEventListener("mousemove", e => {
        let t = e.offsetX / l.offsetWidth * 100,
            $ = F(t * n.duration / 100);
        d.innerHTML = $, d.style.visibility = "visible", Number(t) > 95 ? d.style.left = "90%" : 2 > Number(t) ? d.style.left = "-5%" : d.style.left = `${t-6}%`
    }), l.addEventListener("mouseleave", () => {
        d.style.visibility = "hidden"
    }), n.addEventListener("timeupdate", function() {
        var e, t = (e = n.currentTime) / n.duration;
        if (s.style.width = t * c.offsetWidth + "px", n.currentTime >= n.duration && (i.innerHTML = '\n          <svg width="21px" height="21px" viewBox="0 0 11 14">\n          <g stroke="none" stroke-width="1" fill="none" fill-rule="evenodd">\n              <g transform="translate(-753.000000, -955.000000)">\n                  <g transform="translate(100.000000, 852.000000)">\n                      <g transform="translate(646.000000, 98.000000)">\n                          <g>\n                              <rect x="0" y="0" width="24" height="24"></rect>\n                              <path d="M7,6.82 L7,17.18 C7,17.97 7.87,18.45 8.54,18.02 L16.68,12.84 C17.3,12.45 17.3,11.55 16.68,11.15 L8.54,5.98 C7.87,5.55 7,6.03 7,6.82 Z" fill="#fff"></path>\n                          </g>\n                      </g>\n                  </g>\n               </g>\n          </g>\n          </svg>\n          '), n.currentTime, n.duration, n.buffered.length > 0) {
            if (n.currentTime > n.buffered.end(0)) {
                var $ = n.buffered.end(n.buffered.length - 1) / n.duration * 100;
                L.style.width = "".concat($, "%")
            } else {
                var r = n.buffered.end(0) / n.duration * 100;
                L.style.width = "".concat(r, "%")
            }
        }
        q.textContent = F(n.currentTime)
    }), n.addEventListener("seeking", function() {
        var e = n.buffered.end(n.buffered.length - 1) / n.duration * 100;
        L.style.width = "".concat(e, "%")
    }));
    var K = !1;

    function W() {
        document.exitFullscreen(), K = !1
    }

    function F(e) {
        return "".concat(Math.floor(e / 3600), ":").concat(Math.floor(e % 3600 / 60).toString().padStart(2, "0"), ":").concat(Math.floor(e % 60).toString().padStart(2, "0"))
    }
    if (p && p.addEventListener("click", function() {
            K ? W() : (t.requestFullscreen(), K = !0)
        }), u && u.addEventListener("click", function() {
            n.currentTime += 15
        }), v && v.addEventListener("click", function() {
            n.currentTime -= 15
        }), h && (window.innerWidth > 576 && (h.addEventListener("mousemove", function() {
            h.style.width = "100%", f.style.opacity = "1"
        }), h.addEventListener("mouseleave", function() {
            h.style.width = "32px", f.style.opacity = "0"
        })), f.addEventListener("input", function() {
            "0" === f.value ? n.muted = !0 : (n.muted = !1, n.volume = f.value)
        }), g.addEventListener("click", function() {
            n.muted ? (n.muted = !1, f.value = 1) : (n.muted = !0, f.value = 0)
        }), n.addEventListener("volumechange", function() {
            n.muted ? g.innerHTML = '\n        <svg viewBox="0 2 24 20" width="21" height="21">\n          <g fill="currentcolor" data-viewbox="0 0 24 24">\n            <path d="M10.79 9.77a1 1 0 00.71.29.84.84 0 00.38-.08 1 1 0 00.62-.92V5a1 1 0 00-1.5-.84L8.48 5.74a1 1 0 00-.48.73 1 1 0 00.29.82zM19.57 4.72a1 1 0 10-1.44 1.39A8.5 8.5 0 0119 16.82a1 1 0 00.26 1.39 1 1 0 00.57.18 1 1 0 00.82-.44 10.5 10.5 0 00-1.08-13.23z"></path><path d="M16.5 12a4.42 4.42 0 01-.5 2 1 1 0 00.44 1.34.93.93 0 00.45.11 1 1 0 00.9-.55 6.4 6.4 0 00.71-2.9 6.49 6.49 0 00-2-4.72 1 1 0 10-1.37 1.45A4.46 4.46 0 0116.5 12zM12.21 12.16L7.4 7.35 3.21 3.16a1 1 0 00-1.42 0 1 1 0 000 1.41L4.72 7.5H2.5a1 1 0 00-1 1v7a1 1 0 001 1h3.21L11 19.84a1 1 0 00.54.16 1 1 0 001-1v-3.72l6.43 6.43a1 1 0 001.42 0 1 1 0 000-1.42z">\n            </path>\n          </g>\n        </svg>\n        <span class="control-tooltip end-0">قطع و وصل صدا (M)</span>' : g.innerHTML = '\n        <svg viewBox="0 2 24 20" width="21" height="21">\n          <g fill="currentcolor" data-viewbox="0 0 24 24">\n            <path\n                d="M12 4.12a1 1 0 00-1 0L5.71 7.5H2.5a1 1 0 00-1 1v7a1 1 0 001 1h3.21L11 19.84a1 1 0 00.54.16 1 1 0 001-1V5a1 1 0 00-.54-.88zM19.57 4.72a1 1 0 10-1.44 1.39 8.5 8.5 0 010 11.78 1 1 0 000 1.42 1 1 0 00.7.27 1 1 0 00.72-.3 10.51 10.51 0 000-14.56z">\n            </path>\n            <path\n                d="M16.46 7.28a1 1 0 10-1.37 1.45 4.5 4.5 0 010 6.54 1 1 0 101.37 1.45 6.48 6.48 0 000-9.44z">\n            </path>\n          </g>\n        </svg>\n      <span class="control-tooltip end-0">قطع و وصل صدا (M)</span>'
        })), n && (n.addEventListener("waiting", function() {
            y.style.display = "block"
        }), n.addEventListener("playing", function() {
            y.style.display = "none"
        }), n.addEventListener("ended", function() {
            n.src = n.getAttribute("primary-src"), n.play()
        })), m) {
        var O = [{
                right: 24,
                top: 22
            }, {
                right: 60,
                top: 10
            }, {
                right: 30,
                top: 70
            }, {
                right: 65,
                top: 50
            }],
            V = 0;
        m && setInterval(function() {
            m && (m.style.right = "".concat(O[V].right, "%"), m.style.top = "".concat(O[V].top, "%"), V < O.length - 1 ? V++ : V = 0)
        }, 1e4)
    }
    n.addEventListener("loadedmetadata", function() {
        n.addEventListener("canplaythrough", function() {
            var e = n.currentTime,
                t = n.duration;
            q && (q.textContent = F(e), S.textContent = F(t), E.classList.add("show"))
        })
    }), b && (w.addEventListener("click", function() {
        b.style.right = "0"
    }), k.addEventListener("click", function() {
        b.style.right = "-300px"
    })), n && n.addEventListener("contextmenu", e => {
        e.preventDefault()
    });
    let Z = !1;
    t.addEventListener("mouseover", () => {
        Z = !0
    }), t.addEventListener("mouseout", () => {
        Z = !1
    }), document.addEventListener("keydown", e => {
        ((function e(t) {
            let n = t.getBoundingClientRect();
            return n.top >= 0 && n.left >= 0 && n.bottom <= window.innerHeight && n.right <= window.innerWidth
        })(t) && D || Z) && ((e.preventDefault(), "KeyK" === e.code) ? n.currentTime >= n.duration ? n.play() : D ? n.pause() : n.play() : "KeyL" === e.code ? n.currentTime += 15 : "KeyJ" === e.code ? n.currentTime -= 15 : "KeyM" === e.code ? n.muted ? (n.muted = !1, f.value = 1) : (n.muted = !0, f.value = 0) : "KeyF" === e.code && (K ? (document.exitFullscreen(), K = !1) : (t.requestFullscreen(), K = !0)))
    }), x.forEach(e => {
        e.addEventListener("mousemove", () => {
            var t = e.querySelector(".control-tooltip");
            t && (t.style.visibility = "visible")
        }), e.addEventListener("mouseleave", () => {
            var t = e.querySelector(".control-tooltip");
            t && (t.style.visibility = "hidden")
        })
    }), R && R.addEventListener("click", () => {
        I && (K && W(), n.pause(), A(!1, !0))
    })
}