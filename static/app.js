"use strict";

const byId = (id) => document.getElementById(id);
let accessToken = null; // Page memory only: reloading requires signing in again.
let selectedTrip = null;
let registering = false;
let busy = false;

function message(text, isError = false) {
  byId("status").textContent = text;
  byId("status").dataset.error = String(isError);
}

// One action at a time prevents double clicks and selection changes mid-request.
async function runAction(action) {
  if (busy) return;
  busy = true;
  document.querySelectorAll("fieldset, button").forEach((el) => { el.disabled = true; });
  message("Working…");
  try {
    await action();
  } catch (error) {
    message(error.message, true);
  } finally {
    busy = false;
    document.querySelectorAll("fieldset, button").forEach((el) => { el.disabled = false; });
  }
}

function clearSelection() {
  selectedTrip = null;
  byId("trip-detail").hidden = true;
  byId("selection-empty").hidden = false;
  byId("activity-list").replaceChildren();
  ["selected-title", "selected-meta", "budget-total", "budget-planned", "budget-remaining"]
    .forEach((id) => { byId(id).textContent = ""; });
  byId("activity-form").reset();
  byId("activity-date").removeAttribute("min");
  byId("activity-date").removeAttribute("max");
  markSelection();
}

function clearSession() {
  accessToken = null;
  clearSelection();
  byId("trip-list").replaceChildren();
  byId("account-email").textContent = "";
  byId("account").hidden = true;
  byId("workspace").hidden = true;
  byId("auth-panel").hidden = false;
  byId("trip-form").reset();
  byId("auth-form").reset();
  setAuthMode(false);
}

function errorDetail(data, status) {
  if (typeof data?.detail === "string") return data.detail;
  if (Array.isArray(data?.detail)) {
    return data.detail.map((item) => {
      const field = (item.loc ?? []).filter((part) => part !== "body").join(".");
      return `${field}: ${item.msg ?? "Invalid value"}`;
    }).join("; ");
  }
  return `Request failed (HTTP ${status}).`;
}

async function api(path, { method = "GET", body, auth = true } = {}) {
  const headers = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth) {
    if (!accessToken) throw new Error("Please sign in.");
    headers.Authorization = `Bearer ${accessToken}`;
  }

  let response;
  let raw;
  try {
    response = await fetch(path, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: "no-store",
      signal: AbortSignal.timeout(15000),
    });
    raw = response.status === 204 ? "" : await response.text();
  } catch {
    throw new Error("Could not confirm the result. Check your connection and refresh your trips before retrying a change.");
  }

  if (auth && response.status === 401) {
    clearSession();
    throw new Error("Session expired. Please sign in again.");
  }
  let data = null;
  if (raw) {
    try { data = JSON.parse(raw); } catch { /* Non-JSON errors get a generic message. */ }
  }
  if (!response.ok) {
    const error = new Error(errorDetail(data, response.status));
    error.status = response.status;
    throw error;
  }
  if (response.status === 204) return null; // DELETE has no response body.
  if (data === null) throw new Error("The server returned an unexpected response. Refresh before retrying a change.");
  return data;
}

function centsFromDollars(value) {
  if (!/^\d+(?:\.\d{1,2})?$/.test(value)) {
    throw new Error("Enter money as a nonnegative amount, such as 125.00, with no commas or dollar sign.");
  }
  const [whole, fraction = ""] = value.split(".");
  const cents = Number(whole) * 100 + Number(fraction.padEnd(2, "0"));
  if (!Number.isSafeInteger(cents)) throw new Error("That amount is too large for this browser UI.");
  return cents;
}

function money(cents) {
  if (!Number.isSafeInteger(cents)) throw new Error("The API returned an amount too large for this browser UI.");
  const absolute = Math.abs(cents);
  const dollars = Math.floor(absolute / 100).toLocaleString("en-US");
  const fraction = String(absolute % 100).padStart(2, "0");
  return `${cents < 0 ? "-" : ""}$${dollars}.${fraction}`;
}

function makeText(tag, text) {
  const element = document.createElement(tag);
  element.textContent = text; // User input is text, never executable HTML.
  return element;
}

function setAuthMode(createAccount) {
  registering = createAccount;
  const title = registering ? "Create account" : "Sign in";
  byId("auth-title").textContent = title;
  byId("auth-submit").textContent = title;
  byId("auth-toggle").textContent = registering ? "Already registered? Sign in" : "Create an account";
  byId("auth-help").textContent = registering
    ? "Use a password with 15–128 characters. After registering, sign in."
    : "Sign in to see your trips.";
  byId("password").minLength = registering ? 15 : 1;
  byId("password").autocomplete = registering ? "new-password" : "current-password";
  byId("password").value = "";
}

function markSelection() {
  document.querySelectorAll(".trip-button").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.tripId === selectedTrip?.id));
  });
}

function renderTrips(trips) {
  const list = byId("trip-list");
  list.replaceChildren();
  if (trips.length === 0) list.append(makeText("li", "No trips yet. Plan your first one above."));
  for (const trip of trips) {
    const item = document.createElement("li");
    const button = makeText("button", `${trip.title} · ${trip.destination}`);
    button.type = "button";
    button.className = "trip-button";
    button.dataset.tripId = trip.id;
    button.disabled = busy;
    button.addEventListener("click", () => runAction(async () => {
      await loadSelected(trip.id);
      byId("selected-title").focus();
      message("Trip loaded.");
    }));
    item.append(button);
    list.append(item);
  }
  markSelection();
}

