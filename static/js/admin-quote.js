/* Quote builder helpers for the Django admin quote form:
   - picking a catalogue product fills its description and selling price
   - line totals and the quote summary recalculate as you type */
(function () {
  "use strict";

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function () {
    var live = document.querySelector("[data-quote-live]");
    if (!live) return;
    var infoUrl = live.getAttribute("data-info-url"); // ends in /0/

    function num(value) {
      var n = parseFloat(String(value || "").replace(/,/g, ""));
      return isNaN(n) ? 0 : n;
    }
    function kes(n) {
      return "KES " + n.toLocaleString("en-KE", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    function field(row, name) {
      return row.querySelector('[name$="-' + name + '"]');
    }
    function rows() {
      return Array.prototype.filter.call(
        document.querySelectorAll("#lines-group tr.form-row"),
        function (row) { return !row.classList.contains("empty-form") && field(row, "quantity"); }
      );
    }

    function recalc() {
      var subtotal = 0;
      var taxableSubtotal = 0;
      rows().forEach(function (row) {
        var del = field(row, "DELETE");
        var qty = num(field(row, "quantity").value);
        var price = num(field(row, "unit_price").value);
        var disc = num(field(row, "discount_percent").value);
        var total = qty * price * (100 - disc) / 100;
        var cell = row.querySelector("td.field-total p, td.field-total");
        if (cell) cell.textContent = kes(total);
        if (!(del && del.checked)) {
          subtotal += total;
          var taxedBox = field(row, "taxed");
          if (!taxedBox || taxedBox.checked) taxableSubtotal += total;
        }
      });
      var discountRate = num((document.getElementById("id_discount_percent") || {}).value) / 100;
      var discount = subtotal * discountRate;
      var net = subtotal - discount;
      var vatBox = document.getElementById("id_apply_vat");
      var vatRate = document.getElementById("id_vat_rate");
      var charge = !vatBox || vatBox.checked;
      if (vatRate) {
        vatRate.readOnly = !charge;
        vatRate.style.opacity = charge ? "" : "0.45";
      }
      var taxableNet = taxableSubtotal * (1 - discountRate);
      var vat = charge ? taxableNet * num((vatRate || {}).value) / 100 : 0;
      var vatLabel = live.querySelector('[data-live="vat"]').previousElementSibling;
      if (vatLabel) vatLabel.textContent = charge ? "VAT" : "VAT (not charged)";
      live.querySelector('[data-live="subtotal"]').textContent = kes(subtotal);
      live.querySelector('[data-live="discount"]').textContent = discount ? "- " + kes(discount) : kes(0);
      live.querySelector('[data-live="vat"]').textContent = kes(vat);
      live.querySelector('[data-live="total"]').textContent = kes(net + vat);
    }

    function fillFromProduct(select) {
      var row = select.closest("tr");
      if (!row || !select.value) return;
      fetch(infoUrl.replace(/0\/$/, select.value + "/"), { credentials: "same-origin" })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (data) {
          if (!data) return;
          var desc = field(row, "description");
          var price = field(row, "unit_price");
          if (desc && !desc.value) desc.value = data.title;
          if (price && (!num(price.value) || price.dataset.autofilled === "1")) {
            price.value = data.unit_price;
            price.dataset.autofilled = "1";
          }
          var hint = row.querySelector(".stock-hint");
          if (!hint) {
            hint = document.createElement("div");
            hint.className = "stock-hint";
            select.parentNode.appendChild(hint);
          }
          hint.textContent = (data.sku ? "SKU " + data.sku + " · " : "") + data.stock_on_hand + " in stock";
          hint.classList.toggle("is-low", data.stock_on_hand <= 0);
          recalc();
        });
    }

    document.addEventListener("input", function (event) {
      if (event.target.matches('[name$="-unit_price"]')) event.target.dataset.autofilled = "0";
      if (event.target.matches("input")) recalc();
    });
    document.addEventListener("change", function (event) {
      // Re-run recalc on any change, including the taxed checkbox
      recalc();
    });

    // Product pickers are select2 widgets driven by Django's bundled jQuery.
    if (window.django && window.django.jQuery) {
      window.django.jQuery(document).on("change", 'select[name$="-product"]', function () {
        fillFromProduct(this);
      });
      window.django.jQuery(document).on("formset:added", recalc);
    }
    recalc();
  });
})();
