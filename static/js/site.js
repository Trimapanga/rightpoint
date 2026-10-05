(function () {
  "use strict";

  var header = document.querySelector("[data-header]");

  var toggle = document.querySelector("[data-nav-toggle]");
  var nav = document.getElementById("primary-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    });
    // Tap outside the open menu (page body, tab bar) to close it.
    document.addEventListener("click", function (event) {
      if (!nav.classList.contains("is-open")) return;
      if (nav.contains(event.target) || toggle.contains(event.target)) return;
      nav.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && nav.classList.contains("is-open")) {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.setAttribute("aria-label", "Open menu");
        toggle.focus();
      }
    });
    nav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        if (nav.classList.contains("is-open")) {
          nav.classList.remove("is-open");
          toggle.setAttribute("aria-expanded", "false");
          toggle.setAttribute("aria-label", "Open menu");
        }
      });
    });
  }

  // Mobile filter sheet: the shop rail slides up from the bottom behind a filter icon.
  var sheet = document.querySelector("[data-filter-sheet]");
  if (sheet) {
    var filterScrim = document.querySelector(".m-sheet-scrim");
    var setSheet = function (open) {
      sheet.classList.toggle("is-open", open);
      if (filterScrim) filterScrim.hidden = !open;
      document.body.classList.toggle("m-sheet-lock", open);
    };
    document.querySelectorAll("[data-filter-open]").forEach(function (b) {
      b.addEventListener("click", function () { setSheet(true); });
    });
    document.querySelectorAll("[data-filter-close]").forEach(function (b) {
      b.addEventListener("click", function () { setSheet(false); });
    });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") setSheet(false); });
  }

  // Solutions submenu: click/keyboard driven, hover handled in CSS on desktop.
  document.querySelectorAll(".nav-submenu-toggle").forEach(function (button) {
    var menu = document.getElementById(button.getAttribute("aria-controls"));
    if (!menu) return;
    button.addEventListener("click", function () {
      var open = menu.classList.toggle("is-open");
      button.setAttribute("aria-expanded", open ? "true" : "false");
    });
  });

  if ("IntersectionObserver" in window) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.06 }
    );
    document.querySelectorAll(".card, .pillar, .panel, .step, .capability-intro, .capability-row, .capability-orbit, .capability-foot, .reveal").forEach(function (el) {
      el.classList.add("reveal");
      observer.observe(el);
    });
  }

  // Hero capability row: a counter walks the chips so the row reads as a sequence.
  // Paused on hover/focus and for reduced-motion users; the markup never changes.
  var rotator = document.querySelector("[data-count-rotate]");
  if (rotator) {
    var chips = Array.prototype.slice.call(rotator.querySelectorAll(".chip"));
    var index = 0;
    var paused = false;
    var running = chips.length > 1 && !window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function show(i) {
      chips.forEach(function (chip, n) { chip.classList.toggle("is-current", n === i); });
    }
    show(index);

    if (running) {
      window.setInterval(function () {
        if (paused) return;
        index = (index + 1) % chips.length;
        show(index);
      }, 1900);
      ["pointerenter", "focusin"].forEach(function (evt) {
        rotator.addEventListener(evt, function () { paused = true; });
      });
      ["pointerleave", "focusout"].forEach(function (evt) {
        rotator.addEventListener(evt, function () { paused = false; });
      });
      document.addEventListener("visibilitychange", function () { paused = document.hidden; });
    }
  }

  // Why-right-point rail: dragging and keyboard scrolling are native (overflow +
  // scroll-snap), so this only adds the buttons, the meter and the disabled ends.
  var rail = document.querySelector("[data-rail]");
  if (rail) {
    var meter = document.querySelector("[data-rail-meter]");
    var prevBtn = document.querySelector("[data-rail-prev]");
    var nextBtn = document.querySelector("[data-rail-next]");
    var controls = document.querySelector(".rail-controls");
    var meterTrack = meter ? meter.parentNode : null;
    var curOut = document.querySelector("[data-rail-cur]");
    var totalOut = document.querySelector("[data-rail-total]");
    var cardCount = rail.querySelectorAll(".why-card").length;
    var calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function pad(n) { return (n < 10 ? "0" : "") + n; }

    function stepWidth() {
      var first = rail.querySelector(".why-card");
      if (!first) return rail.clientWidth;
      var gap = parseFloat(window.getComputedStyle(rail).columnGap) || 0;
      return first.getBoundingClientRect().width + gap;
    }

    function sync() {
      var max = rail.scrollWidth - rail.clientWidth;
      var fits = max <= 2;
      var pos = fits ? 0 : rail.scrollLeft / max;
      if (meter) {
        meter.style.setProperty("--rail-frac", (rail.clientWidth / rail.scrollWidth).toFixed(4));
        meter.style.setProperty("--rail-pos", pos.toFixed(4));
      }
      if (curOut) curOut.textContent = pad(Math.min(cardCount, Math.round(rail.scrollLeft / stepWidth()) + 1));
      if (controls) controls.hidden = fits;
      if (meterTrack) meterTrack.hidden = fits;
      if (prevBtn) prevBtn.disabled = rail.scrollLeft <= 2;
      if (nextBtn) nextBtn.disabled = rail.scrollLeft >= max - 2;
    }

    function slide(direction) {
      rail.scrollBy({ left: direction * stepWidth(), behavior: calm ? "auto" : "smooth" });
    }
    if (totalOut) totalOut.textContent = pad(cardCount);
    if (prevBtn) prevBtn.addEventListener("click", function () { slide(-1); });
    if (nextBtn) nextBtn.addEventListener("click", function () { slide(1); });
    rail.addEventListener("scroll", sync, { passive: true });
    window.addEventListener("resize", sync);
    sync();
  }

  // Sort control: a select that submits itself, with the Apply button left in the
  // markup so the form still works before this runs.
  document.querySelectorAll("[data-autosubmit]").forEach(function (select) {
    select.addEventListener("change", function () {
      if (select.form) select.form.submit();
    });
  });

  // Quote list. Every control is a real POST + redirect form; this layer only swaps
  // the response for a fragment repaint and slides the drawer over the page. Browsers
  // without fetch keep the reload path untouched.
  var drawer = document.querySelector("[data-basket-drawer]");
  if (drawer && window.fetch && window.FormData && Element.prototype.closest) {
    var scrim = document.querySelector("[data-basket-scrim]");
    var openers = document.querySelectorAll("[data-basket-open]");
    var lastFocus = null;

    function all(selector) {
      return Array.prototype.slice.call(document.querySelectorAll(selector));
    }

    function focusables() {
      return all('#basket-drawer a[href], #basket-drawer button:not([disabled]), #basket-drawer input:not([disabled]), #basket-drawer select:not([disabled])');
    }

    function setOpen(open) {
      drawer.classList.toggle("is-open", open);
      if (scrim) scrim.classList.toggle("is-open", open);
      drawer.setAttribute("aria-hidden", open ? "false" : "true");
      document.body.classList.toggle("has-basket-drawer", open);
      all("[data-basket-open]").forEach(function (trigger) {
        trigger.setAttribute("aria-expanded", open ? "true" : "false");
      });
      if (open) {
        lastFocus = document.activeElement;
        var first = drawer.querySelector("[data-basket-close]");
        if (first) first.focus();
      } else if (lastFocus && lastFocus.focus) {
        lastFocus.focus();
        lastFocus = null;
      }
    }

    openers.forEach(function (trigger) {
      trigger.addEventListener("click", function (event) {
        event.preventDefault();
        setOpen(true);
      });
    });
    drawer.querySelectorAll("[data-basket-close]").forEach(function (button) {
      button.addEventListener("click", function () { setOpen(false); });
    });
    if (scrim) scrim.addEventListener("click", function () { setOpen(false); });
    document.addEventListener("keydown", function (event) {
      if (!drawer.classList.contains("is-open")) return;
      if (event.key === "Escape") {
        setOpen(false);
        return;
      }
      if (event.key !== "Tab") return;
      var items = focusables();
      if (!items.length) return;
      var first = items[0];
      var last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    });

    function notify(text, kind) {
      var stack = document.querySelector(".flash-stack");
      if (!stack) {
        stack = document.createElement("div");
        stack.className = "flash-stack";
        stack.setAttribute("role", "status");
        var main = document.getElementById("main");
        if (main) main.insertBefore(stack, main.firstChild);
      }
      var note = document.createElement("p");
      note.className = "flash" + (kind ? " flash-" + kind : "");
      note.textContent = text;
      stack.appendChild(note);
      window.setTimeout(function () { note.remove(); }, 5200);
    }

    function repaint(state) {
      // The basket page renders the same panel inline next to the enquiry form, so
      // every copy is swapped at once and the two never disagree.
      all("[data-basket-panel]").forEach(function (target) { target.innerHTML = state.html; });
      all("[data-basket-count]").forEach(function (el) { el.textContent = state.distinct; });
      all("[data-basket-units]").forEach(function (el) { el.textContent = state.count; });
      all(".basket-badge").forEach(function (badge) {
        badge.hidden = state.distinct === 0;
        badge.classList.remove("bump");
        // Reflow so the same animation replays on the next add.
        void badge.offsetWidth;
        badge.classList.add("bump");
      });
      var onList = {};
      (state.slugs || []).forEach(function (slug) { onList[slug] = true; });
      all(".product-card").forEach(function (card) {
        var slug = card.getAttribute("data-basket-slug");
        if (slug) card.classList.toggle("is-on-list", !!onList[slug]);
      });
      all("[data-basket-rail-block]").forEach(function (block) { block.hidden = state.distinct === 0; });
    }

    function confirmClear(form) {
      return window.confirm("Empty your whole list? The products stay in the catalogue.");
    }

    document.addEventListener("submit", function (event) {
      var form = event.target.closest ? event.target.closest("[data-basket-form]") : null;
      if (!form) return;
      if (form.hasAttribute("data-basket-clear") && !confirmClear(form)) {
        event.preventDefault();
        return;
      }
      event.preventDefault();
      var button = form.querySelector("[data-basket-submit]");
      var label = button && button.querySelector("[data-basket-add-label]");
      var original = label ? label.textContent : "";
      if (button) button.setAttribute("aria-busy", "true");

      fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { "X-Requested-With": "XMLHttpRequest" },
        credentials: "same-origin"
      })
        .then(function (response) {
          return response.json().then(function (state) {
            return { ok: response.ok, state: state };
          });
        })
        .then(function (result) {
          if (button) button.removeAttribute("aria-busy");
          if (!result.ok) {
            notify(result.state.error || "That change did not take. Try again.", "error");
            return;
          }
          repaint(result.state);
          if (label) {
            label.textContent = "Added";
            if (button) button.classList.add("is-done");
            window.setTimeout(function () {
              label.textContent = original;
              if (button) button.classList.remove("is-done");
            }, 1400);
          }
        })
        .catch(function () {
          if (button) button.removeAttribute("aria-busy");
          notify("The list could not be updated right now.", "error");
        });
    });

    // Quantity steppers on the shelf cards and product page; the drawer's steppers are
    // real forms and never reach this.
    document.addEventListener("click", function (event) {
      var step = event.target.closest ? event.target.closest("[data-qty-step]") : null;
      if (!step || !step.form) return;
      event.preventDefault();
      var input = step.form.querySelector(".qty-input");
      if (!input) return;
      var delta = parseInt(step.getAttribute("data-qty-step"), 10) || 0;
      var next = (parseInt(input.value, 10) || 1) + delta;
      if (next < parseInt(input.min || "1", 10)) next = parseInt(input.min || "1", 10);
      if (next > parseInt(input.max || "99", 10)) next = parseInt(input.max || "99", 10);
      input.value = next;
    });
  }

  document.querySelectorAll(".flash-stack .flash").forEach(function (flash) {
    window.setTimeout(function () {
      flash.style.transition = "opacity .4s ease, transform .4s ease";
      flash.style.opacity = "0";
      flash.style.transform = "translateY(-8px)";
      window.setTimeout(function () { flash.remove(); }, 450);
    }, 5200);
  });

  // Keep the sticky header from covering anchor targets when navigating by hash.
  if (header) {
    document.querySelectorAll('a[href*="#"]').forEach(function (link) {
      link.addEventListener("click", function (event) {
        var href = link.getAttribute("href");
        if (!href || href === "#") return;
        var parts = href.split("#");
        var id = parts[1];
        if (!id) return;
        // If the link points to a hash on another page, let normal navigation happen
        if (parts[0] && parts[0] !== window.location.pathname && parts[0] !== "") return;
        var target = document.getElementById(id);
        if (target) {
          event.preventDefault();
          var offset = target.getBoundingClientRect().top + window.scrollY - header.offsetHeight - 16;
          window.scrollTo({ top: Math.max(0, offset), behavior: "smooth" });
          if (history.pushState) {
            history.pushState(null, null, "#" + id);
          }
        }
      });
    });
  }
})();
