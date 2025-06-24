
import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Clock, 
  BookOpen, 
  Award, 
  TrendingUp,
  Calendar,
  Play
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface CourseProgress {
  id: string;
  title: string;
  provider: string;
  progress: number;
  totalVideos: number;
  completedVideos: number;
  lastAccessed: string;
  timeSpent: number;
}

const ProgressPage = () => {
  const navigate = useNavigate();
  const [courses, setCourses] = useState<CourseProgress[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalCourses: 0,
    completedCourses: 0,
    totalHours: 0,
    streak: 0
  });

  useEffect(() => {
    const fetchProgress = async () => {
      // Mock API call
      const mockCourses: CourseProgress[] = [
        {
          id: '1',
          title: 'Introduction to Computer Science',
          provider: 'University',
          progress: 65,
          totalVideos: 20,
          completedVideos: 13,
          lastAccessed: '2024-06-20',
          timeSpent: 24
        },
        {
          id: '2',
          title: 'Database Management Systems',
          provider: 'University',
          progress: 30,
          totalVideos: 15,
          completedVideos: 5,
          lastAccessed: '2024-06-18',
          timeSpent: 12
        },
        {
          id: '3',
          title: 'Complete React Developer Course',
          provider: 'Udemy',
          progress: 85,
          totalVideos: 45,
          completedVideos: 38,
          lastAccessed: '2024-06-21',
          timeSpent: 36
        }
      ];

      setCourses(mockCourses);
      setStats({
        totalCourses: mockCourses.length,
        completedCourses: mockCourses.filter(c => c.progress >= 100).length,
        totalHours: mockCourses.reduce((acc, c) => acc + c.timeSpent, 0),
        streak: 7
      });
      setLoading(false);
    };

    fetchProgress();
  }, []);

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
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Your Learning Progress</h1>
          <p className="text-gray-600">Track your learning journey and achievements</p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center">
                <BookOpen className="h-8 w-8 text-blue-600" />
                <div className="ml-4">
                  <p className="text-2xl font-bold">{stats.totalCourses}</p>
                  <p className="text-sm text-gray-600">Active Courses</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center">
                <Award className="h-8 w-8 text-green-600" />
                <div className="ml-4">
                  <p className="text-2xl font-bold">{stats.completedCourses}</p>
                  <p className="text-sm text-gray-600">Completed</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center">
                <Clock className="h-8 w-8 text-purple-600" />
                <div className="ml-4">
                  <p className="text-2xl font-bold">{stats.totalHours}h</p>
                  <p className="text-sm text-gray-600">Time Spent</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center">
                <TrendingUp className="h-8 w-8 text-orange-600" />
                <div className="ml-4">
                  <p className="text-2xl font-bold">{stats.streak}</p>
                  <p className="text-sm text-gray-600">Day Streak</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="active" className="w-full">
          <TabsList>
            <TabsTrigger value="active">Active Courses</TabsTrigger>
            <TabsTrigger value="completed">Completed</TabsTrigger>
          </TabsList>

          <TabsContent value="active" className="space-y-4">
            <div className="grid gap-4">
              {courses.filter(c => c.progress < 100).map((course) => (
                <Card key={course.id} className="hover:shadow-md transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg">{course.title}</CardTitle>
                        <CardDescription className="flex items-center gap-4 mt-1">
                          <Badge variant="secondary">{course.provider}</Badge>
                          <span className="flex items-center gap-1">
                            <Calendar className="h-4 w-4" />
                            Last accessed: {new Date(course.lastAccessed).toLocaleDateString()}
                          </span>
                        </CardDescription>
                      </div>
                      <Button onClick={() => navigate(`/course/${course.id}`)}>
                        <Play className="h-4 w-4 mr-2" />
                        Continue
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <div className="flex justify-between text-sm mb-2">
                          <span>Progress</span>
                          <span>{course.progress}% complete</span>
                        </div>
                        <Progress value={course.progress} className="w-full" />
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
                        <div className="flex items-center gap-2">
                          <BookOpen className="h-4 w-4" />
                          <span>{course.completedVideos}/{course.totalVideos} videos</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Clock className="h-4 w-4" />
                          <span>{course.timeSpent} hours spent</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <TrendingUp className="h-4 w-4" />
                          <span>{Math.round((course.completedVideos / course.totalVideos) * 100)}% completion rate</span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="completed" className="space-y-4">
            <div className="text-center py-12">
              <Award className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No completed courses yet</h3>
              <p className="text-gray-600">Keep learning to see your achievements here!</p>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
};

export default ProgressPage;
