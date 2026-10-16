/* Dark mode toggle. The initial theme is applied by an inline script in
   layout.html; this keeps the toggle, the saved choice and the system
   setting in sync. */
(function () {
    'use strict';
    const root = document.documentElement;
    const media = window.matchMedia('(prefers-color-scheme: dark)');

    function saved() {
        try { return localStorage.getItem('gt-theme'); } catch (e) { return null; }
    }

    function apply(theme) {
        root.setAttribute('data-bs-theme', theme);
        const button = document.getElementById('theme-toggle');
        if (button) {
            const next = theme === 'dark' ? 'light' : 'dark';
            button.setAttribute('aria-label', `Switch to ${next} mode`);
            button.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
        }
    }

    apply(root.getAttribute('data-bs-theme') || (media.matches ? 'dark' : 'light'));

    document.addEventListener('click', event => {
        if (!event.target.closest('#theme-toggle')) return;
        const theme = root.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
        try { localStorage.setItem('gt-theme', theme); } catch (e) { /* storage blocked */ }
        apply(theme);
    });

    // Follow the system setting until the user picks a theme with the toggle.
    const onChange = event => { if (!saved()) apply(event.matches ? 'dark' : 'light'); };
    if (media.addEventListener) media.addEventListener('change', onChange);
    else if (media.addListener) media.addListener(onChange);
})();
