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

document.addEventListener('DOMContentLoaded', () => {
    const search = document.querySelector('.header-search');
    if (!search) return;
    const input = search.querySelector('input');
    const button = search.querySelector('.search-toggle');
    const close = () => search.classList.remove('is-open');

    button.addEventListener('click', (event) => {
        if (!search.classList.contains('is-open')) {
            event.preventDefault();
            search.classList.add('is-open');
            input.focus();
        } else if (!input.value.trim()) {
            event.preventDefault();
            close();
        }
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && search.classList.contains('is-open')) {
            close();
            button.focus();
        }
    });
    document.addEventListener('click', (event) => {
        if (!search.contains(event.target) && !input.value.trim()) close();
    });
});
