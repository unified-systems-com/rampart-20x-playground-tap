/* rampart_countdown (req-rampart-20x-playground-page-reporting-10): the whole days left until a date.
 *
 * The server renders the target date (YYYY-MM-DD) as the text of each [data-rampart-countdown] element, so the page is
 * correct with no script. This file, served as an external static file, replaces that text with the whole days from now
 * to 00:00 UTC of the date, floored. On the date itself it shows 0; after it, "Passed". Anything it cannot read, it leaves
 * as the date. It writes textContent only, never markup, and reads no network.
 */
(function () {
  "use strict";

  var DAY_MS = 86400000;
  var DATE = /^(\d{4})-(\d{2})-(\d{2})$/;

  // Whole days from `now` (ms) to 00:00 UTC of `iso`; null for anything that is not a real calendar date.
  function daysUntil(iso, now) {
    var m = DATE.exec(iso || "");
    if (!m) return null;
    var y = +m[1], mo = +m[2], d = +m[3];
    var at = Date.UTC(y, mo - 1, d);
    var back = new Date(at);
    if (back.getUTCFullYear() !== y || back.getUTCMonth() !== mo - 1 || back.getUTCDate() !== d) return null;
    var days = Math.floor((at - now) / DAY_MS);
    if (days >= 0) return String(days);
    return now < at + DAY_MS ? "0" : "Passed";
  }

  function run(root) {
    var scope = root && root.querySelectorAll ? root : document;
    var nodes = scope.querySelectorAll("[data-rampart-countdown]");
    var now = Date.now();
    for (var i = 0; i < nodes.length; i++) {
      var text = daysUntil(nodes[i].getAttribute("data-rampart-countdown"), now);
      if (text !== null) nodes[i].textContent = text;
    }
  }

  window.RampartCountdown = { daysUntil: daysUntil, render: run };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { run(document); });
  } else {
    run(document);
  }
  // Panels arrive by HTMX swap.
  document.addEventListener("htmx:afterSettle", function (evt) { run(evt.target || document); });
})();
