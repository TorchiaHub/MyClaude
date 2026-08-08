import { useMemo, useState } from 'react'
import { useLibrary, useSetBookmark } from '../api/library'
import { ProjectSelector } from '../components/ProjectSelector'
import { useNavigationStore } from '../store/navigationStore'
import type { LibraryItem } from '../api/types'

function useFolders(items: LibraryItem[]) {
  return useMemo(() => {
    const folders = new Set<string>()
    for (const item of items) {
      folders.add(item.folder || '(radice)')
    }
    return ['Tutte', ...Array.from(folders).sort()]
  }, [items])
}

function useTags(items: LibraryItem[]) {
  return useMemo(() => {
    const tags = new Set<string>()
    for (const item of items) {
      for (const tag of item.tags) tags.add(tag)
    }
    return Array.from(tags).sort()
  }, [items])
}

export function Library() {
  const selectedProjectPath = useNavigationStore((state) => state.selectedProjectPath)
  const { data: items, isLoading, error } = useLibrary(selectedProjectPath)
  const setBookmark = useSetBookmark(selectedProjectPath)

  const [selectedFolder, setSelectedFolder] = useState('Tutte')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [showBookmarkedOnly, setShowBookmarkedOnly] = useState(false)

  const folders = useFolders(items ?? [])
  const tags = useTags(items ?? [])

  const filteredItems = useMemo(() => {
    if (!items) return []
    return items.filter((item) => {
      const itemFolder = item.folder || '(radice)'
      if (selectedFolder !== 'Tutte' && itemFolder !== selectedFolder) return false
      if (selectedTags.length > 0 && !selectedTags.every((tag) => item.tags.includes(tag)))
        return false
      if (showBookmarkedOnly && !item.bookmarked) return false
      return true
    })
  }, [items, selectedFolder, selectedTags, showBookmarkedOnly])

  function toggleTag(tag: string) {
    setSelectedTags((prev) => (prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]))
  }

  return (
    <div className="panel">
      <header className="panel-header">
        <h2>Library & Organization</h2>
        <ProjectSelector />
      </header>

      {isLoading && <p>Caricamento libreria…</p>}
      {error && <p role="alert">Errore nel caricamento della libreria.</p>}

      {items && (
        <div className="library-layout">
          <aside className="library-filters">
            <h4>Cartelle</h4>
            <ul className="folder-tree">
              {folders.map((folder) => (
                <li key={folder}>
                  <button
                    type="button"
                    className={folder === selectedFolder ? 'active' : ''}
                    onClick={() => setSelectedFolder(folder)}
                  >
                    {folder}
                  </button>
                </li>
              ))}
            </ul>

            <h4>Tag</h4>
            <div className="tag-filter">
              {tags.map((tag) => (
                <label key={tag}>
                  <input
                    type="checkbox"
                    checked={selectedTags.includes(tag)}
                    onChange={() => toggleTag(tag)}
                  />
                  {tag}
                </label>
              ))}
            </div>

            <label>
              <input
                type="checkbox"
                checked={showBookmarkedOnly}
                onChange={(e) => setShowBookmarkedOnly(e.target.checked)}
              />
              Solo preferiti
            </label>
          </aside>

          <ul className="library-items">
            {filteredItems.length === 0 && <p className="empty">Nessuna risorsa trovata</p>}
            {filteredItems.map((item) => (
              <li key={item.id} className="library-item">
                <div className="library-item-header">
                  <span className="resource-type">{item.resource_type}</span>
                  <strong>{item.name}</strong>
                  <button
                    type="button"
                    className="bookmark-toggle"
                    aria-label={item.bookmarked ? 'Rimuovi dai preferiti' : 'Aggiungi ai preferiti'}
                    onClick={() =>
                      setBookmark.mutate({ id: item.id, bookmarked: !item.bookmarked })
                    }
                  >
                    {item.bookmarked ? '★' : '☆'}
                  </button>
                </div>
                <p className="description">{item.description}</p>
                {item.tags.length > 0 && (
                  <div className="item-tags">
                    {item.tags.map((tag) => (
                      <span key={tag} className="tag-chip">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
