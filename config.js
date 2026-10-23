// API URL for advanced server-side tools.
// The Docker/full-stack app listens on port 5000 and uses same-origin API routes.
// Static hosting defaults to browser-only mode. For a separate backend, set its HTTPS URL here.
const isLocalFullStack = window.location.port === "5000";
window.IHP_API_BASE = isLocalFullStack ? window.location.origin : "";
