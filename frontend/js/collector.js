const user = Auth.requireAuth(["Collector"]);

if (user) {
  document.getElementById("userName").textContent =
    `${user.full_name} (Collector)`;
}


let jobs = [];
let watchId = null;
let tracking = false;


// ==========================================================
// LOAD COLLECTIONS
// ==========================================================

async function loadJobs() {

  try {

    jobs = await apiRequest("/collections");

    // Sort:
    // In Progress first
    // then Pending
    // then Completed

    jobs.sort((a, b) => {

      const priority = {
        "In Progress": 1,
        "Pending": 2,
        "Missed": 3,
        "Completed": 4
      };

      return (priority[a.status] || 99) -
             (priority[b.status] || 99);

    });

    renderRoute();
    renderTable();

  } catch (err) {

    showToast(err.message);

  }
}


// ==========================================================
// ROUTE CARDS
// ==========================================================

function renderRoute() {

  const container =
    document.getElementById("routeCards");

  const empty =
    document.getElementById("emptyState");

  const activeJobs =
    jobs.filter(j => j.status !== "Completed");

  empty.style.display =
    activeJobs.length ? "none" : "block";


  container.innerHTML = activeJobs
    .map((job, index) => {

      const isCurrent =
        job.status === "In Progress";

      return `

        <div class="route-card ${isCurrent ? "current-stop" : ""}">

          <div class="route-number">
            ${index + 1}
          </div>

          <div class="route-info">

            <div class="route-title">

              <strong>
                ${job.bin_code}
              </strong>

              <span class="badge ${job.status.replace(" ", "")}">
                ${job.status}
              </span>

            </div>


            <div class="route-location">
              📍 ${job.location || "Location unavailable"}
            </div>


            <div class="route-meta">

              Scheduled:
              ${formatDate(job.scheduled_date)}

            </div>


            ${
              job.notes
                ? `<div class="route-notes">
                     ${job.notes}
                   </div>`
                : ""
            }


            <div class="route-actions">

              <button
                class="btn-sm"
                onclick="navigateToBin(${job.bin_id})"
              >
                🗺️ Navigate
              </button>


              ${
                job.status !== "Completed"

                  ? `
                    <button
                      class="btn-sm"
                      onclick="startJob(${job.id})"
                    >
                      🚛 Start
                    </button>
                  `

                  : ""
              }


              ${
                job.status !== "Completed"

                  ? `
                    <button
                      class="btn-sm"
                      onclick="completeJob(${job.id})"
                    >
                      ✓ Complete
                    </button>
                  `

                  : ""
              }

            </div>

          </div>

        </div>

      `;

    })
    .join("");


  updateProgress();
}


// ==========================================================
// TABLE
// ==========================================================

function renderTable() {

  const rows =
    document.getElementById("jobRows");

  rows.innerHTML = jobs
    .map(
      (j) => `

      <tr>

        <td>${j.bin_code}</td>

        <td>
          ${formatDate(j.scheduled_date)}
        </td>

        <td>
          <span class="badge ${j.status.replace(" ", "")}">
            ${j.status}
          </span>
        </td>

        <td>
          ${j.notes || "—"}
        </td>

        <td>

          ${
            j.status !== "Completed"

              ? `
                <button
                  class="btn-sm"
                  onclick="completeJob(${j.id})"
                >
                  Mark Completed
                </button>
              `

              : ""
          }

        </td>

      </tr>

    `
    )
    .join("");
}


// ==========================================================
// START JOB
// ==========================================================

async function startJob(id) {

  try {

    await apiRequest(
      `/collections/${id}`,
      {
        method: "PUT",
        body: {
          status: "In Progress"
        }
      }
    );

    showToast("Collection started");

    await loadJobs();

  } catch (err) {

    showToast(err.message);

  }
}


// ==========================================================
// COMPLETE JOB
// ==========================================================

async function completeJob(id) {

  try {

    await apiRequest(
      `/collections/${id}`,
      {
        method: "PUT",
        body: {
          status: "Completed"
        }
      }
    );

    showToast("Collection completed ✓");

    await loadJobs();

  } catch (err) {

    showToast(err.message);

  }
}


