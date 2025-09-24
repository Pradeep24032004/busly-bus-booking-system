import React, { useState, useContext } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "../contexts/AuthContext";

export default function Signup() {
  const { signup } = useContext(AuthContext);
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", mobile: "" });
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(false);

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const onSubmit = async (e) => {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      await signup(form);
      navigate("/");
    } catch (error) {
      setErr(error.response?.data?.detail || error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card auth-card">
      <h2>Create account</h2>
      <form onSubmit={onSubmit}>
        <label>Name</label>
        <input name="name" value={form.name} onChange={onChange} required />

        <label>Mobile</label>
        <input name="mobile" value={form.mobile} onChange={onChange} required />

        <label>Email</label>
        <input name="email" type="email" value={form.email} onChange={onChange} required />

        <label>Password</label>
        <input name="password" type="password" value={form.password} onChange={onChange} required />

        {err && <div className="error">{JSON.stringify(err)}</div>}
        <button className="btn" type="submit" disabled={loading}>
          {loading ? "Signing up..." : "Sign up (₹1000 credited)"}
        </button>
      </form>
    </div>
  );
}
