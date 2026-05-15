(function() {
    let currentIndex = -1;

    function navigateToPreviousHighlight() {
        const highlightElements = document.querySelectorAll(".highlight");
        if (highlightElements.length === 0) return;

        if (currentIndex !== -1 && currentIndex < highlightElements.length) {
            highlightElements[currentIndex].classList.remove("active");
        }

        currentIndex = (currentIndex - 1 + highlightElements.length) % highlightElements.length;
        highlightElements[currentIndex].classList.add("active");
        highlightElements[currentIndex].scrollIntoView({ behavior: "smooth", block: "center" });
    }

    function navigateToNextHighlight() {
        const highlightElements = document.querySelectorAll(".highlight");
        if (highlightElements.length === 0) return;

        if (currentIndex !== -1 && currentIndex < highlightElements.length) {
            highlightElements[currentIndex].classList.remove("active");
        }

        currentIndex = (currentIndex + 1) % highlightElements.length;
        highlightElements[currentIndex].classList.add("active");
        highlightElements[currentIndex].scrollIntoView({ behavior: "smooth", block: "center" });
    }

    function activateNearestVisibleHighlight() {
        const highlightElements = document.querySelectorAll(".highlight");
        if (highlightElements.length === 0) return;

        highlightElements.forEach(element => element.classList.remove("active"));

        let minDistance = Number.MAX_SAFE_INTEGER;
        let nearestIndex = -1;

        highlightElements.forEach((element, index) => {
            const rect = element.getBoundingClientRect();
            const distance = Math.abs(rect.top);

            if (distance < minDistance) {
                minDistance = distance;
                nearestIndex = index;
            }
        });

        if (nearestIndex !== -1) {
            currentIndex = nearestIndex;
            highlightElements[currentIndex].classList.add("active");
            highlightElements[currentIndex].scrollIntoView({ behavior: "smooth", block: "center" });
        }
    }

    // Global event delegation for buttons
    document.addEventListener("click", function(event) {
        if (event.target.id === "nextButton") navigateToNextHighlight();
        if (event.target.id === "prevButton") navigateToPreviousHighlight();
        if (event.target.id === "nearestButton") activateNearestVisibleHighlight();
    });

    // Keyboard shortcuts
    document.addEventListener("keydown", function(event) {
        // Skip if user is typing in an input or textarea
        if (event.target.tagName === "INPUT" || event.target.tagName === "TEXTAREA") return;

        if (event.keyCode === 65) { // 'a'
            navigateToPreviousHighlight();
            event.preventDefault();
        } else if (event.keyCode === 83) { // 's'
            activateNearestVisibleHighlight();
            event.preventDefault();
        } else if (event.keyCode === 68) { // 'd'
            navigateToNextHighlight();
            event.preventDefault();
        }
    });

    // Reset index when a new search is performed (detected via DOM change in results)
    const observer = new MutationObserver(() => {
        currentIndex = -1;
    });
    // Standalone export uses #results; the main app uses #results-area.
    const resultsContainer = document.getElementById('results') || document.getElementById('results-area');
    if (resultsContainer) {
        observer.observe(resultsContainer, { childList: true });
    }
})();
