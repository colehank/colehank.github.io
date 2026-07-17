---
layout: page
title: muses
permalink: /music/
nav: true
nav_order: 7
---

<p class="music-intro">some of my muses</p>

<div id="music-player" hidden>
  <div class="music-player-bar">
    <a id="music-player-open" href="#" target="_blank" rel="noopener noreferrer">open in NetEase ↗</a>
    <button type="button" id="music-player-close" aria-label="close player">×</button>
  </div>
  <iframe id="music-player-frame" title="NetEase player" frameborder="no" allow="autoplay" src="about:blank"></iframe>
</div>

<h2 class="music-section">Songs</h2>
<div class="music-grid">
  {% for track in site.data.music.songs %}
  <a class="music-card" data-embed data-embed-type="2" data-embed-id="{{ track.url | split: 'id=' | last }}" href="{{ track.url }}" target="_blank" rel="noopener noreferrer">
    <div class="music-cover">
      <img src="{{ track.cover }}" alt="{{ track.title }} cover" loading="lazy" />
    </div>
    <div class="music-meta">
      <span class="music-title">{{ track.title }}</span>
      {% if track.subtitle %}<span class="music-subtitle">{{ track.subtitle }}</span>{% endif %}
    </div>
  </a>
  {% endfor %}
</div>

{% if site.data.music.radio.episodes %}
<h2 class="music-section">Demos</h2>
<div class="music-grid">
  {% for ep in site.data.music.radio.episodes %}
  <a class="music-card" data-embed data-embed-type="3" data-embed-id="{{ ep.url | split: 'id=' | last }}" href="{{ ep.url }}" target="_blank" rel="noopener noreferrer">
    <div class="music-cover">
      <img src="{{ ep.cover }}" alt="{{ ep.title }} cover" loading="lazy" />
    </div>
    <div class="music-meta">
      <span class="music-title">{{ ep.title }}</span>
      {% if ep.subtitle %}<span class="music-subtitle">{{ ep.subtitle }}</span>{% endif %}
    </div>
  </a>
  {% endfor %}
</div>
{% endif %}

<script>
  (function () {
    var box = document.getElementById("music-player");
    var frame = document.getElementById("music-player-frame");
    var openLink = document.getElementById("music-player-open");
    // Delegate in the CAPTURE phase so we intercept the click before
    // medium-zoom (which stopPropagation()s on cover images) and before the
    // anchor's default navigation fires.
    document.addEventListener(
      "click",
      function (e) {
        var card = e.target.closest(".music-card[data-embed]");
        if (!card) return;
        var id = card.getAttribute("data-embed-id");
        var type = card.getAttribute("data-embed-type") || "2";
        if (!id) return; // no id parsed -> let the link work
        e.preventDefault();
        e.stopPropagation();
        // NetEase's web embed can't play on mobile browsers (it funnels users to
        // the app), so on touch devices open the track on NetEase instead.
        if (window.matchMedia && window.matchMedia("(pointer: coarse)").matches) {
          var w = window.open(card.href, "_blank", "noopener");
          if (!w) window.location.href = card.href;
          return;
        }
        var h = 66; // single-item player (type=2 song / type=3 radio program)
        frame.style.height = h + 20 + "px";
        frame.src = "https://music.163.com/outchain/player?type=" + type + "&id=" + id + "&auto=1&height=" + h;
        openLink.href = card.href;
        box.hidden = false;
      },
      true
    );
    document.getElementById("music-player-close").addEventListener("click", function () {
      frame.src = "about:blank"; // stop playback
      box.hidden = true;
    });

    // --- drag the player around by its bar ---
    var bar = box.querySelector(".music-player-bar");
    var dragging = false,
      startX,
      startY,
      startLeft,
      startTop;
    bar.addEventListener("pointerdown", function (e) {
      if (e.target.closest("a, button")) return; // keep the link / close button clickable
      var r = box.getBoundingClientRect();
      box.style.left = r.left + "px";
      box.style.top = r.top + "px";
      box.style.right = "auto";
      box.style.bottom = "auto";
      dragging = true;
      startX = e.clientX;
      startY = e.clientY;
      startLeft = r.left;
      startTop = r.top;
      bar.setPointerCapture(e.pointerId);
      e.preventDefault();
    });
    bar.addEventListener("pointermove", function (e) {
      if (!dragging) return;
      var nl = startLeft + (e.clientX - startX);
      var nt = startTop + (e.clientY - startY);
      nl = Math.max(0, Math.min(nl, window.innerWidth - box.offsetWidth));
      nt = Math.max(0, Math.min(nt, window.innerHeight - box.offsetHeight));
      box.style.left = nl + "px";
      box.style.top = nt + "px";
    });
    function endDrag() {
      dragging = false;
    }
    bar.addEventListener("pointerup", endDrag);
    bar.addEventListener("pointercancel", endDrag);
  })();
