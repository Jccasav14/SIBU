import { reactive } from "vue";

const TOKEN_KEY = "sibu_auth_token";
const USER_KEY = "sibu_auth_user";

const state = reactive({
  token: localStorage.getItem(TOKEN_KEY) || "",
  user: JSON.parse(localStorage.getItem(USER_KEY) || "null"),
});

export const auth = {
  token() {
    return state.token;
  },
  user() {
    return state.user;
  },
  isAuthenticated() {
    return Boolean(state.token);
  },
  mustChangePassword() {
    return Boolean(state.user?.must_change_password);
  },

  // 🔥 ESTA FUNCIÓN FALTABA
  updateUser(patch) {
    if (!state.user) return;
    state.user = { ...state.user, ...patch };
    localStorage.setItem(USER_KEY, JSON.stringify(state.user));
  },

  setSession(token, user) {
    state.token = token;
    state.user = user;
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },

  logout() {
    state.token = "";
    state.user = null;
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
};
