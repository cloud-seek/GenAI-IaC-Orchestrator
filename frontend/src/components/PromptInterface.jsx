import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import TerraformWorkflow from './TerraformWorkflow'
import { Send, Clock, CheckCircle, XCircle, AlertCircle, Zap } from 'lucide-react'

const PromptInterface = () => {
  const [projects, setProjects] = useState([])
  const [selectedProject, setSelectedProject] = useState('')
  const [prompt, setPrompt] = useState('')
  const [prompts, setPrompts] = useState([])
  const [loading, setLoading] = useState(false)
  const [processingPrompt, setProcessingPrompt] = useState(null)
  const [showWorkflow, setShowWorkflow] = useState(false)

  // Cargar proyectos al montar el componente
  useEffect(() => {
    fetchProjects()
  }, [])

  // Cargar prompts cuando se selecciona un proyecto
  useEffect(() => {
    if (selectedProject) {
      fetchPrompts(selectedProject)
    }
  }, [selectedProject])

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

  const fetchPrompts = async (projectId) => {
    try {
      const response = await fetch(`/api/projects/${projectId}/prompts`)
      if (response.ok) {
        const data = await response.json()
        setPrompts(data)
      }
    } catch (error) {
      console.error('Error fetching prompts:', error)
    }
  }

  const handleSubmitPrompt = async () => {
    if (!selectedProject || !prompt.trim()) {
      return
    }

    const selectedProjectData = projects.find(p => p.id.toString() === selectedProject)
    if (!selectedProjectData?.llm_api_key) {
      alert('El proyecto seleccionado no tiene configurada una API key de LLM')
      return
    }

    setLoading(true)
    try {
      // Procesar el prompt con LLM
      const response = await fetch('/api/llm/process-prompt', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_id: parseInt(selectedProject),
          user_prompt: prompt.trim(),
        }),
      })

      const result = await response.json()

      if (result.success) {
        setPrompt('')
        
        // Crear objeto de prompt procesado
        const processedPrompt = {
          id: result.prompt_id,
          user_prompt: prompt.trim(),
          llm_response: result.analysis,
          terraform_code: result.terraform_code,
          status: 'completed',
          created_at: new Date().toISOString()
        }
        
        setProcessingPrompt(processedPrompt)
        setShowWorkflow(true)
        fetchPrompts(selectedProject) // Recargar prompts
      } else {
        alert(`Error procesando prompt: ${result.error}`)
      }
    } catch (error) {
      console.error('Error submitting prompt:', error)
      alert('Error procesando prompt')
    } finally {
      setLoading(false)
    }
  }

  const handleWorkflowComplete = () => {
    setShowWorkflow(false)
    setProcessingPrompt(null)
    fetchPrompts(selectedProject) // Recargar prompts
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-4 w-4" />
      case 'processing':
        return <Clock className="h-4 w-4 animate-spin" />
      case 'completed':
        return <Zap className="h-4 w-4" />
      case 'approved':
        return <CheckCircle className="h-4 w-4" />
      case 'applied':
        return <CheckCircle className="h-4 w-4" />
      case 'failed':
        return <XCircle className="h-4 w-4" />
      default:
        return <AlertCircle className="h-4 w-4" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      case 'processing':
        return 'bg-blue-100 text-blue-800'
      case 'completed':
        return 'bg-purple-100 text-purple-800'
      case 'approved':
        return 'bg-blue-100 text-blue-800'
      case 'applied':
        return 'bg-green-100 text-green-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const selectedProjectData = projects.find(p => p.id.toString() === selectedProject)

  return (
    <div className="space-y-6">
      {/* Selector de proyecto y entrada de prompt */}
      <Card>
        <CardHeader>
          <CardTitle>Consola de Prompts</CardTitle>
          <CardDescription>
            Describe los cambios o recursos que necesitas en lenguaje natural
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">Proyecto</label>
            <Select value={selectedProject} onValueChange={setSelectedProject}>
              <SelectTrigger>
                <SelectValue placeholder="Selecciona un proyecto" />
              </SelectTrigger>
              <SelectContent>
                {projects.map((project) => (
                  <SelectItem key={project.id} value={project.id.toString()}>
                    {project.name} ({project.cloud_provider})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {selectedProjectData && !selectedProjectData.llm_api_key && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Este proyecto no tiene configurada una API key de LLM. Ve a la sección de Proyectos para configurarla.
              </AlertDescription>
            </Alert>
          )}

          <div>
            <label className="text-sm font-medium mb-2 block">Prompt</label>
            <Textarea
              placeholder="Ej: Crear una base de datos PostgreSQL de alta disponibilidad..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={4}
            />
          </div>

          <Button
            onClick={handleSubmitPrompt}
            disabled={!selectedProject || !prompt.trim() || loading || !selectedProjectData?.llm_api_key}
            className="w-full"
          >
            <Send className="h-4 w-4 mr-2" />
            {loading ? 'Procesando...' : 'Enviar Prompt'}
          </Button>
        </CardContent>
      </Card>

      {/* Flujo de trabajo de Terraform */}
      {showWorkflow && processingPrompt && selectedProjectData && (
        <TerraformWorkflow
          selectedProject={selectedProjectData}
          prompt={processingPrompt}
          onWorkflowComplete={handleWorkflowComplete}
        />
      )}

      {/* Historial de prompts */}
      {selectedProject && !showWorkflow && (
        <Card>
          <CardHeader>
            <CardTitle>Historial de Prompts</CardTitle>
            <CardDescription>
              Prompts enviados para el proyecto seleccionado
            </CardDescription>
          </CardHeader>
          <CardContent>
            {prompts.length === 0 ? (
              <p className="text-gray-500 text-center py-4">
                No hay prompts para este proyecto
              </p>
            ) : (
              <div className="space-y-4">
                {prompts.map((promptItem) => (
                  <div
                    key={promptItem.id}
                    className="border rounded-lg p-4 space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <Badge className={getStatusColor(promptItem.status)}>
                        {getStatusIcon(promptItem.status)}
                        <span className="ml-1 capitalize">{promptItem.status}</span>
                      </Badge>
                      <span className="text-sm text-gray-500">
                        {new Date(promptItem.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-sm">{promptItem.user_prompt}</p>
                    {promptItem.llm_response && (
                      <div className="bg-gray-50 p-3 rounded text-sm">
                        <strong>Análisis LLM:</strong>
                        <p className="mt-1">{promptItem.llm_response}</p>
                      </div>
                    )}
                    {promptItem.terraform_code && (
                      <div className="bg-gray-50 p-3 rounded text-sm">
                        <strong>Código Terraform:</strong>
                        <pre className="mt-1 text-xs overflow-x-auto">
                          {promptItem.terraform_code.substring(0, 200)}...
                        </pre>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default PromptInterface

