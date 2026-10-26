/* Мобільне меню — плавна анімація через max-height */
document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.querySelector('.menu-toggle');
    const navigation = document.querySelector('#main-navigation');

    if (!toggle || !navigation) return;

    const openMenu = () => {
        toggle.setAttribute('aria-expanded', 'true');
        navigation.classList.add('is-open');
        toggle.querySelector('.sr-only').textContent = 'Закрити меню';
    };

    const closeMenu = () => {
        toggle.setAttribute('aria-expanded', 'false');
        navigation.classList.remove('is-open');
        toggle.querySelector('.sr-only').textContent = 'Відкрити меню';
    };

    toggle.addEventListener('click', () => {
        const isExpanded = toggle.getAttribute('aria-expanded') === 'true';
        isExpanded ? closeMenu() : openMenu();
    });

    /* Закрити при кліку на посилання */
    navigation.querySelectorAll('a').forEach((link) => {
        link.addEventListener('click', closeMenu);
    });

    /* Закрити при кліку поза меню */
    document.addEventListener('click', (e) => {
        if (
            navigation.classList.contains('is-open') &&
            !navigation.contains(e.target) &&
            !toggle.contains(e.target)
        ) {
            closeMenu();
        }
    });

    /* Закрити при Escape */
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && navigation.classList.contains('is-open')) {
            closeMenu();
            toggle.focus();
        }
    });
});

/* Пошук */
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

/* Full Card Click Navigation */
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.js-product-card').forEach(card => {
        card.addEventListener('click', (e) => {
            if (e.target.closest('button, form, a, input')) return;
            const url = card.dataset.url;
            if (url) window.location.href = url;
        });
    });
});

/* AJAX Wishlist Toggle */
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.js-wishlist-form').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = form.querySelector('.card-btn-wishlist, .wishlist-btn, .wishlist-detail-btn');
            const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]')?.value;

            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrfToken,
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.status === 'ok') {
                        if (btn) {
                            if (data.added) {
                                btn.classList.add('is-active');
                                btn.setAttribute('title', 'У списку бажань');
                                const textSpan = btn.querySelector('span:not(.wishlist-icon)');
                                if (textSpan) textSpan.textContent = 'У списку бажань';
                            } else {
                                btn.classList.remove('is-active');
                                btn.setAttribute('title', 'Видалити зі списку бажань');
                                const textSpan = btn.querySelector('span:not(.wishlist-icon)');
                                if (textSpan) textSpan.textContent = 'В обране';
                            }
                        }
                        const headerCount = document.getElementById('header-wishlist-count');
                        if (headerCount && data.wishlist_count !== undefined) {
                            headerCount.textContent = data.wishlist_count;
                        }
                    }
                } else {
                    form.submit();
                }
            } catch (err) {
                form.submit();
            }
        });
    });
});

/* AJAX Add to Cart from Catalog Cards */
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.js-card-cart-form').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = form.querySelector('.card-btn-cart');
            const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]')?.value;
            const originalHTML = btn ? btn.innerHTML : '';

            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrfToken,
                    },
                    body: new FormData(form),
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.status === 'ok') {
                        const headerCartCount = document.getElementById('header-cart-count');
                        if (headerCartCount && data.cart_count !== undefined) {
                            headerCartCount.textContent = data.cart_count;
                        }
                        if (btn) {
                            btn.innerHTML = '<span>✓ Додано</span>';
                            btn.classList.add('is-added');
                            setTimeout(() => {
                                btn.innerHTML = originalHTML;
                                btn.classList.remove('is-added');
                            }, 1400);
                        }
                    }
                } else {
                    form.submit();
                }
            } catch (err) {
                form.submit();
            }
        });
    });
});


/* ─── Avatar file picker preview ─── */
document.addEventListener('DOMContentLoaded', function () {
    const fileInput = document.getElementById('id_avatar');
    if (!fileInput) return;

    const previewImg = document.getElementById('avatar-preview-img');
    const placeholder = document.getElementById('avatar-preview-placeholder');
    const fileNameEl = document.getElementById('avatar-file-name');

    fileInput.addEventListener('change', function () {
        const file = this.files[0];
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function (e) {
                if (previewImg) {
                    previewImg.src = e.target.result;
                    previewImg.style.display = '';
                }
                if (placeholder) placeholder.style.display = 'none';
            };
            reader.readAsDataURL(file);
            if (fileNameEl) fileNameEl.textContent = file.name;
        }
    });
});
