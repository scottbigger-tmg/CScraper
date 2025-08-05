
// JobDashboard.js - React frontend for career scraper cloud app
import React, { useEffect, useState } from 'react';
import axios from 'axios';

const API = 'https://your-flask-api.onrender.com'; // replace with actual URL

export default function JobDashboard() {
  const [jobs, setJobs] = useState([]);
  const [filter, setFilter] = useState({ company: '', state: '', title: '' });
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    const res = await axios.get(`${API}/jobs`);
    setJobs(res.data);
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    await axios.post(`${API}/upload`, formData);
    setUploading(false);
    fetchJobs();
  };

  const filteredJobs = jobs.filter(j =>
    j.company.toLowerCase().includes(filter.company.toLowerCase()) &&
    j.state.toLowerCase().includes(filter.state.toLowerCase()) &&
    j.title.toLowerCase().includes(filter.title.toLowerCase())
  );

  return (
    <div style={{ padding: 20 }}>
      <h2>Staffing Opportunity Dashboard</h2>

      <div>
        <input placeholder="Filter by company" onChange={e => setFilter({ ...filter, company: e.target.value })} />
        <input placeholder="Filter by state" onChange={e => setFilter({ ...filter, state: e.target.value })} />
        <input placeholder="Filter by title" onChange={e => setFilter({ ...filter, title: e.target.value })} />
        <input type="file" accept=".csv" onChange={handleUpload} />
        {uploading && <span>Uploading...</span>}
        <a href={`${API}/download`} target="_blank" rel="noopener noreferrer">Download CSV</a>
      </div>

      <table border="1" cellPadding="6" style={{ marginTop: 20, width: '100%' }}>
        <thead>
          <tr>
            <th>Company</th>
            <th>Title</th>
            <th>Location</th>
            <th>State</th>
          </tr>
        </thead>
        <tbody>
          {filteredJobs.map((j, i) => (
            <tr key={i}>
              <td>{j.company}</td>
              <td>{j.title}</td>
              <td>{j.location}</td>
              <td>{j.state}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
