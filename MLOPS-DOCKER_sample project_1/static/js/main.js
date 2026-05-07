document.addEventListener('DOMContentLoaded', () => {
    // Form validation animation
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', (e) => {
            const input = form.querySelector('input[type="text"]');
            if (input.value.trim() === '') {
                e.preventDefault();
                input.style.animation = 'none';
                // Trigger reflow
                void input.offsetWidth;
                input.style.animation = 'shake 0.4s';
            } else {
                const btn = form.querySelector('input[type="submit"]');
                btn.value = 'Loading...';
                btn.style.opacity = '0.8';
                btn.style.pointerEvents = 'none';
            }
        });
    }

    // Add confetti effect on the greeting page
    const greetMessage = document.querySelector('.greet-message');
    if (greetMessage) {
        createConfetti();
    }
});

function createConfetti() {
    const colors = ['#a864fd', '#29cdff', '#78ff44', '#ff718d', '#fdff6a'];
    
    for (let i = 0; i < 60; i++) {
        const confetti = document.createElement('div');
        confetti.classList.add('confetti');
        document.body.appendChild(confetti);
        
        // Random positioning and styling
        confetti.style.left = Math.random() * 100 + 'vw';
        confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        
        // Randomize shape (some circles, some squares)
        if (Math.random() > 0.5) {
            confetti.style.borderRadius = '50%';
        }
        
        // Setup animation
        const duration = Math.random() * 3000 + 2000;
        const delay = Math.random() * 1000;
        
        confetti.animate([
            { 
                transform: `translate3d(0, -10vh, 0) rotate(0deg) scale(${Math.random() + 0.5})`, 
                opacity: 1 
            },
            { 
                transform: `translate3d(${Math.random() * 200 - 100}px, 110vh, 0) rotate(${Math.random() * 720}deg) scale(${Math.random() + 0.5})`, 
                opacity: 0 
            }
        ], {
            duration: duration,
            delay: delay,
            iterations: Infinity,
            easing: 'cubic-bezier(.37,0,.63,1)'
        });
    }
}
