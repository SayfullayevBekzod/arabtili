document.addEventListener("DOMContentLoaded", () => {
    const steps = ["intro", "listen", "select", "write", "review"];
    let currentStepIndex = 0;

    // Elements
    const views = {};
    steps.forEach(s => views[s] = document.getElementById(`view-${s}`));

    const audioPlayer = document.getElementById("audio-player");

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

    function playCorrect() {
        playTone(600, 'sine', 0.1);
        setTimeout(() => playTone(800, 'sine', 0.2), 100);
    }

    function playWrong() {
        playTone(300, 'sawtooth', 0.2); // Adjusted for less harshness
        setTimeout(() => playTone(200, 'sawtooth', 0.3), 100);
    }

    // Init
    showStep("intro");

    // --- Step 1: Intro ---
    document.getElementById("btn-intro-next").addEventListener("click", () => {
        playAudio();
        goToStep("listen");
    });

    // --- Step 2: Listen ---
    document.getElementById("btn-listen-play").addEventListener("click", () => {
        playAudio();
    });
    document.getElementById("btn-listen-next").addEventListener("click", () => {
        goToStep("select");
    });

    // --- Step 3: Select (Quiz) ---
    document.querySelectorAll(".option-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const isCorrect = e.currentTarget.dataset.correct === "true"; // Use currentTarget
            if (isCorrect) {
                playCorrect();
                e.currentTarget.classList.add("bg-green-500", "scale-110");
                setTimeout(() => goToStep("write"), 1000);
            } else {
                playWrong();
                e.currentTarget.classList.add("bg-red-500", "shake");
                setTimeout(() => e.currentTarget.classList.remove("bg-red-500", "shake"), 500);
            }
        });
    });

    // --- Step 4: Write (Advanced Tracing) ---
    const path = document.getElementById("letter-path");
    const guideDot = document.getElementById("guide-dot"); // We will add this dynamically if missing

    if (path) {
        const container = path.closest("svg");
        const length = path.getTotalLength();
        // Reset path to be invisible (dashed out)
        path.style.strokeDasharray = length;
        path.style.strokeDashoffset = length;

        let isDrawing = false;
        let progress = 0; // 0 to length
        const tolerance = 40; // Pixel distance to trigger progress

        // Create guide dot if not exists
        const handle = document.getElementById("drag-handle");

        // Init handle position
        if (handle) {
            const startPoint = path.getPointAtLength(0);
            handle.setAttribute("cx", startPoint.x);
            handle.setAttribute("cy", startPoint.y);
            handle.style.display = "block";
        }

        function updateHandle(len) {
            if (!handle) return;
            const pt = path.getPointAtLength(len);
            handle.setAttribute("cx", pt.x);
            handle.setAttribute("cy", pt.y);

            // Show arrow/guide orientation? 
            // Optional: rotate arrow inside handle
        }

        function handleMove(e) {
            if (!isDrawing) return;
            e.preventDefault();

            const point = container.createSVGPoint();
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;
            point.x = clientX;
            point.y = clientY;
            const cursor = point.matrixTransform(container.getScreenCTM().inverse());

            // Scrubbing Logic:
            // Calculate distance from cursor to the "current tip" (progress)
            const tipPoint = path.getPointAtLength(progress);
            const distToTip = Math.hypot(cursor.x - tipPoint.x, cursor.y - tipPoint.y);

            // Also check distance to slightly ahead
            const step = 8;
            const nextPoint = path.getPointAtLength(progress + step);
            const distToNext = Math.hypot(cursor.x - nextPoint.x, cursor.y - nextPoint.y);

            // If user is near the current tip (radius 30 in SVG units - generous)
            // Or if user is "ahead" but close to path? 
            // For now, simple "Close to Tip" logic is best for "Tracing"

            const TOUCH_RADIUS = 30; // SVG units (viewbox 0-100, so 30 is huge? wait viewbox is 100x100? No viewbox is dynamic)
            // If viewbox is 0 0 100 100, then 30 is 30% of width. That's generous.
            // If viewbox is larger, we might need adjustments.
            // But let's assume standard vector scale.

            if (distToTip < TOUCH_RADIUS || distToNext < TOUCH_RADIUS) {
                // Advance progress
                // We advance proportional to movement or fixed steps?
                // Let's just advance loop until we catch up to cursor projection?
                // Simple: Advance by fixed step if close.

                progress += step;
                progress = Math.min(progress, length);

                path.style.strokeDashoffset = length - progress;
                updateHandle(progress);

                if (progress >= length - 2) { // Tolerance at end
                    finishPractice();
                    isDrawing = false;
                }
            }
        }

        container.addEventListener("mousedown", () => isDrawing = true);
        container.addEventListener("touchstart", () => isDrawing = true);

        window.addEventListener("mouseup", () => isDrawing = false);
        window.addEventListener("touchend", () => isDrawing = false);

        container.addEventListener("mousemove", handleMove);
        container.addEventListener("touchmove", handleMove);

        // Add a "Auto Demo" animation hint initially
        function runDemo() {
            if (progress > 10) return; // Don't run if user started

            let demoProgress = 0;
            const demoInterval = setInterval(() => {
                if (progress > 10 || currentStepIndex !== 3) {
                    clearInterval(demoInterval);
                    path.style.strokeDashoffset = length - progress; // Reset to user progress
                    return;
                }

                demoProgress += 2;
                if (demoProgress > length) {
                    demoProgress = 0;
                    // Pause between loops
                }

                // Show a "ghost" fill or just pulsate?
                // Actually, let's just use CSS animation on a cloning path for the "Hint"
            }, 20);
        }
    }

    // --- Navigation ---
    function showStep(stepName) {
        steps.forEach(s => {
            if (views[s]) views[s].classList.add("hidden");
        });
        if (views[stepName]) views[stepName].classList.remove("hidden");

        if (stepName === "write") {
            const path = document.getElementById("letter-path");
            const handle = document.getElementById("drag-handle");
            const container = path ? path.closest("svg") : null;

            if (container) {
                container.style.touchAction = "none"; // Prevent scrolling
            }

            if (path && handle) {
                // Reset state
                const len = path.getTotalLength();
                path.style.strokeDasharray = len;
                path.style.strokeDashoffset = len;

                // Init handle at start
                const start = path.getPointAtLength(0);
                handle.setAttribute("cx", start.x);
                handle.setAttribute("cy", start.y);
                handle.style.display = "block";
            }
        }
    }

    function goToStep(stepName) {
        const idx = steps.indexOf(stepName);
        if (idx >= 0) {
            currentStepIndex = idx;
            showStep(stepName);
        }
    }

    function playAudio() {
        if (audioPlayer && audioPlayer.src) {
            audioPlayer.currentTime = 0;
            audioPlayer.play().catch(e => console.log("Audio play failed", e));
        }
    }

    // --- Finish / Review ---
    let finished = false;
    function finishPractice() {
        if (finished) return;
        finished = true;

        const feedback = document.getElementById("trace-feedback");
        if (feedback) feedback.style.opacity = "1";

        setTimeout(() => {
            goToStep("review");
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
                    document.getElementById("xp-badge").innerText = `+${data.xp_added || 10} XP`;
                })
                .catch(err => console.error(err));
        }, 1000);
    }
});
