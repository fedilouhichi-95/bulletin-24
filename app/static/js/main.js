// Geolocation nicety: find nearest catalog city and reload on it.
(function () {
  "use strict";

  const btn = document.getElementById("geoloc");
  if (!btn || !navigator.geolocation) return;

  btn.addEventListener("click", () => {
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
  });
})();