// ==========================================================
// GOOGLE MAPS NAVIGATION
// ==========================================================

async function navigateToBin(binId) {

  try {

    const bin =
      await apiRequest(`/bins/${binId}`);

    if (!bin.latitude || !bin.longitude) {

      showToast(
        "This bin does not have GPS coordinates yet."
      );

      return;
    }


    const url =
      `https://www.google.com/maps/dir/?api=1&destination=${bin.latitude},${bin.longitude}`;

    window.open(url, "_blank");

  } catch (err) {

    showToast(err.message);

  }
}


// ==========================================================
// START GPS TRACKING
// ==========================================================

function startTracking() {

  if (!navigator.geolocation) {

    showToast(
      "GPS is not supported by this browser."
    );

    return;
  }


  tracking = true;

  document.getElementById(
    "startTrackingBtn"
  ).style.display = "none";


  document.getElementById(
    "stopTrackingBtn"
  ).style.display = "inline-block";


  document.getElementById(
    "trackingStatus"
  ).textContent = "Requesting GPS permission...";


  watchId =
    navigator.geolocation.watchPosition(

      sendLocation,

      handleLocationError,

      {
        enableHighAccuracy: true,
        maximumAge: 5000,
        timeout: 10000
      }

    );

}


// ==========================================================
// SEND GPS LOCATION TO SERVER
// ==========================================================

async function sendLocation(position) {

  const latitude =
    position.coords.latitude;

  const longitude =
    position.coords.longitude;


  const currentJob =
    jobs.find(
      j => j.status === "In Progress"
    );


  try {

    await apiRequest(
      "/admin/collector-location",
      {
        method: "POST",

        body: {

          latitude,
          longitude,

          current_collection_id:
            currentJob
              ? currentJob.id
              : null,

          is_tracking: true

        }
      }
    );


    document.getElementById(
      "trackingStatus"
    ).textContent =
      `Live GPS active • ${latitude.toFixed(5)}, ${longitude.toFixed(5)}`;


  } catch (err) {

    console.error(
      "Location update failed:",
      err
    );

  }

}


// ==========================================================
// GPS ERROR
// ==========================================================

function handleLocationError(error) {

  let message =
    "Unable to access GPS.";

  if (error.code === 1) {
    message =
      "GPS permission was denied.";
  }

  if (error.code === 2) {
    message =
      "GPS position unavailable.";
  }

  if (error.code === 3) {
    message =
      "GPS request timed out.";
  }


  document.getElementById(
    "trackingStatus"
  ).textContent = message;


  showToast(message);

}


// ==========================================================
// STOP GPS TRACKING
// ==========================================================

async function stopTracking() {

  tracking = false;


  if (watchId !== null) {

    navigator.geolocation.clearWatch(
      watchId
    );

    watchId = null;

  }


  document.getElementById(
    "startTrackingBtn"
  ).style.display = "inline-block";


  document.getElementById(
    "stopTrackingBtn"
  ).style.display = "none";


  document.getElementById(
    "trackingStatus"
  ).textContent =
    "Route tracking stopped";


  try {

    await apiRequest(
      "/admin/collector-location/stop",
      {
        method: "POST"
      }
    );

  } catch (err) {

    console.error(err);

  }

}


// ==========================================================
// PROGRESS
// ==========================================================

function updateProgress() {

  const total =
    jobs.length;

  const completed =
    jobs.filter(
      j => j.status === "Completed"
    ).length;


  const percentage =
    total === 0
      ? 0
      : Math.round(
          (completed / total) * 100
        );


  document.getElementById(
    "routeProgressText"
  ).textContent =
    `${completed} / ${total} completed`;


  document.getElementById(
    "routeProgressBar"
  ).style.width =
    `${percentage}%`;

}


// ==========================================================
// INITIAL LOAD
// ==========================================================

loadJobs();


// Refresh jobs periodically

setInterval(
  loadJobs,
  15000
);