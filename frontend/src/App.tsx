import { Routes, Route } from 'react-router-dom'
import Header from './components/layout/Header'
import Footer from './components/layout/Footer'
import ProtectedRoute from './components/ProtectedRoute'
import Home from './pages/Home'
import Vision from './pages/Vision'
import Colibri from './pages/Colibri'
import CommentCaMarche from './pages/CommentCaMarche'
import HeliosIA from './pages/HeliosIA'
import Faq from './pages/Faq'
import Partenaires from './pages/Partenaires'
import Login from './pages/auth/Login'
import Register from './pages/auth/Register'
import VerifyEmail from './pages/auth/VerifyEmail'
import FicheMaison from './pages/FicheMaison'
import EspaceHelios from './pages/EspaceHelios'
import SimulateurSolaire from './pages/SimulateurSolaire'
import EspaceAudits from './pages/EspaceAudits'
import EspaceEnergie from './pages/EspaceEnergie'
import DevenirPartenaire from './pages/DevenirPartenaire'
import EspaceMisesEnRelation from './pages/EspaceMisesEnRelation'

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/vision" element={<Vision />} />
          <Route path="/colibri" element={<Colibri />} />
          <Route path="/comment-ca-marche" element={<CommentCaMarche />} />
          <Route path="/helios" element={<HeliosIA />} />
          <Route path="/faq" element={<Faq />} />
          <Route path="/partenaires" element={<Partenaires />} />
          <Route path="/devenir-partenaire" element={<DevenirPartenaire />} />
          <Route path="/simulateur-solaire" element={<SimulateurSolaire />} />
          <Route path="/connexion" element={<Login />} />
          <Route path="/inscription" element={<Register />} />
          <Route path="/verifier-email" element={<VerifyEmail />} />
          <Route path="/mon-espace" element={<ProtectedRoute><FicheMaison /></ProtectedRoute>} />
          <Route path="/espace/helios" element={<ProtectedRoute><EspaceHelios /></ProtectedRoute>} />
          <Route path="/espace/audits" element={<ProtectedRoute><EspaceAudits /></ProtectedRoute>} />
          <Route path="/espace/energie" element={<ProtectedRoute><EspaceEnergie /></ProtectedRoute>} />
          <Route path="/espace/mises-en-relation" element={<ProtectedRoute><EspaceMisesEnRelation /></ProtectedRoute>} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}
