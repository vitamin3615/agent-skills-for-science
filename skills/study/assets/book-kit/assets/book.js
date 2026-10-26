/* AlphaGenome from the Ground Up: page behavior.
   Loads after MathJax, highlight.js and mermaid. Each widget is an IIFE. */

/* ---------- theme toggle: system -> light -> dark ---------- */
(function () {
  var root = document.documentElement;
  var btn = document.querySelector(".theme-toggle");
  var modes = ["system", "light", "dark"];
  var labels = { system: "Theme: auto", light: "Theme: light", dark: "Theme: dark" };

  function current() {
    var t = root.getAttribute("data-theme");
    return t === "light" || t === "dark" ? t : "system";
  }
  function apply(mode, save) {
    if (mode === "system") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", mode);
    if (btn) btn.textContent = labels[mode];
    if (save) {
      try { localStorage.setItem("ag-theme", mode); } catch (e) { /* storage blocked */ }
    }
    document.dispatchEvent(new CustomEvent("ag-theme", { detail: mode }));
  }

  if (btn) {
    btn.textContent = labels[current()];
    btn.addEventListener("click", function () {
      apply(modes[(modes.indexOf(current()) + 1) % modes.length], true);
    });
  }
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () {
    if (current() === "system") document.dispatchEvent(new CustomEvent("ag-theme", { detail: "system" }));
  });

  // print on a light ground whatever the viewer theme
  var held = null;
  window.addEventListener("beforeprint", function () {
    held = root.getAttribute("data-theme");
    root.setAttribute("data-theme", "light");
  });
  window.addEventListener("afterprint", function () {
    if (held) root.setAttribute("data-theme", held); else root.removeAttribute("data-theme");
  });
})();

