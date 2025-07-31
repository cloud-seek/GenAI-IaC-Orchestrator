import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { CheckCircle, XCircle, Clock, Play, Eye, GitCommit, AlertTriangle } from 'lucide-react'

const TerraformWorkflow = ({ selectedProject, prompt, onWorkflowComplete }) => {
  const [currentStep, setCurrentStep] = useState('processing') // processing, plan, approval, apply, complete
  const [planData, setPlanData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showPlanDialog, setShowPlanDialog] = useState(false)
  const [applyOutput, setApplyOutput] = useState('')

  useEffect(() => {
    if (prompt && prompt.terraform_code) {
      generateTerraformPlan()
    }
  }, [prompt])

  const generateTerraformPlan = async () => {
    setLoading(true)
    setError(null)
    setCurrentStep('processing')

    try {
      const response = await fetch('/api/terraform/plan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_id: selectedProject.id,
          terraform_code: prompt.terraform_code,
          prompt_id: prompt.id
        }),
      })

      const result = await response.json()

      if (result.success) {
        setPlanData(result)
        setCurrentStep('plan')
      } else {
        setError(result.error)
        setCurrentStep('error')
      }
    } catch (error) {
      console.error('Error generating plan:', error)
      setError('Error generando el plan de Terraform')
      setCurrentStep('error')
    } finally {
      setLoading(false)
    }
  }

  const approvePlan = async () => {
    if (!planData?.plan_id) return

    setLoading(true)
    try {
      const response = await fetch(`/api/terraform/plan/${planData.plan_id}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      const result = await response.json()

      if (result.success) {
        setCurrentStep('approval')
      } else {
        setError(result.error)
      }
    } catch (error) {
      console.error('Error approving plan:', error)
      setError('Error aprobando el plan')
    } finally {
      setLoading(false)
    }
  }

  const applyPlan = async () => {
    if (!planData?.plan_id) return

    setLoading(true)
    setCurrentStep('apply')

    try {
      const response = await fetch('/api/terraform/apply', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          plan_id: planData.plan_id
        }),
      })

      const result = await response.json()

      if (result.success) {
        setApplyOutput(result.output)
        setCurrentStep('complete')
        
        // Sincronizar con Git si está configurado
        if (selectedProject.git_repo_url) {
          await syncWithGit()
        }
        
        if (onWorkflowComplete) {
          onWorkflowComplete(result)
        }
      } else {
        setError(result.error)
        setCurrentStep('error')
      }
    } catch (error) {
      console.error('Error applying plan:', error)
      setError('Error aplicando el plan')
      setCurrentStep('error')
    } finally {
      setLoading(false)
    }
  }

  const syncWithGit = async () => {
    try {
      await fetch('/api/git/sync-terraform', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_id: selectedProject.id,
          terraform_code: prompt.terraform_code,
          commit_message: `feat: ${prompt.user_prompt.substring(0, 50)}...`
        }),
      })
    } catch (error) {
      console.error('Error syncing with Git:', error)
    }
  }

  const getStepStatus = (step) => {
    const stepOrder = ['processing', 'plan', 'approval', 'apply', 'complete']
    const currentIndex = stepOrder.indexOf(currentStep)
    const stepIndex = stepOrder.indexOf(step)

    if (currentStep === 'error') {
      return stepIndex <= stepOrder.indexOf('processing') ? 'error' : 'pending'
    }

    if (stepIndex < currentIndex) return 'completed'
    if (stepIndex === currentIndex) return 'current'
    return 'pending'
  }

  const getStepIcon = (step) => {
    const status = getStepStatus(step)
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'current':
        return loading ? <Clock className="h-5 w-5 text-blue-500 animate-spin" /> : <Play className="h-5 w-5 text-blue-500" />
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />
      default:
        return <Clock className="h-5 w-5 text-gray-400" />
    }
  }

  const steps = [
    {
      id: 'processing',
      title: 'Procesando',
      description: 'Generando código Terraform con IA'
    },
    {
      id: 'plan',
      title: 'Plan Generado',
      description: 'Revisión del plan de ejecución'
    },
    {
      id: 'approval',
      title: 'Aprobación',
      description: 'Plan aprobado para ejecución'
    },
    {
      id: 'apply',
      title: 'Aplicando',
      description: 'Ejecutando cambios en la infraestructura'
    },
    {
      id: 'complete',
      title: 'Completado',
      description: 'Cambios aplicados exitosamente'
    }
  ]

  return (
    <div className="space-y-6">
      {/* Progress Steps */}
      <Card>
        <CardHeader>
          <CardTitle>Flujo de Ejecución de Terraform</CardTitle>
          <CardDescription>
            Seguimiento del proceso de aplicación de cambios
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center space-x-3">
                {getStepIcon(step.id)}
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <h4 className="font-medium">{step.title}</h4>
                    <Badge variant={getStepStatus(step.id) === 'completed' ? 'default' : 'secondary'}>
                      {getStepStatus(step.id)}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-500">{step.description}</p>
                </div>
                {index < steps.length - 1 && (
                  <div className="w-px h-8 bg-gray-200 ml-2" />
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Plan Review */}
      {currentStep === 'plan' && planData && (
        <Card>
          <CardHeader>
            <CardTitle>Plan de Terraform Generado</CardTitle>
            <CardDescription>
              Revisa los cambios que se aplicarán a tu infraestructura
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center space-x-2">
              <Badge variant={planData.has_changes ? 'default' : 'secondary'}>
                {planData.has_changes ? 'Cambios detectados' : 'Sin cambios'}
              </Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowPlanDialog(true)}
              >
                <Eye className="h-4 w-4 mr-2" />
                Ver Plan Completo
              </Button>
            </div>

            {planData.has_changes && (
              <div className="space-y-3">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Resumen del Plan:</h4>
                  <pre className="text-sm text-gray-700 whitespace-pre-wrap max-h-40 overflow-y-auto">
                    {planData.plan_output?.substring(0, 500)}...
                  </pre>
                </div>

                <div className="flex space-x-2">
                  <Button onClick={approvePlan} disabled={loading}>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    {loading ? 'Aprobando...' : 'Aprobar Plan'}
                  </Button>
                  <Button variant="outline" onClick={() => setCurrentStep('error')}>
                    <XCircle className="h-4 w-4 mr-2" />
                    Rechazar
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Approval Confirmation */}
      {currentStep === 'approval' && (
        <Card>
          <CardHeader>
            <CardTitle>Plan Aprobado</CardTitle>
            <CardDescription>
              El plan ha sido aprobado y está listo para aplicarse
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Alert>
                <CheckCircle className="h-4 w-4" />
                <AlertDescription>
                  El plan ha sido aprobado. Los cambios se aplicarán a tu infraestructura.
                </AlertDescription>
              </Alert>
              
              <Button onClick={applyPlan} disabled={loading}>
                <Play className="h-4 w-4 mr-2" />
                {loading ? 'Aplicando...' : 'Aplicar Cambios'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Apply Progress */}
      {currentStep === 'apply' && (
        <Card>
          <CardHeader>
            <CardTitle>Aplicando Cambios</CardTitle>
            <CardDescription>
              Terraform está aplicando los cambios a tu infraestructura
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-blue-500 animate-spin" />
              <span>Aplicando cambios...</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Completion */}
      {currentStep === 'complete' && (
        <Card>
          <CardHeader>
            <CardTitle>Cambios Aplicados Exitosamente</CardTitle>
            <CardDescription>
              Los cambios han sido aplicados a tu infraestructura
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>
                Los cambios se han aplicado exitosamente a tu infraestructura.
              </AlertDescription>
            </Alert>

            {selectedProject.git_repo_url && (
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <GitCommit className="h-4 w-4" />
                <span>Cambios sincronizados con Git</span>
              </div>
            )}

            {applyOutput && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium mb-2">Salida de Terraform:</h4>
                <pre className="text-sm text-gray-700 whitespace-pre-wrap max-h-40 overflow-y-auto">
                  {applyOutput}
                </pre>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Plan Detail Dialog */}
      <Dialog open={showPlanDialog} onOpenChange={setShowPlanDialog}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Plan Completo de Terraform</DialogTitle>
            <DialogDescription>
              Detalles completos del plan de ejecución
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Textarea
              value={planData?.plan_output || ''}
              readOnly
              rows={20}
              className="font-mono text-sm"
            />
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default TerraformWorkflow

