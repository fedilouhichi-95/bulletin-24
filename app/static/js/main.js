// Geolocation nicety: find nearest catalog city and reload on it.
// Any element with [data-geoloc] triggers it (menu item + page button).
(function () {
  "use strict";

  const buttons = document.querySelectorAll("[data-geoloc]");
  if (!buttons.length || !navigator.geolocation) {
    buttons.forEach((b) => (b.disabled = true));
    return;
  }

  const locate = (btn) => {
    btn.disabled = true;
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const q = new URLSearchParams({
            lat: String(pos.coords.latitude),
            lon: String(pos.coords.longitude),
          });
          const res = await fetch("/api/position?" + q.toString());
          if (!res.ok) throw new Error("api");
          const city = await res.json();
          document.cookie =
            "city=" + encodeURIComponent(city.slug) +
            ";max-age=31536000;samesite=Lax";
          window.location.reload();
        } catch {
          btn.textContent = "Impossible de trouver ta ville";
        }
      },
      () => {
        btn.textContent = "Position refusée";
      },
      { timeout: 8000, maximumAge: 600000 },
    );
  };

  buttons.forEach((btn) => btn.addEventListener("click", () => locate(btn)));
})();
