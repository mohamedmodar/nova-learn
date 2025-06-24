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

interface Course {
  id: string;
  title: string;
  description: string;
  provider: string;
  level: string;
  rating: number;
  adjustedRating: number;
  duration: string;
  skills: string[];
  progress?: number;
  isExternal?: boolean;
}

const Home = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [internalCourses, setInternalCourses] = useState<Course[]>([]);
  const [externalCourses, setExternalCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user needs onboarding
    if (!user?.hasCompletedOnboarding) {
      navigate('/onboarding');
      return;
    }

    // Mock API calls to fetch courses
    const fetchCourses = async () => {
      // Mock internal courses
      const mockInternalCourses: Course[] = [
        {
          id: '1',
          title: 'Introduction to Computer Science',
          description: 'Fundamental concepts of programming and computer science',
          provider: 'University',
          level: 'Beginner',
          rating: 4.5,
          adjustedRating: 4.5,
          duration: '12 weeks',
          skills: ['Programming', 'Algorithms', 'Data Structures'],
          progress: 65
        },
        {
          id: '2',
          title: 'Database Management Systems',
          description: 'Learn SQL and database design principles',
          provider: 'University',
          level: 'Intermediate',
          rating: 4.2,
          adjustedRating: 4.2,
          duration: '10 weeks',
          skills: ['SQL', 'Database Design', 'Data Modeling'],
          progress: 30
        }
      ];

      // Mock external recommendations
      const mockExternalCourses: Course[] = [
        {
          id: '3',
          title: 'Complete React Developer Course',
          description: 'Build modern web applications with React, Redux, and more',
          provider: 'Udemy',
          level: 'Intermediate',
          rating: 4.6,
          adjustedRating: 4.8,
          duration: '40 hours',
          skills: ['React', 'JavaScript', 'Redux', 'Web Development'],
          isExternal: true
        },
        {
          id: '4',
          title: 'Python for Data Science',
          description: 'Master Python programming for data analysis and visualization',
          provider: 'Coursera',
          level: 'Beginner',
          rating: 4.4,
          adjustedRating: 4.6,
          duration: '6 weeks',
          skills: ['Python', 'Data Analysis', 'Pandas', 'NumPy'],
          isExternal: true
        },
        {
          id: '5',
          title: 'Machine Learning A-Z',
          description: 'Hands-on machine learning with Python and R',
          provider: 'Udemy',
          level: 'Advanced',
          rating: 4.5,
          adjustedRating: 4.7,
          duration: '44 hours',
          skills: ['Machine Learning', 'Python', 'Statistics', 'AI'],
          isExternal: true
        }
      ];

      setInternalCourses(mockInternalCourses);
      setExternalCourses(mockExternalCourses);
      setLoading(false);
    };

    fetchCourses();
  }, [user, navigate]);

  const handleCourseClick = (courseId: string) => {
    navigate(`/course/${courseId}`);
  };

  const handleLike = (courseId: string) => {
    console.log('Liked course:', courseId);
    // API call to save interaction
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
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg p-6 text-white">
          <h1 className="text-2xl font-bold mb-2">Welcome back, {user?.name}!</h1>
          <p className="text-blue-100">Continue your learning journey with personalized recommendations</p>
        </div>

        <Tabs defaultValue={user?.isStudent ? "internal" : "external"} className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            {/* Removed the conditional rendering for Internal Courses TabTrigger */}
            <TabsTrigger value="internal">Internal Courses</TabsTrigger>
            <TabsTrigger value="external">Recommendations</TabsTrigger>
          </TabsList>

          {/* Removed the conditional rendering for Internal Courses TabsContent */}
          <TabsContent value="internal" className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">Your University Courses</h2>
              <Button variant="outline" onClick={() => navigate('/progress')}>
                View All Progress
              </Button>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              {internalCourses.map((course) => (
                <Card key={course.id} className="hover:shadow-md transition-shadow cursor-pointer">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg">{course.title}</CardTitle>
                        <CardDescription>{course.description}</CardDescription>
                      </div>
                      <Badge variant="secondary">{course.level}</Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex flex-wrap gap-2">
                        {course.skills.slice(0, 3).map((skill) => (
                          <Badge key={skill} variant="outline" className="text-xs">
                            {skill}
                          </Badge>
                        ))}
                      </div>

                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>Progress</span>
                          <span>{course.progress}%</span>
                        </div>
                        <Progress value={course.progress || 0} className="w-full" />
                      </div>

                      <div className="flex items-center justify-between pt-2">
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          <div className="flex items-center gap-1">
                            <Clock className="h-4 w-4" />
                            {course.duration}
                          </div>
                          <div className="flex items-center gap-1">
                            <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                            {course.rating}
                          </div>
                        </div>
                        <Button onClick={() => handleCourseClick(course.id)}>
                          Continue
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="external" className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">Recommended for You</h2>
              <Button variant="outline" onClick={() => navigate('/search')}>
                Explore More
              </Button>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {externalCourses.map((course) => (
                <Card key={course.id} className="hover:shadow-md transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg">{course.title}</CardTitle>
                        <CardDescription className="line-clamp-2">{course.description}</CardDescription>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleLike(course.id)}
                        className="text-gray-400 hover:text-red-500"
                      >
                        <Heart className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between text-sm">
                        <Badge variant="secondary">{course.provider}</Badge>
                        <Badge>{course.level}</Badge>
                      </div>

                      <div className="flex flex-wrap gap-1">
                        {course.skills.slice(0, 4).map((skill) => (
                          <Badge key={skill} variant="outline" className="text-xs">
                            {skill}
                          </Badge>
                        ))}
                      </div>

                      <div className="flex items-center justify-between pt-2">
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          <div className="flex items-center gap-1">
                            <Clock className="h-4 w-4" />
                            {course.duration}
                          </div>
                          <div className="flex items-center gap-1">
                            <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                            {course.adjustedRating}
                          </div>
                        </div>
                        <Button
                          onClick={() => handleCourseClick(course.id)}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          <ExternalLink className="h-4 w-4 mr-1" />
                          Enroll
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
};

export default Home;