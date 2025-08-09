import { motion } from 'framer-motion'
import { 
  Cloud, 
  DollarSign, 
  Shield, 
  Activity, 
  FileText, 
  Settings,
  X,
  BarChart3,
  Users,
  Home
} from 'lucide-react'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'

const menuItems = [
  { id: 'dashboard', label: 'Dashboard', icon: Home },
  { id: 'cost-analysis', label: 'Análise de Custos', icon: DollarSign },
  { id: 'sla-monitoring', label: 'Monitoramento SLA', icon: Activity },
  { id: 'compliance', label: 'Compliance', icon: Shield },
  { id: 'agents', label: 'Status dos Agentes', icon: Users },
  { id: 'reports', label: 'Relatórios', icon: FileText }
]

export default function Sidebar({ isOpen, onClose, currentPage, onPageChange }) {
  return (
    <>
      {/* Desktop Sidebar */}
      <div className="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0 lg:bg-card lg:border-r lg:border-border">
        <div className="flex flex-col flex-1 min-h-0">
          {/* Logo */}
          <div className="flex items-center h-16 px-6 border-b border-border">
            <Cloud className="h-8 w-8 text-primary" />
            <span className="ml-3 text-lg font-semibold text-foreground">
              Cloud Agents
            </span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {menuItems.map((item) => {
              const Icon = item.icon
              const isActive = currentPage === item.id
              
              return (
                <Button
                  key={item.id}
                  variant={isActive ? "default" : "ghost"}
                  className={`w-full justify-start h-12 ${
                    isActive 
                      ? 'bg-primary text-primary-foreground' 
                      : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                  }`}
                  onClick={() => onPageChange(item.id)}
                >
                  <Icon className="h-5 w-5 mr-3" />
                  {item.label}
                </Button>
              )
            })}
          </nav>

          {/* Status */}
          <div className="p-4 border-t border-border">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Sistema</span>
              <Badge variant="default" className="bg-green-500">
                Online
              </Badge>
            </div>
            <div className="mt-2 text-xs text-muted-foreground">
              8 agentes ativos
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Sidebar */}
      <motion.div
        initial={{ x: -300 }}
        animate={{ x: isOpen ? 0 : -300 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="fixed inset-y-0 left-0 z-50 w-64 bg-card border-r border-border lg:hidden"
      >
        <div className="flex flex-col flex-1 min-h-0">
          {/* Header */}
          <div className="flex items-center justify-between h-16 px-6 border-b border-border">
            <div className="flex items-center">
              <Cloud className="h-8 w-8 text-primary" />
              <span className="ml-3 text-lg font-semibold text-foreground">
                Cloud Agents
              </span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {menuItems.map((item) => {
              const Icon = item.icon
              const isActive = currentPage === item.id
              
              return (
                <Button
                  key={item.id}
                  variant={isActive ? "default" : "ghost"}
                  className={`w-full justify-start h-12 ${
                    isActive 
                      ? 'bg-primary text-primary-foreground' 
                      : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                  }`}
                  onClick={() => {
                    onPageChange(item.id)
                    onClose()
                  }}
                >
                  <Icon className="h-5 w-5 mr-3" />
                  {item.label}
                </Button>
              )
            })}
          </nav>

          {/* Status */}
          <div className="p-4 border-t border-border">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Sistema</span>
              <Badge variant="default" className="bg-green-500">
                Online
              </Badge>
            </div>
            <div className="mt-2 text-xs text-muted-foreground">
              8 agentes ativos
            </div>
          </div>
        </div>
      </motion.div>

      {/* Spacer for desktop */}
      <div className="hidden lg:block lg:w-64 lg:flex-shrink-0" />
    </>
  )
}

