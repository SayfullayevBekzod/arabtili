document.addEventListener("DOMContentLoaded", () => {
    // Audio Context (Synth)
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

    function playTone(freq, type, duration) {
        if (audioCtx.state === 'suspended') audioCtx.resume();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = type;
        osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + duration);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + duration);
    }

    window.playCorrect = () => {
        playTone(600, 'sine', 0.1);
        setTimeout(() => playTone(800, 'sine', 0.2), 100);
    };

    window.playWrong = () => {
        playTone(300, 'sawtooth', 0.2);
        setTimeout(() => playTone(200, 'sawtooth', 0.3), 100);
    };

    // --- Quiz Handler ---
    // --- Pure Vanilla JS Logic ---
    window.handleVanillaSelect = (card) => {
        // 1. Prevent multiple interactions
        const container = document.getElementById('select-options-grid');
        if (container.classList.contains('locked')) return;

        // 2. Lock board
        container.classList.add('locked'); // Custom visual lock if needed, mostly logical

        // 3. Get values
        const selectedLetter = card.dataset.letter;
        const correctLetter = container.dataset.correctVal;

        // 4. Disable all siblings visually and functionally
        const allCards = container.querySelectorAll('.letter-card');
        allCards.forEach(c => {
            c.style.pointerEvents = 'none'; // Disable clicks
            if (c !== card) {
                c.style.opacity = '0.5'; // Visual disabled state
                c.classList.remove('hover:border-yellow-400/50', 'hover:bg-white/10', 'active:scale-95');
            }
        });

        // 5. Compare & Feedback
        if (selectedLetter === correctLetter) {
            // Correct State
            window.playCorrect();
            card.classList.remove('bg-white/5', 'border-white/10');
            card.classList.add('!bg-emerald-600', '!border-emerald-400', 'scale-105', 'shadow-emerald-500/50');

            // Trigger Next Step
            setTimeout(() => {
                const el = document.getElementById('practice-container');
                if (el && el._x_dataStack) {
                    const alpineData = Array.from(el._x_dataStack).find(d => d.nextStep);
                    if (alpineData) alpineData.nextStep('write');
                } else if (el && el.__x && el.__x.$data) {
                    el.__x.$data.nextStep('write');
                }
            }, 1000);

        } else {
            // Incorrect State
            window.playWrong();
            card.classList.remove('bg-white/5', 'border-white/10');
            card.classList.add('!bg-red-600', '!border-red-400', 'shake');

            // Optional: Reveal correct answer after mistake? 
            // The constraint says "Disable all... Prevent multiple selections". 
            // Usually we might want to let them try again or show the right one. 
            // But requirements say "After one selection: Disable all...". 
            // So they fail this attempt.

            // If strictly following "Disable all", the user is stuck? 
            // "Prevent multiple selections" implies single attempt.
            // Let's assume we show error, then maybe reset or move on?
            // "The logic must be... fully working."

            // Re-enabling for retry (UX decision to prevent hard lock)
            // or maybe treating it as a failure state.
            // Given it's a practice, usually we let them proceed or retry.
            // However, "Disable all other letter cards" implies the choice is final.
            // I will implement a reset after error for better UX, 
            // OR if it's strict, we just show red.
            // Let's stick to strict visual feedback first.

            setTimeout(() => {
                card.classList.remove('shake');
                // Auto-retry capability? 
                // "Disable all other letter cards" -> implies locking.
                // But if they are wrong, they need to proceed.
                // I'll re-enable after a short delay so they can try again CORRECTLY,
                // unless it's a strict test. Practice usually allows retry.
                // But prompt said "After one selection: Disable all...". 
                // Implies "One Shot".

                // If I leave it locked, the user is stuck.
                // I will UNLOCK if it was wrong, to allow progress.
                container.classList.remove('locked');
                allCards.forEach(c => {
                    c.style.pointerEvents = '';
                    c.style.opacity = '1';
                    c.classList.add('hover:border-yellow-400/50', 'hover:bg-white/10', 'active:scale-95');
                });

                // Reset card style
                card.classList.remove('!bg-red-600', '!border-red-400');
                card.classList.add('bg-white/5', 'border-white/10');
            }, 1000);
        }
    };

    // --- Tracing Logic ---
    let tracingInited = false;
    window.reinitStep = (stepName) => {
        if (stepName === 'write') {
            // Need to wait for Alpine to render the template
            setTimeout(() => initTracing(), 100);
        }
        if (stepName === 'intro') {
            finished = false;
        }
    };

    function initTracing() {
        const path = document.getElementById("letter-path");
        const handHint = document.getElementById("hand-hint");
        const feedback = document.getElementById("trace-feedback");
        const clearBtn = document.getElementById("btn-clear-trace");
        const container = document.getElementById("practice-svg");

        if (!path || !container) return;

        const length = path.getTotalLength();
        path.style.strokeDasharray = length;
        path.style.strokeDashoffset = length;

        let isDrawing = false;
        let progress = 0;
        const step = 6;

        function handleMove(e) {
            if (!isDrawing) return;
            e.preventDefault();

            if (handHint) handHint.style.opacity = "0";
            if (feedback) feedback.style.opacity = "1";

            const point = container.createSVGPoint();
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;
            point.x = clientX;
            point.y = clientY;
            const cursor = point.matrixTransform(container.getScreenCTM().inverse());

            const tipPoint = path.getPointAtLength(progress);
            const dist = Math.hypot(cursor.x - tipPoint.x, cursor.y - tipPoint.y);

            if (dist < 50) { // Increased tolerance for better UX
                progress += step;
                progress = Math.min(progress, length);
                path.style.strokeDashoffset = length - progress;

                if (progress >= length - 5) {
                    finishPractice();
                    isDrawing = false;
                }
            }
        }

        container.addEventListener("mousedown", () => isDrawing = true);
        container.addEventListener("touchstart", (e) => { isDrawing = true; e.preventDefault(); }, { passive: false });
        window.addEventListener("mouseup", () => isDrawing = false);
        window.addEventListener("touchend", () => isDrawing = false);
        container.addEventListener("mousemove", handleMove);
        container.addEventListener("touchmove", handleMove, { passive: false });

        if (clearBtn) {
            clearBtn.addEventListener("click", () => {
                progress = 0;
                path.style.strokeDashoffset = length;
                if (handHint) handHint.style.opacity = "0.5";
                if (feedback) feedback.style.opacity = "0";
            });
        }
    }

    // --- Finish / Review ---
    let finished = false;
    function finishPractice() {
        if (finished) return;
        finished = true;

        const feedback = document.getElementById("trace-feedback");
        if (feedback) {
            feedback.innerText = "AJOYIB!";
            feedback.style.color = "#fbbf24";
        }

        setTimeout(() => {
            const el = document.getElementById('practice-container');
            if (el && el._x_dataStack) {
                const alpineData = Array.from(el._x_dataStack).find(d => d.nextStep);
                if (alpineData) alpineData.nextStep('review');
            } else if (el && el.__x && el.__x.$data) {
                el.__x.$data.nextStep('review');
            }

            // Call API
            const letterId = document.getElementById("letter-id").value;
            const csrfTokenElement = document.querySelector("[name=csrfmiddlewaretoken]");
            if (!csrfTokenElement) return;

            fetch(`/api/letter/${letterId}/finish/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfTokenElement.value
                }
            })
                .then(r => r.json())
                .then(data => {
                    const badge = document.getElementById("xp-badge");
                    if (badge) badge.innerText = `+${data.xp_added || 10} XP`;
                })
                .catch(err => console.error(err));
        }, 1200);
    }
});
