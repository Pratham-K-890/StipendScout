import { Route, Routes } from 'react-router-dom'

import { ApplicationDetailPage } from '@/pages/ApplicationDetailPage'
import { ApplicationsListPage } from '@/pages/ApplicationsListPage'
import { ProfilePage } from '@/pages/ProfilePage'
import { SearchSettingsPage } from '@/pages/SearchSettingsPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<ApplicationsListPage />} />
      <Route path="/applications/:id" element={<ApplicationDetailPage />} />
      <Route path="/profile" element={<ProfilePage />} />
      <Route path="/search-settings" element={<SearchSettingsPage />} />
    </Routes>
  )
}

export default App
