---
layout: about
title: about
permalink: /
subtitle: PhD Student · <a href='https://psych.bnu.edu.cn/'>Department of Psychology</a>, <a href='https://www.bnu.edu.cn/'>Beijing Normal University</a>

profile:
  align: right
  image: prof_pic.png
  image_circular: true # crops the image to make it circular
  more_info: >
    guohao2045@gmail.com

selected_papers: false # keep the about page minimal — publications live on their own page
social: false # social icons now live in the top-right navbar (enable_navbar_social)

announcements:
  enabled: false # news lives on its own page (see /news/)

latest_posts:
  enabled: false
---

Hi! I'm Guohao Zhang, a PhD student in the Department of Psychology at Beijing Normal University, China.

Before that, I earned my MSc in Psychology at Beijing Normal University (2022–2025) and my BSc at Southwest University of Science and Technology (2018–2022). Along the way I helped build NOD and HAD, two large-scale fMRI/MEG/EEG datasets of the brain responding to thousands of naturalistic images and video clips — resources for studying how we recognize visual content in the messy, real world.

My research lives at the intersection of brains and machines. I study how the human visual system represents the natural world with large-scale neuroimaging, and I'm increasingly drawn to **NeuroAI** — asking what artificial and biological intelligence can teach each other. Lately I've been thinking a lot about giving language-model **agents** a more human-like **memory**, and about **decentralized science** as a way to make research more open, reproducible, and collaborative.
<style>
/* Make the NetEase custom social icon match the Font Awesome icons:
   single-colour (follows theme colour + hover) and vertically aligned. */
a[title="NetEase Cloud Music"] svg {
  width: 1em;
  height: 1em;
  vertical-align: -0.41em;
  background-color: var(--global-text-color);
  -webkit-mask: url("/assets/img/netease.svg") center / contain no-repeat;
  mask: url("/assets/img/netease.svg") center / contain no-repeat;
}
a[title="NetEase Cloud Music"]:hover svg { background-color: var(--global-theme-color); }
a[title="NetEase Cloud Music"] svg image { display: none; }
/* Hide the RSS feed icon */
a[title="Rss icon"] { display: none !important; }
/* Thumbnail matches the text block height exactly. Absolute positioning keeps a
   tall image (e.g. a portrait book cover) from stretching the whole row. */
.bibliography li .row { align-items: stretch !important; }
.bibliography li .col-sm-2.abbr { position: relative !important; display: block !important; margin-bottom: 0 !important; padding: 0 8px !important; }
.bibliography li .col-sm-2.abbr figure { position: absolute !important; top: 0 !important; bottom: 0 !important; left: 8px !important; right: 8px !important; margin: 0 !important; width: auto !important; height: auto !important; }
.bibliography li .col-sm-2.abbr img { width: 100% !important; height: 100% !important; object-fit: cover !important; border-radius: 6px !important; }
/* Keep the header text clear of the avatar column (desktop only) */
@media (min-width: 768px) {
  .post-header { padding-right: calc(30% + 1.5rem); }
}
/* Center the email under the avatar */
.profile .more-info { text-align: center; }
/* Make the whole "Guohao Zhang" title bold, not just the first name */
.post-title { font-weight: 700 !important; }
</style>

<script>
  // Lift the avatar so its top edge lines up with the "Guohao Zhang" title.
  (function () {
    function alignAvatar() {
      var header = document.querySelector(".post-header");
      var profile = document.querySelector(".profile.float-right");
      if (!header || !profile) return;
      profile.style.marginTop = "0px"; // reset before measuring
      if (window.innerWidth < 768) return; // avatar stacks on small screens
      var delta = profile.getBoundingClientRect().top - header.getBoundingClientRect().top;
      var cur = parseFloat(getComputedStyle(profile).marginTop) || 0;
      profile.style.marginTop = cur - delta + "px";
    }
    window.addEventListener("load", alignAvatar);
    window.addEventListener("resize", alignAvatar);
    alignAvatar();
  })();
</script>

