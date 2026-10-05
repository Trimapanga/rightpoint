/* Scroll motion: a reading-progress line on the header, headings that rise word by
   word, images that open like a curtain, and figures that count up. Nothing here
   changes content - it only decorates what is already on the page - and the whole
   file stands down for reduced-motion users. */
(function () {
  "use strict";

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  // Phones get the page as-is: no scroll-triggered reveals, nothing half-faded mid-scroll.
  if (window.matchMedia("(max-width: 768px)").matches) return;

  var root = document.documentElement;
  root.classList.add("motion-on");

  function onEnter(elements, callback, margin) {
    if (!("IntersectionObserver" in window)) {
      elements.forEach(callback);
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          callback(entry.target);
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: margin || "0px 0px -12% 0px" });
    elements.forEach(function (el) { io.observe(el); });
  }

  /* ---------- 1. reading progress ---------- */

  var header = document.querySelector(".site-header");
  if (header) {
    var bar = document.createElement("span");
    bar.className = "motion-progress";
    bar.setAttribute("aria-hidden", "true");
    header.appendChild(bar);
    var ticking = false;
    var update = function () {
      ticking = false;
      var max = root.scrollHeight - window.innerHeight;
      var p = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0;
      bar.style.transform = "scaleX(" + p.toFixed(4) + ")";
    };
    window.addEventListener("scroll", function () {
      if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
    }, { passive: true });
    window.addEventListener("resize", update);
    update();
  }

  /* ---------- 2. word-by-word headings ----------
     Text nodes are split into words, each wrapped in a clipping span, so markup such
     as <br> or <span> inside a heading survives. The heading keeps its full text for
     assistive tech through an aria-label. */

  function splitWords(heading) {
    heading.setAttribute("aria-label", heading.textContent.replace(/\s+/g, " ").trim());
    var index = 0;
    var walker = document.createTreeWalker(heading, NodeFilter.SHOW_TEXT);
    var nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(function (node) {
      var parts = node.nodeValue.split(/(\s+)/);
      var frag = document.createDocumentFragment();
      parts.forEach(function (part) {
        if (!part) return;
        if (/^\s+$/.test(part)) {
          frag.appendChild(document.createTextNode(part));
          return;
        }
        var mask = document.createElement("span");
        mask.className = "motion-w";
        mask.setAttribute("aria-hidden", "true");
        var inner = document.createElement("span");
        inner.textContent = part;
        inner.style.setProperty("--w", index++);
        mask.appendChild(inner);
        frag.appendChild(mask);
      });
      node.parentNode.replaceChild(frag, node);
    });
    heading.classList.add("motion-words");
  }

  var headings = Array.prototype.slice.call(document.querySelectorAll(
    ".section-head h2, .banner h1, .split h2, .shop-title"
  ));
  headings.forEach(splitWords);
  // Headings already on screen (page heroes) start at once rather than waiting on the
  // observer, so an opening title can never sit hidden.
  var viewport = window.innerHeight || root.clientHeight;
  var later = headings.filter(function (h) {
    var rect = h.getBoundingClientRect();
    if (rect.top < viewport && rect.bottom > 0) {
      window.requestAnimationFrame(function () { h.classList.add("is-in"); });
      return false;
    }
    return true;
  });
  onEnter(later, function (h) { h.classList.add("is-in"); });

  /* ---------- 3. curtain image reveals ---------- */

  var media = Array.prototype.slice.call(document.querySelectorAll(
    ".capability-visual, .frame:not(.logo-plate), .deliver-visual"
  ));
  media.forEach(function (m) { m.classList.add("motion-curtain"); });
  onEnter(media, function (m) { m.classList.add("is-in"); }, "0px 0px -18% 0px");

  /* ---------- 4. counting figures ---------- */

  function countUp(el) {
    var text = el.textContent.trim();
    var target = parseInt(text, 10);
    if (isNaN(target) || target < 1) return;
    var width = text.length;
    var start = null;
    var duration = 900 + target * 60;
    function pad(n) {
      var s = String(n);
      while (s.length < width) s = "0" + s;
      return s;
    }
    function step(now) {
      if (start === null) start = now;
      var t = Math.min(1, (now - start) / duration);
      var eased = 1 - Math.pow(1 - t, 3);
      el.textContent = pad(Math.round(eased * target));
      if (t < 1) window.requestAnimationFrame(step);
    }
    el.textContent = pad(0);
    window.requestAnimationFrame(step);
  }

  var figures = Array.prototype.slice.call(document.querySelectorAll(
    ".hero-proof strong, .capability-count"
  ));
  onEnter(figures, countUp, "0px");
})();
