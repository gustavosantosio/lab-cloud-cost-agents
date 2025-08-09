import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  FileText, 
  Download, 
  Calendar, 
  Filter,
  Eye,
  Share,
  Mail,
  Printer,
  Clock,
  TrendingUp,
  DollarSign,
  Shield,
  Activity,
  Users
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog.jsx'

export default function Reports() {
  const [selectedPeriod, setSelectedPeriod] = useState('monthly')
  const [selectedType, setSelectedType] = useState('all')
  const [isGenerating, setIsGenerating] = useState(false)

  // Dados simulados de relatórios
  const availableReports = [
    {
      id: 1,
      title: 'Relatório Executivo de Custos',
      description: 'Análise completa dos custos cloud com recomendações de otimização',
      type: 'cost',
      period: 'monthly',
      lastGenerated: '2024-06-01',
      size: '2.4 MB',
      pages: 15,
      status: 'ready',
      insights: [
        'Economia potencial de $8,934 identificada',
        '7 oportunidades de otimização encontradas',
        'Crescimento de custos de 12% vs mês anterior'
      ]
    },
    {
      id: 2,
      title: 'Relatório de SLA e Performance',
      description: 'Monitoramento de disponibilidade e performance dos serviços',
      type: 'sla',
      period: 'monthly',
      lastGenerated: '2024-06-01',
      size: '1.8 MB',
      pages: 12,
      status: 'ready',
      insights: [
        'SLA geral de 99.2% mantido',
        '3 incidentes registrados no período',
        'MTTR médio de 1h 23min'
      ]
    },
    {
      id: 3,
      title: 'Relatório de Compliance',
      description: 'Status de conformidade com frameworks de segurança',
      type: 'compliance',
      period: 'quarterly',
      lastGenerated: '2024-06-01',
      size: '3.1 MB',
      pages: 22,
      status: 'ready',
      insights: [
        'Score geral de compliance: 94.8%',
        '3 questões críticas identificadas',
        'LGPD: 92.5% de conformidade'
      ]
    },
    {
      id: 4,
      title: 'Relatório de Agentes IA',
      description: 'Performance e saúde dos agentes de inteligência artificial',
      type: 'agents',
      period: 'weekly',
      lastGenerated: '2024-06-01',
      size: '1.2 MB',
      pages: 8,
      status: 'ready',
      insights: [
        '8 agentes operacionais ativos',
        'Saúde média do sistema: 96.2%',
        '1,182 tarefas concluídas com sucesso'
      ]
    },
    {
      id: 5,
      title: 'Análise Comparativa de Provedores',
      description: 'Comparação detalhada entre AWS e Google Cloud',
      type: 'comparison',
      period: 'monthly',
      lastGenerated: '2024-05-28',
      size: '2.7 MB',
      pages: 18,
      status: 'generating',
      insights: [
        'AWS: 58% dos custos totais',
        'GCP: Melhor performance em SLA',
        'Recomendação: Estratégia híbrida'
      ]
    },
    {
      id: 6,
      title: 'Relatório Jurídico e Regulamentações',
      description: 'Análise de conformidade com legislação brasileira',
      type: 'legal',
      period: 'quarterly',
      lastGenerated: '2024-05-15',
      size: '4.2 MB',
      pages: 28,
      status: 'ready',
      insights: [
        'LGPD: Conformidade parcial identificada',
        '12 recomendações jurídicas',
        'Risco legal estimado: Médio'
      ]
    }
  ]

  const reportTemplates = [
    {
      id: 'executive-summary',
      name: 'Resumo Executivo',
      description: 'Relatório conciso para liderança executiva',
      sections: ['Resumo', 'Métricas-chave', 'Recomendações'],
      estimatedPages: '3-5'
    },
    {
      id: 'detailed-analysis',
      name: 'Análise Detalhada',
      description: 'Relatório técnico completo com análises profundas',
      sections: ['Introdução', 'Metodologia', 'Análise', 'Conclusões', 'Anexos'],
      estimatedPages: '15-25'
    },
    {
      id: 'compliance-audit',
      name: 'Auditoria de Compliance',
      description: 'Relatório focado em conformidade regulatória',
      sections: ['Frameworks', 'Verificações', 'Não-conformidades', 'Plano de ação'],
      estimatedPages: '20-30'
    },
    {
      id: 'cost-optimization',
      name: 'Otimização de Custos',
      description: 'Relatório com foco em economia e eficiência',
      sections: ['Análise atual', 'Oportunidades', 'ROI', 'Implementação'],
      estimatedPages: '10-15'
    }
  ]

  const getStatusColor = (status) => {
    switch (status) {
      case 'ready': return 'bg-green-500'
      case 'generating': return 'bg-blue-500'
      case 'error': return 'bg-red-500'
      case 'scheduled': return 'bg-yellow-500'
      default: return 'bg-gray-500'
    }
  }

  const getStatusText = (status) => {
    switch (status) {
      case 'ready': return 'Pronto'
      case 'generating': return 'Gerando'
      case 'error': return 'Erro'
      case 'scheduled': return 'Agendado'
      default: return 'Desconhecido'
    }
  }

  const getTypeIcon = (type) => {
    switch (type) {
      case 'cost': return DollarSign
      case 'sla': return Activity
      case 'compliance': return Shield
      case 'agents': return Users
      case 'comparison': return TrendingUp
      case 'legal': return FileText
      default: return FileText
    }
  }

  const getTypeColor = (type) => {
    switch (type) {
      case 'cost': return 'text-green-600'
      case 'sla': return 'text-blue-600'
      case 'compliance': return 'text-purple-600'
      case 'agents': return 'text-orange-600'
      case 'comparison': return 'text-indigo-600'
      case 'legal': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }

  const handleGenerateReport = async (templateId) => {
    setIsGenerating(true)
    // Simular geração de relatório
    await new Promise(resolve => setTimeout(resolve, 3000))
    setIsGenerating(false)
  }

  const filteredReports = availableReports.filter(report => {
    if (selectedType !== 'all' && report.type !== selectedType) return false
    if (selectedPeriod !== 'all' && report.period !== selectedPeriod) return false
    return true
  })

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-3xl font-bold text-foreground">Relatórios</h2>
          <p className="text-muted-foreground">
            Geração e gerenciamento de relatórios executivos e técnicos
          </p>
        </div>
        <div className="flex space-x-2">
          <Dialog>
            <DialogTrigger asChild>
              <Button>
                <FileText className="h-4 w-4 mr-2" />
                Novo Relatório
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Gerar Novo Relatório</DialogTitle>
                <DialogDescription>
                  Selecione um template e configure os parâmetros do relatório
                </DialogDescription>
              </DialogHeader>
              
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="template" className="text-right">
                    Template
                  </Label>
                  <Select>
                    <SelectTrigger className="col-span-3">
                      <SelectValue placeholder="Selecione um template" />
                    </SelectTrigger>
                    <SelectContent>
                      {reportTemplates.map(template => (
                        <SelectItem key={template.id} value={template.id}>
                          {template.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="period" className="text-right">
                    Período
                  </Label>
                  <Select>
                    <SelectTrigger className="col-span-3">
                      <SelectValue placeholder="Selecione o período" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="last-week">Última semana</SelectItem>
                      <SelectItem value="last-month">Último mês</SelectItem>
                      <SelectItem value="last-quarter">Último trimestre</SelectItem>
                      <SelectItem value="custom">Personalizado</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="title" className="text-right">
                    Título
                  </Label>
                  <Input
                    id="title"
                    placeholder="Título do relatório"
                    className="col-span-3"
                  />
                </div>
                
                <div className="grid grid-cols-4 items-start gap-4">
                  <Label htmlFor="description" className="text-right">
                    Descrição
                  </Label>
                  <Textarea
                    id="description"
                    placeholder="Descrição opcional do relatório"
                    className="col-span-3"
                  />
                </div>
              </div>
              
              <DialogFooter>
                <Button variant="outline">Cancelar</Button>
                <Button onClick={() => handleGenerateReport('executive-summary')} disabled={isGenerating}>
                  {isGenerating ? 'Gerando...' : 'Gerar Relatório'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex items-center space-x-2">
              <Label htmlFor="type-filter">Tipo:</Label>
              <Select value={selectedType} onValueChange={setSelectedType}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos</SelectItem>
                  <SelectItem value="cost">Custos</SelectItem>
                  <SelectItem value="sla">SLA</SelectItem>
                  <SelectItem value="compliance">Compliance</SelectItem>
                  <SelectItem value="agents">Agentes</SelectItem>
                  <SelectItem value="comparison">Comparação</SelectItem>
                  <SelectItem value="legal">Jurídico</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex items-center space-x-2">
              <Label htmlFor="period-filter">Período:</Label>
              <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos</SelectItem>
                  <SelectItem value="weekly">Semanal</SelectItem>
                  <SelectItem value="monthly">Mensal</SelectItem>
                  <SelectItem value="quarterly">Trimestral</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="text-sm text-muted-foreground">
              {filteredReports.length} relatório(s) encontrado(s)
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Reports Grid */}
      <div className="grid gap-6">
        {filteredReports.map((report, index) => {
          const TypeIcon = getTypeIcon(report.type)
          
          return (
            <motion.div
              key={report.id}
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
                          <TypeIcon className="h-6 w-6 text-white" />
                        </div>
                      </div>
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold">{report.title}</h3>
                        <p className="text-sm text-muted-foreground mb-2">{report.description}</p>
                        <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                          <span className="flex items-center">
                            <Calendar className="h-4 w-4 mr-1" />
                            {report.lastGenerated}
                          </span>
                          <span>{report.size}</span>
                          <span>{report.pages} páginas</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Badge className={getStatusColor(report.status)}>
                        {getStatusText(report.status)}
                      </Badge>
                    </div>
                  </div>
                  
                  {/* Insights */}
                  <div className="mb-4">
                    <h4 className="text-sm font-medium mb-2">Principais Insights:</h4>
                    <ul className="space-y-1">
                      {report.insights.map((insight, idx) => (
                        <li key={idx} className="text-sm text-muted-foreground flex items-start">
                          <span className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 mr-2 flex-shrink-0" />
                          {insight}
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  {/* Actions */}
                  <div className="flex justify-between items-center">
                    <div className="flex space-x-2">
                      <Button variant="outline" size="sm" disabled={report.status !== 'ready'}>
                        <Eye className="h-4 w-4 mr-2" />
                        Visualizar
                      </Button>
                      <Button variant="outline" size="sm" disabled={report.status !== 'ready'}>
                        <Download className="h-4 w-4 mr-2" />
                        Download
                      </Button>
                      <Button variant="outline" size="sm" disabled={report.status !== 'ready'}>
                        <Share className="h-4 w-4 mr-2" />
                        Compartilhar
                      </Button>
                    </div>
                    
                    <div className="flex space-x-1">
                      <Button variant="ghost" size="sm" disabled={report.status !== 'ready'}>
                        <Mail className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm" disabled={report.status !== 'ready'}>
                        <Printer className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )
        })}
      </div>

      {/* Report Templates */}
      <Card>
        <CardHeader>
          <CardTitle>Templates Disponíveis</CardTitle>
          <CardDescription>
            Templates pré-configurados para diferentes tipos de relatórios
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {reportTemplates.map((template) => (
              <div key={template.id} className="p-4 border rounded-lg">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-medium">{template.name}</h4>
                  <Badge variant="outline">{template.estimatedPages} páginas</Badge>
                </div>
                <p className="text-sm text-muted-foreground mb-3">{template.description}</p>
                <div className="mb-3">
                  <div className="text-xs text-muted-foreground mb-1">Seções incluídas:</div>
                  <div className="flex flex-wrap gap-1">
                    {template.sections.map((section, idx) => (
                      <Badge key={idx} variant="secondary" className="text-xs">
                        {section}
                      </Badge>
                    ))}
                  </div>
                </div>
                <Button 
                  size="sm" 
                  className="w-full"
                  onClick={() => handleGenerateReport(template.id)}
                  disabled={isGenerating}
                >
                  {isGenerating ? 'Gerando...' : 'Usar Template'}
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <FileText className="h-5 w-5 text-blue-500" />
              <div>
                <div className="text-2xl font-bold">{availableReports.length}</div>
                <div className="text-xs text-muted-foreground">Total de Relatórios</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-green-500" />
              <div>
                <div className="text-2xl font-bold">
                  {availableReports.filter(r => r.status === 'ready').length}
                </div>
                <div className="text-xs text-muted-foreground">Prontos</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5 text-purple-500" />
              <div>
                <div className="text-2xl font-bold">
                  {availableReports.filter(r => r.status === 'generating').length}
                </div>
                <div className="text-xs text-muted-foreground">Em Geração</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Download className="h-5 w-5 text-orange-500" />
              <div>
                <div className="text-2xl font-bold">47</div>
                <div className="text-xs text-muted-foreground">Downloads Este Mês</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

