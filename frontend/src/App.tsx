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
          <Route path="/simulateur-solaire" element={<SimulateurSolaire />} />
          <Route path="/connexion" element={<Login />} />
          <Route path="/inscription" element={<Register />} />
          <Route path="/verifier-email" element={<VerifyEmail />} />
          <Route path="/mon-espace" element={<ProtectedRoute><FicheMaison /></ProtectedRoute>} />
          <Route path="/espace/helios" element={<ProtectedRoute><EspaceHelios /></ProtectedRoute>} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}
