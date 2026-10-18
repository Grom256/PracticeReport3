document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.querySelector('.menu-toggle');
    const navigation = document.querySelector('#main-navigation');

    if (!toggle || !navigation) return;

    toggle.addEventListener('click', () => {
        const isExpanded = toggle.getAttribute('aria-expanded') === 'true';
        toggle.setAttribute('aria-expanded', String(!isExpanded));
        navigation.classList.toggle('is-open', !isExpanded);
        toggle.querySelector('.sr-only').textContent = isExpanded
            ? 'Відкрити меню'
            : 'Закрити меню';
    });

    navigation.querySelectorAll('a').forEach((link) => {
        link.addEventListener('click', () => {
            toggle.setAttribute('aria-expanded', 'false');
            navigation.classList.remove('is-open');
            toggle.querySelector('.sr-only').textContent = 'Відкрити меню';
        });
    });
});