</script>

<style>
  /* Use the oyster mark AS the muses page title (hide the text) */
  .post-title {
    font-size: 0;
  }
  .post-title::after {
    content: "";
    display: inline-block;
    width: 148px;
    height: 96px;
    vertical-align: middle;
    background: url("/assets/img/oyster-mark.png") center / contain no-repeat;
  }
  .music-intro {
    margin-bottom: 1.5rem;
    font-size: 0.95rem;
  }
  #music-player {
    position: fixed;
    right: 20px;
    bottom: 20px;
    z-index: 1000;
    width: 340px;
    max-width: calc(100vw - 40px);
    background: var(--global-bg-color, #fff);
    border-radius: 10px;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.25);
    overflow: hidden;
  }
  @media (max-width: 480px) {
    #music-player {
      right: 10px;
      left: 10px;
      bottom: 10px;
      width: auto;
    }
  }
  .music-player-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.35rem 0.6rem;
    font-size: 0.8rem;
    cursor: move;
    user-select: none;
    touch-action: none;
  }
  #music-player-open {
    color: var(--global-theme-color);
    text-decoration: none;
  }
  #music-player-close {
    border: none;
    background: none;
    cursor: pointer;
    font-size: 1.2rem;
    line-height: 1;
    color: inherit;
    opacity: 0.6;
  }
  #music-player-close:hover {
    opacity: 1;
  }
  #music-player-frame {
    display: block;
    width: 100%;
    border: 0;
  }
  .music-section {
    margin: 2.2rem 0 1.2rem;
    font-size: 1.3rem;
    font-weight: 600;
  }
  .music-section a {
    color: inherit;
  }
  .music-section a:hover {
    color: var(--global-theme-color);
  }
  .music-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 1.5rem;
  }
  .music-card {
    display: block;
    text-decoration: none;
    color: inherit;
    transition: transform 0.2s ease;
  }
  .music-card:hover {
    transform: translateY(-4px);
  }
  .music-cover {
    position: relative;
    width: 100%;
    aspect-ratio: 1 / 1;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  }
  .music-cover img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
    transition: transform 0.3s ease;
  }
  .music-card:hover .music-cover img {
    transform: scale(1.05);
  }
  .music-cover::after {
    content: "▶";
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    color: #fff;
    background: rgba(0, 0, 0, 0.35);
    opacity: 0;
    transition: opacity 0.25s ease;
  }
  .music-card:hover .music-cover::after {
    opacity: 1;
  }
  /* cards without inline playback (radio episodes) jump out -> show ↗ instead of ▶ */
  .music-card:not([data-embed]) .music-cover::after {
    content: "↗";
  }
  .music-meta {
    margin-top: 0.6rem;
    display: flex;
    flex-direction: column;
    line-height: 1.3;
  }
  .music-title {
    font-weight: 600;
  }
  .music-card:hover .music-title {
    color: var(--global-theme-color);
  }
  .music-subtitle {
    font-size: 0.8rem;
    opacity: 0.7;
  }
</style>
