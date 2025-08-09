import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Shield, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  FileText,
  Download,
  RefreshCw,
  Filter,
  Eye,
  Clock
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
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  LineChart,
  Line
} from 'recharts'

export default function ComplianceReport() {
  const [selectedFramework, setSelectedFramework] = useState('all')
  const [selectedProvider, setSelectedProvider] = useState('all')

  // Dados simulados de compliance
  const complianceOverview = {
    overallScore: 94.8,
    totalChecks: 1247,
    passedChecks: 1182,
    failedChecks: 65,
    criticalIssues: 3,
    highIssues: 12,
    mediumIssues: 28,
    lowIssues: 22
  }

  const frameworkScores = [
    {
      framework: 'LGPD',
      description: 'Lei Geral de Proteção de Dados',
      score: 92.5,
      status: 'compliant',
      totalControls: 45,
      passedControls: 42,
      failedControls: 3,
      lastAssessment: '2024-06-01',
      nextReview: '2024-09-01',
      riskLevel: 'Medium'
    },
    {
      framework: 'ISO 27001',
      description: 'Segurança da Informação',
      score: 96.8,
      status: 'compliant',
      totalControls: 114,
      passedControls: 110,
      failedControls: 4,
      lastAssessment: '2024-05-15',
      nextReview: '2024-08-15',
      riskLevel: 'Low'
    },
    {
      framework: 'SOC 2',
      description: 'Service Organization Control 2',
      score: 94.2,
      status: 'compliant',
      totalControls: 67,
      passedControls: 63,
      failedControls: 4,
      lastAssessment: '2024-05-30',
      nextReview: '2024-08-30',
      riskLevel: 'Low'
    },
    {
      framework: 'PCI DSS',
      description: 'Payment Card Industry Data Security',
      score: 89.3,
      status: 'partial',
      totalControls: 78,
      passedControls: 70,
      failedControls: 8,
      lastAssessment: '2024-06-05',
      nextReview: '2024-09-05',
      riskLevel: 'High'
    },
    {
      framework: 'NIST',
      description: 'National Institute of Standards',
      score: 97.1,
      status: 'compliant',
      totalControls: 156,
      passedControls: 151,
      failedControls: 5,
      lastAssessment: '2024-05-20',
      nextReview: '2024-08-20',
      riskLevel: 'Low'
    }
  ]

  const complianceByProvider = [
    { provider: 'AWS', score: 95.2, controls: 623, passed: 593, failed: 30 },
    { provider: 'GCP', score: 94.4, controls: 624, passed: 589, failed: 35 }
  ]

  const complianceTrend = [
    { month: 'Jan', score: 91.2, issues: 78 },
    { month: 'Fev', score: 92.8, issues: 65 },
    { month: 'Mar', score: 93.5, issues: 58 },
    { month: 'Abr', score: 94.1, issues: 52 },
    { month: 'Mai', score: 94.8, issues: 48 },
    { month: 'Jun', score: 94.8, issues: 65 }
  ]

  const criticalIssues = [
    {
      id: 1,
      title: 'Dados pessoais sem criptografia',
      framework: 'LGPD',
      provider: 'AWS',
      severity: 'Critical',
      status: 'Open',
      description: 'Base de dados RDS sem criptografia em repouso detectada',
      impact: 'Violação potencial da LGPD - dados pessoais expostos',
      remediation: 'Habilitar criptografia RDS e migrar dados existentes',
      dueDate: '2024-06-15',
      assignee: 'Equipe de Segurança',
      estimatedEffort: '8 horas'
    },
    {
      id: 2,
      title: 'Logs de auditoria desabilitados',
      framework: 'SOC 2',
      provider: 'GCP',
      severity: 'High',
      status: 'In Progress',
      description: 'Cloud Audit Logs não configurados para alguns serviços',
      impact: 'Falta de rastreabilidade para auditoria',
      remediation: 'Configurar Cloud Audit Logs para todos os serviços críticos',
      dueDate: '2024-06-20',
      assignee: 'Equipe DevOps',
      estimatedEffort: '4 horas'
    },
    {
      id: 3,
      title: 'Acesso privilegiado sem MFA',
      framework: 'ISO 27001',
      provider: 'AWS',
      severity: 'High',
      status: 'Open',
      description: 'Usuários com acesso administrativo sem MFA habilitado',
      impact: 'Risco de acesso não autorizado a recursos críticos',
      remediation: 'Forçar MFA para todos os usuários administrativos',
      dueDate: '2024-06-18',
      assignee: 'Equipe de Identidade',
      estimatedEffort: '2 horas'
    },
    {
      id: 4,
      title: 'Backup sem teste de restauração',
      framework: 'NIST',
      provider: 'GCP',
      severity: 'Medium',
      status: 'Open',
      description: 'Backups criados mas sem testes regulares de restauração',
      impact: 'Incerteza sobre a viabilidade dos backups em caso de desastre',
      remediation: 'Implementar testes automatizados de restauração',
      dueDate: '2024-06-25',
      assignee: 'Equipe de Infraestrutura',
      estimatedEffort: '12 horas'
    }
  ]

  const getStatusColor = (status) => {
    switch (status) {
      case 'compliant': return 'bg-green-500'
      case 'partial': return 'bg-yellow-500'
      case 'non-compliant': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const getStatusText = (status) => {
    switch (status) {
      case 'compliant': return 'Conforme'
      case 'partial': return 'Parcialmente Conforme'
      case 'non-compliant': return 'Não Conforme'
      default: return 'Desconhecido'
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'Critical': return 'bg-red-600'
      case 'High': return 'bg-red-500'
      case 'Medium': return 'bg-yellow-500'
      case 'Low': return 'bg-blue-500'
      default: return 'bg-gray-500'
    }
  }

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'High': return 'text-red-600'
      case 'Medium': return 'text-yellow-600'
      case 'Low': return 'text-green-600'
      default: return 'text-gray-600'
    }
  }

  const COLORS = ['#10B981', '#F59E0B', '#EF4444', '#6B7280']

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-3xl font-bold text-foreground">Relatório de Compliance</h2>
          <p className="text-muted-foreground">
            Monitoramento de conformidade com frameworks de segurança e regulamentações
          </p>
        </div>
        <div className="flex space-x-2">
          <Select value={selectedFramework} onValueChange={setSelectedFramework}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Framework" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              <SelectItem value="lgpd">LGPD</SelectItem>
              <SelectItem value="iso27001">ISO 27001</SelectItem>
              <SelectItem value="soc2">SOC 2</SelectItem>
              <SelectItem value="pci">PCI DSS</SelectItem>
              <SelectItem value="nist">NIST</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Atualizar
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Exportar
          </Button>
        </div>
      </div>

      {/* Compliance Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Score Geral</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{complianceOverview.overallScore}%</div>
              <Progress value={complianceOverview.overallScore} className="mt-2" />
              <div className="text-xs text-muted-foreground mt-1">
                {complianceOverview.passedChecks}/{complianceOverview.totalChecks} controles
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
              <CardTitle className="text-sm font-medium">Questões Críticas</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{complianceOverview.criticalIssues}</div>
              <div className="text-xs text-muted-foreground">
                Requerem ação imediata
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
              <CardTitle className="text-sm font-medium">Questões Altas</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">{complianceOverview.highIssues}</div>
              <div className="text-xs text-muted-foreground">
                Prioridade alta
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
              <CardTitle className="text-sm font-medium">Total de Questões</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{complianceOverview.failedChecks}</div>
              <div className="text-xs text-muted-foreground">
                Todas as severidades
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="frameworks" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="frameworks">Frameworks</TabsTrigger>
          <TabsTrigger value="issues">Questões</TabsTrigger>
          <TabsTrigger value="trends">Tendências</TabsTrigger>
          <TabsTrigger value="providers">Por Provedor</TabsTrigger>
        </TabsList>

        {/* Frameworks Overview */}
        <TabsContent value="frameworks" className="space-y-6">
          <div className="grid gap-4">
            {frameworkScores.map((framework, index) => (
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
                        <h3 className="text-lg font-semibold">{framework.framework}</h3>
                        <p className="text-sm text-muted-foreground">{framework.description}</p>
                      </div>
                      <div className="flex space-x-2">
                        <Badge className={getStatusColor(framework.status)}>
                          {getStatusText(framework.status)}
                        </Badge>
                        <Badge variant="outline" className={getRiskColor(framework.riskLevel)}>
                          Risco {framework.riskLevel}
                        </Badge>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                      <div>
                        <div className="text-sm text-muted-foreground">Score</div>
                        <div className="text-2xl font-bold">{framework.score}%</div>
                        <Progress value={framework.score} className="mt-1" />
                      </div>
                      <div>
                        <div className="text-sm text-muted-foreground">Controles</div>
                        <div className="text-lg font-semibold">
                          {framework.passedControls}/{framework.totalControls}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {framework.failedControls} falharam
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-muted-foreground">Última Avaliação</div>
                        <div className="text-sm font-medium">{framework.lastAssessment}</div>
                      </div>
                      <div>
                        <div className="text-sm text-muted-foreground">Próxima Revisão</div>
                        <div className="text-sm font-medium">{framework.nextReview}</div>
                      </div>
                      <div className="flex justify-end">
                        <Button variant="outline" size="sm">
                          <Eye className="h-4 w-4 mr-2" />
                          Detalhes
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </TabsContent>

        {/* Issues Management */}
        <TabsContent value="issues" className="space-y-6">
          <div className="grid gap-4">
            {criticalIssues.map((issue) => (
              <motion.div
                key={issue.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: issue.id * 0.1 }}
              >
                <Card>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-lg">{issue.title}</CardTitle>
                        <CardDescription>
                          {issue.framework} - {issue.provider}
                        </CardDescription>
                      </div>
                      <div className="flex space-x-2">
                        <Badge className={getSeverityColor(issue.severity)}>
                          {issue.severity}
                        </Badge>
                        <Badge variant={issue.status === 'Open' ? 'destructive' : 'default'}>
                          {issue.status}
                        </Badge>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                      <div>
                        <div className="text-sm text-muted-foreground">Prazo</div>
                        <div className="font-medium flex items-center">
                          <Clock className="h-4 w-4 mr-1" />
                          {issue.dueDate}
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-muted-foreground">Responsável</div>
                        <div className="font-medium">{issue.assignee}</div>
                      </div>
                      <div>
                        <div className="text-sm text-muted-foreground">Esforço Estimado</div>
                        <div className="font-medium">{issue.estimatedEffort}</div>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      <div>
                        <div className="text-sm font-medium text-muted-foreground">Descrição:</div>
                        <div className="text-sm">{issue.description}</div>
                      </div>
                      <div>
                        <div className="text-sm font-medium text-muted-foreground">Impacto:</div>
                        <div className="text-sm">{issue.impact}</div>
                      </div>
                      <div>
                        <div className="text-sm font-medium text-muted-foreground">Remediação:</div>
                        <div className="text-sm">{issue.remediation}</div>
                      </div>
                    </div>
                    
                    <div className="mt-4 flex justify-end space-x-2">
                      <Button variant="outline" size="sm">
                        Atribuir
                      </Button>
                      <Button size="sm">
                        Resolver
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </TabsContent>

        {/* Compliance Trends */}
        <TabsContent value="trends" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Evolução do Score de Compliance</CardTitle>
                <CardDescription>
                  Tendência dos últimos 6 meses
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={complianceTrend}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis domain={[90, 96]} />
                    <Tooltip formatter={(value) => [`${value}%`, 'Score']} />
                    <Line 
                      type="monotone" 
                      dataKey="score" 
                      stroke="#10B981" 
                      strokeWidth={3}
                      name="Score de Compliance"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Questões por Severidade</CardTitle>
                <CardDescription>
                  Distribuição atual das questões
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Críticas', value: complianceOverview.criticalIssues, color: '#EF4444' },
                        { name: 'Altas', value: complianceOverview.highIssues, color: '#F59E0B' },
                        { name: 'Médias', value: complianceOverview.mediumIssues, color: '#10B981' },
                        { name: 'Baixas', value: complianceOverview.lowIssues, color: '#6B7280' }
                      ]}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }) => `${name}: ${value}`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {[
                        { name: 'Críticas', value: complianceOverview.criticalIssues, color: '#EF4444' },
                        { name: 'Altas', value: complianceOverview.highIssues, color: '#F59E0B' },
                        { name: 'Médias', value: complianceOverview.mediumIssues, color: '#10B981' },
                        { name: 'Baixas', value: complianceOverview.lowIssues, color: '#6B7280' }
                      ].map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Provider Comparison */}
        <TabsContent value="providers" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Compliance por Provedor</CardTitle>
              <CardDescription>
                Comparação de conformidade entre AWS e GCP
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={complianceByProvider}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="provider" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="score" fill="#10B981" name="Score (%)" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {complianceByProvider.map((provider, index) => (
              <Card key={index}>
                <CardHeader>
                  <CardTitle>{provider.provider}</CardTitle>
                  <CardDescription>
                    Detalhamento de compliance
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium">Score Geral</span>
                        <span className="text-lg font-bold">{provider.score}%</span>
                      </div>
                      <Progress value={provider.score} />
                    </div>
                    
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div>
                        <div className="text-2xl font-bold">{provider.controls}</div>
                        <div className="text-xs text-muted-foreground">Total</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold text-green-600">{provider.passed}</div>
                        <div className="text-xs text-muted-foreground">Passou</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold text-red-600">{provider.failed}</div>
                        <div className="text-xs text-muted-foreground">Falhou</div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

