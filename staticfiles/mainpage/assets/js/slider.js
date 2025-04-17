var isSwiperLinked = document.querySelector("script[src*='swiper-bundle.min.js']");
if (isSwiperLinked) {
    var e, i = {
        slidesPerView: 4,
        spaceBetween: 30,
        autoplay: {
            delay: 3000,
            disableOnInteraction: !1
        },
        navigation: {
            nextEl: ".swiper-button-next",
            prevEl: ".swiper-button-prev"
        }
    };

    function n() {
        window.innerWidth <= 992 && window.innerWidth > 556 ? (i.slidesPerView = 2, e = new Swiper("#sliderPosts", i)) : window.innerWidth <= 556 ? (i.slidesPerView = 1, e = new Swiper("#sliderPosts", i)) : window.innerWidth > 992 && (i.slidesPerView = 4, e = new Swiper("#sliderPosts", i))
    }
    window.addEventListener("resize", n), n();
}