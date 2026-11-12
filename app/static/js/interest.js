// The interest page sends people to the interest form only after they confirm the two checkboxes.
// The form's address is kept in data-href (not href) so it can't be followed before they do.
// /register?ref=DAL25 also passes the code on to the form as ?ref=DAL25 (for a hidden "ref" field).
(function () {
  var button = document.querySelector("button[data-interest-link]");
  if (!button) return;
  var boxes = document.querySelectorAll("input[data-consent]");
  var target = button.getAttribute("data-href") || "";

  function destination() {
    var url = new URL(target);
    var ref = new URLSearchParams(window.location.search).get("ref") || "";
    if (/^[A-Za-z0-9_-]{1,40}$/.test(ref)) url.searchParams.set("ref", ref.toUpperCase());
    return url.toString();
  }

  function update() {
    var ready = target !== "";
    for (var i = 0; i < boxes.length; i++) if (!boxes[i].checked) ready = false;
    button.disabled = !ready;
  }

  for (var i = 0; i < boxes.length; i++) boxes[i].addEventListener("change", update);
  button.addEventListener("click", function () {
    if (!button.disabled) window.location.assign(destination());
  });
  update();
})();
