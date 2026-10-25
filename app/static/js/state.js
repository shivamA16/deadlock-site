// Decides whether registration is open, using the dates baked into <html> at build time.
// Loaded in <head> so the right message shows before the page paints.
(function () {
  var root = document.documentElement;
  var override = root.getAttribute("data-override");
  var state = "open";
  if (override === "open" || override === "closed") {
    state = override;
  } else {
    var now = Date.now();
    var opens = Date.parse(root.getAttribute("data-opens"));
    var closes = Date.parse(root.getAttribute("data-closes"));
    if (now < opens) state = "not_open";
    else if (now > closes) state = "closed";
  }
  root.setAttribute("data-reg", state);
})();
