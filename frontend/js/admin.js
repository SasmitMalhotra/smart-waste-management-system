const user = Auth.requireAuth(["Admin"]);

if (user) {

  const userName =
    document.getElementById("userName");

  if (userName) {

    userName.textContent =
      `${user.full_name} (Admin)`;

  }

}


/* ==========================================================
   GLOBAL MAP STATE
   ========================================================== */

let wasteMap = null;

let binMarkers = [];

let collectorMarkers = [];

let locationPreviewMarker = null;


/* ==========================================================
   BIN FORM
   ========================================================== */

function toggleBinForm() {

  const form =
    document.getElementById("newBinForm");

  if (!form) return;

  form.style.display =
    form.style.display === "none" ||
    form.style.display === ""
      ? "grid"
      : "none";

}


/* ==========================================================
   INITIALISE MAP
   ========================================================== */

function initializeMap() {

  const mapElement =
    document.getElementById("wasteMap");

  if (!mapElement) return;

  if (typeof L === "undefined") {

    mapElement.innerHTML =
      "<div style='padding:20px'>Map library failed to load.</div>";

    return;

  }

  wasteMap =
    L.map("wasteMap")
      .setView(
        [22.3072, 73.1812],
        12
      );

  L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
      maxZoom: 19,
      attribution:
        "&copy; OpenStreetMap contributors"
    }
  ).addTo(wasteMap);

}


/* ==========================================================
   MAP ICONS
   ========================================================== */

function createBinIcon(status) {

  let className = "empty";

  if (status === "Half") {

    className = "warning";

  }

  if (
    status === "Full" ||
    status === "Overflowing"
  ) {

    className = "full";

  }

  return L.divIcon({

    className: "",

    html: `
      <div class="bin-marker ${className}">
        🗑
      </div>
    `,

    iconSize: [30, 30],

    iconAnchor: [15, 15]

  });

}


function createCollectorIcon() {

  return L.divIcon({

    className: "",

    html: `
      <div class="collector-marker">
        🚛
      </div>
    `,

    iconSize: [38, 38],

    iconAnchor: [19, 19]

  });

}


/* ==========================================================
   CLEAR MAP MARKERS
   ========================================================== */

function clearMapMarkers() {

  binMarkers.forEach(
    marker => {

      if (wasteMap) {

        wasteMap.removeLayer(
          marker
        );

      }

    }
  );

  collectorMarkers.forEach(
    marker => {

      if (wasteMap) {

        wasteMap.removeLayer(
          marker
        );

      }

    }
  );

  binMarkers = [];

  collectorMarkers = [];

}


/* ==========================================================
   BIN POPUP
   ========================================================== */

function createBinPopup(bin) {

  return `
    <div class="map-popup">

      <h4>
        ${bin.bin_code}
      </h4>

      <p>
        <strong>Location:</strong>
        ${bin.location || "Unknown"}
      </p>

      <p>
        <strong>Zone:</strong>
        ${bin.zone || "Unknown"}
      </p>

      <p>
        <strong>Waste:</strong>
        ${bin.waste_type || "General"}
      </p>

      <p>
        <strong>Fill:</strong>
        ${bin.current_fill_level ?? 0}%
      </p>

      <p>
        <strong>Status:</strong>
        ${bin.status || "Empty"}
      </p>

    </div>
  `;

}


/* ==========================================================
   LOAD MAP DATA
   ========================================================== */

async function loadMap() {

  if (!wasteMap) return;

  try {

    const bins =
      await apiRequest("/bins");

    clearMapMarkers();

    const validPoints = [];

    bins.forEach(bin => {

      const latitude =
        parseFloat(bin.latitude);

      const longitude =
        parseFloat(bin.longitude);

      if (
        !Number.isFinite(latitude) ||
        !Number.isFinite(longitude)
      ) {

        return;

      }

      const marker =
        L.marker(
          [latitude, longitude],
          {
            icon:
              createBinIcon(
                bin.status
              )
          }
        )
        .addTo(wasteMap);

      marker.bindPopup(
        createBinPopup(bin)
      );

      binMarkers.push(marker);

      validPoints.push([
        latitude,
        longitude
      ]);

    });


    try {

      const collectors =
        await apiRequest(
          "/admin/collector-locations"
        );

      if (Array.isArray(collectors)) {

        collectors.forEach(
          location => {

            const latitude =
              parseFloat(
                location.latitude
              );

            const longitude =
              parseFloat(
                location.longitude
              );

            if (
              !Number.isFinite(latitude) ||
              !Number.isFinite(longitude)
            ) {

              return;

            }

            const marker =
              L.marker(
                [
                  latitude,
                  longitude
                ],
                {
                  icon:
                    createCollectorIcon()
                }
              )
              .addTo(wasteMap);

            marker.bindPopup(`

              <div class="map-popup">

                <h4>
                  🚛
                  ${
                    location.collector_name ||
                    "Collector"
                  }
                </h4>

                <p>
                  <strong>Status:</strong>
                  ${
                    location.is_tracking
                      ? "Live Tracking"
                      : "Tracking stopped"
                  }
                </p>

                <p>
                  <strong>Last update:</strong>
                  ${formatDate(
                    location.recorded_at
                  )}
                </p>

              </div>

            `);

            collectorMarkers.push(
              marker
            );

            validPoints.push([
              latitude,
              longitude
            ]);

          }
        );

      }

    } catch (collectorError) {

      console.warn(
        "Collector locations unavailable:",
        collectorError
      );

    }


    if (
      validPoints.length > 0
    ) {

      wasteMap.fitBounds(
        L.latLngBounds(
          validPoints
        ),
        {
          padding: [30, 30],
          maxZoom: 15
        }
      );

    }

  } catch (err) {

    console.error(
      "Map loading failed:",
      err
    );

  }

}


