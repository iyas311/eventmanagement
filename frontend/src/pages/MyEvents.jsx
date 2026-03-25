import { useState, useEffect } from 'react';
import axios from 'axios';
import { Calendar, MapPin, Users, Trash2, Plus } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function MyEvents() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const user = JSON.parse(localStorage.getItem('user'));

  const [editingEvent, setEditingEvent] = useState(null);
  const [editFormData, setEditFormData] = useState({});

  const fetchMyEvents = async () => {
    if (!user) return;
    try {
      const res = await axios.get(`/api/events/events/organizer/${user.id}`);
      setEvents(res.data);
    } catch (err) {
      setError('Failed to load your events');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMyEvents();
  }, [user?.id]);

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this event?')) return;
    try {
      await axios.delete(`/api/events/events/${id}`);
      setEvents(events.filter(e => e.id !== id));
    } catch (err) {
      alert('Failed to delete event');
    }
  };

  const handleEditClick = (event) => {
    setEditingEvent(event);
    setEditFormData({ ...event });
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`/api/events/events/${editingEvent.id}`, editFormData);
      setEvents(events.map(e => e.id === editingEvent.id ? { ...e, ...editFormData } : e));
      setEditingEvent(null);
    } catch (err) {
      alert('Failed to update event');
    }
  };

  if (loading) return <div style={{ textAlign: 'center', padding: '4rem' }}>Loading your events...</div>;

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '2rem' }}>
      {/* ... existing header ... */}
      <div className="flex-between" style={{ marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>My <span className="text-gradient">Events</span></h1>
          <p style={{ color: 'var(--text-sub)' }}>Manage the events you've created</p>
        </div>
        <button className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Plus size={20} /> Create New Event
        </button>
      </div>

      {error && <div style={{ color: '#ef4444', marginBottom: '2rem' }}>{error}</div>}

      {events.length === 0 ? (
        <div className="glass-card" style={{ textAlign: 'center', padding: '4rem' }}>
          <Calendar size={48} style={{ margin: '0 auto 1rem', opacity: 0.5 }} />
          <h3>No events found</h3>
          <p style={{ color: 'var(--text-sub)', marginBottom: '2rem' }}>You haven't created any events yet.</p>
          <button className="btn btn-outline">Start Creating</button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '2rem' }}>
          {events.map(event => (
            <div key={event.id} className="glass-card event-card" style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '1.25rem' }}>
              <div style={{ position: 'relative', height: '200px', borderRadius: '12px', overflow: 'hidden', marginBottom: '1.5rem', background: 'var(--bg-dark)' }}>
                {event.image_url ? (
                  <img 
                    src={event.image_url} 
                    alt={event.title}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                ) : (
                  <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: 0.3 }}>
                    <Calendar size={48} />
                  </div>
                )}
                <div style={{ position: 'absolute', top: '10px', right: '10px', display: 'flex', gap: '0.5rem' }}>
                  <button 
                    onClick={() => handleDelete(event.id)}
                    className="btn-icon"
                    style={{ background: 'rgba(239, 68, 68, 0.9)', color: 'white', border: 'none' }}
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
              
              <h3 style={{ fontSize: '1.5rem', marginBottom: '1rem', color: 'var(--text-main)' }}>{event.title}</h3>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', color: 'var(--text-sub)', fontSize: '0.9rem', flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Calendar size={16} className="text-primary" /> {event.date}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <MapPin size={16} className="text-primary" /> {event.location}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Users size={16} className="text-primary" /> {event.capacity} Capacity
                </div>
              </div>
              
              <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--primary)' }}>${event.price}</span>
                <button onClick={() => handleEditClick(event)} className="btn btn-outline" style={{ fontSize: '0.85rem' }}>Edit Details</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Edit Modal */}
      {editingEvent && (
        <div className="modal-overlay" onClick={() => setEditingEvent(null)}>
          <div className="glass-card" onClick={e => e.stopPropagation()} style={{ width: '100%', maxWidth: '500px', animation: 'modalIn 0.3s ease-out' }}>
            <h2 style={{ marginBottom: '1.5rem' }}>Edit Event</h2>
            <form onSubmit={handleEditSubmit}>
              <div className="input-group">
                <label className="input-label">Title</label>
                <input 
                  className="input-field"
                  value={editFormData.title}
                  onChange={e => setEditFormData({ ...editFormData, title: e.target.value })}
                  required
                />
              </div>
              <div className="input-group">
                <label className="input-label">Date</label>
                <input 
                  type="date"
                  className="input-field"
                  value={editFormData.date}
                  onChange={e => setEditFormData({ ...editFormData, date: e.target.value })}
                  required
                />
              </div>
              <div className="input-group">
                <label className="input-label">Location</label>
                <input 
                  className="input-field"
                  value={editFormData.location}
                  onChange={e => setEditFormData({ ...editFormData, location: e.target.value })}
                  required
                />
              </div>
              <div className="input-group">
                <label className="input-label">Image URL</label>
                <input 
                  className="input-field"
                  placeholder="https://example.com/image.jpg"
                  value={editFormData.image_url || ''}
                  onChange={e => setEditFormData({ ...editFormData, image_url: e.target.value })}
                />
              </div>
              <div className="input-group">
                <label className="input-label">Price ($)</label>
                <input 
                  type="number"
                  className="input-field"
                  value={editFormData.price}
                  onChange={e => setEditFormData({ ...editFormData, price: parseFloat(e.target.value) })}
                  required
                />
              </div>
              <div className="flex-between" style={{ marginTop: '2rem' }}>
                <button type="button" className="btn btn-outline" onClick={() => setEditingEvent(null)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Save Changes</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
