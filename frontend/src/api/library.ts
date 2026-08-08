import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPost } from './client'
import type { LibraryItem } from './types'

function libraryQueryKey(projectPath: string | null) {
  return ['library', projectPath] as const
}

export function useLibrary(projectPath: string | null) {
  return useQuery({
    queryKey: libraryQueryKey(projectPath),
    queryFn: () =>
      apiGet<LibraryItem[]>(
        projectPath ? `/library?project_path=${encodeURIComponent(projectPath)}` : '/library',
      ),
  })
}

export function useSetBookmark(projectPath: string | null) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: { id: string; bookmarked: boolean }) => apiPost('/library/bookmark', input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: libraryQueryKey(projectPath) })
    },
  })
}
