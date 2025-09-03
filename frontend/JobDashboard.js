// frontend/JobDashboard.js
export default function JobDashboard() {
  const { useEffect, useState } = React;
  const [jobs, setJobs] = useState([]);
  const [filter, setFilter] = useState({ company: '', state: '', title: '' });
  const [uploading, setUploading] = useState(false);

  async function fetchJobs() {
    try {
      const res = await axios.get(`${API}/jobs`);
      setJobs(res.data);
    } catch (e) {
      console.error('Fetch jobs failed', e);
    }
  }

  useEffect(() => { fetchJobs(); }, []);

  async function handleUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      await axios.post(`${API}/upload`, formData);
      await fetchJobs();
    } catch (e) {
      console.error('Upload failed', e);
    } finally {
      setUploading(false);
    }
  }

  const filtered = jobs.filter(j =>
    (j.company || '').toLowerCase().includes(filter.company.toLowerCase()) &&
    (j.state || '').toLowerCase().includes(filter.state.toLowerCase()) &&
    (j.title || '').toLowerCase().includes(filter.title.toLowerCase())
  );

  return React.createElement('div', { style: { padding: 20 } },
    React.createElement('h2', null, 'Career Scraper Dashboard'),

    React.createElement('div', { style: { display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 } },
      React.createElement('input', {
        placeholder: 'Filter by company',
        onChange: e => setFilter(f => ({ ...f, company: e.target.value }))
      }),
      React.createElement('input', {
        placeholder: 'Filter by state',
        onChange: e => setFilter(f => ({ ...f, state: e.target.value }))
      }),
      React.createElement('input', {
        placeholder: 'Filter by title',
        onChange: e => setFilter(f => ({ ...f, title: e.target.value }))
      }),
      React.createElement('input', { type: 'file', accept: '.csv', onChange: handleUpload }),
      uploading && React.createElement('span', null, 'Uploading...')
    ),

    React.createElement('table', { border: '1', cellPadding: 6, style: { width: '100%' } },
      React.createElement('thead', null,
        React.createElement('tr', null,
          React.createElement('th', null, 'Company'),
          React.createElement('th', null, 'Title'),
          React.createElement('th', null, 'Location'),
          React.createElement('th', null, 'State')
        )
      ),
      React.createElement('tbody', null,
        filtered.map((j, i) =>
          React.createElement('tr', { key: i },
            React.createElement('td', null, j.company),
            React.createElement('td', null, j.title),
            React.createElement('td', null, j.location),
            React.createElement('td', null, j.state)
          )
        )
      )
    ),

    React.createElement('div', { style: { marginTop: 12 } },
      React.createElement('a', {
        href: `${API}/download`,
        target: '_blank',
        rel: 'noopener noreferrer'
      }, 'Download CSV')
    )
  );
}
