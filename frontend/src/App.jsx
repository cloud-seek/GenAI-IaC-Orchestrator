import { useState } from 'react'
import PromptInterface from './components/PromptInterface'
import ProjectManager from './components/ProjectManager'
import ResourceInventory from './components/ResourceInventory'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Terminal, Database, GitBranch, Cloud } from 'lucide-react'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('prompts')

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <Terminal className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">GenAI-IaC Platform</h1>
            </div>
            <nav className="flex space-x-4">
              <Button
                variant={activeTab === 'prompts' ? 'default' : 'ghost'}
                onClick={() => setActiveTab('prompts')}
              >
                <Terminal className="h-4 w-4 mr-2" />
                Prompts
              </Button>
              <Button
                variant={activeTab === 'projects' ? 'default' : 'ghost'}
                onClick={() => setActiveTab('projects')}
              >
                <Cloud className="h-4 w-4 mr-2" />
                Proyectos
              </Button>
              <Button
                variant={activeTab === 'resources' ? 'default' : 'ghost'}
                onClick={() => setActiveTab('resources')}
              >
                <Database className="h-4 w-4 mr-2" />
                Recursos
              </Button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'prompts' && (
          <div>
            <div className="mb-6">
              <h2 className="text-3xl font-bold text-gray-900">Consola de Prompts</h2>
              <p className="text-gray-600 mt-2">
                Describe tus necesidades de infraestructura en lenguaje natural
              </p>
            </div>
            <PromptInterface />
          </div>
        )}

        {activeTab === 'projects' && <ProjectManager />}

        {activeTab === 'resources' && <ResourceInventory />}
      </main>
    </div>
  )
}

export default App
