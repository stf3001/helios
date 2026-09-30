import { Routes, Route, Navigate } from 'react-router-dom'
import Header from './components/layout/Header'
import Footer from './components/layout/Footer'
import ProtectedRoute from './components/ProtectedRoute'
import Home from './pages/Home'
import Vision from './pages/Vision'
import Colibri from './pages/Colibri'
import HeliosIA from './pages/HeliosIA'
import Faq from './pages/Faq'
import FaqDetail from './pages/FaqDetail'
import Partenaires from './pages/Partenaires'
import Login from './pages/auth/Login'
import Register from './pages/auth/Register'
import VerifyEmail from './pages/auth/VerifyEmail'
import FicheMaison from './pages/FicheMaison'
import EspaceHelios from './pages/EspaceHelios'
import EspaceJardin from './pages/EspaceJardin'
import SimulateurSolaire from './pages/SimulateurSolaire'
import Vent from './pages/Vent'
import AchatEnergie from './pages/AchatEnergie'
import EspaceAudits from './pages/EspaceAudits'
import EspaceEnergie from './pages/EspaceEnergie'
import DevenirPartenaire from './pages/DevenirPartenaire'
import EspaceMisesEnRelation from './pages/EspaceMisesEnRelation'
import PartnerPortal from './pages/PartnerPortal'
import Espace from './pages/Espace'
import EspaceCompte from './pages/EspaceCompte'
import Glossaire from './pages/Glossaire'
import PotentielHydrique from './pages/PotentielHydrique'
import EspacePro from './pages/EspacePro'
import Engagements from './pages/Engagements'
import Eau from './pages/Eau'
import Terre from './pages/Terre'
import QuiSommesNous from './pages/QuiSommesNous'
import Pilier from './pages/Pilier'
import Ville from './pages/Ville'
import piliers from './data/piliers.json'
import AdminRoute from './components/admin/AdminRoute'
import AdminDashboard from './pages/admin/AdminDashboard'
import AdminPartenaires from './pages/admin/AdminPartenaires'
import AdminServices from './pages/admin/AdminServices'
import AdminAgents from './pages/admin/AdminAgents'
import AdminConversations from './pages/admin/AdminConversations'
import AdminConnaissances from './pages/admin/AdminConnaissances'
import AdminSignalements from './pages/admin/AdminSignalements'
import AdminFoyers from './pages/admin/AdminFoyers'

/** Le back-office a sa propre coquille (fond sombre, pas de header/footer public) :
 * il est donc monté AVANT le site public, en dehors de sa mise en page. */
function AdminRoutes() {
  return (
    <Routes>
      <Route path="/" element={<AdminRoute><AdminDashboard /></AdminRoute>} />
      <Route path="/conversations" element={<AdminRoute><AdminConversations /></AdminRoute>} />
      <Route path="/connaissances" element={<AdminRoute><AdminConnaissances /></AdminRoute>} />
      <Route path="/signalements" element={<AdminRoute><AdminSignalements /></AdminRoute>} />
      <Route path="/foyers" element={<AdminRoute><AdminFoyers /></AdminRoute>} />
      <Route path="/partenaires" element={<AdminRoute><AdminPartenaires /></AdminRoute>} />
      <Route path="/services" element={<AdminRoute><AdminServices /></AdminRoute>} />
      <Route path="/agents" element={<AdminRoute><AdminAgents /></AdminRoute>} />
    </Routes>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/admin/*" element={<AdminRoutes />} />
      <Route path="*" element={<SitePublic />} />
    </Routes>
  )
}

function SitePublic() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/vision" element={<Vision />} />
          <Route path="/colibri" element={<Colibri />} />
          <Route path="/qui-sommes-nous" element={<QuiSommesNous />} />
          {/* « Qui est Helios ? » a fusionné avec « Helios (IA) » le 30/09/2026 : les deux
              disaient la même chose à deux endroits du menu. L'ancienne adresse redirige
              plutôt que de disparaître — elle est dans des liens et référencée. */}
          <Route path="/comment-ca-marche" element={<Navigate to="/helios" replace />} />
          <Route path="/engagements" element={<Engagements />} />
          <Route path="/helios" element={<HeliosIA />} />
          <Route path="/glossaire" element={<Glossaire />} />
          <Route path="/faq" element={<Faq />} />
          <Route path="/faq/:slug" element={<FaqDetail />} />
          {/* Section Guides supprimée le 28/09/2026 : elle redisait la FAQ. Les 301 vivent
              dans deploy/nginx.conf pour les visiteurs venus d'un lien externe ; celle-ci
              couvre le développement et le cas où la configuration nginx ne serait pas à jour. */}
          <Route path="/guides/*" element={<Navigate to="/faq" replace />} />
          <Route path="/guides" element={<Navigate to="/faq" replace />} />
          <Route path="/partenaires" element={<Partenaires />} />
          <Route path="/devenir-partenaire" element={<DevenirPartenaire />} />
          <Route path="/partenaire" element={<PartnerPortal />} />
          <Route path="/simulateur-solaire" element={<SimulateurSolaire />} />
          <Route path="/eau" element={<Eau />} />
          <Route path="/le-vent" element={<Vent />} />
          <Route path="/la-terre" element={<Terre />} />
          <Route path="/achat-energie" element={<AchatEnergie />} />
          {/* Pages chapeau : routes dérivées de data/piliers.json. Celles marquées
              `pageDediee` ont déjà leur propre page (ex. /eau) et sont donc exclues. */}
          <Route path="/solaire/:slug" element={<Ville />} />
          {piliers.filter((p) => !(p as { pageDediee?: boolean }).pageDediee).map((p) => (
            <Route key={p.slug} path={`/${p.slug}`} element={<Pilier />} />
          ))}
          <Route path="/potentiel-hydrique" element={<PotentielHydrique />} />
          <Route path="/connexion" element={<Login />} />
          <Route path="/inscription" element={<Register />} />
          <Route path="/verifier-email" element={<VerifyEmail />} />
          <Route path="/espace" element={<ProtectedRoute><Espace /></ProtectedRoute>} />
          <Route path="/espace/compte" element={<ProtectedRoute><EspaceCompte /></ProtectedRoute>} />
          <Route path="/espace/pro" element={<ProtectedRoute><EspacePro /></ProtectedRoute>} />
          <Route path="/mon-espace" element={<ProtectedRoute><FicheMaison /></ProtectedRoute>} />
          <Route path="/espace/helios" element={<ProtectedRoute><EspaceHelios /></ProtectedRoute>} />
          <Route path="/espace/jardin" element={<ProtectedRoute><EspaceJardin /></ProtectedRoute>} />
          <Route path="/espace/audits" element={<ProtectedRoute><EspaceAudits /></ProtectedRoute>} />
          <Route path="/espace/energie" element={<ProtectedRoute><EspaceEnergie /></ProtectedRoute>} />
          <Route path="/espace/mises-en-relation" element={<ProtectedRoute><EspaceMisesEnRelation /></ProtectedRoute>} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}
