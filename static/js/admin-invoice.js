/* Invoice builder helpers for the Django admin:
   - line totals recalculate as you type
   - summary panel updates live */
(function () {
  "use strict";

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function () {
    var totals = document.querySelector("[data-invoice-totals]");
    if (!totals) return;

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
        var total = qty * price;
        var cell = row.querySelector("td.field-total p, td.field-total");
        if (cell) cell.textContent = kes(total);
        if (!(del && del.checked)) {
          subtotal += total;
          var taxedBox = field(row, "taxed");
          if (!taxedBox || taxedBox.checked) taxableSubtotal += total;
        }
      });
      var discount = num((document.getElementById("id_discount_amount") || {}).value);
      var net = subtotal - discount;
      var vatBox = document.getElementById("id_apply_vat");
      var vatRate = document.getElementById("id_vat_rate");
      var charge = !vatBox || vatBox.checked;
      if (vatRate) { vatRate.readOnly = !charge; vatRate.style.opacity = charge ? "" : "0.45"; }
      var taxableNet = subtotal ? taxableSubtotal * (1 - discount / subtotal) : taxableSubtotal;
      var vat = charge ? taxableNet * num((vatRate || {}).value) / 100 : 0;

      // Update the read-only totals table cells by row index
      var trs = totals.querySelectorAll("tr");
      // Row 0: Subtotal, Row 1: Discount, Row 2: Net, Row 3: VAT, Row 4: Grand
      function setRow(tr, val) {
        if (!tr) return;
        var td = tr.querySelectorAll("td");
        if (td.length >= 2) td[1].textContent = kes(Math.abs(val));
      }
      if (trs[0]) setRow(trs[0], subtotal);
      if (trs[1]) { var discTd = trs[1].querySelectorAll("td"); if (discTd.length >= 2) discTd[1].textContent = discount ? "- " + kes(discount) : kes(0); }
      if (trs[2]) setRow(trs[2], net);
      if (trs[3]) setRow(trs[3], vat);
      if (trs[4]) setRow(trs[4], net + vat);
    }

    document.addEventListener("input", function (e) {
      if (e.target.matches("input")) recalc();
    });
    document.addEventListener("change", recalc);

    if (window.django && window.django.jQuery) {
      window.django.jQuery(document).on("formset:added", recalc);
    }
    recalc();
  });
})();
