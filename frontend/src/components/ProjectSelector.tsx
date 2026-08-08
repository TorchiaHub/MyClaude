import { useProjects } from '../api/projects'
import { useNavigationStore } from '../store/navigationStore'

export function ProjectSelector() {
  const { data: projects } = useProjects()
  const selectedProjectPath = useNavigationStore((state) => state.selectedProjectPath)
  const setSelectedProjectPath = useNavigationStore((state) => state.setSelectedProjectPath)

  return (
    <label className="project-selector">
      Progetto:
      <select
        value={selectedProjectPath ?? ''}
        onChange={(e) => setSelectedProjectPath(e.target.value || null)}
      >
        <option value="">Globale</option>
        {projects?.map((project) => (
          <option key={project.path} value={project.path}>
            {project.path}
          </option>
        ))}
      </select>
    </label>
  )
}
