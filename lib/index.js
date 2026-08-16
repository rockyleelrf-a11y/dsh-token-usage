// Host half: the dashboard is a client-side UI plugin. This host entry keeps
// the plugin present in the profile/loader graph without adding server logic.
export const name = "dsh-token-usage"
export const inject = []
export function apply() {
  // no-op: all functionality is in lib/client.js
}