/* ==========================================================
   FIT MAP
   ========================================================== */

async function centerMapOnAll() {

  if (!wasteMap) return;

  try {

    const bins =
      await apiRequest("/bins");

    const points = [];

    bins.forEach(bin => {

      const latitude =
        parseFloat(
          bin.latitude
        );

      const longitude =
        parseFloat(
          bin.longitude
        );

      if (
        Number.isFinite(latitude) &&
        Number.isFinite(longitude)
      ) {

        points.push([
          latitude,
          longitude
        ]);

      }

    });

    if (points.length === 0) {

      wasteMap.setView(
        [22.3072, 73.1812],
        12
      );

      showToast(
        "No bin GPS coordinates available yet."
      );

      return;

    }

    wasteMap.fitBounds(
      L.latLngBounds(points),
      {
        padding: [30, 30],
        maxZoom: 15
      }
    );

  } catch (err) {

    showToast(
      err.message
    );

  }

}


/* ==========================================================
   ADMIN STATISTICS
   ========================================================== */

async function loadStats() {

  try {

    const stats =
      await apiRequest(
        "/admin/dashboard"
      );

    const grid =
      document.getElementById(
        "statGrid"
      );

    if (!grid) return;

    grid.innerHTML = `

      <div class="stat-card">

        <div class="value">
          ${stats.total_bins ?? 0}
        </div>

        <div class="label">
          Total Bins
        </div>

      </div>


      <div class="stat-card">

        <div class="value">
          ${stats.bins_needing_collection ?? 0}
        </div>

        <div class="label">
          Bins Needing Collection
        </div>

      </div>


      <div class="stat-card">

        <div class="value">
          ${stats.pending_collections ?? 0}
        </div>

        <div class="label">
          Pending Collections
        </div>

      </div>


      <div class="stat-card">

        <div class="value">
          ${stats.pending_complaints ?? 0}
        </div>

        <div class="label">
          Pending Complaints
        </div>

      </div>


      <div class="stat-card">

        <div class="value">
          ${stats.total_citizens ?? 0}
        </div>

        <div class="label">
          Registered Citizens
        </div>

      </div>


      <div class="stat-card">

        <div class="value">
          ${stats.total_collectors ?? 0}
        </div>

        <div class="label">
          Active Collectors
        </div>

      </div>


      <div class="stat-card">

        <div class="value">
          ${stats.total_zones ?? 0}
        </div>

        <div class="label">
          Zones
        </div>

      </div>

    `;

  } catch (err) {

    console.error(
      "Statistics loading failed:",
      err
    );

    showToast(
      `Statistics: ${err.message}`
    );

  }

}


/* ==========================================================
   LOAD BINS
   ========================================================== */

