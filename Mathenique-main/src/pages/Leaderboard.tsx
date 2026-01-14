import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import axios from 'axios';
import { Navigation } from '@/components/layout/Navigation';

interface LeaderboardEntry {
  rank: number;
  user_name: string;
  score: number;
  games_won: number;
  games_played: number;
  accuracy: number;
  streak: number;
}

interface UserRank {
  user_rank: number;
  total_players: number;
  user_score: number;
  user_name: string;
}

export default function Leaderboard() {
  const [globalLeaderboard, setGlobalLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [topPlayers, setTopPlayers] = useState<any[]>([]);
  const [userRank, setUserRank] = useState<UserRank | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);

  const itemsPerPage = 10;
  const token = localStorage.getItem('access_token');

  useEffect(() => {
    fetchLeaderboardData();
  }, [page]);

  const fetchLeaderboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const headers = token ? { Authorization: `Bearer ${token}` } : {};

      const [globalRes, topRes, rankRes] = await Promise.all([
        axios.get(
          `${import.meta.env.VITE_API_URL}/leaderboard/global?skip=${page * itemsPerPage}&limit=${itemsPerPage}`,
          { headers }
        ),
        axios.get(`${import.meta.env.VITE_API_URL}/leaderboard/top-10`, { headers }),
        token
          ? axios.get(`${import.meta.env.VITE_API_URL}/leaderboard/my-rank`, { headers })
          : Promise.resolve({ data: null })
      ]);

      setGlobalLeaderboard(globalRes.data);
      setTopPlayers(topRes.data);
      if (rankRes.data) {
        setUserRank(rankRes.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load leaderboard');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getRankBadgeColor = (rank: number) => {
    if (rank === 1) return 'bg-yellow-500';
    if (rank === 2) return 'bg-gray-400';
    if (rank === 3) return 'bg-amber-600';
    return 'bg-blue-500';
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800">
      <Navigation />
      
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Leaderboard</h1>
          <p className="text-slate-300">See how you stack up against other players</p>
        </div>

        {error && (
          <Card className="mb-6 border-red-500 bg-red-50">
            <CardContent className="pt-6">
              <p className="text-red-800">{error}</p>
            </CardContent>
          </Card>
        )}

        {userRank && (
          <Card className="mb-6 bg-gradient-to-r from-purple-600 to-indigo-600 border-none">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between text-white">
                <div>
                  <p className="text-sm opacity-90">Your Rank</p>
                  <p className="text-3xl font-bold">#{userRank.user_rank}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm opacity-90">Your Score</p>
                  <p className="text-3xl font-bold">{userRank.user_score.toLocaleString()}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm opacity-90">Out of</p>
                  <p className="text-3xl font-bold">{userRank.total_players}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <Tabs defaultValue="global" className="w-full">
          <TabsList className="grid w-full grid-cols-2 mb-6">
            <TabsTrigger value="global">Global Rankings</TabsTrigger>
            <TabsTrigger value="top">Top 10</TabsTrigger>
          </TabsList>

          <TabsContent value="top" className="space-y-4">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Top 10 Players</CardTitle>
              </CardHeader>
              <CardContent>
                {topPlayers.length === 0 ? (
                  <p className="text-slate-400 text-center py-8">No leaderboard data yet</p>
                ) : (
                  <div className="space-y-2">
                    {topPlayers.map((player) => (
                      <div
                        key={player.rank}
                        className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg hover:bg-slate-700 transition"
                      >
                        <div className="flex items-center gap-4 flex-1">
                          <Badge className={`${getRankBadgeColor(player.rank)} text-white text-lg w-12 h-12 flex items-center justify-center rounded-full`}>
                            {player.rank}
                          </Badge>
                          <div>
                            <p className="text-white font-semibold">{player.name}</p>
                            <p className="text-slate-400 text-sm">{player.accuracy}% Accuracy</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-white font-bold text-lg">{player.score.toLocaleString()}</p>
                          <p className="text-slate-400 text-sm">points</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="global" className="space-y-4">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">All Players</CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="text-center py-8">
                    <p className="text-slate-400">Loading leaderboard...</p>
                  </div>
                ) : globalLeaderboard.length === 0 ? (
                  <p className="text-slate-400 text-center py-8">No players yet</p>
                ) : (
                  <>
                    <div className="space-y-2">
                      {globalLeaderboard.map((entry) => (
                        <div
                          key={`${entry.rank}-${entry.user_name}`}
                          className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg hover:bg-slate-700 transition"
                        >
                          <div className="flex items-center gap-4 flex-1">
                            <Badge className={`${getRankBadgeColor(entry.rank)} text-white text-lg w-12 h-12 flex items-center justify-center rounded-full`}>
                              {entry.rank}
                            </Badge>
                            <div className="min-w-0">
                              <p className="text-white font-semibold truncate">{entry.user_name}</p>
                              <div className="flex gap-4 text-sm text-slate-400">
                                <span>{entry.games_won}/{entry.games_played} wins</span>
                                <span>{entry.accuracy}% accuracy</span>
                                <span>Streak: {entry.streak}</span>
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-white font-bold text-lg">{entry.score.toLocaleString()}</p>
                            <p className="text-slate-400 text-sm">points</p>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="flex justify-between items-center mt-6 pt-6 border-t border-slate-600">
                      <button
                        onClick={() => setPage(Math.max(0, page - 1))}
                        disabled={page === 0}
                        className="px-4 py-2 bg-slate-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-600 transition"
                      >
                        Previous
                      </button>
                      <p className="text-slate-400">
                        Page {page + 1}
                      </p>
                      <button
                        onClick={() => setPage(page + 1)}
                        disabled={globalLeaderboard.length < itemsPerPage}
                        className="px-4 py-2 bg-slate-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-600 transition"
                      >
                        Next
                      </button>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
