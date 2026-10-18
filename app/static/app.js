const SAMPLE = `Every push to main runs the Jenkins pipeline: lint, unit tests, a coverage check and a Docker build.
If all of them pass, Jenkins deploys the new image and this page shows its build number.
The quick brown fox jumps over the lazy dog!`;

const HOT_TEXT_AT = 0.55;

const text = document.getElementById("text");
const status = document.getElementById("status");
const keys = new Map(
  [...document.querySelectorAll(".key")].map((el) => [el.dataset.key, el]),
);

let timer;
let inflight;

function setText(id, value) {
  document.getElementById(id).textContent = value;
}

function render(result) {
  for (const [id, el] of keys) {
    const heat = result.intensity[id] || 0;
    const count = result.counts[id] || 0;
    el.style.setProperty("--heat", heat);
    el.classList.toggle("hot", heat >= HOT_TEXT_AT);
    el.querySelector(".count").textContent = count || "";
    el.title = `${count} ${count === 1 ? "press" : "presses"}`;
  }

  setText("keystrokes", result.keystrokes.toLocaleString());
  setText("characters", result.characters.toLocaleString());
  setText("shift", result.shift_presses.toLocaleString());
  setText("hands", `${Math.round(result.hands.left)}% / ${Math.round(result.hands.right)}%`);
  setText("home", `${Math.round(result.home_row)}%`);

  const list = document.getElementById("top-keys");
  list.replaceChildren();
  if (result.top_keys.length === 0) {
    const empty = document.createElement("li");
    empty.className = "empty";
    empty.textContent = "Nothing typed yet.";
    list.append(empty);
  }
  for (const { label, count } of result.top_keys) {
    const item = document.createElement("li");
    const name = document.createElement("span");
    name.className = "name";
    name.textContent = label;
    item.append(name, count.toLocaleString());
    list.append(item);
  }

  const unmapped = document.getElementById("unmapped");
  unmapped.hidden = result.unmapped === 0;
  unmapped.textContent = `${result.unmapped} character${result.unmapped === 1 ? "" : "s"} `
    + "can't be typed on a US keyboard and were skipped.";
}

async function analyze() {
  inflight?.abort();
  inflight = new AbortController();
  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text.value }),
      signal: inflight.signal,
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || "Something went wrong.");
    status.textContent = "";
    status.classList.remove("error");
    render(body);
  } catch (error) {
    if (error.name === "AbortError") return;
    status.textContent = error instanceof TypeError
      ? "Can't reach the server. Is the app running?"
      : error.message;
    status.classList.add("error");
  }
}

function schedule() {
  clearTimeout(timer);
  timer = setTimeout(analyze, 150);
}

text.addEventListener("input", schedule);

document.getElementById("sample").addEventListener("click", () => {
  text.value = SAMPLE;
  analyze();
});

document.getElementById("clear").addEventListener("click", () => {
  text.value = "";
  analyze();
  text.focus();
});
