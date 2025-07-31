import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  Database, 
  Server, 
  Cloud, 
  Network, 
  Shield, 
  HardDrive, 
  Cpu, 
  Search, 
  Filter, 
  Eye,
  GitBranch,
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock
} from 'lucide-react'

const ResourceInventory = () => {
  const [projects, setProjects] = useState([])
  const [selectedProject, setSelectedProject] = useState('')
  const [resources, setResources] = useState([])
  const [filteredResources, setFilteredResources] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState('all')
  const [filterStatus, setFilterStatus] = useState('all')
  const [selectedResource, setSelectedResource] = useState(null)
  const [showResourceDialog, setShowResourceDialog] = useState(false)

  useEffect(() => {
    fetchProjects()
  }, [])

  useEffect(() => {
    if (selectedProject) {
      fetchResources(selectedProject)
    }
  }, [selectedProject])

  useEffect(() => {
    filterResources()
  }, [resources, searchTerm, filterType, filterStatus])

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

  const fetchResources = async (projectId) => {
    setLoading(true)
    try {
      const response = await fetch(`/api/projects/${projectId}/resources`)
      if (response.ok) {
        const data = await response.json()
        setResources(data)
      } else {
        // Si no hay recursos, mostrar datos simulados para demostración
        setResources(generateMockResources())
      }
    } catch (error) {
      console.error('Error fetching resources:', error)
      // Mostrar datos simulados en caso de error
      setResources(generateMockResources())
    } finally {
      setLoading(false)
    }
  }

  const generateMockResources = () => {
    return [
      {
        id: 1,
        name: 'web-server-01',
        type: 'aws_instance',
        provider: 'aws',
        status: 'running',
        region: 'us-east-1',
        created_at: '2024-01-15T10:30:00Z',
        last_modified: '2024-01-20T14:22:00Z',
        attributes: {
          instance_type: 't3.medium',
          ami: 'ami-0abcdef1234567890',
          vpc_id: 'vpc-12345678',
          subnet_id: 'subnet-87654321',
          security_groups: ['sg-web-servers'],
          public_ip: '54.123.45.67',
          private_ip: '10.0.1.100'
        },
        tags: {
          Environment: 'production',
          Application: 'web-frontend',
          Owner: 'devops-team'
        }
      },
      {
        id: 2,
        name: 'database-primary',
        type: 'aws_db_instance',
        provider: 'aws',
        status: 'available',
        region: 'us-east-1',
        created_at: '2024-01-10T09:15:00Z',
        last_modified: '2024-01-18T11:45:00Z',
        attributes: {
          engine: 'postgres',
          engine_version: '14.9',
          instance_class: 'db.t3.micro',
          allocated_storage: 20,
          storage_type: 'gp2',
          multi_az: false,
          publicly_accessible: false,
          endpoint: 'database-primary.abc123.us-east-1.rds.amazonaws.com'
        },
        tags: {
          Environment: 'production',
          Application: 'backend-db',
          Backup: 'daily'
        }
      },
      {
        id: 3,
        name: 'app-load-balancer',
        type: 'aws_lb',
        provider: 'aws',
        status: 'active',
        region: 'us-east-1',
        created_at: '2024-01-12T16:20:00Z',
        last_modified: '2024-01-19T08:30:00Z',
        attributes: {
          load_balancer_type: 'application',
          scheme: 'internet-facing',
          ip_address_type: 'ipv4',
          dns_name: 'app-lb-123456789.us-east-1.elb.amazonaws.com',
          availability_zones: ['us-east-1a', 'us-east-1b']
        },
        tags: {
          Environment: 'production',
          Application: 'load-balancer'
        }
      },
      {
        id: 4,
        name: 'storage-bucket',
        type: 'aws_s3_bucket',
        provider: 'aws',
        status: 'active',
        region: 'us-east-1',
        created_at: '2024-01-08T12:00:00Z',
        last_modified: '2024-01-22T15:10:00Z',
        attributes: {
          bucket_name: 'my-app-storage-bucket-prod',
          versioning: 'Enabled',
          encryption: 'AES256',
          public_access_block: true,
          lifecycle_policy: 'enabled'
        },
        tags: {
          Environment: 'production',
          Application: 'file-storage',
          CostCenter: 'engineering'
        }
      },
      {
        id: 5,
        name: 'vpc-main',
        type: 'aws_vpc',
        provider: 'aws',
        status: 'available',
        region: 'us-east-1',
        created_at: '2024-01-05T08:45:00Z',
        last_modified: '2024-01-15T13:20:00Z',
        attributes: {
          cidr_block: '10.0.0.0/16',
          enable_dns_hostnames: true,
          enable_dns_support: true,
          instance_tenancy: 'default'
        },
        tags: {
          Environment: 'production',
          Network: 'main-vpc'
        }
      }
    ]
  }

  const filterResources = () => {
    let filtered = resources

    // Filtrar por término de búsqueda
    if (searchTerm) {
      filtered = filtered.filter(resource =>
        resource.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        resource.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        Object.values(resource.tags || {}).some(tag =>
          tag.toLowerCase().includes(searchTerm.toLowerCase())
        )
      )
    }

    // Filtrar por tipo
    if (filterType !== 'all') {
      filtered = filtered.filter(resource => resource.type === filterType)
    }

    // Filtrar por estado
    if (filterStatus !== 'all') {
      filtered = filtered.filter(resource => resource.status === filterStatus)
    }

    setFilteredResources(filtered)
  }

  const getResourceIcon = (type) => {
    if (type.includes('instance') || type.includes('server')) {
      return <Server className="h-5 w-5" />
    } else if (type.includes('db') || type.includes('database')) {
      return <Database className="h-5 w-5" />
    } else if (type.includes('bucket') || type.includes('storage')) {
      return <HardDrive className="h-5 w-5" />
    } else if (type.includes('lb') || type.includes('balancer')) {
      return <Network className="h-5 w-5" />
    } else if (type.includes('vpc') || type.includes('network')) {
      return <Network className="h-5 w-5" />
    } else if (type.includes('security')) {
      return <Shield className="h-5 w-5" />
    } else {
      return <Cloud className="h-5 w-5" />
    }
  }

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'running':
      case 'active':
      case 'available':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'pending':
      case 'creating':
        return <Clock className="h-4 w-4 text-yellow-500" />
      case 'stopped':
      case 'terminated':
      case 'failed':
        return <AlertTriangle className="h-4 w-4 text-red-500" />
      default:
        return <Activity className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'running':
      case 'active':
      case 'available':
        return 'bg-green-100 text-green-800'
      case 'pending':
      case 'creating':
        return 'bg-yellow-100 text-yellow-800'
      case 'stopped':
      case 'terminated':
      case 'failed':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getUniqueTypes = () => {
    const types = [...new Set(resources.map(r => r.type))]
    return types.sort()
  }

  const getUniqueStatuses = () => {
    const statuses = [...new Set(resources.map(r => r.status))]
    return statuses.sort()
  }

  const openResourceDialog = (resource) => {
    setSelectedResource(resource)
    setShowResourceDialog(true)
  }

  const selectedProjectData = projects.find(p => p.id.toString() === selectedProject)

  return (
    <div className="space-y-6">
      {/* Header y controles */}
      <div className="space-y-4">
        <div>
          <h2 className="text-2xl font-bold">Inventario de Recursos</h2>
          <p className="text-gray-600">Visualiza y gestiona los recursos de tu infraestructura</p>
        </div>

        {/* Selector de proyecto */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
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
        </div>

        {/* Filtros y búsqueda */}
        {selectedProject && (
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Buscar recursos..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-full sm:w-48">
                <SelectValue placeholder="Tipo de recurso" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos los tipos</SelectItem>
                {getUniqueTypes().map((type) => (
                  <SelectItem key={type} value={type}>
                    {type}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-full sm:w-48">
                <SelectValue placeholder="Estado" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos los estados</SelectItem>
                {getUniqueStatuses().map((status) => (
                  <SelectItem key={status} value={status}>
                    {status}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
      </div>

      {/* Contenido principal */}
      {!selectedProject ? (
        <Card>
          <CardContent className="text-center py-8">
            <Cloud className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Selecciona un proyecto</h3>
            <p className="text-gray-500">Elige un proyecto para ver su inventario de recursos</p>
          </CardContent>
        </Card>
      ) : loading ? (
        <Card>
          <CardContent className="text-center py-8">
            <Activity className="h-8 w-8 text-blue-500 animate-spin mx-auto mb-4" />
            <p>Cargando recursos...</p>
          </CardContent>
        </Card>
      ) : filteredResources.length === 0 ? (
        <Card>
          <CardContent className="text-center py-8">
            <Database className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No se encontraron recursos</h3>
            <p className="text-gray-500">
              {resources.length === 0 
                ? 'Este proyecto no tiene recursos desplegados aún'
                : 'No hay recursos que coincidan con los filtros aplicados'
              }
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Estadísticas */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <Database className="h-5 w-5 text-blue-500" />
                  <div>
                    <p className="text-sm font-medium">Total Recursos</p>
                    <p className="text-2xl font-bold">{filteredResources.length}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <div>
                    <p className="text-sm font-medium">Activos</p>
                    <p className="text-2xl font-bold">
                      {filteredResources.filter(r => 
                        ['running', 'active', 'available'].includes(r.status?.toLowerCase())
                      ).length}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <Cloud className="h-5 w-5 text-purple-500" />
                  <div>
                    <p className="text-sm font-medium">Tipos</p>
                    <p className="text-2xl font-bold">{getUniqueTypes().length}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <Activity className="h-5 w-5 text-orange-500" />
                  <div>
                    <p className="text-sm font-medium">Región</p>
                    <p className="text-lg font-bold">
                      {filteredResources[0]?.region || 'N/A'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Lista de recursos */}
          <div className="grid gap-4">
            {filteredResources.map((resource) => (
              <Card key={resource.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {getResourceIcon(resource.type)}
                      <div>
                        <h3 className="font-medium">{resource.name}</h3>
                        <p className="text-sm text-gray-500">{resource.type}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <Badge className={getStatusColor(resource.status)}>
                        {getStatusIcon(resource.status)}
                        <span className="ml-1">{resource.status}</span>
                      </Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openResourceDialog(resource)}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  
                  {/* Tags */}
                  {resource.tags && Object.keys(resource.tags).length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1">
                      {Object.entries(resource.tags).slice(0, 3).map(([key, value]) => (
                        <Badge key={key} variant="secondary" className="text-xs">
                          {key}: {value}
                        </Badge>
                      ))}
                      {Object.keys(resource.tags).length > 3 && (
                        <Badge variant="secondary" className="text-xs">
                          +{Object.keys(resource.tags).length - 3} más
                        </Badge>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}

      {/* Dialog de detalles del recurso */}
      <Dialog open={showResourceDialog} onOpenChange={setShowResourceDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              {selectedResource && getResourceIcon(selectedResource.type)}
              <span>{selectedResource?.name}</span>
            </DialogTitle>
            <DialogDescription>
              Detalles del recurso {selectedResource?.type}
            </DialogDescription>
          </DialogHeader>
          
          {selectedResource && (
            <div className="space-y-4">
              {/* Información básica */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">Estado</label>
                  <div className="flex items-center space-x-2 mt-1">
                    {getStatusIcon(selectedResource.status)}
                    <span>{selectedResource.status}</span>
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium">Región</label>
                  <p className="mt-1">{selectedResource.region}</p>
                </div>
                <div>
                  <label className="text-sm font-medium">Creado</label>
                  <p className="mt-1">
                    {new Date(selectedResource.created_at).toLocaleString()}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium">Modificado</label>
                  <p className="mt-1">
                    {new Date(selectedResource.last_modified).toLocaleString()}
                  </p>
                </div>
              </div>

              {/* Atributos */}
              {selectedResource.attributes && (
                <div>
                  <label className="text-sm font-medium">Atributos</label>
                  <div className="mt-2 bg-gray-50 p-3 rounded-lg">
                    <pre className="text-sm overflow-x-auto">
                      {JSON.stringify(selectedResource.attributes, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {/* Tags */}
              {selectedResource.tags && (
                <div>
                  <label className="text-sm font-medium">Tags</label>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {Object.entries(selectedResource.tags).map(([key, value]) => (
                      <Badge key={key} variant="secondary">
                        {key}: {value}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default ResourceInventory

