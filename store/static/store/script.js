// ──────────────────────────────────────────────
// Navigation bar toggle
// ──────────────────────────────────────────────
var bar = document.getElementById("bar");
var closeNav = document.getElementById("close");
var nav = document.getElementById("navbar");

if (bar) {
    bar.addEventListener('click', function() {
        nav.classList.add("actives");
    });
}

if (closeNav) {
    closeNav.addEventListener('click', function() {
        nav.classList.remove("actives");
    });
}

// ──────────────────────────────────────────────
// Wishlist Toggle (AJAX - stays client-side)
// ──────────────────────────────────────────────
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

window.toggleWishlist = function(e, element) {
    e.preventDefault();
    var productId = element.getAttribute('data-product-id');
    var icon = element.querySelector('i');

    fetch('/toggle-wishlist/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ product_id: productId })
    })
    .then(function(response) {
        if (response.redirected) {
            window.location.href = response.url;
            return null;
        }
        if (response.ok) return response.json();
        return null;
    })
    .then(function(data) {
        if (!data) return;
        if (data.status === 'added') {
            icon.classList.remove('fa-regular');
            icon.classList.add('fa-solid');
        } else if (data.status === 'removed') {
            icon.classList.remove('fa-solid');
            icon.classList.add('fa-regular');
        }
    })
    .catch(function(error) {
        console.error('Error toggling wishlist:', error);
    });
};

// ──────────────────────────────────────────────
// View Product (navigate to single product page)
// ──────────────────────────────────────────────
window.viewProduct = function(element) {
    window.location.href = '/sproduct/';
};

// ──────────────────────────────────────────────
// Small image gallery (sproduct page)
// ──────────────────────────────────────────────
var smallImgs = document.querySelectorAll('.small-img');
var mainImg = document.getElementById('MainImg');
if (mainImg && smallImgs.length > 0) {
    smallImgs.forEach(function(img) {
        img.addEventListener('click', function() {
            mainImg.src = this.src;
        });
    });
}

// ----------------------------------------------
// Scroll Animations (React-like Interactivity)
// ----------------------------------------------
document.addEventListener("DOMContentLoaded", function() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px"
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('show-animate');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    const hiddenElements = document.querySelectorAll('.hidden-animate');
    hiddenElements.forEach(el => observer.observe(el));
});
