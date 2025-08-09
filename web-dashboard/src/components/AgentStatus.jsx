import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Users, 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Cpu,
  Memory,
  HardDrive,
  Wifi,
  RefreshCw,
  Settings,
  Play,
  Pause,
  Square,
  MoreVertical
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu.jsx'
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts'

export default function AgentStatus({ agents }) {
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [systemMetrics, setSystemMetrics] = useState({
    totalAgents: 8,
    activeAgents: 7,
    warningAgents: 1,
    errorAgents: 0,
    averageHealth: 96.2,
    totalTasks: 1247,
    completedTasks: 1182,
    failedTasks: 15,
    avgResponseTime: 245
  })

  // Dados simulados de performance dos agentes
  const agentPerformance = [
    { time: '00:00', operational: 98, specialist: 96, coordinator: 94 },
    { time: '04:00', operational: 97, specialist: 95, coordinator: 93 },
    { time: '08:00', operational: 99, specialist: 97, coordinator: 95 },
    { time: '12:00', operational: 98, specialist: 98, coordinator: 96 },
    { time: '16:00', operational: 97, specialist: 96, coordinator: 94 },
    { time: '20:00', operational: 98, specialist: 97, coordinator: 95 },
    { time: '23:59', operational: 99, specialist: 98, coordinator: 96 }
  ]

  const taskHistory = [
    { hour: '00:00', completed: 45, failed: 2 },
    { hour: '04:00', completed: 38, failed: 1 },
    { hour: '08:00', completed: 67, failed: 3 },
    { hour: '12:00', completed: 89, failed: 4 },
    { hour: '16:00', completed: 76, failed: 2 },
    { hour: '20:00', completed: 54, failed: 1 },
    { hour: '23:59', completed: 42, failed: 2 }
  ]

  const agentDetails = {
    'Gerente Operacional': {
      type: 'operational',
      description: 'Coordena toda a cadeia de agentes do sistema',
      capabilities: ['Gerenciamento de workflow', 'Coordenação de tarefas', 'Monitoramento geral'],
      currentTask: 'Orquestrando análise de custos mensal',
      tasksCompleted: 156,
      averageResponseTime: 180,
      uptime: '99.8%',
      lastRestart: '2024-05-15 10:30',
      version: '2.1.0',
      resources: { cpu: 15, memory: 32, disk: 8 }
    },
    'Especialista AWS': {
      type: 'specialist',
      description: 'Especialista em recursos e serviços AWS',
      capabilities: ['Cost Explorer API', 'EC2 Analysis', 'S3 Optimization', 'RDS Monitoring'],
      currentTask: 'Analisando custos de EC2 Reserved Instances',
      tasksCompleted: 234,
      averageResponseTime: 320,
      uptime: '99.6%',
      lastRestart: '2024-05-20 14:15',
      version: '1.8.2',
      resources: { cpu: 22, memory: 45, disk: 12 }
    },
    'Especialista GCP': {
      type: 'specialist',
      description: 'Especialista em recursos e serviços Google Cloud',
      capabilities: ['Billing API', 'Compute Engine', 'Cloud Storage', 'BigQuery'],
      currentTask: 'Coletando métricas de BigQuery',
      tasksCompleted: 198,
      averageResponseTime: 280,
      uptime: '99.9%',
      lastRestart: '2024-05-18 09:45',
      version: '1.8.2',
      resources: { cpu: 18, memory: 38, disk: 10 }
    },
    'Coordenador SLA': {
      type: 'coordinator',
      description: 'Monitora e analisa acordos de nível de serviço',
      capabilities: ['SLA Monitoring', 'Incident Analysis', 'Performance Metrics'],
      currentTask: 'Calculando SLA mensal dos serviços',
      tasksCompleted: 89,
      averageResponseTime: 450,
      uptime: '99.4%',
      lastRestart: '2024-05-22 16:20',
      version: '1.5.1',
      resources: { cpu: 12, memory: 28, disk: 6 }
    },
    'Coordenador Custos': {
      type: 'coordinator',
      description: 'Analisa e otimiza custos de recursos cloud',
      capabilities: ['Cost Analysis', 'Optimization Recommendations', 'Budget Monitoring'],
      currentTask: 'Identificando oportunidades de economia',
      tasksCompleted: 145,
      averageResponseTime: 380,
      uptime: '99.7%',
      lastRestart: '2024-05-19 11:30',
      version: '1.6.0',
      resources: { cpu: 20, memory: 42, disk: 14 }
    },
    'Coordenador Compliance': {
      type: 'coordinator',
      description: 'Verifica conformidade com frameworks de segurança',
      capabilities: ['Security Scanning', 'Compliance Checks', 'Risk Assessment'],
      currentTask: 'Executando verificações LGPD',
      tasksCompleted: 67,
      averageResponseTime: 520,
      uptime: '98.9%',
      lastRestart: '2024-05-25 08:15',
      version: '1.4.3',
      resources: { cpu: 25, memory: 35, disk: 9 }
    },
    'Coordenador Jurídico': {
      type: 'coordinator',
      description: 'Analisa documentos jurídicos e regulamentações',
      capabilities: ['Document Analysis', 'RAG Queries', 'Legal Research'],
      currentTask: 'Consultando documentos sobre LGPD',
      tasksCompleted: 78,
      averageResponseTime: 680,
      uptime: '99.5%',
      lastRestart: '2024-05-21 13:45',
      version: '1.3.2',
      resources: { cpu: 30, memory: 55, disk: 18 }
    },
    'Gerador Relatórios': {
      type: 'coordinator',
      description: 'Compila dados e gera relatórios executivos',
      capabilities: ['Data Aggregation', 'Report Generation', 'Visualization'],
      currentTask: 'Gerando relatório executivo mensal',
      tasksCompleted: 45,
      averageResponseTime: 1200,
      uptime: '100%',
      lastRestart: '2024-05-16 07:00',
      version: '1.2.1',
      resources: { cpu: 35, memory: 48, disk: 22 }
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'bg-green-500'
      case 'warning': return 'bg-yellow-500'
      case 'error': return 'bg-red-500'
      case 'inactive': return 'bg-gray-500'
      default: return 'bg-gray-500'
    }
  }

  const getStatusText = (status) => {
    switch (status) {
      case 'active': return 'Ativo'
      case 'warning': return 'Atenção'
      case 'error': return 'Erro'
      case 'inactive': return 'Inativo'
      default: return 'Desconhecido'
    }
  }

  const getTypeColor = (type) => {
    switch (type) {
      case 'operational': return 'bg-blue-500'
      case 'specialist': return 'bg-purple-500'
      case 'coordinator': return 'bg-green-500'
      default: return 'bg-gray-500'
    }
  }

  const getTypeText = (type) => {
    switch (type) {
      case 'operational': return 'Operacional'
      case 'specialist': return 'Especialista'
      case 'coordinator': return 'Coordenador'
      default: return 'Desconhecido'
    }
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-3xl font-bold text-foreground">Status dos Agentes</h2>
          <p className="text-muted-foreground">
            Monitoramento em tempo real da saúde e performance dos agentes de IA
          </p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Atualizar
          </Button>
          <Button variant="outline" size="sm">
            <Settings className="h-4 w-4 mr-2" />
            Configurar
          </Button>
        </div>
      </div>

      {/* System Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total de Agentes</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{systemMetrics.totalAgents}</div>
              <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-1" />
                  {systemMetrics.activeAgents} ativos
                </div>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full mr-1" />
                  {systemMetrics.warningAgents} atenção
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Saúde Média</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{systemMetrics.averageHealth}%</div>
              <Progress value={systemMetrics.averageHealth} className="mt-2" />
              <div className="text-xs text-muted-foreground mt-1">
                Sistema operacional
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Tarefas Concluídas</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{systemMetrics.completedTasks}</div>
              <div className="text-xs text-muted-foreground">
                {systemMetrics.failedTasks} falharam ({((systemMetrics.failedTasks / systemMetrics.totalTasks) * 100).toFixed(1)}%)
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Tempo de Resposta</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{systemMetrics.avgResponseTime}ms</div>
              <div className="text-xs text-muted-foreground">
                Média das últimas 24h
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="agents" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="agents">Lista de Agentes</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="tasks">Histórico de Tarefas</TabsTrigger>
        </TabsList>

        {/* Agents List */}
        <TabsContent value="agents" className="space-y-6">
          <div className="grid gap-4">
            {agents.map((agent, index) => {
              const details = agentDetails[agent.name] || {}
              
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card>
                    <CardContent className="p-6">
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex items-start space-x-4">
                          <div className="flex-shrink-0">
                            <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                              <Users className="h-6 w-6 text-white" />
                            </div>
                          </div>
                          <div>
                            <h3 className="text-lg font-semibold">{agent.name}</h3>
                            <p className="text-sm text-muted-foreground">{details.description}</p>
                            <div className="flex items-center space-x-2 mt-2">
                              <Badge className={getTypeColor(details.type)}>
                                {getTypeText(details.type)}
                              </Badge>
                              <Badge className={getStatusColor(agent.status)}>
                                {getStatusText(agent.status)}
                              </Badge>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <div className="text-right">
                            <div className="text-2xl font-bold">{agent.health}%</div>
                            <div className="text-xs text-muted-foreground">Saúde</div>
                          </div>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm">
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuLabel>Ações</DropdownMenuLabel>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem>
                                <Play className="mr-2 h-4 w-4" />
                                Iniciar
                              </DropdownMenuItem>
                              <DropdownMenuItem>
                                <Pause className="mr-2 h-4 w-4" />
                                Pausar
                              </DropdownMenuItem>
                              <DropdownMenuItem>
                                <RefreshCw className="mr-2 h-4 w-4" />
                                Reiniciar
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem>
                                <Settings className="mr-2 h-4 w-4" />
                                Configurar
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                        <div>
                          <div className="text-sm text-muted-foreground">Última Atualização</div>
                          <div className="font-medium flex items-center">
                            <Clock className="h-4 w-4 mr-1" />
                            {agent.lastUpdate}
                          </div>
                        </div>
                        <div>
                          <div className="text-sm text-muted-foreground">Tarefa Atual</div>
                          <div className="font-medium text-sm">{details.currentTask}</div>
                        </div>
                        <div>
                          <div className="text-sm text-muted-foreground">Tarefas Concluídas</div>
                          <div className="font-medium">{details.tasksCompleted}</div>
                        </div>
                        <div>
                          <div className="text-sm text-muted-foreground">Tempo de Resposta</div>
                          <div className="font-medium">{details.averageResponseTime}ms</div>
                        </div>
                      </div>
                      
                      {/* Resource Usage */}
                      <div className="grid grid-cols-3 gap-4">
                        <div>
                          <div className="flex items-center justify-between text-sm mb-1">
                            <span className="flex items-center">
                              <Cpu className="h-3 w-3 mr-1" />
                              CPU
                            </span>
                            <span>{details.resources?.cpu}%</span>
                          </div>
                          <Progress value={details.resources?.cpu || 0} className="h-2" />
                        </div>
                        <div>
                          <div className="flex items-center justify-between text-sm mb-1">
                            <span className="flex items-center">
                              <Memory className="h-3 w-3 mr-1" />
                              Memória
                            </span>
                            <span>{details.resources?.memory}%</span>
                          </div>
                          <Progress value={details.resources?.memory || 0} className="h-2" />
                        </div>
                        <div>
                          <div className="flex items-center justify-between text-sm mb-1">
                            <span className="flex items-center">
                              <HardDrive className="h-3 w-3 mr-1" />
                              Disco
                            </span>
                            <span>{details.resources?.disk}%</span>
                          </div>
                          <Progress value={details.resources?.disk || 0} className="h-2" />
                        </div>
                      </div>
                      
                      <div className="mt-4 flex justify-end">
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => setSelectedAgent(agent.name)}
                        >
                          Ver Detalhes
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              )
            })}
          </div>
        </TabsContent>

        {/* Performance Charts */}
        <TabsContent value="performance" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Performance dos Agentes por Tipo</CardTitle>
              <CardDescription>
                Saúde média dos agentes nas últimas 24 horas
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={agentPerformance}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis domain={[90, 100]} />
                  <Tooltip formatter={(value) => [`${value}%`, '']} />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="operational" 
                    stroke="#3B82F6" 
                    strokeWidth={3}
                    name="Operacionais"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="specialist" 
                    stroke="#8B5CF6" 
                    strokeWidth={3}
                    name="Especialistas"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="coordinator" 
                    stroke="#10B981" 
                    strokeWidth={3}
                    name="Coordenadores"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Task History */}
        <TabsContent value="tasks" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Histórico de Execução de Tarefas</CardTitle>
              <CardDescription>
                Tarefas concluídas e falhadas nas últimas 24 horas
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={taskHistory}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hour" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area 
                    type="monotone" 
                    dataKey="completed" 
                    stackId="1" 
                    stroke="#10B981" 
                    fill="#10B981"
                    fillOpacity={0.6}
                    name="Concluídas"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="failed" 
                    stackId="1" 
                    stroke="#EF4444" 
                    fill="#EF4444"
                    fillOpacity={0.6}
                    name="Falhadas"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

