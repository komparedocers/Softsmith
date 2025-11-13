import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

interface Event {
  timestamp: string;
  level: string;
  message: string;
}

export default function ProjectDetail() {
  const { id } = useParams();
  const [project, setProject] = useState<any>(null);
  const [events, setEvents] = useState<Event[]>([]);

  useEffect(() => {
    fetchProject();
    fetchEvents();
  }, [id]);

  const fetchProject = async () => {
    try {
      const response = await axios.get(`/api/projects/${id}`);
      setProject(response.data);
    } catch (error) {
      console.error('Failed to fetch project:', error);
    }
  };

  const fetchEvents = async () => {
    try {
      const response = await axios.get(`/api/projects/${id}/events`);
      setEvents(response.data);
    } catch (error) {
      console.error('Failed to fetch events:', error);
    }
  };

  if (!project) return <div>Loading...</div>;

  return (
    <main>
      <h2>{project.name}</h2>
      <p>Status: {project.status}</p>
      <p>Progress: {project.completed_tasks}/{project.total_tasks}</p>

      <div className="events">
        <h3>Activity Log</h3>
        {events.map((event, idx) => (
          <div key={idx} className="event">
            <span className="timestamp">{event.timestamp}</span>
            <span className={`level ${event.level}`}>{event.level}</span>
            <span className="message">{event.message}</span>
          </div>
        ))}
      </div>
    </main>
  );
}
