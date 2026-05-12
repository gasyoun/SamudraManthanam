    let currentIndex = -1;

    document.addEventListener("keydown", function(event) {
      if (event.key === "F6") {
        activateFirstVisibleHighlight();
        event.preventDefault(); // Предотвращаем дополнительные действия по умолчанию
      } else if (event.key === "F7") {
        navigateToNextHighlight();
        event.preventDefault(); // Предотвращаем дополнительные действия по умолчанию
      }
    });

    function activateFirstVisibleHighlight() {
      const highlightElements = document.querySelectorAll(".highlight");

      highlightElements.forEach(element => element.classList.remove("active"));

      const visibleHighlights = Array.from(highlightElements).filter(element => {
        const rect = element.getBoundingClientRect();
        return rect.top >= 0 && rect.bottom <= window.innerHeight;
      });

      if (visibleHighlights.length > 0) {
        currentIndex = Array.from(highlightElements).indexOf(visibleHighlights[0]);
        highlightElements[currentIndex].classList.add("active");
        highlightElements[currentIndex].scrollIntoView({ behavior: "smooth" });
      }
    }

    function navigateToNextHighlight() {
      const highlightElements = document.querySelectorAll(".highlight");

      if (currentIndex !== -1) {
        highlightElements[currentIndex].classList.remove("active");
      }

      currentIndex = (currentIndex + 1) % highlightElements.length;
      highlightElements[currentIndex].classList.add("active");
      highlightElements[currentIndex].scrollIntoView({ behavior: "smooth" });
    }