async function loadBins() {

  try {

    const bins =
      await apiRequest("/bins");

    const grid =
      document.getElementById(
        "binGrid"
      );

    if (!grid) return;

    if (
      !bins ||
      bins.length === 0
    ) {

      grid.innerHTML = `
        <div class="empty-state">
          No bins have been added yet.
        </div>
      `;

      await loadMap();

      return;

    }

    grid.innerHTML =
      bins
        .map(b => {

          const level =
            Number(
              b.current_fill_level
            ) || 0;

          return `

            <div class="bin-card">

              <div class="bin-head">

                <span class="bin-code">
                  ${b.bin_code}
                </span>

                <span
                  class="badge ${b.status}"
                >
                  ${b.status}
                </span>

              </div>


              <div class="bin-meta">

                📍
                ${
                  b.location ||
                  "Location unavailable"
                }

              </div>


              <div class="bin-meta">

                Zone:
                ${b.zone || "—"}

                ·

                ${b.waste_type || "General"}

              </div>


              <div class="fill-bar-track">

                <div
                  class="fill-bar ${fillBarClass(level)}"
                  style="
                    width:${Math.min(
                      level,
                      100
                    )}%
                  "
                ></div>

              </div>


              <div class="bin-meta">

                ${level}% full

              </div>


              <div class="bin-actions">

                <button
                  class="btn-sm"
                  onclick="simulateSensor(${b.id})"
                  ${
                    level >= 100
                      ? "disabled"
                      : ""
                  }
                >

                  ${
                    level >= 100
                      ? "Sensor at Maximum"
                      : "🔄 Simulate Sensor"
                  }

                </button>


                <button
                  class="btn-sm btn-outline"
                  onclick="markCollected(${b.id})"
                >

                  ✓ Mark Collected

                </button>

              </div>

            </div>

          `;

        })
        .join("");

    await loadMap();

  } catch (err) {

    showToast(
      `Bins: ${err.message}`
    );

  }

}


/* ==========================================================
   FIND BIN LOCATION
   ========================================================== */

async function findBinLocation() {

  const locationInput =
    document.getElementById(
      "binLocation"
    );

  const latitudeInput =
    document.getElementById(
      "binLatitude"
    );

  const longitudeInput =
    document.getElementById(
      "binLongitude"
    );

  const status =
    document.getElementById(
      "locationStatus"
    );

  if (!locationInput) return;

  const query =
    locationInput.value.trim();

  if (!query) {

    showToast(
      "Enter a location first."
    );

    return;

  }

  status.textContent =
    "Finding location...";

  try {

    const url =
      "https://nominatim.openstreetmap.org/search" +
      "?format=jsonv2" +
      "&limit=1" +
      "&countrycodes=in" +
      "&q=" +
      encodeURIComponent(query);

    const response =
      await fetch(
        url,
        {
          headers: {
            "Accept":
              "application/json"
          }
        }
      );

    if (!response.ok) {

      throw new Error(
        "Location service unavailable."
      );

    }

    const results =
      await response.json();

    if (!results.length) {

      status.textContent =
        "Location not found.";

      showToast(
        "Could not find that location."
      );

      return;

    }

    const result =
      results[0];

    const latitude =
      parseFloat(
        result.lat
      );

    const longitude =
      parseFloat(
        result.lon
      );

    latitudeInput.value =
      latitude;

    longitudeInput.value =
      longitude;

    status.textContent =
      `✓ Found: ${result.display_name}`;

    if (wasteMap) {

      if (locationPreviewMarker) {

        wasteMap.removeLayer(
          locationPreviewMarker
        );

      }

      locationPreviewMarker =
        L.marker([
          latitude,
          longitude
        ])
        .addTo(wasteMap)
        .bindPopup(
          `<strong>New Bin Location</strong><br>${result.display_name}`
        )
        .openPopup();

      wasteMap.setView(
        [
          latitude,
          longitude
        ],
        16
      );

    }

  } catch (err) {

    console.error(
      "Geocoding error:",
      err
    );

    status.textContent =
      "Could not find location.";

    showToast(
      err.message
    );

  }

}


/* ==========================================================
   LOAD COMPLAINTS
   ========================================================== */

async function loadComplaints() {

  try {

    const complaints =
      await apiRequest(
        "/complaints?status=Pending"
      );

    const rows =
      document.getElementById(
        "complaintRows"
      );

    if (!rows) return;

    rows.innerHTML =
      complaints.length

        ? complaints
            .map(c => `

              <tr>

                <td>
                  #${c.id}
                </td>

                <td>
                  ${c.reporter_name || "—"}
                </td>

                <td>
                  ${c.bin_code || "—"}
                </td>

                <td>
                  ${c.reason || "—"}
                </td>

                <td>

                  <span
                    class="badge ${c.status}"
                  >
                    ${c.status}
                  </span>

                </td>

                <td>

                  <button
                    class="btn-sm"
                    onclick="resolveComplaint(${c.id})"
                  >
                    Resolve
                  </button>

                </td>

              </tr>

            `)
            .join("")

        : `

            <tr>

              <td
                colspan="6"
                class="empty-state"
              >
                No pending complaints 🎉
              </td>

            </tr>

          `;

  } catch (err) {

    showToast(
      `Complaints: ${err.message}`
    );

  }

}


/* ==========================================================
   ZONE NORMALIZER
   ========================================================== */

