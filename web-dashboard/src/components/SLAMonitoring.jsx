import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Filter
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select.jsx'
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts'

export default function SLAMonitoring() {
  const [selectedPeriod, setSelectedPeriod] = useState('7d')
  const [selectedProvider, setSelectedProvider] = useState('all')

  // Dados simulados de SLA
  const slaOverview = {
    overallSLA: 99.2,
    target: 99.9,
    uptime: '99.2%',
    downtime: '5h 47m',
    incidents: 3,
    mttr: '1h 23m'
  }

  const servicesSLA = [
    {
      service: 'EC2 Instances',
      provider: 'AWS',
      current: 99.8,
      target: 99.9,
      status: 'healthy',
      uptime: '99.8%',
      incidents: 1,
      lastIncident: '2 dias atrás'
    },
    {
      service: 'Compute Engine',
      provider: 'GCP',
      current: 99.9,
      target: 99.9,
      status: 'healthy',
      uptime: '99.9%',
      incidents: 0,
      lastIncident: '15 dias atrás'
    },
    {
      service: 'RDS Database',
      provider: 'AWS',
      current: 98.5,
      target: 99.5,
      status: 'warning',
      uptime: '98.5%',
      incidents: 2,
      lastIncident: '1 dia atrás'
    },
    {
      service: 'Cloud SQL',
      provider: 'GCP',
      current: 99.7,
      target: 99.5,
      status: 'healthy',
      uptime: '99.7%',
      incidents: 0,
      lastIncident: '8 dias atrás'
    },
    {
      service: 'S3 Storage',
      provider: 'AWS',
      current: 99.99,
      target: 99.9,
      status: 'excellent',
      uptime: '99.99%',
      incidents: 0,
      lastIncident: '30+ dias atrás'
    },
    {
      service: 'Cloud Storage',
      provider: 'GCP',
      current: 99.95,
      target: 99.9,
      status: 'excellent',
      uptime: '99.95%',
      incidents: 0,
      lastIncident: '20 dias atrás'
    }
  ]

  const slaHistory = [
    { date: '01/06', aws: 99.5, gcp: 99.8, overall: 99.65 },
    { date: '02/06', aws: 99.2, gcp: 99.9, overall: 99.55 },
    { date: '03/06', aws: 99.8, gcp: 99.7, overall: 99.75 },
    { date: '04/06', aws: 99.9, gcp: 99.9, overall: 99.9 },
    { date: '05/06', aws: 99.6, gcp: 99.8, overall: 99.7 },
    { date: '06/06', aws: 99.8, gcp: 99.9, overall: 99.85 },
    { date: '07/06', aws: 99.7, gcp: 99.9, overall: 99.8 }
  ]

  const incidents = [
    {
      id: 1,
      title: 'RDS Connection Timeout',
      service: 'RDS Database',
      provider: 'AWS',
      severity: 'High',
      status: 'Resolved',
      startTime: '2024-06-06 14:30',
      endTime: '2024-06-06 16:15',
      duration: '1h 45m',
      impact: 'Database queries experiencing high latency',
      resolution: 'Increased connection pool size and optimized queries'
    },
    {
      id: 2,
      title: 'EC2 Instance Failure',
      service: 'EC2 Instances',
      provider: 'AWS',
      severity: 'Medium',
      status: 'Resolved',
      startTime: '2024-06-04 09:15',
      endTime: '2024-06-04 09:45',
      duration: '30m',
      impact: 'Single instance unavailable, auto-scaling compensated',
      resolution: 'Instance automatically replaced by auto-scaling group'
    },
    {
      id: 3,
      title: 'Network Latency Spike',
      service: 'VPC Network',
      provider: 'AWS',
      severity: 'Low',
      status: 'Monitoring',
      startTime: '2024-06-06 20:00',
      endTime: null,
      duration: 'Ongoing',
      impact: 'Intermittent high latency in us-east-1',
      resolution: 'Monitoring network performance, no action required yet'
    }
  ]

  const responseTimeData = [
    { time: '00:00', aws: 120, gcp: 95, target: 100 },
    { time: '04:00', aws: 110, gcp: 88, target: 100 },
    { time: '08:00', aws: 135, gcp: 102, target: 100 },
    { time: '12:00', aws: 145, gcp: 115, target: 100 },
    { time: '16:00', aws: 125, gcp: 98, target: 100 },
    { time: '20:00', aws: 115, gcp: 92, target: 100 },
    { time: '23:59', aws: 108, gcp: 89, target: 100 }
  ]

  const getStatusColor = (status) => {
    switch (status) {
      case 'excellent': return 'bg-green-500'
      case 'healthy': return 'bg-blue-500'
      case 'warning': return 'bg-yellow-500'
      case 'critical': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const getStatusText = (status) => {
    switch (status) {
      case 'excellent': return 'Excelente'
      case 'healthy': return 'Saudável'
      case 'warning': return 'Atenção'
      case 'critical': return 'Crítico'
      default: return 'Desconhecido'
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'High': return 'bg-red-500'
      case 'Medium': return 'bg-yellow-500'
      case 'Low': return 'bg-blue-500'
      default: return 'bg-gray-500'
    }
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-3xl font-bold text-foreground">Monitoramento SLA</h2>
          <p className="text-muted-foreground">
            Acompanhamento em tempo real da disponibilidade e performance dos serviços
          </p>
        </div>
        <div className="flex space-x-2">
          <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="24h">24 Horas</SelectItem>
              <SelectItem value="7d">7 Dias</SelectItem>
              <SelectItem value="30d">30 Dias</SelectItem>
              <SelectItem value="90d">90 Dias</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Atualizar
          </Button>
        </div>
      </div>

      {/* SLA Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">SLA Geral</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{slaOverview.overallSLA}%</div>
              <Progress value={slaOverview.overallSLA} className="mt-2" />
              <div className="text-xs text-muted-foreground mt-1">
                Meta: {slaOverview.target}%
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
              <CardTitle className="text-sm font-medium">Tempo Inativo</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{slaOverview.downtime}</div>
              <div className="text-xs text-muted-foreground">
                Últimos 30 dias
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
              <CardTitle className="text-sm font-medium">Incidentes</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{slaOverview.incidents}</div>
              <div className="text-xs text-muted-foreground">
                Últimos 7 dias
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
              <CardTitle className="text-sm font-medium">MTTR</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{slaOverview.mttr}</div>
              <div className="text-xs text-muted-foreground">
                Tempo médio de resolução
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="services" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="services">Serviços</TabsTrigger>
          <TabsTrigger value="history">Histórico</TabsTrigger>
          <TabsTrigger value="incidents">Incidentes</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
        </TabsList>

        {/* Services SLA */}
        <TabsContent value="services" className="space-y-6">
          <div className="grid gap-4">
            {servicesSLA.map((service, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card>
                  <CardContent className="p-6">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="text-lg font-semibold">{service.service}</h3>
                        <p className="text-sm text-muted-foreground">{service.provider}</p>
                      </div>
                      <Badge className={getStatusColor(service.status)}>
                        {getStatusText(service.status)}
                      </Badge>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div>
                        <div className="text-sm text-muted-foreground">SLA Atual</div>
                        <div className="text-2xl font-bold">{service.current}%</div>
                        <Progress value={service.current} className="mt-1" />
                      </div>
                      <div>
                        <div className="text-sm text-muted-foreground">Meta SLA</div>
                        <div className="text-lg font-semibold">{service.target}%</div>
                        <div className={`text-xs ${service.current >= service.target ? 'text-green-600' : 'text-red-600'}`}>
                          {service.current >= service.target ? '✓ Dentro da meta' : '⚠ Abaixo da meta'}
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-muted-foreground">Incidentes</div>
                        <div className="text-lg font-semibold">{service.incidents}</div>
                        <div className="text-xs text-muted-foreground">Últimos 7 dias</div>
                      </div>
                      <div>
                        <div className="text-sm text-muted-foreground">Último Incidente</div>
                        <div className="text-sm font-medium">{service.lastIncident}</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </TabsContent>

        {/* SLA History */}
        <TabsContent value="history" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Histórico de SLA</CardTitle>
              <CardDescription>
                Evolução da disponibilidade dos serviços nos últimos 7 dias
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={slaHistory}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis domain={[98, 100]} />
                  <Tooltip formatter={(value) => [`${value}%`, '']} />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="aws" 
                    stroke="#FF9500" 
                    strokeWidth={3}
                    name="AWS"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="gcp" 
                    stroke="#4285F4" 
                    strokeWidth={3}
                    name="GCP"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="overall" 
                    stroke="#34A853" 
                    strokeWidth={3}
                    strokeDasharray="5 5"
                    name="Geral"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Incidents */}
        <TabsContent value="incidents" className="space-y-6">
          <div className="grid gap-4">
            {incidents.map((incident) => (
              <motion.div
                key={incident.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: incident.id * 0.1 }}
              >
                <Card>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-lg">{incident.title}</CardTitle>
                        <CardDescription>
                          {incident.service} - {incident.provider}
                        </CardDescription>
                      </div>
                      <div className="flex space-x-2">
                        <Badge className={getSeverityColor(incident.severity)}>
                          {incident.severity}
                        </Badge>
                        <Badge variant={incident.status === 'Resolved' ? 'default' : 'secondary'}>
                          {incident.status}
                        </Badge>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                      <div>
                        <div className="text-sm text-muted-foreground">Início</div>
                        <div className="font-medium">{incident.startTime}</div>
                      </div>
                      <div>
                        <div className="text-sm text-muted-foreground">
                          {incident.endTime ? 'Fim' : 'Duração'}
                        </div>
                        <div className="font-medium">
                          {incident.endTime || incident.duration}
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-muted-foreground">Duração</div>
                        <div className="font-medium">{incident.duration}</div>
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <div>
                        <div className="text-sm font-medium text-muted-foreground">Impacto:</div>
                        <div className="text-sm">{incident.impact}</div>
                      </div>
                      <div>
                        <div className="text-sm font-medium text-muted-foreground">Resolução:</div>
                        <div className="text-sm">{incident.resolution}</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </TabsContent>

        {/* Performance Metrics */}
        <TabsContent value="performance" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Tempo de Resposta</CardTitle>
              <CardDescription>
                Latência média dos serviços nas últimas 24 horas
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={responseTimeData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip formatter={(value) => [`${value}ms`, '']} />
                  <Legend />
                  <Area 
                    type="monotone" 
                    dataKey="target" 
                    stroke="#666" 
                    fill="transparent"
                    strokeDasharray="5 5"
                    name="Meta (100ms)"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="aws" 
                    stroke="#FF9500" 
                    fill="#FF9500"
                    fillOpacity={0.3}
                    name="AWS"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="gcp" 
                    stroke="#4285F4" 
                    fill="#4285F4"
                    fillOpacity={0.3}
                    name="GCP"
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

