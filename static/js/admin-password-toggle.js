/* Adds a Show/Hide control beside every password field in the admin: the login
   page, "add user" (two fields) and the password change form.

   Loaded from templates/admin/base_site.html rather than a ModelAdmin Media,
   because the login page has no ModelAdmin to hang it on. The input is wrapped
   in a positioned span so the button tracks the field it belongs to - the
   admin's own row markup differs between the login <p> and a change-form
   .form-row, and anchoring to the row would put the control at the wrong
   height on one of them. */
(function () {
  "use strict";

  function attach(input) {
    var wrap = document.createElement("span");
    wrap.className = "rps-pw";
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);

    var button = document.createElement("button");
    button.type = "button";
    button.className = "rps-pw-toggle";
    button.textContent = "Show";
    button.setAttribute("aria-pressed", "false");
    button.addEventListener("click", function () {
      var shown = input.type === "text";
      input.type = shown ? "password" : "text";
      button.textContent = shown ? "Show" : "Hide";
      button.setAttribute("aria-pressed", String(!shown));
      input.focus();
    });
    wrap.appendChild(button);
  }

  document.addEventListener("DOMContentLoaded", function () {
    Array.prototype.forEach.call(
      document.querySelectorAll('input[type="password"]:not([data-rps-pw])'),
      function (input) {
        input.setAttribute("data-rps-pw", "1");
        attach(input);
      }
    );
  });
})();