/* ---------- model map: 11 nodes, 14 labeled edges ---------- */
(function () {
  var NS = "http://www.w3.org/2000/svg";
  var W = 128, H = 54;
  // SUBJECT-SPECIFIC: node layout and edge routes of the whole-subject map (keep ids, labels and edges identical to README).
  var NODES = {
    N1: { x: 70, y: 200, t: "1 Mb DNA + organism", ch: 1, d: "One-hot DNA of 1,048,576 bases plus an organism index (human or mouse)." },
    N2: { x: 300, y: 200, t: "Sequence encoder", ch: 2, d: "Convolution and pooling that shrink 1 bp positions to 128 bp tokens." },
    N3: { x: 540, y: 80, t: "Transformer tower", ch: 3, d: "Nine attention blocks (multi-query attention with RoPE) across 8,192 tokens." },
    N4: { x: 540, y: 320, t: "Pair representation", ch: 3, d: "A 2D map over 2,048 bp bins that is updated by the tower and biases its attention." },
    N5: { x: 770, y: 200, t: "Sequence decoder", ch: 2, d: "U-Net upsampling from 128 bp back to 1 bp, using encoder skips." },
    N6: { x: 980, y: 200, t: "Output embeddings", ch: 3, d: "Three embeddings: 1 bp, 128 bp and pair resolution." },
    N7: { x: 1200, y: 200, t: "Heads", ch: 4, d: "Linear readouts for tracks, splicing and contact maps." },
    N8: { x: 1200, y: 360, t: "Scaling + losses", ch: 4, d: "Target scaling and the loss that scores each head against its targets." },
    N9: { x: 1200, y: 520, t: "Training regime", ch: 5, d: "Pretraining on folds, then distillation into the all-folds model." },
    N10: { x: 940, y: 360, t: "Data", ch: 1, d: "TFRecord bundles of real tracks, split into cross-validation folds." },
    N11: { x: 1200, y: 60, t: "Evaluation + variants", ch: 5, d: "REF and ALT predictions are compared to score variants and evaluate the model." }
  };
  // pts: polyline in viewBox units; lab: [x, y, anchor, lines]
  var EDGES = [
    { a: "N1", b: "N2", l: "is downsampled by", pts: [[134, 200], [236, 200]], lab: [185, 176, "middle", ["is downsampled", "by"]] },
    { a: "N2", b: "N3", l: "feeds 128 bp tokens to", pts: [[300, 173], [300, 80], [476, 80]], lab: [388, 52, "middle", ["feeds 128 bp", "tokens to"]] },
    { a: "N3", b: "N4", l: "creates and updates", pts: [[510, 107], [510, 293]], lab: [502, 196, "end", ["creates and", "updates"]] },
    { a: "N4", b: "N3", l: "biases attention logits of", pts: [[570, 293], [570, 107]], lab: [578, 190, "start", ["biases attention", "logits of"]] },
    { a: "N2", b: "N5", l: "supplies U-Net skips to", pts: [[300, 227], [300, 470], [770, 470], [770, 227]], lab: [535, 460, "middle", ["supplies U-Net skips to"]] },
    { a: "N3", b: "N5", l: "is upsampled by", pts: [[604, 94], [740, 94], [740, 173]], lab: [748, 140, "start", ["is upsampled by"]] },
    { a: "N3", b: "N6", l: "is projected into", pts: [[604, 66], [980, 66], [980, 173]], lab: [800, 56, "middle", ["is projected into"]] },
    { a: "N4", b: "N6", l: "is symmetrized into", pts: [[604, 305], [980, 305], [980, 227]], lab: [872, 297, "middle", ["is symmetrized into"]] },
    { a: "N5", b: "N6", l: "is projected into", pts: [[834, 200], [916, 200]], lab: [875, 176, "middle", ["is projected", "into"]] },
    { a: "N6", b: "N7", l: "is read out linearly by", pts: [[1044, 200], [1136, 200]], lab: [1090, 176, "middle", ["is read out", "linearly by"]] },
    { a: "N7", b: "N8", l: "is scored against scaled targets by", pts: [[1200, 227], [1200, 333]], lab: [1192, 275, "end", ["is scored against", "scaled targets by"]] },
    { a: "N10", b: "N8", l: "provides targets for", pts: [[1004, 360], [1136, 360]], lab: [1070, 335, "middle", ["provides", "targets for"]] },
    { a: "N8", b: "N9", l: "gradients define", pts: [[1200, 387], [1200, 493]], lab: [1192, 443, "end", ["gradients define"]] },
    { a: "N7", b: "N11", l: "REF vs ALT outputs are compared by", pts: [[1200, 173], [1200, 87]], lab: [1192, 118, "end", ["REF vs ALT outputs", "are compared by"]] }
  ];

  function el(tag, attrs, parent) {
    var n = document.createElementNS(NS, tag);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }

  document.querySelectorAll(".ag-map").forEach(function (box) {
    var hl = (box.dataset.highlight || "").split(",").map(function (s) { return s.trim(); }).filter(Boolean);
    var links = {};
    try { links = JSON.parse(box.dataset.links || "{}"); } catch (e) { links = {}; }

    var scroll = document.createElement("div");
    scroll.className = "ag-map__scroll";
    var svg = el("svg", { viewBox: "0 0 1270 560", role: "group", "aria-label": "Map of the whole AlphaGenome model" }, scroll);
    var defs = el("defs", {}, svg);
    var mk = el("marker", { id: "arrow", viewBox: "0 0 10 10", refX: "9", refY: "5", markerWidth: "7", markerHeight: "7", orient: "auto-start-reverse" }, defs);
    el("path", { d: "M0,0 L10,5 L0,10 z", "class": "arrow" }, mk);

    EDGES.forEach(function (e) {
      var g = el("g", {}, svg);
      var d = e.pts.map(function (p, i) { return (i ? "L" : "M") + p[0] + "," + p[1]; }).join(" ");
      el("path", { d: d, "class": "edge", "marker-end": "url(#arrow)" }, g);
      var t = el("text", { x: e.lab[0], y: e.lab[1], "text-anchor": e.lab[2], "class": "elabel" }, g);
      e.lab[3].forEach(function (line, i) {
        var ts = el("tspan", { x: e.lab[0], dy: i ? "1.15em" : "0" }, t);
        ts.textContent = line;
      });
    });

    var tip = document.createElement("div");
    tip.className = "ag-map__tip";
    tip.setAttribute("role", "tooltip");
    tip.hidden = true;

    function show(g, id) {
      var n = NODES[id];
      tip.textContent = id + " · " + n.d + " (Chapter " + n.ch + ")";
      tip.hidden = false;
      var b = box.getBoundingClientRect(), r = g.getBoundingClientRect();
      var left = r.left - b.left + r.width / 2 - tip.offsetWidth / 2;
      left = Math.max(0, Math.min(left, b.width - tip.offsetWidth));
      var top = r.top - b.top - tip.offsetHeight - 8;
      if (top < 0) top = r.bottom - b.top + 8;
      tip.style.left = left + "px";
      tip.style.top = top + "px";
    }

    Object.keys(NODES).forEach(function (id) {
      var n = NODES[id];
      var link = links[id];
      var g = el("g", { "class": "node" + (hl.indexOf(id) >= 0 ? " hl" : "") + (link ? " link" : ""), tabindex: "0", "data-id": id, "aria-label": id + ": " + n.t + ". " + n.d }, svg);
      if (link) g.setAttribute("role", "link"); else g.setAttribute("role", "img");
      el("rect", { x: n.x - W / 2, y: n.y - H / 2, width: W, height: H, rx: 6 }, g);
      el("text", { x: n.x, y: n.y - 6, "text-anchor": "middle", "class": "nid" }, g).textContent = id;
      el("text", { x: n.x, y: n.y + 13, "text-anchor": "middle", "class": "ntitle" }, g).textContent = n.t;
      g.addEventListener("mouseenter", function () { show(g, id); });
      g.addEventListener("focus", function () { show(g, id); });
      g.addEventListener("mouseleave", function () { tip.hidden = true; });
      g.addEventListener("blur", function () { tip.hidden = true; });
      if (link) {
        g.addEventListener("click", function () { window.location.href = link; });
        g.addEventListener("keydown", function (ev) { if (ev.key === "Enter") window.location.href = link; });
      }
    });

    var text = document.createElement("details");
    text.className = "ag-map__text";
    var sum = document.createElement("summary");
    sum.textContent = "Read the map as sentences";
    var ul = document.createElement("ul");
    EDGES.forEach(function (e) {
      var li = document.createElement("li");
      li.textContent = e.a + " (" + NODES[e.a].t + ") " + e.l + " " + e.b + " (" + NODES[e.b].t + ").";
      ul.appendChild(li);
    });
    text.appendChild(sum);
    text.appendChild(ul);

    box.textContent = "";
    box.appendChild(scroll);
    box.appendChild(tip);
    box.appendChild(text);
  });
})();