function normalizeZone(zone) {

  let value =
    String(zone || "")
      .trim()
      .toUpperCase();

  while (
    value.startsWith("ZONE ")
  ) {

    value =
      value.substring(5).trim();

  }

  return value;

}


/* ==========================================================
   LOAD COLLECTION JOBS
   ========================================================== */

async function loadCollections() {

  try {

    const jobs =
      await apiRequest(
        "/collections"
      );

    const collectors =
      await apiRequest(
        "/admin/users?role=Collector"
      );

    const rows =
      document.getElementById(
        "collectionRows"
      );

    if (!rows) return;

    if (
      !jobs ||
      jobs.length === 0
    ) {

      rows.innerHTML = `

        <tr>

          <td
            colspan="6"
            class="empty-state"
          >
            No collection jobs yet.
          </td>

        </tr>

      `;

      return;

    }

    rows.innerHTML =
      jobs
        .map(j => {

          /*
            IMPORTANT:
            Only show collectors belonging
            to the same zone as this bin.
          */

          const zoneCollectors =
            collectors.filter(
              collector =>
                normalizeZone(
                  collector.zone
                ) ===
                normalizeZone(
                  j.zone
                )
            );

          return `

            <tr>

              <!-- BIN -->

              <td>

                <strong>
                  ${j.bin_code || "—"}
                </strong>

                <div class="bin-meta">

                  ${
                    j.location ||
                    "Location unavailable"
                  }

                </div>

                <div class="bin-meta">

                  Zone:
                  ${
                    j.zone ||
                    "—"
                  }

                </div>

              </td>


              <!-- COLLECTOR -->

              <td>

                <select
                  id="collector-${j.id}"
                >

                  <option value="">
                    Select Collector
                  </option>

                  ${
                    zoneCollectors
                      .map(
                        collector => `

                          <option
                            value="${collector.id}"
                            ${
                              Number(
                                j.collector_id
                              ) ===
                              Number(
                                collector.id
                              )
                                ? "selected"
                                : ""
                            }
                          >
                            ${collector.full_name}
                          </option>

                        `
                      )
                      .join("")
                  }

                </select>


                ${
                  j.collector_name

                    ? `

                      <div class="bin-meta">

                        Assigned:
                        <strong>
                          ${j.collector_name}
                        </strong>

                      </div>

                    `

                    : `

                      <div class="bin-meta">
                        Not assigned
                      </div>

                    `
                }

              </td>


              <!-- SCHEDULE -->

              <td>

                ${formatDate(
                  j.scheduled_date
                )}

              </td>


              <!-- STATUS -->

              <td>

                <span
                  class="badge ${
                    String(
                      j.status || ""
                    ).replace(
                      " ",
                      ""
                    )
                  }"
                >

                  ${
                    j.status ||
                    "Pending"
                  }

                </span>

              </td>


              <!-- FILL -->

              <td>

                ${
                  j.current_fill_level !== null &&
                  j.current_fill_level !== undefined

                    ? `${j.current_fill_level}%`

                    : "—"
                }

              </td>


              <!-- ACTION -->

              <td>

                <button
                  class="btn-sm"
                  onclick="assignCollector(${j.id})"
                >
                  Assign
                </button>

              </td>

            </tr>

          `;

        })
        .join("");

  } catch (err) {

    showToast(
      `Collection jobs: ${err.message}`
    );

    console.error(
      "Collection loading failed:",
      err
    );

  }

}


/* ==========================================================
   ASSIGN COLLECTOR
   ========================================================== */

async function assignCollector(
  collectionId
) {

  try {

    const select =
      document.getElementById(
        `collector-${collectionId}`
      );

    if (!select) {

      showToast(
        "Collector selector not found."
      );

      return;

    }

    const collectorId =
      select.value;

    if (!collectorId) {

      showToast(
        "Please select a collector."
      );

      return;

    }

    await apiRequest(
      `/collections/${collectionId}`,
      {
        method: "PUT",

        body: {
          collector_id:
            Number(
              collectorId
            )
        }

      }
    );

    showToast(
      "Collector assigned successfully ✓"
    );

    await loadCollections();

  } catch (err) {

    showToast(
      err.message
    );

  }

}


/* ==========================================================
   SENSOR SIMULATION
   ========================================================== */

async function simulateSensor(
  binId
) {

  try {

    const bin =
      await apiRequest(
        `/bins/${binId}`
      );

    const current =
      Number(
        bin.current_fill_level
      ) || 0;

    if (current >= 100) {

      showToast(
        "Bin is already at maximum capacity."
      );

      return;

    }

    await apiRequest(
      `/bins/${binId}/sensor-update`,
      {
        method: "POST",
        body: {}
      }
    );

    showToast(
      "Sensor reading recorded ✓"
    );

    await loadBins();

    await loadStats();

    await loadCollections();

  } catch (err) {

    showToast(
      err.message
    );

  }

}


