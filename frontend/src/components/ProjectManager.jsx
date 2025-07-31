import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Plus, Edit, Trash2, Settings, Cloud, Database, GitBranch, Key, TestTube } from 'lucide-react'

const ProjectManager = () => {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(false)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [selectedProject, setSelectedProject] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    cloud_provider: '',
    state_bucket_url: '',
    git_repo_url: '',
    git_ssh_key: '',
    llm_provider: 'gemini',
    llm_api_key: '',
    system_prompt: ''
  })

  useEffect(() => {
    fetchProjects()
  }, [])

  const fetchProjects = async () => {
    try {
      const response = await fetch('/api/projects')
      if (response.ok) {
        const data = await response.json()
        setProjects(data)
      }
    } catch (error) {
      console.error('Error fetching projects:', error)
    }
  }

  const handleCreateProject = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      if (response.ok) {
        setIsCreateDialogOpen(false)
        resetForm()
        fetchProjects()
      } else {
        const error = await response.json()
        alert(`Error: ${error.error}`)
      }
    } catch (error) {
      console.error('Error creating project:', error)
      alert('Error creating project')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateProject = async () => {
    setLoading(true)
    try {
      const response = await fetch(`/api/projects/${selectedProject.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      if (response.ok) {
        setIsEditDialogOpen(false)
        resetForm()
        fetchProjects()
      } else {
        const error = await response.json()
        alert(`Error: ${error.error}`)
      }
    } catch (error) {
      console.error('Error updating project:', error)
      alert('Error updating project')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteProject = async (projectId) => {
    if (!confirm('¿Estás seguro de que quieres eliminar este proyecto?')) {
      return
    }

    try {
      const response = await fetch(`/api/projects/${projectId}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        fetchProjects()
      } else {
        const error = await response.json()
        alert(`Error: ${error.error}`)
      }
    } catch (error) {
      console.error('Error deleting project:', error)
      alert('Error deleting project')
    }
  }

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      cloud_provider: '',
      state_bucket_url: '',
      git_repo_url: '',
      git_ssh_key: '',
      llm_provider: 'gemini',
      llm_api_key: '',
      system_prompt: ''
    })
    setSelectedProject(null)
  }

  const openEditDialog = (project) => {
    setSelectedProject(project)
    setFormData({
      name: project.name || '',
      description: project.description || '',
      cloud_provider: project.cloud_provider || '',
      state_bucket_url: project.state_bucket_url || '',
      git_repo_url: project.git_repo_url || '',
      git_ssh_key: project.git_ssh_key || '',
      llm_provider: project.llm_provider || 'gemini',
      llm_api_key: project.llm_api_key || '',
      system_prompt: project.system_prompt || ''
    })
    setIsEditDialogOpen(true)
  }

  const testConnection = async (type, projectId) => {
    try {
      let endpoint = ''
      switch (type) {
        case 'llm':
          endpoint = '/api/llm/test-connection'
          break
        case 'git':
          endpoint = '/api/git/test-connection'
          break
        case 'state':
          endpoint = '/api/state/test-connection'
          break
        default:
          return
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ project_id: projectId }),
      })

      const result = await response.json()
      if (result.success) {
        alert(`Conexión ${type.toUpperCase()} exitosa`)
      } else {
        alert(`Error en conexión ${type.toUpperCase()}: ${result.error}`)
      }
    } catch (error) {
      console.error(`Error testing ${type} connection:`, error)
      alert(`Error probando conexión ${type.toUpperCase()}`)
    }
  }

  const getCloudProviderIcon = (provider) => {
    switch (provider?.toLowerCase()) {
      case 'aws':
        return '🟠'
      case 'azure':
        return '🔵'
      case 'gcp':
        return '🟡'
      default:
        return '☁️'
    }
  }

  const ProjectForm = ({ isEdit = false }) => (
    <Tabs defaultValue="basic" className="w-full">
      <TabsList className="grid w-full grid-cols-4">
        <TabsTrigger value="basic">Básico</TabsTrigger>
        <TabsTrigger value="llm">LLM</TabsTrigger>
        <TabsTrigger value="state">Estado</TabsTrigger>
        <TabsTrigger value="git">Git</TabsTrigger>
      </TabsList>

      <TabsContent value="basic" className="space-y-4">
        <div>
          <Label htmlFor="name">Nombre del Proyecto</Label>
          <Input
            id="name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="mi-proyecto-iac"
          />
        </div>
        <div>
          <Label htmlFor="description">Descripción</Label>
          <Textarea
            id="description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="Descripción del proyecto..."
          />
        </div>
        <div>
          <Label htmlFor="cloud_provider">Proveedor de Nube</Label>
          <Select value={formData.cloud_provider} onValueChange={(value) => setFormData({ ...formData, cloud_provider: value })}>
            <SelectTrigger>
              <SelectValue placeholder="Selecciona un proveedor" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="aws">Amazon Web Services (AWS)</SelectItem>
              <SelectItem value="azure">Microsoft Azure</SelectItem>
              <SelectItem value="gcp">Google Cloud Platform (GCP)</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </TabsContent>

      <TabsContent value="llm" className="space-y-4">
        <div>
          <Label htmlFor="llm_provider">Proveedor LLM</Label>
          <Select value={formData.llm_provider} onValueChange={(value) => setFormData({ ...formData, llm_provider: value })}>
            <SelectTrigger>
              <SelectValue placeholder="Selecciona un proveedor LLM" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="gemini">Google Gemini</SelectItem>
              <SelectItem value="openai">OpenAI GPT</SelectItem>
              <SelectItem value="claude">Anthropic Claude</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label htmlFor="llm_api_key">API Key del LLM</Label>
          <Input
            id="llm_api_key"
            type="password"
            value={formData.llm_api_key}
            onChange={(e) => setFormData({ ...formData, llm_api_key: e.target.value })}
            placeholder="sk-..."
          />
        </div>
        <div>
          <Label htmlFor="system_prompt">System Prompt Personalizado</Label>
          <Textarea
            id="system_prompt"
            value={formData.system_prompt}
            onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
            placeholder="Instrucciones específicas para el LLM..."
            rows={4}
          />
        </div>
      </TabsContent>

      <TabsContent value="state" className="space-y-4">
        <div>
          <Label htmlFor="state_bucket_url">URL del Bucket de Estado</Label>
          <Input
            id="state_bucket_url"
            value={formData.state_bucket_url}
            onChange={(e) => setFormData({ ...formData, state_bucket_url: e.target.value })}
            placeholder="s3://mi-bucket-terraform o gs://mi-bucket-terraform"
          />
        </div>
      </TabsContent>

      <TabsContent value="git" className="space-y-4">
        <div>
          <Label htmlFor="git_repo_url">URL del Repositorio Git</Label>
          <Input
            id="git_repo_url"
            value={formData.git_repo_url}
            onChange={(e) => setFormData({ ...formData, git_repo_url: e.target.value })}
            placeholder="https://github.com/usuario/repositorio.git"
          />
        </div>
        <div>
          <Label htmlFor="git_ssh_key">Clave SSH (opcional)</Label>
          <Textarea
            id="git_ssh_key"
            value={formData.git_ssh_key}
            onChange={(e) => setFormData({ ...formData, git_ssh_key: e.target.value })}
            placeholder="-----BEGIN OPENSSH PRIVATE KEY-----..."
            rows={4}
          />
        </div>
      </TabsContent>
    </Tabs>
  )

  return (
    <div className="space-y-6">
      {/* Header con botón de crear */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Gestión de Proyectos</h2>
          <p className="text-gray-600">Configura y administra tus proyectos de infraestructura</p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={resetForm}>
              <Plus className="h-4 w-4 mr-2" />
              Nuevo Proyecto
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Crear Nuevo Proyecto</DialogTitle>
              <DialogDescription>
                Configura un nuevo proyecto de infraestructura como código
              </DialogDescription>
            </DialogHeader>
            <ProjectForm />
            <div className="flex justify-end space-x-2 pt-4">
              <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                Cancelar
              </Button>
              <Button onClick={handleCreateProject} disabled={loading}>
                {loading ? 'Creando...' : 'Crear Proyecto'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Lista de proyectos */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {projects.map((project) => (
          <Card key={project.id} className="relative">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center space-x-2">
                  <span>{getCloudProviderIcon(project.cloud_provider)}</span>
                  <span>{project.name}</span>
                </CardTitle>
                <div className="flex space-x-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => openEditDialog(project)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteProject(project.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <CardDescription>{project.description || 'Sin descripción'}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center space-x-2">
                <Cloud className="h-4 w-4 text-gray-500" />
                <Badge variant="secondary">{project.cloud_provider?.toUpperCase()}</Badge>
              </div>
              
              {project.llm_provider && (
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Key className="h-4 w-4 text-gray-500" />
                    <span className="text-sm">LLM: {project.llm_provider}</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => testConnection('llm', project.id)}
                  >
                    <TestTube className="h-4 w-4" />
                  </Button>
                </div>
              )}
              
              {project.state_bucket_url && (
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Database className="h-4 w-4 text-gray-500" />
                    <span className="text-sm">Estado configurado</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => testConnection('state', project.id)}
                  >
                    <TestTube className="h-4 w-4" />
                  </Button>
                </div>
              )}
              
              {project.git_repo_url && (
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <GitBranch className="h-4 w-4 text-gray-500" />
                    <span className="text-sm">Git configurado</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => testConnection('git', project.id)}
                  >
                    <TestTube className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {projects.length === 0 && (
        <Card>
          <CardContent className="text-center py-8">
            <Cloud className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No hay proyectos</h3>
            <p className="text-gray-500 mb-4">Crea tu primer proyecto para comenzar</p>
            <Button onClick={() => setIsCreateDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Crear Primer Proyecto
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Dialog de edición */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Editar Proyecto</DialogTitle>
            <DialogDescription>
              Modifica la configuración del proyecto
            </DialogDescription>
          </DialogHeader>
          <ProjectForm isEdit={true} />
          <div className="flex justify-end space-x-2 pt-4">
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              Cancelar
            </Button>
            <Button onClick={handleUpdateProject} disabled={loading}>
              {loading ? 'Guardando...' : 'Guardar Cambios'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default ProjectManager

