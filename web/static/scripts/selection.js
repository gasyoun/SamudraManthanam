    let currentIndex = -1;
    const nextButton = document.getElementById("nextButton");
    const prevButton = document.getElementById("prevButton");
    const nearestButton = document.getElementById("nearestButton");


    nextButton.addEventListener("click", function() {
      navigateToNextHighlight();
    });

    nearestButton.addEventListener("click", function() {
      activateNearestVisibleHighlight();
    });

    prevButton.addEventListener("click", function() {
      navigateToPreviousHighlight();
    });

    document.addEventListener("keydown", function(event) {
      if (event.keyCode === 65) { // Код клавиши "a"
        navigateToPreviousHighlight();
        event.preventDefault(); // Предотвращаем стандартное действие браузера
      } else if (event.keyCode === 83) { // Код клавиши "s"
        activateNearestVisibleHighlight();
        event.preventDefault(); // Предотвращаем стандартное действие браузера
      } else if (event.keyCode === 68) { // Код клавиши "d"
        navigateToNextHighlight();
        event.preventDefault(); // Предотвращаем стандартное действие браузера
      }
    });

    function navigateToPreviousHighlight() {
      const highlightElements = document.querySelectorAll(".highlight");

      if (currentIndex !== -1) {
        highlightElements[currentIndex].classList.remove("active");
      }

      currentIndex = (currentIndex - 1 + highlightElements.length) % highlightElements.length;
      highlightElements[currentIndex].classList.add("active");
      highlightElements[currentIndex].scrollIntoView({ behavior: "smooth" });
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

    function activateNearestVisibleHighlight() {
      const highlightElements = document.querySelectorAll(".highlight");

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
        highlightElements[currentIndex].scrollIntoView({ behavior: "smooth" });
      }
    }
