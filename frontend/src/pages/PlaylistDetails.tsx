import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from "@/components/ui/checkbox"
import { ExternalLink, GraduationCap, PlayCircle, ListVideo, Tv, ChevronRight } from 'lucide-react';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { toast } from 'sonner';

interface Video {
  id: number;
  video_title: string;
  video_url: string;
  playlist_title: string;
}

interface VideoProgress {
  video_id: number;
  completed: boolean;
}

const getYoutubeEmbedUrl = (url: string): string | null => {
    if (!url) return null;
    let videoId = '';
    
    if (url.includes('youtube.com/watch?v=')) {
        videoId = url.split('v=')[1].split('&')[0];
    } else if (url.includes('youtu.be/')) {
        videoId = url.split('youtu.be/')[1].split('?')[0];
    } else {
        return null; // Not a supported YouTube URL
    }
    
    return `https://www.youtube.com/embed/${videoId}?autoplay=1`;
};

const PlaylistDetails = () => {
  const { playlistTitle } = useParams<{ playlistTitle: string }>();
  const [videos, setVideos] = useState<Video[]>([]);
  const [currentVideo, setCurrentVideo] = useState<Video | null>(null);
  const [completedVideos, setCompletedVideos] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const decodedTitle = playlistTitle ? decodeURIComponent(playlistTitle) : '';

  useEffect(() => {
    const token = localStorage.getItem('novalearn_token');
    if (!playlistTitle || !token) return;

    const fetchPlaylistData = async () => {
      setLoading(true);
      setError(null);
      try {
        // Fetch videos in the playlist
        const videosResponse = await fetch(`http://localhost:8000/courses/internal/playlist/${playlistTitle}`);
        if (!videosResponse.ok) {
          throw new Error(`Failed to fetch playlist. Status: ${videosResponse.status}`);
        }
        const videosData = await videosResponse.json();
        setVideos(videosData);

        // Set the first video as the current one
        if (videosData.length > 0) {
            setCurrentVideo(videosData[0]);
        }

        // Fetch user's progress
        const progressResponse = await fetch(`http://localhost:8000/progress/videos`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (!progressResponse.ok) {
          throw new Error(`Failed to fetch progress. Status: ${progressResponse.status}`);
        }
        const progressData: VideoProgress[] = await progressResponse.json();
        const completedIds = new Set(progressData.filter(p => p.completed).map(p => p.video_id));
        setCompletedVideos(completedIds);

      } catch (err: any) {
        setError(err.message || 'An unknown error occurred.');
      } finally {
        setLoading(false);
      }
    };

    fetchPlaylistData();
  }, [playlistTitle]);

  const handleProgressChange = async (videoId: number, completed: boolean) => {
    const token = localStorage.getItem('novalearn_token');
    if (!token) {
        toast.error("You must be logged in to update your progress.");
        return;
    }

    // Optimistically update the UI
    const newCompletedVideos = new Set(completedVideos);
    if (completed) {
        newCompletedVideos.add(videoId);
    } else {
        newCompletedVideos.delete(videoId);
    }
    setCompletedVideos(newCompletedVideos);

    try {
        const response = await fetch('http://localhost:8000/progress/videos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({ video_id: videoId, completed }),
        });

        if (!response.ok) {
            throw new Error("Failed to update progress.");
        }
        toast.success("Progress updated!");

    } catch (error: any) {
        toast.error(error.message || "Could not update progress.");
        // Revert optimistic update on failure
        const revertedCompleted = new Set(completedVideos);
        if (completed) {
            revertedCompleted.delete(videoId);
        } else {
            revertedCompleted.add(videoId);
        }
        setCompletedVideos(revertedCompleted);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="text-center p-8">
          <h2 className="text-xl text-red-600">Error</h2>
          <p>{error}</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="grid md:grid-cols-3 gap-8 p-4 sm:p-6 lg:p-8">
        {/* Main Content: Video Player */}
        <div className="md:col-span-2 space-y-6">
            <div className="bg-black rounded-lg aspect-video overflow-hidden shadow-2xl">
                {currentVideo ? (
                    <iframe
                        width="100%"
                        height="100%"
                        src={getYoutubeEmbedUrl(currentVideo.video_url) || ''}
                        title="YouTube video player"
                        frameBorder="0"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowFullScreen
                    ></iframe>
                ) : (
                    <div className="w-full h-full bg-gray-900 flex flex-col items-center justify-center text-white">
                        <Tv className="h-16 w-16 mb-4" />
                        <h3 className="text-xl">Select a video to play</h3>
                    </div>
                )}
            </div>
            
            <div>
              <h1 className="text-3xl font-bold">{currentVideo?.video_title || decodedTitle}</h1>
              <p className="text-lg text-gray-600 mt-1">Playlist: {decodedTitle}</p>
            </div>
        </div>

        {/* Sidebar: Playlist */}
        <div className="md:col-span-1">
            <Card>
                <CardHeader>
                    <div className="flex items-center space-x-2">
                        <ListVideo className="h-6 w-6" />
                        <CardTitle>Playlist Videos ({videos.length})</CardTitle>
                    </div>
                </CardHeader>
                <CardContent className="space-y-2">
                    {videos.map((video) => (
                        <div 
                            key={video.id} 
                            onClick={() => setCurrentVideo(video)}
                            className={`p-3 rounded-md cursor-pointer transition-colors ${
                                currentVideo?.id === video.id ? 'bg-blue-100' : 'hover:bg-gray-100'
                            }`}
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-3">
                                    <PlayCircle className={`h-5 w-5 ${currentVideo?.id === video.id ? 'text-blue-600' : 'text-gray-500'}`} />
                                    <span className={`font-medium ${currentVideo?.id === video.id ? 'text-blue-700' : ''}`}>
                                        {video.video_title}
                                    </span>
                                </div>
                                {currentVideo?.id === video.id && <ChevronRight className="h-5 w-5 text-blue-600"/>}
                            </div>
                            <div className="pl-8 pt-2">
                                <div className="flex items-center space-x-2" onClick={(e) => e.stopPropagation()}>
                                    <Checkbox
                                        id={`progress-${video.id}`}
                                        checked={completedVideos.has(video.id)}
                                        onCheckedChange={(checked) => handleProgressChange(video.id, !!checked)}
                                    />
                                    <label htmlFor={`progress-${video.id}`} className="text-sm font-medium text-gray-600">
                                        Mark as Completed
                                    </label>
                                </div>
                            </div>
                        </div>
                    ))}
                </CardContent>
            </Card>
        </div>
      </div>
    </Layout>
  );
};

export default PlaylistDetails; 