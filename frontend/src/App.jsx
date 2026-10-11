import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Home from './pages/Home';
import StudioLayout from './layouts/StudioLayout';
import TextStudio from './pages/studio/TextStudio';
import DocumentStudio from './pages/studio/DocumentStudio';
import MediaStudio from './pages/studio/MediaStudio';
import YouTubeStudio from './pages/studio/YouTubeStudio';
import './App.css';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Marketing Landing Page */}
        <Route path="/" element={<Home />} />

        {/* Studio Workspace (Independent layout with no home hero) */}
        <Route path="/studio" element={<StudioLayout />}>
          <Route index element={<Navigate to="/studio/text" replace />} />
          <Route path="text" element={<TextStudio />} />
          <Route path="document" element={<DocumentStudio />} />
          <Route path="media" element={<MediaStudio />} />
          <Route path="youtube" element={<YouTubeStudio />} />
        </Route>

        {/* Fallback route */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