/* ---------- predict boxes: answers saved per viewer ---------- */
(function () {
  document.querySelectorAll(".predict textarea").forEach(function (ta) {
    var key = "ag-predict-" + ta.id;
    try {
      var saved = localStorage.getItem(key);
      if (saved) ta.value = saved;
    } catch (e) { /* storage blocked */ }
    ta.addEventListener("input", function () {
      try { localStorage.setItem(key, ta.value); } catch (e) { /* storage blocked */ }
    });
  });
})();

/* ---------- code: raw copy text, highlight, #n badges, copy buttons ---------- */
(function () {
  var BADGE = /#(\d+)\s*$/;

  function badge(n) {
    var b = document.createElement("span");
    b.className = "badge";
    b.textContent = n;
    b.setAttribute("aria-label", "note " + n);
    return b;
  }

  // turn a trailing "#n" inside a highlighted comment into a circled number
  function badges(code) {
    code.querySelectorAll(".hljs-comment").forEach(function (c) {
      var m = BADGE.exec(c.textContent);
      if (!m) return;
      var last = c.lastChild;
      while (last && last.nodeType !== 3) last = last.lastChild;
      if (!last) return;
      last.nodeValue = last.nodeValue.replace(BADGE, "");
      if (!c.textContent.replace(/^#\s*/, "").trim()) c.textContent = "";
      c.appendChild(badge(m[1]));
    });
  }

  function highlight(code) {
    if (code.dataset.done) return;
    code.dataset.done = "1";
    if (!window.hljs || !/language-(python|bash)/.test(code.className)) return;
    window.hljs.highlightElement(code);
    badges(code);
  }

  document.querySelectorAll("pre > code").forEach(function (code) {
    var box = code.parentNode.parentNode;
    if (box.classList.contains("codebox")) {
      code.parentNode.dataset.raw = code.textContent;
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "copy";
      btn.textContent = "Copy";
      btn.setAttribute("aria-label", "Copy code");
      btn.addEventListener("click", function () {
        var raw = code.parentNode.dataset.raw;
        function done() {
          btn.textContent = "Copied";
          btn.classList.add("done");
          setTimeout(function () { btn.textContent = "Copy"; btn.classList.remove("done"); }, 1400);
        }
        if (navigator.clipboard && window.isSecureContext) {
          navigator.clipboard.writeText(raw).then(done, fallback);
        } else {
          fallback();
        }
        function fallback() {
          var ta = document.createElement("textarea");
          ta.value = raw;
          ta.style.position = "fixed";
          ta.style.opacity = "0";
          document.body.appendChild(ta);
          ta.select();
          try { document.execCommand("copy"); done(); } catch (e) { btn.textContent = "Press Ctrl+C"; }
          document.body.removeChild(ta);
        }
      });
      box.appendChild(btn);
    }
    var file = code.closest("details.code-file");
    if (file && !file.open) {
      file.addEventListener("toggle", function () { highlight(code); }, { once: true });
    } else {
      highlight(code);
    }
  });
  window.addEventListener("beforeprint", function () {
    document.querySelectorAll("pre > code").forEach(highlight);
  });
})();

/* ---------- contents rail: collapse on narrow screens, scrollspy ---------- */
(function () {
  var toc = document.querySelector(".toc");
  if (!toc) return;
  var mq = window.matchMedia("(max-width: 900px)");
  function sync() { toc.open = !mq.matches; }
  sync();
  mq.addEventListener("change", sync);

  var links = {};
  toc.querySelectorAll("a[href^='#']").forEach(function (a) { links[a.getAttribute("href").slice(1)] = a; });
  var heads = Array.prototype.slice.call(document.querySelectorAll(".main h2[id], .main h3[id]")).filter(function (h) { return links[h.id]; });
  if (!heads.length || !("IntersectionObserver" in window)) return;
  var seen = {};
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) { seen[e.target.id] = e.isIntersecting; });
    var first = heads.find(function (h) { return seen[h.id]; });
    if (!first) return;
    Object.keys(links).forEach(function (id) { links[id].classList.toggle("active", id === first.id); });
  }, { rootMargin: "-10% 0px -70% 0px" });
  heads.forEach(function (h) { io.observe(h); });
})();

