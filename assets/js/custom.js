$(document).ready(function () {
  $(".nice-select").niceSelect();
});

document.addEventListener("click", function (event) {
  var trigger = event.target.closest("[data-open-zendesk]");
  if (!trigger) return;
  event.preventDefault();
  if (typeof zE !== "undefined") {
    zE("webWidget", "open");
  }
});

document.addEventListener("DOMContentLoaded", function () {
  const toggler = document.querySelector(".navbar-toggler");
  const collapseEl = document.querySelector("#navbarNavDropdown");

  const bsCollapse = new bootstrap.Collapse(collapseEl, {
    toggle: false,
  });

  toggler.addEventListener("click", function () {
    if (collapseEl.classList.contains("show")) {
      bsCollapse.hide();
    } else {
      bsCollapse.show();
    }
  });
});

document.addEventListener("DOMContentLoaded", function () {
  if (window.innerWidth <= 991) {
    const dropdownToggles = document.querySelectorAll(
      ".custom-dropdown > .nav-link",
    );

    dropdownToggles.forEach(function (toggle) {
      toggle.addEventListener("click", function (e) {
        e.preventDefault();

        const parent = this.closest(".custom-dropdown");

        // same dropdown toggle
        parent.classList.toggle("open");

        // optional: baqi dropdown band karne ke liye
        document.querySelectorAll(".custom-dropdown").forEach(function (item) {
          if (item !== parent) {
            item.classList.remove("open");
          }
        });
      });
    });
  }
});
// AOS.init();

function initAOS() {
  if (window.innerWidth > 1400) {
    AOS.init({
      once: true, // animation will happen only once
    });
  } else {
    const aosElements = document.querySelectorAll("[data-aos]");
    aosElements.forEach((el) => el.removeAttribute("data-aos")); // Remove data-aos attributes
  }
}
initAOS();
// Optional: Reinitialize AOS on window resize
window.addEventListener("resize", initAOS);

let counters = document.querySelectorAll(".count");
let duration = 2000; // animation time (ms)
let started = false;

function formatNumber(num) {
  return Number(num).toLocaleString();
}

function startCounter() {
  let startTime = null;

  function animate(timestamp) {
    if (!startTime) startTime = timestamp;

    let progress = Math.min((timestamp - startTime) / duration, 1);

    counters.forEach((counter) => {
      let target = +counter.dataset.number;
      let current = Math.floor(progress * target);
      counter.innerHTML = formatNumber(current);
    });

    if (progress < 1) {
      requestAnimationFrame(animate);
    } else {
      counters.forEach((counter) => {
        counter.innerHTML = formatNumber(counter.dataset.number);
      });
    }
  }

  requestAnimationFrame(animate);
}

// 👀 Scroll detection
let observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting && !started) {
        started = true;
        startCounter();
        observer.disconnect(); // sirf ek dafa
      }
    });
  },
  {
    threshold: 0.4, // 40% visible hone par start
  },
);

// Observe parent section ya pehla counter
observer.observe(counters[0]);

$(".brand-slider").slick({
  slidesToShow: 7,
  slidesToScroll: 1,
  autoplay: true,
  autoplaySpeed: 0,
  speed: 13000,
  arrows: false,
  dots: false,
  pauseOnHover: false,
  cssEase: "linear",
  responsive: [
    {
      breakpoint: 992,
      settings: {
        slidesToShow: 4,
      },
    },
    {
      breakpoint: 768,
      settings: {
        slidesToShow: 3,
      },
    },
    {
      breakpoint: 500,
      settings: {
        slidesToShow: 3,
      },
    },
    {
      breakpoint: 400,
      settings: {
        slidesToShow: 3,
      },
    },
  ],
});

$(".publish-slider").slick({
  slidesToShow: 2,
  slidesToScroll: 1,
  autoplay: true,
  arrows: false,
  dots: true,
  autoplaySpeed: 2000,
  responsive: [
    {
      breakpoint: 576,
      settings: {
        slidesToShow: 1,
      },
    },
  ],
});

$(".ads-slider").slick({
  slidesToShow: 7,
  slidesToScroll: 1,
  autoplay: true,
  autoplaySpeed: 0,
  speed: 13000,
  arrows: false,
  dots: false,
  pauseOnHover: false,
  cssEase: "linear",
  responsive: [
    {
      breakpoint: 992,
      settings: {
        slidesToShow: 4,
      },
    },
    {
      breakpoint: 768,
      settings: {
        slidesToShow: 3,
      },
    },
    {
      breakpoint: 500,
      settings: {
        slidesToShow: 3,
      },
    },
    {
      breakpoint: 400,
      settings: {
        slidesToShow: 3,
      },
    },
  ],
});

const boxes = document.querySelectorAll(".hvr-effect");

boxes.forEach(function (box) {
  box.addEventListener("mouseenter", function () {
    const target = box.querySelector(".effect"); // .effect wala element
    if (target) {
      target.classList.add("fa-shake");
    }
  });

  box.addEventListener("mouseleave", function () {
    const target = box.querySelector(".effect");
    if (target) {
      target.classList.remove("fa-shake");
    }
  });
});

window.addEventListener("scroll", function () {
  let scrollValue = window.scrollY;

  document.querySelectorAll(".img-left").forEach(function (img) {
    img.style.transform = `
       translateX(${-scrollValue * 0.8}px)

            
        `;
  });

  document.querySelectorAll(".img-right").forEach(function (img) {
    img.style.transform = `
            translateX(${scrollValue * 0.8}px)
            
        `;
  });
});

$(".process-for").slick({
  slidesToShow: 1,
  slidesToScroll: 1,
  arrows: false,
  fade: true,
  infinite: false,
  asNavFor: ".process-nav",
});

$(".process-nav").slick({
  slidesToShow: 6,
  slidesToScroll: 1,
  asNavFor: ".process-for",
  arrows: false,
  dots: false,
  centerMode: false,
  focusOnSelect: true,
  infinite: false,

  swipe: false,
  draggable: false,
  touchMove: false,

  responsive: [
    {
      breakpoint: 992,
      settings: {
        slidesToShow: 3,
        arrows: false,
        swipe: true,
        draggable: true,
        touchMove: true,
        dots: true,
      },
    },
    {
      breakpoint: 768,
      settings: {
        slidesToShow: 2,
        arrows: false,
        swipe: true,
        draggable: true,
        touchMove: true,
        dots: true,
      },
    },
  ],
});







// const observer = new IntersectionObserver(
//     (e, o) => {
//         e.forEach((e) => {
//             e.isIntersecting && (e.target.classList.contains("lazy-loaded-image") && (e.target.classList.add("show"), (e.target.src = e.target.dataset.src), e.target.classList.remove("lazy")), o.unobserve(e.target));
//         });
//     },
//     { root: null, rootMargin: "0px", threshold: 0.1 }
// );

// [...document.querySelectorAll(".lazy-loaded-image.lazy"), ...document.querySelectorAll(".hidden")].forEach((e) => observer.observe(e));



// document.querySelectorAll('.custom-acc-btn').forEach(btn => {
//     btn.addEventListener('click', function () {
//         const target = document.querySelector(this.dataset.target);
//         const isOpen = target.classList.contains('show');

//         // close all
//         document.querySelectorAll('.accordion-collapse').forEach(col => {
//             col.classList.remove('show');
//         });

//         document.querySelectorAll('.accordion-button').forEach(b => {
//             b.classList.add('collapsed');
//         });

//         // toggle current
//         if (!isOpen) {
//             target.classList.add('show');
//             this.classList.remove('collapsed');
//         }
//     });
// });