/* ==========================================================
   MARK BIN COLLECTED
   ========================================================== */

async function markCollected(
  binId
) {

  try {

    await apiRequest(
      `/bins/${binId}/collected`,
      {
        method: "POST"
      }
    );

    showToast(
      "Bin marked as collected ✓"
    );

    await loadBins();

    await loadStats();

    await loadCollections();

  } catch (err) {

    showToast(
      err.message
    );

  }

}


/* ==========================================================
   RESOLVE COMPLAINT
   ========================================================== */

async function resolveComplaint(
  id
) {

  try {

    await apiRequest(
      `/complaints/${id}`,
      {
        method: "PUT",

        body: {
          status: "Resolved"
        }

      }
    );

    showToast(
      "Complaint resolved ✓"
    );

    await loadComplaints();

    await loadStats();

  } catch (err) {

    showToast(
      err.message
    );

  }

}


/* ==========================================================
   AUTO-SCHEDULE FULL BINS
   ========================================================== */

async function autoSchedule() {

  try {

    const response =
      await apiRequest(
        "/collections/auto-schedule",
        {
          method: "POST"
        }
      );

    showToast(
      response.message ||
      "Collection scheduling completed."
    );

    await loadCollections();

    await loadStats();

  } catch (err) {

    showToast(
      err.message
    );

  }

}


/* ==========================================================
   CREATE NEW BIN
   ========================================================== */

const newBinForm =
  document.getElementById(
    "newBinForm"
  );

if (newBinForm) {

  newBinForm.addEventListener(
    "submit",
    async event => {

      event.preventDefault();

      try {

        const binCode =
          document.getElementById(
            "binCode"
          ).value.trim();

        const zone =
          document.getElementById(
            "binZone"
          ).value.trim();

        const location =
          document.getElementById(
            "binLocation"
          ).value.trim();

        const wasteType =
          document.getElementById(
            "binWasteType"
          ).value;

        const capacity =
          Number(
            document.getElementById(
              "binCapacity"
            ).value
          ) || 100;

        const latitudeValue =
          document.getElementById(
            "binLatitude"
          ).value;

        const longitudeValue =
          document.getElementById(
            "binLongitude"
          ).value;

        if (!binCode) {

          showToast(
            "Enter a bin code."
          );

          return;

        }

        if (!zone) {

          showToast(
            "Enter a zone."
          );

          return;

        }

        if (!location) {

          showToast(
            "Enter a location."
          );

          return;

        }

        const body = {

          bin_code:
            binCode,

          zone:
            zone,

          location:
            location,

          waste_type:
            wasteType,

          capacity_liters:
            capacity

        };

        if (
          latitudeValue !== "" &&
          longitudeValue !== ""
        ) {

          const latitude =
            Number(
              latitudeValue
            );

          const longitude =
            Number(
              longitudeValue
            );

          if (
            Number.isFinite(
              latitude
            ) &&
            Number.isFinite(
              longitude
            )
          ) {

            body.latitude =
              latitude;

            body.longitude =
              longitude;

          }

        }

        await apiRequest(
          "/bins",
          {
            method: "POST",
            body
          }
        );

        showToast(
          "Bin created ✓"
        );

        newBinForm.reset();

        document.getElementById(
          "binCapacity"
        ).value = 100;

        const locationStatus =
          document.getElementById(
            "locationStatus"
          );

        if (locationStatus) {

          locationStatus.textContent =
            "";

        }

        if (
          locationPreviewMarker &&
          wasteMap
        ) {

          wasteMap.removeLayer(
            locationPreviewMarker
          );

          locationPreviewMarker =
            null;

        }

        newBinForm.style.display =
          "none";

        await loadBins();

        await loadStats();

      } catch (err) {

        showToast(
          err.message
        );

      }

    }
  );

}


/* ==========================================================
   INITIAL LOAD
   ========================================================== */

initializeMap();

loadStats();

loadBins();

loadComplaints();

loadCollections();


/* ==========================================================
   AUTOMATIC REFRESH
   ========================================================== */

setInterval(
  async () => {

    await loadStats();

    await loadBins();

    await loadComplaints();

    await loadCollections();

  },
  15000
);


/* ==========================================================
   COLLECTOR GPS REFRESH
   ========================================================== */

setInterval(
  async () => {

    await loadMap();

  },
  10000
);