/* ---------- mermaid: tokens as theme variables, re-render on theme change ---------- */
(function () {
  var blocks = Array.prototype.slice.call(document.querySelectorAll("pre.mermaid"));
  if (!blocks.length || !window.mermaid) return;
  blocks.forEach(function (b) { b.dataset.src = b.textContent; });
  var count = 0;

  function token(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }
  function init() {
    window.mermaid.initialize({
      startOnLoad: false,
      theme: "base",
      securityLevel: "strict",
      themeVariables: {
        background: token("--paper"),
        primaryColor: token("--panel"),
        primaryTextColor: token("--ink"),
        primaryBorderColor: token("--accent"),
        lineColor: token("--muted"),
        secondaryColor: token("--panel"),
        tertiaryColor: token("--paper"),
        edgeLabelBackground: token("--paper"),
        clusterBkg: token("--paper"),
        clusterBorder: token("--rule"),
        titleColor: token("--ink"),
        fontFamily: token("--f-display")
      }
    });
  }
  function render() {
    init();
    return Promise.all(blocks.map(function (b) {
      return window.mermaid.render("mmd" + (count++), b.dataset.src).then(function (r) {
        b.innerHTML = r.svg;
        b.dataset.rendered = "1";
      }).catch(function (err) {
        b.textContent = b.dataset.src;
        console.error("mermaid failed", err);
      });
    }));
  }
  window.agMermaid = render();
  document.addEventListener("ag-theme", function () { window.agMermaid = render(); });
})();

