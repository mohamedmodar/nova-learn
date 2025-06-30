import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Layout from '../components/Layout';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Heart, BookOpen, Clock, Star, ExternalLink } from 'lucide-react';
import CourseCard, { Course } from '../components/shared/CourseCard';
import { toast } from 'sonner';

const Home = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [recommendations, setRecommendations] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchRecommendations = async () => {
    if (!user) return;
    setLoading(true);
    try {
      const token = localStorage.getItem('novalearn_token');
      const response = await fetch('http://localhost:8000/recommendations/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ top_n: 6 }), // Fetch 6 recommendations for the homepage
      });

      if (!response.ok) {
        throw new Error('Failed to fetch recommendations');
      }

      const data = await response.json();
      
      const transformedCourses: Course[] = data.map((c: any) => ({
        ...c,
        id: c.item_id || c.id.toString(),
        course_type: 'external' // Recommendations are currently only external
      }));
      
      setRecommendations(transformedCourses);

    } catch (error) {
      console.error("Failed to fetch recommendations:", error);
      toast.error("Could not load recommendations.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
        fetchRecommendations();
    } else {
        setLoading(false);
    }
  }, [user]);

  const handleCourseClick = (courseId: string, url?: string, isExternal?: boolean) => {
    if (isExternal && url) {
      window.open(url, '_blank');
    } else {
      navigate(`/course/${courseId}`);
    }
  };

  const handleLike = async (courseId: string) => {
    const token = localStorage.getItem('novalearn_token');
    if (!token) {
      toast.error("You must be logged in to like a course.");
      return;
    }
    try {
      const response = await fetch('http://localhost:8000/interactions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ course_id: courseId, interaction_type: 'like' }),
      });
      if (!response.ok) {
        throw new Error("Failed to save like.");
      }
      toast.success("Thanks for your feedback! Updating recommendations...");
      
      // Refresh recommendations after like
      fetchRecommendations();
    } catch (error: any) {
      toast.error(error.message || "Could not save feedback.");
    }
  };

  const handleDislike = async (courseId: string) => {
    const token = localStorage.getItem('novalearn_token');
    if (!token) {
      toast.error("You must be logged in to dislike a course.");
      return;
    }
    try {
      const response = await fetch('http://localhost:8000/interactions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ course_id: courseId, interaction_type: 'dislike' }),
      });
      if (!response.ok) {
        throw new Error("Failed to save dislike.");
      }
      toast.success("Feedback saved! Updating recommendations...");
      
      // Refresh recommendations after dislike
      fetchRecommendations();
    } catch (error: any) {
      toast.error(error.message || "Could not save feedback.");
    }
  };

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
      <div className="space-y-6">
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg p-8 text-white shadow-lg">
          <h1 className="text-3xl font-bold mb-2">Welcome back, {user?.full_name}!</h1>
          <p className="text-blue-100 text-lg">Here are some courses we've picked just for you.</p>
        </div>

        <div className="pt-4">
            <h2 className="text-2xl font-semibold mb-4">Recommended For You</h2>
            {recommendations.length > 0 ? (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {recommendations.map((course) => (
                    <CourseCard 
                        key={course.id} 
                        course={course}
                        onLike={handleLike}
                        onDislike={handleDislike}
                    />
                ))}
                </div>
            ) : (
                <div className="text-center py-12 bg-gray-100 rounded-lg">
                    <p className="text-gray-600">No recommendations available at the moment. Please complete your profile to get personalized suggestions.</p>
                </div>
            )}
        </div>
      </div>
    </Layout>
  );
};

export default Home;