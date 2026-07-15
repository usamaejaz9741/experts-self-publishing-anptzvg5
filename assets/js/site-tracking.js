(function () {
  var GA_ID = "G-XXXXXXXXXX";
  var META_PIXEL_ID = "YOUR_META_PIXEL_ID";
  var BING_UET_ID = "YOUR_BING_UET_ID";
  var ZENDESK_KEY = "YOUR_ZENDESK_WIDGET_KEY";

  function isPlaceholder(value) {
    return !value || value.indexOf("YOUR_") === 0 || value === "G-XXXXXXXXXX";
  }

  if (!isPlaceholder(GA_ID)) {
    var gaScript = document.createElement("script");
    gaScript.async = true;
    gaScript.src = "https://www.googletagmanager.com/gtag/js?id=" + GA_ID;
    document.head.appendChild(gaScript);

    window.dataLayer = window.dataLayer || [];
    function gtag() {
      window.dataLayer.push(arguments);
    }
    window.gtag = gtag;
    gtag("js", new Date());
    gtag("config", GA_ID);
  }

  if (!isPlaceholder(META_PIXEL_ID)) {
    !(function (f, b, e, v, n, t, s) {
      if (f.fbq) return;
      n = f.fbq = function () {
        n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments);
      };
      if (!f._fbq) f._fbq = n;
      n.push = n;
      n.loaded = !0;
      n.version = "2.0";
      n.queue = [];
      t = b.createElement(e);
      t.async = !0;
      t.src = v;
      s = b.getElementsByTagName(e)[0];
      s.parentNode.insertBefore(t, s);
    })(window, document, "script", "https://connect.facebook.net/en_US/fbevents.js");
    fbq("init", META_PIXEL_ID);
    fbq("track", "PageView");
  }

  if (!isPlaceholder(BING_UET_ID)) {
    (function (w, d, t, r, u) {
      var f, n, i;
      w[u] = w[u] || [];
      f = function () {
        var o = { ti: BING_UET_ID, enableAutoSpaTracking: true };
        o.q = w[u];
        w[u] = new UET(o);
        w[u].push("pageLoad");
      };
      n = d.createElement(t);
      n.src = r;
      n.async = 1;
      n.onload = n.onreadystatechange = function () {
        var s = this.readyState;
        s && s !== "loaded" && s !== "complete" || (f(), (n.onload = n.onreadystatechange = null));
      };
      i = d.getElementsByTagName(t)[0];
      i.parentNode.insertBefore(n, i);
    })(window, document, "script", "https://bat.bing.com/bat.js", "uetq");
  }

  if (!isPlaceholder(ZENDESK_KEY)) {
    var zendeskScript = document.createElement("script");
    zendeskScript.id = "ze-snippet";
    zendeskScript.defer = true;
    zendeskScript.src =
      "https://static.zdassets.com/ekr/snippetb14a.js?key=" + ZENDESK_KEY;
    document.body.appendChild(zendeskScript);

    window.addEventListener("load", function () {
      setTimeout(function () {
        if (typeof zE !== "undefined") {
          zE("webWidget", "open");
        }
      }, 5000);
    });
  }
})();