/* ---------- reading progress: resume point and furthest read, saved per viewer ---------- */
(function () {
  // one record per book folder, so books opened from disk never share it
  var KEY = "ag-progress:" + document.currentScript.src.replace(/assets\/book\.js.*$/, "");
  var main = document.querySelector(".main");
  if (!main) return;

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) || { pages: {} }; } catch (e) { return null; }
  }
  var data = load();
  if (!data) return;

  var num = main.querySelector(".opener__num");
  if (num) {
    // chapter page: save on scroll, offer a jump back to the saved reading position
    var page = location.pathname.split("/").pop();
    var label = num.textContent.trim() + " · " + main.querySelector(".opener__title").textContent.trim();
    var heads = Array.prototype.slice.call(main.querySelectorAll("h2[id], h3[id]"));
    var saved = data.pages[page];
    var pill = null;

    // the reading line sits a quarter down the viewport; its section is the last heading above it
    function line() { return window.innerHeight * 0.25; }
    function current() {
      var cur = null;
      heads.forEach(function (h) { if (h.getBoundingClientRect().top < line()) cur = h; });
      return cur;
    }
    function bounds(h) {
      // page offsets where section h starts and where the next heading (or the page) ends it
      var next = heads[heads.indexOf(h) + 1];
      return [h.getBoundingClientRect().top + window.scrollY,
        next ? next.getBoundingClientRect().top + window.scrollY : document.documentElement.scrollHeight];
    }
    function resume() {
      // put the reading line back at the same fraction of the saved section, which survives
      // reflow at another window width and rebuilds that change other sections
      var b = bounds(document.getElementById(saved.id));
      window.scrollTo({ top: b[0] + (saved.frac || 0) * (b[1] - b[0]) - line() });
    }
    function save() {
      // MathJax and mermaid move the layout until ready; positions read before then are wrong
      if (!document.documentElement.dataset.ready) return;
      var span = document.documentElement.scrollHeight - window.innerHeight;
      var pct = span > 0 ? Math.min(1, window.scrollY / span) : 1;
      var cur = current();
      var frac = 0;
      if (cur) {
        var b = bounds(cur);
        frac = Math.min(1, (window.scrollY + line() - b[0]) / (b[1] - b[0]));
      }
      var d = load() || { pages: {} };
      var max = Math.max((d.pages[page] || {}).max || 0, pct);
      d.pages[page] = { id: cur ? cur.id : "", sec: cur ? cur.textContent.trim() : "", frac: frac, pct: pct, max: max };
      d.last = { page: page, label: label, id: d.pages[page].id, sec: d.pages[page].sec };
      try { localStorage.setItem(KEY, JSON.stringify(d)); } catch (e) { /* storage blocked */ }
      if (pill && cur && cur.id === saved.id) pill.hidden = true;
    }
    var timer;
    window.addEventListener("scroll", function () { clearTimeout(timer); timer = setTimeout(save, 400); }, { passive: true });

    var found = saved && saved.id && document.getElementById(saved.id);
    if (found && location.hash === "#resume") {
      // the index's Continue link: go straight to the saved position, then drop the hash
      history.replaceState(null, "", location.pathname + location.search);
      document.addEventListener("DOMContentLoaded", function () { window.agReady.then(resume); });
    } else if (found && saved.pct > 0.02) {
      pill = document.createElement("div");
      pill.className = "resume";
      var a = document.createElement("a");
      a.href = "#" + saved.id;
      a.textContent = "Resume at ";
      var b = document.createElement("b");
      b.textContent = saved.sec;
      a.appendChild(b);
      a.addEventListener("click", function (ev) {
        ev.preventDefault();
        pill.hidden = true;
        window.agReady.then(resume);
      });
      var x = document.createElement("button");
      x.type = "button";
      x.textContent = "×";
      x.setAttribute("aria-label", "Dismiss");
      x.addEventListener("click", function () { pill.hidden = true; });
      pill.appendChild(a);
      pill.appendChild(x);
      document.body.appendChild(pill);
    }
  } else if (main.querySelector(".opener--cover")) {
    // index: continue link plus furthest-read percent beside each chapter link
    if (data.last) {
      var p = document.createElement("p");
      p.className = "continue";
      p.appendChild(document.createTextNode("Continue reading: "));
      var link = document.createElement("a");
      link.href = data.last.page + (data.last.id ? "#resume" : "");
      link.textContent = data.last.label + (data.last.sec ? " › " + data.last.sec : "");
      p.appendChild(link);
      main.querySelector(".opener").appendChild(p);
    }
    main.querySelectorAll("td a[href]").forEach(function (a) {
      var rec = data.pages[a.getAttribute("href")];
      if (!rec) return;
      var tag = document.createElement("span");
      tag.className = "read-pct";
      tag.textContent = rec.max >= 0.98 ? "read" : Math.round(rec.max * 100) + "%";
      a.parentNode.appendChild(tag);
    });
  }
})();

/* ---------- ready flag (used by the screenshot script) ---------- */
(function () {
  var mj = window.MathJax && window.MathJax.startup ? window.MathJax.startup.promise : Promise.resolve();
  // fonts too: a late web font reflows the text, and resume positions are measured after ready
  window.agReady = Promise.all([mj, window.agMermaid || Promise.resolve(), document.fonts.ready]).then(function () {
    document.documentElement.dataset.ready = "1";
  });
})();

