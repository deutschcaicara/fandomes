import { useEffect, useState } from 'react'
import { getAnalytics } from '../services/api'
import type { AnalyticsData } from '../types/analytics'

export const useAnalytics = () => {
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await getAnalytics()
        setData(res)
      } catch (e) {
        setError('Erro ao carregar KPIs')
      } finally {
        setLoading(false)
      }
    }
    fetch()
    const id = setInterval(fetch, 60_000) // refresh 1 min
    return () => clearInterval(id)
  }, [])

  return { data, loading, error }
}
