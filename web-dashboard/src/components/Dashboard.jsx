import { motion } from 'framer-motion'
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  Shield, 
  Activity, 
  AlertTriangle,
  CheckCircle,
  Server,
  Cloud
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  PieChart, 
  Cell, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts'

const COLORS = ['#FF9500', '#4285F4', '#34A853', '#EA4335']

export default function Dashboard({ data, costTrend, providerComparison }) {
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'USD'
    }).format(value)
  }

  const formatPercentage = (value) => {
    return `${value.toFixed(1)}%`
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-3xl font-bold text-foreground">Dashboard</h2>
        <p className="text-muted-foreground">
          Visão geral dos custos e performance dos recursos cloud
        </p>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Cost */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Custo Total Mensal</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(data.totalCost)}</div>
              <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                {data.monthlyChange < 0 ? (
                  <>
                    <TrendingDown className="h-3 w-3 text-green-500" />
                    <span className="text-green-500">{Math.abs(data.monthlyChange)}% menor</span>
                  </>
                ) : (
                  <>
                    <TrendingUp className="h-3 w-3 text-red-500" />
                    <span className="text-red-500">{data.monthlyChange}% maior</span>
                  </>
                )}
                <span>que o mês anterior</span>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Potential Savings */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Economia Potencial</CardTitle>
              <TrendingDown className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {formatCurrency(data.potentialSavings)}
              </div>
              <div className="text-xs text-muted-foreground">
                {data.optimizationOpportunities} oportunidades identificadas
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* SLA Score */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Score SLA</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatPercentage(data.slaScore)}</div>
              <Progress value={data.slaScore} className="mt-2" />
              <div className="text-xs text-muted-foreground mt-1">
                Disponibilidade média dos serviços
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Compliance Score */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Compliance</CardTitle>
              <Shield className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatPercentage(data.complianceScore)}</div>
              <Progress value={data.complianceScore} className="mt-2" />
              <div className="flex items-center space-x-1 text-xs text-muted-foreground mt-1">
                {data.criticalIssues > 0 ? (
                  <>
                    <AlertTriangle className="h-3 w-3 text-yellow-500" />
                    <span>{data.criticalIssues} questões críticas</span>
                  </>
                ) : (
                  <>
                    <CheckCircle className="h-3 w-3 text-green-500" />
                    <span>Sem questões críticas</span>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cost Trend Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>Tendência de Custos</CardTitle>
              <CardDescription>
                Evolução dos custos por provedor nos últimos 6 meses
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={costTrend}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip 
                    formatter={(value) => [formatCurrency(value), '']}
                    labelFormatter={(label) => `Mês: ${label}`}
                  />
                  <Legend />
                  <Area 
                    type="monotone" 
                    dataKey="aws" 
                    stackId="1" 
                    stroke="#FF9500" 
                    fill="#FF9500" 
                    fillOpacity={0.6}
                    name="AWS"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="gcp" 
                    stackId="1" 
                    stroke="#4285F4" 
                    fill="#4285F4" 
                    fillOpacity={0.6}
                    name="GCP"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>

        {/* Provider Distribution */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>Distribuição por Provedor</CardTitle>
              <CardDescription>
                Percentual de custos por provedor cloud
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={providerComparison}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {providerComparison.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [`${value}%`, 'Percentual']} />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex justify-center space-x-4 mt-4">
                {providerComparison.map((provider, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{ backgroundColor: provider.color }}
                    />
                    <span className="text-sm text-muted-foreground">
                      {provider.name}: {provider.value}%
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Agent Health Status */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
      >
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Server className="h-5 w-5" />
              <span>Status dos Agentes</span>
            </CardTitle>
            <CardDescription>
              Saúde geral do sistema de agentes de IA
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="text-3xl font-bold text-green-600">
                  {formatPercentage(data.agentHealth)}
                </div>
                <div>
                  <div className="text-sm font-medium">Saúde Geral</div>
                  <div className="text-xs text-muted-foreground">
                    8 agentes operacionais
                  </div>
                </div>
              </div>
              <div className="flex space-x-2">
                <Badge variant="default" className="bg-green-500">
                  7 Ativos
                </Badge>
                <Badge variant="secondary">
                  1 Atenção
                </Badge>
              </div>
            </div>
            <Progress value={data.agentHealth} className="mt-4" />
          </CardContent>
        </Card>
      </motion.div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Ações Rápidas</CardTitle>
            <CardDescription>
              Principais recomendações baseadas na análise atual
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 border border-border rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <DollarSign className="h-4 w-4 text-green-500" />
                  <span className="font-medium">Otimização de Custos</span>
                </div>
                <p className="text-sm text-muted-foreground">
                  Identificadas 7 oportunidades de economia que podem reduzir custos em até 19%.
                </p>
              </div>
              
              <div className="p-4 border border-border rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <Shield className="h-4 w-4 text-blue-500" />
                  <span className="font-medium">Compliance</span>
                </div>
                <p className="text-sm text-muted-foreground">
                  2 questões de compliance requerem atenção para manter conformidade total.
                </p>
              </div>
              
              <div className="p-4 border border-border rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <Activity className="h-4 w-4 text-purple-500" />
                  <span className="font-medium">Performance</span>
                </div>
                <p className="text-sm text-muted-foreground">
                  SLA mantido acima de 99% com excelente disponibilidade dos serviços.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}

