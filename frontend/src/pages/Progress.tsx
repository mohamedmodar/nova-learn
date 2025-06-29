import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { BookOpen, Award } from 'lucide-react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';

interface PlaylistProgress {
  playlist_title: string;
  completed_videos: number;
  total_videos: number;
  playlist_url?: string;
}

const ProgressPage = () => {
  const [playlists, setPlaylists] = useState<PlaylistProgress[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('novalearn_token');
    if (!token) {
      setLoading(false);
      return;
    }

    const fetchProgress = async () => {
      setLoading(true);
      try {
        const response = await fetch('http://localhost:8000/progress/playlists', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        if (!response.ok) {
          throw new Error('Failed to fetch learning progress.');
        }
        const data: PlaylistProgress[] = await response.json();
        setPlaylists(data);
      } catch (error: any) {
        toast.error(error.message || "Could not fetch progress.");
      } finally {
        setLoading(false);
      }
    };

    fetchProgress();
  }, []);

  const activePlaylists = playlists.filter(p => p.completed_videos < p.total_videos);
  const completedPlaylists = playlists.filter(p => p.completed_videos === p.total_videos);

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6 p-4 sm:p-6 lg:p-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Your Learning Progress</h1>
          <p className="text-gray-600">Track your journey through our internal course playlists.</p>
        </div>

        {playlists.length === 0 && !loading && (
           <div className="text-center py-12">
             <BookOpen className="h-16 w-16 text-gray-400 mx-auto mb-4" />
             <h3 className="text-lg font-medium text-gray-900 mb-2">No Progress Yet</h3>
             <p className="text-gray-600">Start an internal course to see your progress here.</p>
           </div>
        )}
        
        {activePlaylists.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-2xl font-semibold">In Progress</h2>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {activePlaylists.map((playlist) => {
                const percentage = playlist.total_videos > 0 ? (playlist.completed_videos / playlist.total_videos) * 100 : 0;
                return (
                  <Link to={`/playlist/${encodeURIComponent(playlist.playlist_title)}`} key={playlist.playlist_title} className="block hover:shadow-lg transition-shadow rounded-lg">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">{playlist.playlist_title}</CardTitle>
                        <CardDescription>
                          {playlist.completed_videos} of {playlist.total_videos} videos completed.
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <Progress value={percentage} className="w-full" />
                        <span className="text-sm text-gray-500 mt-2 block">{Math.round(percentage)}% complete</span>
                      </CardContent>
                    </Card>
                  </Link>
                );
              })}
            </div>
          </div>
        )}

        {completedPlaylists.length > 0 && (
           <div className="space-y-4">
            <h2 className="text-2xl font-semibold">Completed</h2>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {completedPlaylists.map((playlist) => (
                <Link to={`/playlist/${encodeURIComponent(playlist.playlist_title)}`} key={playlist.playlist_title} className="block">
                  <Card className="border-green-500">
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <CardTitle className="text-lg">{playlist.playlist_title}</CardTitle>
                        <Award className="h-6 w-6 text-green-500" />
                      </div>
                      <CardDescription>
                        {playlist.total_videos} of {playlist.total_videos} videos completed.
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                       <Progress value={100} className="w-full" />
                       <span className="text-sm text-green-600 font-semibold mt-2 block">Completed!</span>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default ProgressPage;
