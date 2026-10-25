// /register?ref=DAL25 attaches the code to the student's Stripe payment as its client reference ID.
(function () {
  var link = document.querySelector("a[data-pay-link]");
  if (!link) return;
  var ref = new URLSearchParams(window.location.search).get("ref") || "";
  if (!/^[A-Za-z0-9_-]{1,40}$/.test(ref)) return; // Stripe accepts letters, numbers, dashes and underscores
  var url = new URL(link.href);
  url.searchParams.set("client_reference_id", ref.toUpperCase());
  link.href = url.toString();
})();
