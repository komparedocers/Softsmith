import { useState, useEffect } from 'react';
import axios from 'axios';

interface Project {
  id: string;
  name: string;
  status: string;
  created_at: string;
  completed_tasks: number;
  total_tasks: number;
}

export default function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [newPrompt, setNewPrompt] = useState('');

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await axios.get('/api/projects');
      setProjects(response.data);
    } catch (error) {
      console.error('Failed to fetch projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const createProject = async () => {
    if (!newPrompt.trim()) return;

    try {
      await axios.post('/api/projects', { prompt: newPrompt });
      setNewPrompt('');
      fetchProjects();
    } catch (error) {
      console.error('Failed to create project:', error);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <main>
      <h2>Dashboard</h2>

      <div className="create-project">
        <h3>Create New Project</h3>
        <textarea
          value={newPrompt}
          onChange={(e) => setNewPrompt(e.target.value)}
          placeholder="Describe the software you want to build..."
          rows={4}
        />
        <button onClick={createProject}>Create Project</button>
      </div>

      <div className="projects-list">
        <h3>Projects</h3>
        {projects.map((project) => (
          <div key={project.id} className="project-card">
            <h4>{project.name}</h4>
            <p>Status: {project.status}</p>
            <p>Progress: {project.completed_tasks}/{project.total_tasks}</p>
            <a href={`/project/${project.id}`}>View Details</a>
          </div>
        ))}
      </div>
    </main>
  );
}
