import React, { useState, useEffect } from 'react';
import useAuthStore from '../store/authStore';
import { aiAPI, taskAPI, gmailAPI } from '../services/api';

function Dashboard() {
  const logout = useAuthStore((state) => state.logout);
  const [tasks, setTasks] = useState([]);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const fetchTasks = async () => {
    try {
      const res = await taskAPI.getAll();
      setTasks(res.data);
    } catch (err) {
      console.error("Failed to fetch tasks", err);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const handleSyncAndAnalyze = async () => {
    setIsSyncing(true);
    try {
      await gmailAPI.sync();
    } catch (e) {
      console.error("Sync error", e);
    }
    setIsSyncing(false);
    
    setIsAnalyzing(true);
    try {
      const res = await aiAPI.analyze();
      alert(`Processed ${res.data.emails_processed} emails. Created ${res.data.tasks_created} tasks!`);
      fetchTasks();
    } catch (e) {
      console.error("Analysis error", e);
      alert("Analysis failed");
    }
    setIsAnalyzing(false);
  };

  const markCompleted = async (id) => {
    try {
      await taskAPI.updateStatus(id, "Completed");
      fetchTasks();
    } catch (e) {
      console.error(e);
      alert("Update failed");
    }
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Dashboard</h1>
        <div className="header-actions">
          <button 
            className="btn-primary" 
            onClick={handleSyncAndAnalyze} 
            disabled={isSyncing || isAnalyzing}
          >
            {isSyncing ? "Syncing Gmail..." : isAnalyzing ? "AI Analyzing..." : "Sync & Analyze Emails"}
          </button>
          <button className="btn-secondary" onClick={logout}>Logout</button>
        </div>
      </header>
      <main className="dashboard-main">
        {tasks.length === 0 ? (
          <p>No actionable tasks found. Click "Sync & Analyze Emails" to get started.</p>
        ) : (
          <div className="task-list">
            {tasks.map(task => (
              <div key={task._id} className={`task-card ${task.status === 'Completed' ? 'completed' : ''}`}>
                <div className="task-header">
                  <h3>{task.title}</h3>
                  <span className={`priority-badge ${task.priority.toLowerCase()}`}>
                    {task.priority}
                  </span>
                </div>
                <p className="task-desc">{task.description}</p>
                <div className="task-meta">
                  {task.deadline && <span className="deadline">Deadline: {task.deadline}</span>}
                  <span className="category">{task.category}</span>
                </div>
                <p className="task-summary"><strong>Context:</strong> {task.summary}</p>
                
                {task.status !== 'Completed' && (
                  <button className="btn-success" onClick={() => markCompleted(task._id)}>
                    Mark Completed
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

export default Dashboard;
