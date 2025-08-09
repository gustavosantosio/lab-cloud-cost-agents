import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  Filter,
  Download,
  RefreshCw,
  AlertCircle,
  CheckCircle
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
import { 
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts'

export default function CostAnalysis({ costTrend, providerComparison }) {
  const [selectedPeriod, setSelectedPeriod] = useState('6m')
  const [selectedProvider, setSelectedProvider] = useState('all')

  // Dados simulados para análise detalhada
  const serviceBreakdown = [
    { service: 'Compute (EC2/Compute Engine)', aws: 12000, gcp: 8000, total: 20000, percentage: 45 },
    { service: 'Storage (S3/Cloud Storage)', aws: 4000, gcp: 3500, total: 7500, percentage: 17 },
    { service: 'Database (RDS/Cloud SQL)', aws: 3500, gcp: 2800, total: 6300, percentage: 14 },
    { service: 'Networking', aws: 2500, gcp: 2200, total: 4700, percentage: 11 },
    { service: 'Outros Serviços', aws: 3000, gcp: 2700, total: 5700, percentage: 13 }
  ]

  const optimizationOpportunities = [
    {
      id: 1,
      title: 'Reserved Instances AWS EC2',
      description: 'Migrar instâncias On-Demand para Reserved Instances',
      currentCost: 8500,
      potentialSavings: 2550,
      savingsPercentage: 30,
      effort: 'Baixo',
      priority: 'Alta',
      roi: '3 meses'
    },
    {
      id: 2,
      title: 'Otimização Storage Classes',
      description: 'Mover dados antigos para classes de armazenamento mais baratas',
      currentCost: 4000,
      potentialSavings: 1200,
      savingsPercentage: 30,
      effort: 'Médio',
      priority: 'Alta',
      roi: '2 meses'
    },
    {
      id: 3,
      title: 'Right-sizing GCP Compute',
      description: 'Ajustar tamanho das instâncias baseado no uso real',
      currentCost: 6000,
      potentialSavings: 1800,
      savingsPercentage: 30,
      effort: 'Alto',
      priority: 'Média',
      roi: '4 meses'
    },
    {
      id: 4,
      title: 'Cleanup de Recursos Órfãos',
      description: 'Remover volumes, snapshots e IPs não utilizados',
      currentCost: 1500,
      potentialSavings: 1200,
      savingsPercentage: 80,
      effort: 'Baixo',
      priority: 'Alta',
      roi: '1 mês'
    }
  ]

  const regionCosts = [
    { region: 'us-east-1', cost: 15000, percentage: 35 },
    { region: 'us-west-2', cost: 12000, percentage: 28 },
    { region: 'eu-west-1', cost: 8000, percentage: 19 },
    { region: 'ap-southeast-1', cost: 5000, percentage: 12 },
    { region: 'sa-east-1', cost: 2500, percentage: 6 }
  ]

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'USD'
    }).format(value)
  }

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'Alta': return 'bg-red-500'
      case 'Média': return 'bg-yellow-500'
      case 'Baixa': return 'bg-green-500'
      default: return 'bg-gray-500'
    }
  }

  const getEffortColor = (effort) => {
    switch (effort) {
      case 'Baixo': return 'text-green-600'
      case 'Médio': return 'text-yellow-600'
      case 'Alto': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-3xl font-bold text-foreground">Análise de Custos</h2>
          <p className="text-muted-foreground">
            Análise detalhada dos custos e oportunidades de otimização
          </p>
        </div>
        <div className="flex space-x-2">
          <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1m">1 Mês</SelectItem>
              <SelectItem value="3m">3 Meses</SelectItem>
              <SelectItem value="6m">6 Meses</SelectItem>
              <SelectItem value="1y">1 Ano</SelectItem>
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

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Custo Total</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(44200)}</div>
            <div className="text-xs text-muted-foreground">Últimos 30 dias</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Economia Potencial</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{formatCurrency(6750)}</div>
            <div className="text-xs text-muted-foreground">15.3% do total</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Maior Gasto</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Compute</div>
            <div className="text-xs text-muted-foreground">{formatCurrency(20000)} (45%)</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Oportunidades</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">4</div>
            <div className="text-xs text-muted-foreground">Ações recomendadas</div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="breakdown" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="breakdown">Breakdown por Serviço</TabsTrigger>
          <TabsTrigger value="trends">Tendências</TabsTrigger>
          <TabsTrigger value="optimization">Otimizações</TabsTrigger>
          <TabsTrigger value="regions">Por Região</TabsTrigger>
        </TabsList>

        {/* Service Breakdown */}
        <TabsContent value="breakdown" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Custos por Categoria de Serviço</CardTitle>
              <CardDescription>
                Distribuição detalhada dos custos por tipo de serviço
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={serviceBreakdown}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="service" 
                    angle={-45}
                    textAnchor="end"
                    height={100}
                  />
                  <YAxis />
                  <Tooltip formatter={(value) => formatCurrency(value)} />
                  <Legend />
                  <Bar dataKey="aws" fill="#FF9500" name="AWS" />
                  <Bar dataKey="gcp" fill="#4285F4" name="GCP" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Service Details Table */}
          <Card>
            <CardHeader>
              <CardTitle>Detalhamento por Serviço</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Serviço</th>
                      <th className="text-right p-2">AWS</th>
                      <th className="text-right p-2">GCP</th>
                      <th className="text-right p-2">Total</th>
                      <th className="text-right p-2">% do Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {serviceBreakdown.map((service, index) => (
                      <tr key={index} className="border-b">
                        <td className="p-2 font-medium">{service.service}</td>
                        <td className="p-2 text-right">{formatCurrency(service.aws)}</td>
                        <td className="p-2 text-right">{formatCurrency(service.gcp)}</td>
                        <td className="p-2 text-right font-medium">{formatCurrency(service.total)}</td>
                        <td className="p-2 text-right">{service.percentage}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Trends */}
        <TabsContent value="trends" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Tendência de Custos por Provedor</CardTitle>
              <CardDescription>
                Evolução dos custos nos últimos 6 meses
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={costTrend}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip formatter={(value) => formatCurrency(value)} />
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
                    dataKey="total" 
                    stroke="#34A853" 
                    strokeWidth={3}
                    strokeDasharray="5 5"
                    name="Total"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Optimization Opportunities */}
        <TabsContent value="optimization" className="space-y-6">
          <div className="grid gap-6">
            {optimizationOpportunities.map((opportunity) => (
              <motion.div
                key={opportunity.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: opportunity.id * 0.1 }}
              >
                <Card>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-lg">{opportunity.title}</CardTitle>
                        <CardDescription>{opportunity.description}</CardDescription>
                      </div>
                      <Badge className={getPriorityColor(opportunity.priority)}>
                        {opportunity.priority}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                      <div>
                        <div className="text-sm text-muted-foreground">Custo Atual</div>
                        <div className="text-lg font-semibold">
                          {formatCurrency(opportunity.currentCost)}
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-muted-foreground">Economia Potencial</div>
                        <div className="text-lg font-semibold text-green-600">
                          {formatCurrency(opportunity.potentialSavings)}
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-muted-foreground">% Economia</div>
                        <div className="text-lg font-semibold text-green-600">
                          {opportunity.savingsPercentage}%
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-muted-foreground">Esforço</div>
                        <div className={`text-lg font-semibold ${getEffortColor(opportunity.effort)}`}>
                          {opportunity.effort}
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-muted-foreground">ROI</div>
                        <div className="text-lg font-semibold">
                          {opportunity.roi}
                        </div>
                      </div>
                    </div>
                    <div className="mt-4 flex justify-end">
                      <Button size="sm">
                        Implementar Otimização
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </TabsContent>

        {/* Regional Costs */}
        <TabsContent value="regions" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Custos por Região</CardTitle>
                <CardDescription>
                  Distribuição geográfica dos recursos
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={regionCosts}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ region, percentage }) => `${region}: ${percentage}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="cost"
                    >
                      {regionCosts.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={`hsl(${index * 72}, 70%, 50%)`} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => formatCurrency(value)} />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Detalhamento Regional</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {regionCosts.map((region, index) => (
                    <div key={index} className="flex justify-between items-center p-3 border rounded-lg">
                      <div>
                        <div className="font-medium">{region.region}</div>
                        <div className="text-sm text-muted-foreground">
                          {region.percentage}% do total
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold">{formatCurrency(region.cost)}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