function renderSelected(trip, budget) {
  // Check amounts before changing the visible selection.
  const total = money(budget.budget_cents);
  const planned = money(budget.planned_cost_cents);
  const remaining = money(budget.remaining_cents);
  const activityAmounts = trip.activities.map((activity) => money(activity.cost_cents));
  selectedTrip = trip;
  byId("selected-title").textContent = trip.title;
  byId("selected-meta").textContent = `${trip.destination} · ${trip.start_date} to ${trip.end_date} · ${trip.travelers} traveler(s)`;
  byId("budget-total").textContent = total;
  byId("budget-planned").textContent = planned;
  byId("budget-remaining").textContent = remaining;
  byId("budget-remaining").classList.toggle("negative", budget.remaining_cents < 0);
  byId("activity-date").min = trip.start_date;
  byId("activity-date").max = trip.end_date;

  const list = byId("activity-list");
  list.replaceChildren();
  if (trip.activities.length === 0) list.append(makeText("li", "No activities yet."));
  trip.activities.forEach((activity, index) => {
    const row = document.createElement("li");
    row.className = "activity-row";
    const description = document.createElement("div");
    description.append(
      makeText("strong", activity.title),
      makeText("small", `${activity.activity_date} · ${activityAmounts[index]}`),
    );
    const button = makeText("button", "Delete");
    button.type = "button";
    button.disabled = busy;
    button.setAttribute("aria-label", `Delete ${activity.title}`);
    button.addEventListener("click", () => runAction(async () => {
      await api(`/trips/${encodeURIComponent(trip.id)}/activities/${encodeURIComponent(activity.id)}`, { method: "DELETE" });
      await afterChange("Activity deleted.", trip.id);
    }));
    row.append(description, button);
    list.append(row);
  });
  byId("selection-empty").hidden = true;
  byId("trip-detail").hidden = false;
  markSelection();
}

async function loadSelected(id) {
  const changed = selectedTrip?.id !== id;
  try {
    const url = `/trips/${encodeURIComponent(id)}`;
    const trip = await api(url);
    const budget = await api(`${url}/budget`);
    renderSelected(trip, budget);
    if (changed) byId("activity-form").reset();
  } catch (error) {
    // Do not leave stale details or a stale activity form after a failed refresh.
    clearSelection();
    throw error;
  }
}

async function refreshTrips(preferredId = selectedTrip?.id) {
  const trips = await api("/trips");
  renderTrips(trips);
  if (trips.some((trip) => trip.id === preferredId)) await loadSelected(preferredId);
  else clearSelection();
}

async function afterChange(successMessage, tripId) {
  // A failed refresh must not make a confirmed write look like a failed write.
  try {
    await refreshTrips(tripId);
    message(successMessage);
  } catch (error) {
    clearSelection();
    message(`${successMessage} Refresh failed: ${error.message}`, true);
  }
}

byId("auth-toggle").addEventListener("click", () => {
  if (busy) return;
  setAuthMode(!registering);
  message("");
});

byId("auth-form").addEventListener("submit", (event) => {
  event.preventDefault();
  runAction(async () => {
    const email = byId("email").value.trim();
    const password = byId("password").value; // Do not trim or alter passwords.
    byId("password").value = "";
    if (registering) {
      await api("/auth/register", { method: "POST", body: { email, password }, auth: false });
      setAuthMode(false);
      message("Account created. Sign in with your email and password.");
      return;
    }
    const token = await api("/auth/login", { method: "POST", body: { email, password }, auth: false });
    if (typeof token.access_token !== "string" || !token.access_token) throw new Error("The server did not return an access token.");
    accessToken = token.access_token;
    let user;
    try { user = await api("/auth/me"); } catch (error) { clearSession(); throw error; }
    byId("account-email").textContent = user.email;
    byId("auth-panel").hidden = true;
    byId("account").hidden = false;
    byId("workspace").hidden = false;
    await refreshTrips();
    message("Signed in. Create a trip or select one from your list.");
  });
});

byId("logout").addEventListener("click", () => {
  if (busy) return;
  clearSession();
  message("Signed out.");
});

byId("refresh").addEventListener("click", () => runAction(async () => {
  await refreshTrips();
  message("Trips refreshed.");
}));

byId("trip-form").addEventListener("submit", (event) => {
  event.preventDefault();
  runAction(async () => {
    const travelers = Number(byId("travelers").value);
    if (!Number.isSafeInteger(travelers) || travelers < 1 || travelers > 2147483647) {
      throw new Error("Travelers must be a whole number from 1 to 2147483647.");
    }
    const trip = await api("/trips", {
      method: "POST",
      body: {
        title: byId("trip-title").value,
        destination: byId("destination").value,
        start_date: byId("start-date").value,
        end_date: byId("end-date").value,
        travelers,
        budget_cents: centsFromDollars(byId("budget").value.trim()),
      },
    });
    byId("trip-form").reset();
    await afterChange("Trip created.", trip.id);
  });
});

byId("activity-form").addEventListener("submit", (event) => {
  event.preventDefault();
  runAction(async () => {
    if (!selectedTrip) throw new Error("Select a trip first.");
    const tripId = selectedTrip.id;
    await api(`/trips/${encodeURIComponent(tripId)}/activities`, {
      method: "POST",
      body: {
        title: byId("activity-title").value,
        activity_date: byId("activity-date").value,
        cost_cents: centsFromDollars(byId("activity-cost").value.trim()),
      },
    });
    byId("activity-form").reset();
    await afterChange("Activity added.", tripId);
  });
});

// Browsers can restore an old page from their back/forward cache.
window.addEventListener("pageshow", (event) => {
  if (event.persisted) window.location.reload();
});

