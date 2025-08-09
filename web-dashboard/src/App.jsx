import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  Cloud, 
  DollarSign, 
  Shield, 
  Activity, 
  FileText, 
  Settings,
  Menu,
  X,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  PieChart,
  Users,
  Server
} from 'lucide-react'
import { Button } from './components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card.jsx'
import { Badge } from './components/ui/badge.jsx'
import { Progress } from './components/ui/progress.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs.jsx'
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  PieChart as RechartsPieChart, 
  Cell, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts'
import './App.css'

// Componentes
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import Dashboard from './components/Dashboard'
import CostAnalysis from './components/CostAnalysis'
import SLAMonitoring from './components/SLAMonitoring'
import ComplianceReport from './components/ComplianceReport'
import AgentStatus from './components/AgentStatus'
import Reports from './components/Reports'

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [darkMode, setDarkMode] = useState(false)

  // Dados simulados para demonstração
  const [dashboardData, setDashboardData] = useState({
    totalCost: 45678.90,
    monthlyChange: -12.5,
    potentialSavings: 8934.50,
    slaScore: 99.2,
    complianceScore: 94.8,
    agentHealth: 98.5,
    criticalIssues: 2,
    optimizationOpportunities: 7
  })

  const [costTrend, setCostTrend] = useState([
    { month: 'Jan', aws: 15000, gcp: 12000, total: 27000 },
    { month: 'Fev', aws: 18000, gcp: 14000, total: 32000 },
    { month: 'Mar', aws: 16500, gcp: 13500, total: 30000 },
    { month: 'Abr', aws: 19000, gcp: 15000, total: 34000 },
    { month: 'Mai', aws: 17500, gcp: 14500, total: 32000 },
    { month: 'Jun', aws: 20000, gcp: 16000, total: 36000 }
  ])

  const [providerComparison, setProviderComparison] = useState([
    { name: 'AWS', value: 58, color: '#FF9500' },
    { name: 'GCP', value: 42, color: '#4285F4' }
  ])

  const [agentStatus, setAgentStatus] = useState([
    { name: 'Gerente Operacional', status: 'active', health: 98, lastUpdate: '2 min' },
    { name: 'Especialista AWS', status: 'active', health: 96, lastUpdate: '1 min' },
    { name: 'Especialista GCP', status: 'active', health: 99, lastUpdate: '30 seg' },
    { name: 'Coordenador SLA', status: 'active', health: 94, lastUpdate: '5 min' },
    { name: 'Coordenador Custos', status: 'active', health: 97, lastUpdate: '3 min' },
    { name: 'Coordenador Compliance', status: 'warning', health: 89, lastUpdate: '10 min' },
    { name: 'Coordenador Jurídico', status: 'active', health: 95, lastUpdate: '2 min' },
    { name: 'Gerador Relatórios', status: 'active', health: 100, lastUpdate: '1 min' }
  ])

  useEffect(() => {
    // Simular atualizações em tempo real
    const interval = setInterval(() => {
      setDashboardData(prev => ({
        ...prev,
        agentHealth: Math.max(90, Math.min(100, prev.agentHealth + (Math.random() - 0.5) * 2))
      }))
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const toggleDarkMode = () => {
    setDarkMode(!darkMode)
    document.documentElement.classList.toggle('dark')
  }

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard data={dashboardData} costTrend={costTrend} providerComparison={providerComparison} />
      case 'cost-analysis':
        return <CostAnalysis costTrend={costTrend} providerComparison={providerComparison} />
      case 'sla-monitoring':
        return <SLAMonitoring />
      case 'compliance':
        return <ComplianceReport />
      case 'agents':
        return <AgentStatus agents={agentStatus} />
      case 'reports':
        return <Reports />
      default:
        return <Dashboard data={dashboardData} costTrend={costTrend} providerComparison={providerComparison} />
    }
  }

  return (
    <div className={`min-h-screen bg-background ${darkMode ? 'dark' : ''}`}>
      <div className="flex">
        {/* Sidebar */}
        <Sidebar 
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          currentPage={currentPage}
          onPageChange={setCurrentPage}
        />

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <Header 
            onMenuClick={() => setSidebarOpen(true)}
            darkMode={darkMode}
            onToggleDarkMode={toggleDarkMode}
          />

          {/* Page Content */}
          <main className="flex-1 p-6 overflow-auto">
            <motion.div
              key={currentPage}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              {renderPage()}
            </motion.div>
          </main>
        </div>
      </div>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  )
}

export default App

