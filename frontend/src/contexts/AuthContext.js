
// src/contexts/AuthContext.jsx
import React, { createContext, useState, useEffect } from "react";
import api from "../api";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  // store the hydrated user object (null when not signed in)
  const [user, setUser] = useState(null);
  // loadingMe indicates whether we are hydrating from backend
  const [loadingMe, setLoadingMe] = useState(false);

  useEffect(() => {
    // hydrate on mount if token present
    const token = localStorage.getItem("access_token");
    if (!token) return;

    // ensure axios will send the token immediately
    api.defaults.headers.common.Authorization = `Bearer ${token}`;

    setLoadingMe(true);
    (async () => {
      try {
        const res = await api.get("/users/me");
        setUser(res.data);
      } catch (err) {
        console.error("Auth hydration failed", err?.response?.status, err?.response?.data);
        // token invalid -> remove it
        localStorage.removeItem("access_token");
        delete api.defaults.headers.common.Authorization;
        setUser(null);
      } finally {
        setLoadingMe(false);
      }
    })();
  }, []);

  const signup = async ({ name, email, password, mobile }) => {
    const res = await api.post("/auth/signup", { name, email, password, mobile });
    const token = res.data.access_token;
    localStorage.setItem("access_token", token);
    // set default header immediately so next request has it
    api.defaults.headers.common.Authorization = `Bearer ${token}`;

    const me = await api.get("/users/me");
    setUser(me.data);
    return res;
  };

  const signin = async ({ email, password }) => {
    const res = await api.post("/auth/signin", { email, password });
    const token = res.data.access_token;
    localStorage.setItem("access_token", token);
    api.defaults.headers.common.Authorization = `Bearer ${token}`;

    const me = await api.get("/users/me");
    setUser(me.data);
    return res;
  };

  const signout = () => {
    localStorage.removeItem("access_token");
    delete api.defaults.headers.common.Authorization;
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loadingMe, signup, signin, signout }}>
      {children}
    </AuthContext.Provider>
  );
};
