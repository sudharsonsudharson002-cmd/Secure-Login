document.addEventListener('DOMContentLoaded', () => {
    const matrixLayer = document.getElementById('matrixLayer');
    const particlesLayer = document.getElementById('particlesLayer');
    const passwordInput = document.getElementById('passwordMeter');
    const strengthBar = document.getElementById('passwordStrengthBar');
    const rules = document.getElementById('passwordRules');

    if (matrixLayer) {
        const chars = '01abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
        const columns = Math.floor(window.innerWidth / 20);
        for (let i = 0; i < columns; i++) {
            const span = document.createElement('span');
            span.style.left = `${i * 20}px`;
            span.style.animationDuration = `${8 + Math.random() * 10}s`;
            span.style.opacity = String(0.2 + Math.random() * 0.5);
            span.textContent = chars[Math.floor(Math.random() * chars.length)];
            span.style.position = 'absolute';
            span.style.top = '-20px';
            span.style.color = '#00ffa3';
            span.style.fontSize = '12px';
            span.style.animation = 'fall 10s linear infinite';
            matrixLayer.appendChild(span);
        }
    }

    if (particlesLayer) {
        for (let i = 0; i < 40; i++) {
            const dot = document.createElement('span');
            dot.style.position = 'absolute';
            dot.style.left = `${Math.random() * 100}%`;
            dot.style.top = `${Math.random() * 100}%`;
            dot.style.width = `${2 + Math.random() * 4}px`;
            dot.style.height = dot.style.width;
            dot.style.borderRadius = '50%';
            dot.style.background = '#00ffa3';
            dot.style.opacity = String(0.4 + Math.random() * 0.6);
            particlesLayer.appendChild(dot);
        }
    }

    if (passwordInput && strengthBar && rules) {
        passwordInput.addEventListener('input', () => {
            const value = passwordInput.value;
            let score = 0;
            if (value.length >= 12) score += 1;
            if (/[A-Z]/.test(value)) score += 1;
            if (/[a-z]/.test(value)) score += 1;
            if (/\d/.test(value)) score += 1;
            if (/[^A-Za-z0-9]/.test(value)) score += 1;
            const width = (score / 5) * 100;
            strengthBar.style.width = `${width}%`;
            let label = 'Weak';
            if (score >= 4) label = 'Strong';
            else if (score >= 3) label = 'Good';
            rules.textContent = `Password strength: ${label}`;
        });
    }

    document.querySelectorAll('.counter').forEach((counter) => {
        const target = Number(counter.getAttribute('data-target'));
        let current = 0;
        const step = target / 50;
        const timer = setInterval(() => {
            current += step;
            if (current >= target) {
                counter.textContent = target;
                clearInterval(timer);
            } else {
                counter.textContent = Math.round(current);
            }
        }, 40);
    });
});