/* ---------- notes: highlight selected text and attach a note, saved per viewer ---------- */
(function () {
  var main = document.querySelector(".main");
  if (!main) return;
  var KEY = "ag-notes:" + document.currentScript.src.replace(/assets\/book\.js.*$/, "");
  var page = location.pathname.split("/").pop();
  var num = main.querySelector(".opener__num");
  var label = (num ? num.textContent.trim() + " · " : "") + main.querySelector(".opener__title").textContent.trim();
  var heads = Array.prototype.slice.call(main.querySelectorAll("h2[id], h3[id]"));
  var HL = window.CSS && CSS.highlights;
  // text that is not part of the reading (or is re-rendered) never anchors a note
  var SKIP = "script, style, textarea, svg, .mermaid, .copy, .ag-map__tip, .continue, .read-pct";
  var CTX = 32; // characters kept on each side of the quote to find it again after a rebuild
  var ranges = {}, pending = null, editing = null;

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch (e) { return []; }
  }
  function store(list) {
    try { localStorage.setItem(KEY, JSON.stringify(list)); } catch (e) { /* storage blocked */ }
  }
  function byId(id) { return load().find(function (n) { return n.id === id; }); }
  function flat(s) { return s.replace(/\s+/g, " ").trim(); }

  // create an element. tag: element name. cls: class name or "". text: text content or omitted.
  function make(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text) e.textContent = text;
    return e;
  }

  // all readable text of the page as one string plus the node where each piece starts
  function index() {
    var w = document.createTreeWalker(main, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) { return n.parentNode.closest(SKIP) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT; }
    });
    var ix = { nodes: [], starts: [], text: "" }, n;
    while ((n = w.nextNode())) {
      ix.nodes.push(n);
      ix.starts.push(ix.text.length);
      ix.text += n.data;
    }
    return ix;
  }

  // DOM boundary point (node, off) -> offset into ix.text
  function offset(ix, node, off) {
    var i = node.nodeType === 3 ? ix.nodes.indexOf(node) : -1;
    if (i >= 0) return ix.starts[i] + off;
    var r = document.createRange();
    r.setStart(node, off);
    for (i = 0; i < ix.nodes.length; i++) if (r.comparePoint(ix.nodes[i], 0) >= 0) return ix.starts[i];
    return ix.text.length;
  }

  // offset into ix.text -> [text node, offset]; end: true for the end of a range
  function point(ix, pos, end) {
    for (var i = 0; i < ix.nodes.length; i++) {
      var s = ix.starts[i], e = s + ix.nodes[i].data.length;
      if (end ? pos > s && pos <= e : pos >= s && pos < e) return [ix.nodes[i], pos - s];
    }
    var last = ix.nodes[ix.nodes.length - 1];
    return [last, last.data.length];
  }

  function rangeAt(ix, start, end) {
    var r = document.createRange(), a = point(ix, start, false), b = point(ix, end, true);
    r.setStart(a[0], a[1]);
    r.setEnd(b[0], b[1]);
    return r;
  }

  // where the quote is now: occurrences with matching context win, ties go to the one nearest its old offset
  function find(ix, n) {
    var best = -1, top = -Infinity, i = ix.text.indexOf(n.exact);
    while (i >= 0) {
      var score = (ix.text.slice(Math.max(0, i - n.prefix.length), i) === n.prefix ? 1 : 0) +
        (ix.text.substr(i + n.exact.length, n.suffix.length) === n.suffix ? 1 : 0) -
        Math.abs(i - n.pos) / (ix.text.length + 1);
      if (score > top) { top = score; best = i; }
      i = ix.text.indexOf(n.exact, i + 1);
    }
    return best;
  }

  function paint() {
    var ix = index();
    ranges = {};
    load().forEach(function (n) {
      if (n.page !== page) return;
      var i = find(ix, n);
      if (i >= 0) ranges[n.id] = rangeAt(ix, i, i + n.exact.length);
    });
    if (!HL) return;
    var h = new Highlight();
    Object.keys(ranges).forEach(function (id) { h.add(ranges[id]); });
    HL.set("ag-note", h);
  }

  // a selection -> unsaved note plus its range, or null when it holds no readable text
  function anchor(sel) {
    var ix = index();
    var s = offset(ix, sel.startContainer, sel.startOffset), e = offset(ix, sel.endContainer, sel.endOffset);
    var exact = ix.text.slice(s, e);
    if (!exact.trim()) return null;
    var sec = "";
    heads.forEach(function (h) { if (sel.comparePoint(h, 0) < 0) sec = h.textContent.trim(); });
    return {
      note: { page: page, label: label, sec: sec, exact: exact, prefix: ix.text.slice(Math.max(0, s - CTX), s), suffix: ix.text.slice(e, e + CTX), pos: s },
      range: rangeAt(ix, s, e)
    };
  }

  /* add button, shown under a selection */
  var add = make("button", "note-add", "Add note");
  add.type = "button";
  add.hidden = true;
  add.addEventListener("mousedown", function (ev) { ev.preventDefault(); }); // keep the selection
  add.addEventListener("click", function () {
    var p = pending;
    pending = null;
    add.hidden = true;
    open(p.note, p.range);
    window.getSelection().removeAllRanges();
  });
  document.body.appendChild(add);

  function check() {
    var sel = window.getSelection();
    var r = sel.rangeCount && !sel.isCollapsed ? sel.getRangeAt(0) : null;
    pending = r && main.contains(r.commonAncestorContainer) ? anchor(r) : null;
    if (!pending) { add.hidden = true; return; }
    var rects = r.getClientRects(), b = rects[rects.length - 1] || r.getBoundingClientRect();
    add.hidden = false;
    add.style.top = b.bottom + window.scrollY + 6 + "px";
    add.style.left = Math.max(16, Math.min(b.right - add.offsetWidth, document.documentElement.clientWidth - add.offsetWidth - 16)) + window.scrollX + "px";
  }
  var timer;
  document.addEventListener("selectionchange", function () { clearTimeout(timer); timer = setTimeout(check, 300); });

  /* note editor */
  var pop = make("div", "note-pop");
  pop.hidden = true;
  pop.setAttribute("role", "dialog");
  pop.setAttribute("aria-label", "Note");
  var quote = make("blockquote");
  var ta = make("textarea");
  ta.rows = 4;
  ta.placeholder = "Your note (Ctrl+Enter saves)";
  ta.setAttribute("aria-label", "Note text");
  var row = make("div", "note-pop__row");
  var save = make("button", "", "Save"), cancel = make("button", "", "Cancel"), del = make("button", "note-pop__del", "Delete");
  [save, cancel, del].forEach(function (b) { b.type = "button"; row.appendChild(b); });
  pop.appendChild(quote);
  pop.appendChild(ta);
  pop.appendChild(row);
  document.body.appendChild(pop);

  function open(note, range) {
    editing = note;
    quote.textContent = flat(note.exact);
    ta.value = note.text || "";
    del.hidden = !note.id;
    del.textContent = "Delete";
    delete del.dataset.armed;
    pop.hidden = false;
    var b = range.getBoundingClientRect();
    pop.style.top = b.bottom + window.scrollY + 8 + "px";
    pop.style.left = Math.max(16, Math.min(b.left, document.documentElement.clientWidth - pop.offsetWidth - 16)) + window.scrollX + "px";
    if (HL) HL.set("ag-note-active", new Highlight(range));
    ta.focus({ preventScroll: true });
    var pb = pop.getBoundingClientRect();
    if (pb.bottom > window.innerHeight) window.scrollBy({ top: pb.bottom - window.innerHeight + 16 });
  }
  function close() {
    pop.hidden = true;
    editing = null;
    if (HL) HL.delete("ag-note-active");
  }
  function changed() {
    close();
    paint();
    if (!panel.hidden) list();
  }

  save.addEventListener("click", function () {
    var notes = load(), now = new Date().toISOString();
    if (editing.id) {
      notes.forEach(function (n) { if (n.id === editing.id) { n.text = ta.value.trim(); n.time = now; } });
    } else {
      editing.id = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
      editing.text = ta.value.trim();
      editing.time = now;
      notes.push(editing);
    }
    store(notes);
    changed();
  });
  cancel.addEventListener("click", close);
  del.addEventListener("click", function () {
    if (!del.dataset.armed) { del.dataset.armed = "1"; del.textContent = "Click again to delete"; return; }
    var id = editing.id;
    store(load().filter(function (n) { return n.id !== id; }));
    changed();
  });
  ta.addEventListener("keydown", function (ev) {
    if (ev.key === "Enter" && (ev.ctrlKey || ev.metaKey)) save.click();
  });

  // a click on highlighted text opens its note
  main.addEventListener("click", function (ev) {
    if (!window.getSelection().isCollapsed) return;
    Object.keys(ranges).some(function (id) {
      var hit = Array.prototype.some.call(ranges[id].getClientRects(), function (b) {
        return ev.clientX >= b.left && ev.clientX <= b.right && ev.clientY >= b.top && ev.clientY <= b.bottom;
      });
      if (hit) open(byId(id), ranges[id]);
      return hit;
    });
  });

  /* notes panel: every note in the book, export and import */
  var toggle = make("button", "notes-toggle", "Notes");
  toggle.type = "button";
  toggle.setAttribute("aria-expanded", "false");
  var bar = document.querySelector(".theme-toggle");
  bar.parentNode.insertBefore(toggle, bar);

  var panel = make("aside", "notes-panel");
  panel.hidden = true;
  panel.setAttribute("aria-label", "Notes");
  var head = make("div", "notes-panel__head");
  head.appendChild(make("b", "", "Notes"));
  var exp = make("button", "", "Export"), imp = make("button", "", "Import"), shut = make("button", "", "×");
  shut.setAttribute("aria-label", "Close notes");
  [exp, imp, shut].forEach(function (b) { b.type = "button"; head.appendChild(b); });
  var status = make("p", "notes-panel__status", "Stored in this browser only. Export to keep a copy or to move notes to another browser.");
  var body = make("div", "notes-panel__list");
  var file = make("input");
  file.type = "file";
  file.accept = ".md";
  file.hidden = true;
  panel.appendChild(head);
  panel.appendChild(status);
  panel.appendChild(body);
  panel.appendChild(file);
  document.body.appendChild(panel);

  function sorted() {
    return load().sort(function (a, b) { return a.page < b.page ? -1 : a.page > b.page ? 1 : a.pos - b.pos; });
  }

  function jump(n) {
    var r = ranges[n.id];
    panel.hidden = true;
    toggle.setAttribute("aria-expanded", "false");
    open(n, r);
    window.scrollTo({ top: r.getBoundingClientRect().top + window.scrollY - window.innerHeight / 3 });
  }

  function list() {
    var notes = sorted(), group = null;
    body.textContent = "";
    if (!notes.length) body.appendChild(make("p", "", "No notes yet. Select text in a chapter, then press Add note."));
    notes.forEach(function (n) {
      if (n.page !== group) {
        group = n.page;
        body.appendChild(make("h3", "", n.label));
      }
      var a = make("a", "notes-panel__item");
      a.href = n.page + "#ag-note-" + n.id;
      if (n.sec) a.appendChild(make("small", "", n.sec));
      a.appendChild(make("q", "", flat(n.exact)));
      if (n.text) a.appendChild(make("span", "", n.text));
      if (n.page === page && !ranges[n.id]) a.appendChild(make("em", "", "Quoted text not found on this page"));
      a.addEventListener("click", function (ev) {
        if (n.page === page && ranges[n.id]) { ev.preventDefault(); jump(n); }
      });
      body.appendChild(a);
    });
  }

  toggle.addEventListener("click", function () {
    panel.hidden = !panel.hidden;
    toggle.setAttribute("aria-expanded", String(!panel.hidden));
    if (!panel.hidden) list();
  });
  shut.addEventListener("click", function () { toggle.click(); });

  // Markdown for reading; each note also carries its full record in a comment so Import can restore it
  exp.addEventListener("click", function () {
    var title = document.querySelector(".topbar__title").textContent.trim(), group = null, sec = null;
    var md = "# Notes: " + title + "\n\nExported " + new Date().toISOString().slice(0, 10) + ". Import this file in the book's Notes panel to restore the notes.\n";
    sorted().forEach(function (n) {
      if (n.page !== group) { group = n.page; sec = null; md += "\n## " + n.label + "\n"; }
      if (n.sec !== sec) { sec = n.sec; if (sec) md += "\n### " + sec + "\n"; }
      md += "\n> " + flat(n.exact) + "\n" + (n.text ? "\n" + n.text + "\n" : "");
      md += "\n<!-- ag-note " + JSON.stringify(n).replace(/>/g, "\\u003e") + " -->\n";
    });
    var a = make("a");
    a.href = URL.createObjectURL(new Blob([md], { type: "text/markdown" }));
    a.download = title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") + "-notes.md";
    a.click();
    URL.revokeObjectURL(a.href);
  });

  imp.addEventListener("click", function () { file.click(); });
  file.addEventListener("change", function () {
    file.files[0].text().then(function (txt) {
      var notes = load(), at = {}, re = /<!-- ag-note (\{.*?\}) -->/g, m, count = 0;
      notes.forEach(function (n, i) { at[n.id] = i; });
      while ((m = re.exec(txt))) {
        var n = JSON.parse(m[1]);
        count++;
        if (!(n.id in at)) notes.push(n);
        else if (n.time > notes[at[n.id]].time) notes[at[n.id]] = n;
      }
      store(notes);
      file.value = "";
      paint();
      list();
      status.textContent = "Imported " + count + " note(s); newer local edits kept.";
    });
  });

  document.addEventListener("keydown", function (ev) {
    if (ev.key !== "Escape") return;
    if (!pop.hidden) close();
    else if (!panel.hidden) toggle.click();
  });

  // lazily highlighted code rebuilds its text nodes, so ranges inside it must be found again
  document.querySelectorAll("details.code-file").forEach(function (d) { d.addEventListener("toggle", paint); });
  window.agReady.then(function () {
    paint();
    var id = location.hash.indexOf("#ag-note-") === 0 ? location.hash.slice(9) : null;
    if (id && ranges[id]) jump(byId(id));
  });
})();
