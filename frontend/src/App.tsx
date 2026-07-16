import { Routes, Route } from 'react-router-dom'
import Header from './components/layout/Header'
import Footer from './components/layout/Footer'
import Home from './pages/Home'
import Vision from './pages/Vision'
import Colibri from './pages/Colibri'
import CommentCaMarche from './pages/CommentCaMarche'
import HeliosIA from './pages/HeliosIA'
import Faq from './pages/Faq'
import Partenaires from './pages/Partenaires'

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
        </Routes>
      </main>
      <Footer />
    </div>
  )
}
