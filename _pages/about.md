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

<!-- Navbar/social-icon styling is site-wide; see `footer_text` in _config.yml.
     This page sets `selected_papers: false`, so it renders no bibliography. -->

<style>
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
  // The offset can only be measured after layout, so this runs in JS. It is
  // deliberately NOT bound to `load`: waiting for the avatar image to finish
  // downloading is what used to make the avatar visibly jump on first paint.
  // ResizeObserver catches the image settling; rAF coalesces bursts of events.
  (function () {
    var pending = null;

    function align() {
      pending = null;
      var header = document.querySelector(".post-header");
      var profile = document.querySelector(".profile.float-right");
      if (!header || !profile) return;
      if (window.innerWidth < 768) {
        profile.style.marginTop = ""; // avatar stacks on small screens
        return;
      }
      profile.style.marginTop = "0px"; // reset before measuring
      var delta = profile.getBoundingClientRect().top - header.getBoundingClientRect().top;
      profile.style.marginTop = -delta + "px";
    }

    function schedule() {
      if (pending === null) pending = requestAnimationFrame(align);
    }

    function start() {
      schedule();
      window.addEventListener("resize", schedule);
      var profile = document.querySelector(".profile.float-right");
      var header = document.querySelector(".post-header");
      if (window.ResizeObserver && profile && header) {
        var ro = new ResizeObserver(schedule);
        ro.observe(profile);
        ro.observe(header);
      }
    }

    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
    else start();
  })();
</script>
